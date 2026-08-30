# langgraph_logic.py
"""
AI Diagnostic Assistant — LangGraph State Machine
--------------------------------------------------
- PatientState gains an `interview_state` field (the persistent memory object)
- Question generation is batched: the system queues 3-4 clinically relevant
  follow-ups in one LLM call and asks them sequentially, instead of invoking
  the LLM after every individual patient reply.
- The patient reply is stored directly in the transcript; no per-reply memory
  extraction LLM pass is used for routine interview tracking.
- `ask_one_question_node` pulls from a queue, checks semantic duplicates, and
  respects MAX_TURNS.
- All specialist nodes inject `memory_context` into their prompts.
- `decide_if_chat_needed` and `decide_to_continue_chat` are updated accordingly.
"""

import json
import os
import uuid
from typing import Any, Dict, List, Optional, TypedDict, cast

import fitz  # PyMuPDF
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from utils.rag import retrieve_medical_context
from utils.interview_memory import (
    MAX_TURNS,
    build_memory_context_block,
    is_duplicate_question,
    make_interview_state,
    register_question,
    should_force_terminate,
    update_confidence,
)
from utils.llm import (
    cardiology_llm,
    dermatology_llm,
    general_medicine_llm,
    lab_report_llm,
    llm,
    triage_llm,
    small_llm
)
from utils.pdf_generator import create_pdf_report
from utils.prompts import (
    batch_question_prompt,
    cardiology_prompt,
    dermatology_prompt,
    general_medicine_prompt,
    intake_prompt,
    lab_prompt,
    medical_report_prompt,
    question_refinement_prompt,
    triage_router_prompt,
)

load_dotenv()


# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------

class PatientState(TypedDict, total=False):
    raw_input: Dict[str, Any]
    structured_input: Dict[str, Any]
    messages: List[Dict[str, Any]]
    interview_state: Dict[str, Any]
    pending_question: Optional[str]
    diagnosis_path: str
    final_analysis: Dict[str, Any]
    report_path: str
    analysis_history: List[Dict[str, Any]]
    report_json_path: str
    retrieved_context: str
    red_flags: List[str]
    patient_profile: Dict[str, Any]

def format_patient_profile(profile: Optional[Dict[str, Any]]) -> str:
    """Formats the patient profile dictionary into a readable string for the LLM prompt."""
    if not profile:
        return "No permanent profile found."
    return f"""
    Name: {profile.get('name', 'Unknown')}
    Age: {profile.get('age', 'Unknown')}
    Gender: {profile.get('gender', 'Unknown')}
    Blood Group: {profile.get('blood_group', 'Unknown')}
    Pre-existing Conditions: {profile.get('pre_existing_conditions', 'None')}
    Family History: {profile.get('family_history', 'None')}
    Prescriptions: {profile.get('prescriptions', 'None')}
    """


# ---------------------------------------------------------------------------
# Utility: PDF text extraction & lab report summarisation
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text from a given PDF file using PyMuPDF."""
    if not os.path.exists(pdf_path):
        return "File not found."
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text("text") for page in doc).strip()


def summarize_lab_report(pdf_path: str) -> Dict[str, Any]:
    """Uses an LLM to generate a summary of the extracted lab report text."""
    text = extract_text_from_pdf(pdf_path)
    if text == "File not found.":
        return {"error": "Lab report file not found."}
    chain = lab_prompt | lab_report_llm
    summary = chain.invoke({"report_text": text}).content
    return {"summary": summary}

# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------

def retrieve_context_node(state: PatientState) -> Dict[str, Any]:
    """Retrieves relevant medical guidelines (RAG) based on symptoms and extracted facts."""
    print("--- 📚 RETRIEVING SPECIALTY GUIDELINES (RAG) ---")
    specialty = state.get("diagnosis_path", "general_medicine")

    # 1. Get the raw initial symptoms
    base_symptoms = state.get("raw_input", {}).get("symptoms", "")

    # 2. Include dynamically gathered replies in the retrieval query
    interview_state = state.get("interview_state", {})
    known_facts = interview_state.get("known_facts", {})
    patient_replies = interview_state.get("patient_replies", [])

    # 3. Build a highly contextual query string for ChromaDB
    # e.g., "chest pain. fever_duration: 3 days, pain_level: 7/10"
    facts_string = ", ".join([f"{k}: {v}" for k, v in known_facts.items()])
    replies_string = "; ".join(
        f"{item.get('question', '')} {item.get('reply', '')}"
        for item in patient_replies
    )
    enhanced_query = f"{base_symptoms}. {facts_string}. {replies_string}".strip()

    print(f"--- SEARCH: Enhanced RAG Query: {enhanced_query} ---")

    # 4. Retrieve targeted docs using the enhanced query
    context = retrieve_medical_context(enhanced_query, specialty)

    return {"retrieved_context": context}

# ---------------------------------------------------------------------------
# Helper: clean JSON from LLM output
# ---------------------------------------------------------------------------

def _clean_and_parse(raw: str) -> Dict[str, Any]:
    """Strips markdown formatting from the LLM output and parses it into a JSON dictionary."""
    raw = raw.strip()
    # Strip common markdown fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()
    return json.loads(raw)


def _conversation_history_text(messages: List[Dict[str, Any]], max_messages: int = 0) -> str:
    """Formats the conversation messages into a plain text transcript."""
    msgs_to_process = messages[-max_messages:] if max_messages > 0 else messages
    return "\n".join(
        f"{msg['role'].upper()}: {msg['content']}" for msg in msgs_to_process
    )


def summarize_and_replace_history(
    summarizer_llm: Any,
    history: List[Dict[str, Any]],
    summary_prompt: Optional[str] = None,
    max_summary_sentences: int = 5,
) -> str:
    """Compress a long chat history into a short clinical summary."""
    if not history:
        return ""

    if summary_prompt is None:
        summary_prompt = (
            "Summarize the following patient interview transcript into 3-5 concise sentences. "
            "Keep all clinically relevant facts: symptoms, onset, severity, duration, risk factors, "
            "medications, past history, and any unanswered questions. Do not invent new information."
        )

    transcript = _conversation_history_text(history)
    try:
        response = summarizer_llm.invoke(f"{summary_prompt}\n\nTRANSCRIPT:\n{transcript}")
        summary = getattr(response, "content", str(response)).strip()
        if summary:
            return summary
    except Exception as e:
        print(f"--- ERROR summarizing interview history: {e}. ---")

    # Fallback: keep the most recent turns rather than dropping the whole history.
    return _conversation_history_text(history, max_messages=8)


# ---------------------------------------------------------------------------
# Node 1: Preprocess
# ---------------------------------------------------------------------------

def preprocess_node(state: PatientState) -> Dict[str, Any]:
    """Initializes the interview state and uses an LLM to structure the raw patient intake data."""
    print("--- DOC: PREPROCESSING INITIAL DATA ---")
    raw = state.get("raw_input", {})
    messages = state.get("messages", [])
    messages.append(
        {"role": "human", "content": f"Patient provided input:\n{json.dumps(raw, indent=2)}"}
    )

    vitals = raw.get("vitals") or {}
    patient_profile_text = format_patient_profile(state.get("patient_profile"))
    chain = intake_prompt | small_llm
    llm_response = chain.invoke({
        "patient_profile": patient_profile_text,
        "patient_data": json.dumps(raw),
        "temperature": vitals.get("temperature", ""),
        "bp": vitals.get("bp", ""),
        "pulse": vitals.get("pulse", ""),
        "spo2": vitals.get("spo2", ""),
    })
    messages.append({"role": "ai", "content": llm_response.content})

    try:
        structured_input = _clean_and_parse(llm_response.content)
    except Exception as e:
        structured_input = {"raw_llm_output": llm_response.content, "parsing_error": str(e)}

    # Initialise a fresh interview state
    interview_state = make_interview_state()

    # Pre-populate known facts from the raw vitals / symptoms
    vitals_facts = {k: v for k, v in vitals.items() if v}
    if vitals_facts:
        interview_state["known_facts"]["vitals"] = vitals_facts
    if raw.get("symptoms"):
        interview_state["known_facts"]["initial_complaint"] = raw["symptoms"]

    # If the patient uploaded no files, mark lab/health records as unavailable
    # upfront so the LLM never wastes turns asking for them. The specialist
    # will instead recommend what tests to get rather than requesting them.
    files = raw.get("files", {})
    if not files.get("lab_report"):
        interview_state["unavailable_information"].append("lab_reports")
    if not files.get("health_record"):
        interview_state["unavailable_information"].append("previous_health_records")

    return {
        "structured_input": structured_input,
        "messages": messages,
        "interview_state": interview_state,
    }


# ---------------------------------------------------------------------------
# Node 2: Process Lab Reports
# ---------------------------------------------------------------------------

def process_all_lab_reports_node(state: PatientState) -> Dict[str, Any]:
    """Processes and summarizes all uploaded lab reports, updating the structured input."""
    print("--- FILE: PROCESSING LAB REPORTS ---")
    files = state.get("raw_input", {}).get("files", {})
    lab_results: Dict[str, Any] = {}

    if not files:
        # No files uploaded — explicitly flag this so specialists know to
        # recommend tests rather than wait for lab data.
        print("--- No files uploaded. Marking lab_results as not provided. ---")
        lab_results = {"_status": "not_provided",
                       "_note": "Patient did not upload any lab reports or health records."}
    else:
        # If multiple files are present, batch-summarize them in one LLM call to save repeated token overhead.
        if len(files) > 1:
            try:
                # Build a concatenated text with filename markers so the LLM can return per-file summaries
                combined_parts = []
                for report_name, file_path in files.items():
                    text = extract_text_from_pdf(file_path)
                    combined_parts.append(f"===REPORT:{report_name}===\n{text}\n")
                combined_text = "\n\n".join(combined_parts)
                chain = lab_prompt | lab_report_llm
                # Ask the LLM to return a JSON mapping {"report_name": {"summary": "..."}, ...}
                prompt_input = {"report_text": combined_text}
                response = chain.invoke(prompt_input)
                raw = response.content
                # Attempt to parse JSON from LLM output; fall back to per-file summarize if parsing fails
                try:
                    parsed = json.loads(raw)
                    # Expecting dict-like mapping
                    if isinstance(parsed, dict):
                        lab_results = parsed
                    else:
                        raise ValueError("Parsed response not a dict")
                except Exception:
                    # Parsing failed — fallback to per-file summarization
                    lab_results = {}
                    for report_name, file_path in files.items():
                        try:
                            lab_results[report_name] = summarize_lab_report(file_path)
                        except Exception as e:
                            lab_results[report_name] = {"error": str(e)}
            except Exception as e:
                print(f"--- ERROR batching lab summaries: {e}. Falling back to per-file. ---")
                lab_results = {}
                for report_name, file_path in files.items():
                    try:
                        lab_results[report_name] = summarize_lab_report(file_path)
                    except Exception as e:
                        lab_results[report_name] = {"error": str(e)}
        else:
            # Single file — keep existing behavior
            lab_results = {}
            for report_name, file_path in files.items():
                try:
                    lab_results[report_name] = summarize_lab_report(file_path)
                except Exception as e:
                    lab_results[report_name] = {"error": str(e)}

    structured_input = state.get("structured_input", {}).copy()
    structured_input["lab_results"] = lab_results
    structured_input["has_lab_data"] = bool(files)  # handy flag for prompts
    return {"structured_input": structured_input}


# ---------------------------------------------------------------------------
# Node 3: Refine Questions  (optional; still used if labs are present)
# ---------------------------------------------------------------------------

def refine_questions_node(state: PatientState) -> Dict[str, Any]:
    """Refines the initial missing information questions based on the lab report summaries."""
    print("--- 🧠 REFINING QUESTIONS BASED ON LABS ---")
    structured_input = state.get("structured_input", {})
    initial_questions = structured_input.get("missing_information", [])
    lab_summary = structured_input.get("lab_results", {})
    interview_state = state.get("interview_state", make_interview_state())

    if not lab_summary or not initial_questions:
        print("--- No labs or initial questions to refine. Skipping. ---")
        return {}

    memory_context = build_memory_context_block(interview_state)
    chain = question_refinement_prompt | small_llm
    llm_response = chain.invoke({
        "initial_questions": json.dumps(initial_questions),
        "lab_summary": json.dumps(lab_summary),
        "memory_context": memory_context,
    })
    try:
        response_json = _clean_and_parse(llm_response.content)
        refined = response_json.get("refined_questions", initial_questions)
        updated = structured_input.copy()
        updated["missing_information"] = refined
        print(f"--- Questions refined. Count: {len(refined)} ---")
        return {"structured_input": updated}
    except Exception as e:
        print(f"--- ERROR: Failed to parse refined questions ({e}). Keeping originals. ---")
        return {}


# ---------------------------------------------------------------------------
# Batch question generation and patient-reply pause
# ---------------------------------------------------------------------------

def generate_question_batch(state: PatientState, interview_state: Dict[str, Any]) -> List[str]:
    """Generate a short queue of relevant follow-up questions in one LLM call."""
    messages = state.get("messages", [])
    structured_input = state.get("structured_input", {})

    if should_force_terminate(interview_state):
        return []

    memory_context = build_memory_context_block(interview_state)
    patient_profile_text = format_patient_profile(state.get("patient_profile"))

    # Reduce conversation history size to save tokens:
    # - If very long, summarize using the small_llm once (costs 1 call but reduces future tokens)
    # - Otherwise, trim to the recent N turns
    convo_len = len(messages)
    if convo_len > 20:
        # Summarize long history into 3-5 sentences
        try:
            summary = summarize_and_replace_history(summarizer_llm=small_llm, history=messages,
                                                    summary_prompt=None)
            conversation_history = summary
        except Exception:
            conversation_history = _conversation_history_text(messages, max_messages=8)
    else:
        # Trim to recent 8 messages by default
        conversation_history = _conversation_history_text(messages, max_messages=8)

    chain = batch_question_prompt | small_llm
    llm_response = chain.invoke({
        "patient_profile": patient_profile_text,
        "memory_context": memory_context,
        "structured_data": json.dumps(structured_input, indent=2),
        "conversation_history": conversation_history,
    })

    try:
        response_json = _clean_and_parse(llm_response.content)
    except Exception as e:
        print(f"--- ERROR parsing batch question response: {e}. ---")
        return []

    questions = response_json.get("questions", [])
    if not isinstance(questions, list):
        return []

    valid_questions: List[str] = []
    seen = set()
    for question in questions:
        candidate = str(question).strip()
        if not candidate:
            continue
        normalized = candidate.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        is_dup, _ = is_duplicate_question(candidate, interview_state)
        if is_dup:
            continue
        valid_questions.append(candidate)

    return valid_questions[:4]


def await_patient_reply_node(state: PatientState) -> Dict[str, Any]:
    """No-op node used as the checkpoint boundary before the next queued question."""
    return {}


# ---------------------------------------------------------------------------
# Node 5: Ask One Queued Question (batched, dedup-aware)
# ---------------------------------------------------------------------------

def ask_one_question_node(state: PatientState) -> Dict[str, Any]:
    """
    Pull the next question from the pre-generated queue. If the queue is empty,
    generate a new 3-4 question batch in a single LLM call.
    """
    print("--- ❓ GENERATING / PULLING NEXT QUESTION ---")
    messages = state.get("messages", [])
    interview_state = state.get("interview_state", make_interview_state()).copy()

    if should_force_terminate(interview_state):
        print("--- MAX_TURNS reached. Forcing termination. ---")
        return {"pending_question": None, "interview_state": interview_state}

    pending_questions = list(interview_state.get("pending_questions", []))
    if not pending_questions:
        pending_questions = generate_question_batch(state, interview_state)
        interview_state["pending_questions"] = pending_questions

    if not pending_questions:
        print("--- No queued questions available. Ending interview. ---")
        return {"pending_question": None, "interview_state": interview_state}

    question = pending_questions[0]
    remaining_questions = pending_questions[1:]
    interview_state["pending_questions"] = remaining_questions

    # If the LLM somehow generated a duplicate, skip it and keep moving through the queue.
    is_dup, sim = is_duplicate_question(question, interview_state)
    if is_dup:
        print(f"--- Duplicate question suppressed (similarity={sim:.2f}). Trying next queued item. ---")
        if remaining_questions:
            interview_state["pending_questions"] = remaining_questions[1:]
            question = remaining_questions[0]
        else:
            return {"pending_question": None, "interview_state": interview_state}

    interview_state = register_question(question, interview_state)
    messages = list(messages)
    messages.append({"role": "ai", "content": question})

    print(f"--- ❓ ASKING: {question} ---")
    return {
        "pending_question": question,
        "messages": messages,
        "interview_state": interview_state,
    }


# ---------------------------------------------------------------------------
# Node 6: Triage Router
# ---------------------------------------------------------------------------

def triage_router_node(state: PatientState) -> Dict[str, Any]:
    """Routes the patient to the appropriate medical specialist based on their primary complaint."""
    print("--- 📧 TRIAGE ROUTER ---")
    initial_status = {
        "status": "pending",
        "condition": "Waiting for AI Specialist Analysis...",
        "confidence": 0,
        "reasoning": "The system is routing the case to the appropriate specialist.",
        "evidence": [],
        "urgency": "low",
    }
    primary_complaint = state.get("raw_input", {}).get("symptoms", "")
    chain = triage_router_prompt | triage_llm
    llm_response = chain.invoke({"primary_complaint": primary_complaint})
    try:
        route_json = _clean_and_parse(llm_response.content)
        department = route_json.get("department", "general_medicine")
    except Exception:
        department = "general_medicine"
    print(f"--- Routing to {department} ---")
    return {"diagnosis_path": department, "analysis_history": [initial_status]}


# ---------------------------------------------------------------------------
# Node 7: Specialist Analysis  (memory-aware)
# ---------------------------------------------------------------------------

def run_specialist_analysis(
    state: PatientState,
    specialist_prompt,
    specialist_llm,
) -> Dict[str, Any]:
    """Runs a specialist LLM to analyze the gathered patient data and interview facts."""
    interview_state = state.get("interview_state", make_interview_state())
    memory_context = build_memory_context_block(interview_state)
    structured_data = json.dumps(state.get("structured_input", {}), indent=2)
    conversation_history = _conversation_history_text(state.get("messages", []))

    retrieved_context = state.get("retrieved_context", "No additional guidelines retrieved.")
    red_flags = "\n".join(state.get("red_flags", ["None detected"]))
    patient_profile_text = format_patient_profile(state.get("patient_profile"))

    messages = specialist_prompt.build_messages(
        memory_context=memory_context,
        red_flags=red_flags,
        retrieved_context=retrieved_context,
        patient_profile=patient_profile_text,
        structured_data=structured_data,
        conversation_history=conversation_history,
    )
    llm_response = specialist_llm.invoke(messages)

    try:
        response_json = _clean_and_parse(llm_response.content)
    except Exception as e:
        print(f"--- ERROR in specialist analysis: {e} ---")
        response_json = {"error": "Failed to parse analysis.", "raw_output": llm_response.content}

    analysis_history = list(state.get("analysis_history", []))
    analysis_history.append(response_json)
    updates: Dict[str, Any] = {
        "final_analysis": response_json,
        "analysis_history": analysis_history,
    }

    if response_json.get("status") == "incomplete":
        print("--- MED: SPECIALIST REQUIRES MORE INFORMATION ---")
        updated_structured = state.get("structured_input", {}).copy()
        updated_structured["missing_information"] = response_json.get("missing_information", [])
        updates["structured_input"] = updated_structured

        # Update interview_state stage so it doesn't loop forever
        updated_interview = interview_state.copy()
        updated_interview = update_confidence(updated_interview, specialist_status="incomplete")
        updates["interview_state"] = updated_interview
    else:
        print("--- DONE: SPECIALIST ANALYSIS COMPLETE ---")
        updated_interview = interview_state.copy()
        updated_interview = update_confidence(updated_interview, specialist_status="complete")
        updates["interview_state"] = updated_interview

    return updates


def general_medicine_analysis_node(state: PatientState) -> Dict[str, Any]:
    """Executes the General Medicine specialist analysis."""
    print("--- MED: GENERAL MEDICINE ANALYSIS ---")
    return run_specialist_analysis(state, general_medicine_prompt, general_medicine_llm)


def cardiology_analysis_node(state: PatientState) -> Dict[str, Any]:
    """Executes the Cardiology specialist analysis."""
    print("--- MED: CARDIOLOGY ANALYSIS ---")
    return run_specialist_analysis(state, cardiology_prompt, cardiology_llm)


def dermatology_analysis_node(state: PatientState) -> Dict[str, Any]:
    """Executes the Dermatology specialist analysis."""
    print("--- MED: DERMATOLOGY ANALYSIS ---")
    return run_specialist_analysis(state, dermatology_prompt, dermatology_llm)


# ---------------------------------------------------------------------------
# Node 8: Generate Report
# ---------------------------------------------------------------------------

def generate_report_node(state: PatientState) -> Dict[str, str]:
    """Compiles all data into a final Medical Report, saves it to a JSON file, and generates a PDF."""
    print("--- ✍️ GENERATING FINAL CLINICIAN REPORT ---")
    structured_input = state.get("structured_input", {})
    has_lab_data = structured_input.get("has_lab_data", False)
    report_data = {
        "raw_input": state.get("raw_input"),
        "patient_profile": state.get("patient_profile", {}),
        "final_analysis": state.get("final_analysis", {}),
        "lab_results": structured_input.get("lab_results"),
        "has_lab_data": has_lab_data,
        "interview_summary": {
            "known_facts": state.get("interview_state", {}).get("known_facts", {}),
            "unavailable_information": state.get("interview_state", {}).get("unavailable_information", []),
            "total_turns": state.get("interview_state", {}).get("turn_count", 0),
            "final_confidence": state.get("interview_state", {}).get("confidence_score", 0.0),
        },
    }

    os.makedirs("generated_reports", exist_ok=True)
    report_id = str(uuid.uuid4())
    base_path = f"generated_reports/summary_{report_id}.pdf"
    json_file_path = f"generated_reports/summary_{report_id}.json"

    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)
    print(f"--- 💾 Report data saved to {json_file_path} ---")

    final_json_data = json.dumps(report_data, indent=2)
    report_chain = medical_report_prompt | llm
    markdown_report = report_chain.invoke({"final_json_data": final_json_data}).content
    final_pdf_path = create_pdf_report(markdown_report, filename=base_path)

    return {
        "report_path": final_pdf_path,
        "report_json_path": json_file_path,
    }


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def decide_if_chat_needed(state: PatientState) -> str:
    """
    Always start the dynamic interview — ask_one_question_node uses the LLM
    to decide when enough information has been gathered (status: "sufficient").
    We no longer gate on missing_information because that list only reflects
    what the intake prompt flagged; the dynamic interviewer may surface more.
    """
    print("--- 🤔 CHAT NEEDED? Always yes — starting dynamic interview. ---")
    return "start_chat"


def decide_to_continue_chat(state: PatientState) -> str:
    """
    After ask_one_question: continue if a pending_question was set,
    otherwise move to triage.
    """
    print("--- 🤔 CONTINUE CHAT? ---")
    if state.get("pending_question"):
        print("--- ROUTING TO: interrupt (waiting for human reply) ---")
        return "continue_chat"
    print("--- ROUTING TO: triage_router ---")
    return "end_chat"


def route_to_specialist(state: PatientState) -> str:
    """Returns the determined specialist path for conditional routing."""
    return cast(str, state.get("diagnosis_path", "general_medicine"))


def decide_after_analysis(state: PatientState) -> str:
    """
    After specialist: loop back for more questions only if:
    - status == "incomplete"
    - AND we have new missing_information
    - AND we haven't hit MAX_TURNS
    """
    print("--- 🤔 REVIEWING SPECIALIST ANALYSIS ---")
    interview_state = state.get("interview_state", {})
    final_analysis = state.get("final_analysis", {})
    status = final_analysis.get("status", "complete")
    turn_count = interview_state.get("turn_count", 0)

    if (
        status == "incomplete"
        and final_analysis.get("missing_information")
        and turn_count < MAX_TURNS
    ):
        print("--- ROUTING TO: ask_one_question (specialist needs more info) ---")
        return "ask_more_questions"

    print("--- ROUTING TO: generate_report ---")
    return "end_process"


# ---------------------------------------------------------------------------
# Build and compile the LangGraph state machine
# ---------------------------------------------------------------------------

builder = StateGraph(PatientState)

# Register nodes
builder.add_node("preprocess",                  preprocess_node)
builder.add_node("process_lab_reports",         process_all_lab_reports_node)
builder.add_node("refine_questions",            refine_questions_node)
builder.add_node("await_patient_reply",         await_patient_reply_node)
builder.add_node("ask_one_question",            ask_one_question_node)
builder.add_node("triage_router",               triage_router_node)
builder.add_node("retrieve_context",            retrieve_context_node)
builder.add_node("general_medicine_analysis",   general_medicine_analysis_node)
builder.add_node("cardiology_analysis",         cardiology_analysis_node)
builder.add_node("dermatology_analysis",        dermatology_analysis_node)
builder.add_node("generate_report",             generate_report_node)

# Entry point
builder.set_entry_point("preprocess")

# Fixed edges
builder.add_edge("preprocess",          "process_lab_reports")
builder.add_edge("process_lab_reports", "refine_questions")

# After refine: start interview or go straight to triage
builder.add_conditional_edges(
    "refine_questions",
    decide_if_chat_needed,
    {"start_chat": "ask_one_question", "no_chat_needed": "triage_router"},
)

# After human reply comes in: resume from the checkpoint and continue to ask
# the next queued question without a separate memory-extraction LLM pass.
builder.add_edge("await_patient_reply", "ask_one_question")

# After ask_one_question:
# - 'continue_chat' → await_patient_reply (pause point before the next queued question)
# - 'end_chat'      → triage_router (interview finished)
builder.add_conditional_edges(
    "ask_one_question",
    decide_to_continue_chat,
    {"continue_chat": "await_patient_reply", "end_chat": "triage_router"},
)
# Triage always goes to RAG first
builder.add_edge("triage_router", "retrieve_context")
# Triage routes to specialist
# RAG then routes to the right specialist using diagnosis_path
builder.add_conditional_edges(
    "retrieve_context",
    route_to_specialist,   # already exists, reads state["diagnosis_path"]
    {
        "general_medicine": "general_medicine_analysis",
        "cardiology":       "cardiology_analysis",
        "dermatology":      "dermatology_analysis",
    },
)

# Specialist decides: more questions or generate report
def _add_specialist_edges(name: str) -> None:
    builder.add_conditional_edges(
        name,
        decide_after_analysis,
        {"ask_more_questions": "ask_one_question", "end_process": "generate_report"},
    )

_add_specialist_edges("general_medicine_analysis")
_add_specialist_edges("cardiology_analysis")
_add_specialist_edges("dermatology_analysis")

builder.add_edge("generate_report", END)

# ---------------------------------------------------------------------------
# Compile with checkpoint + interrupt
# ---------------------------------------------------------------------------

checkpointer = MemorySaver()

graph_with_checkpoint = builder.compile(
    checkpointer=checkpointer,
    # Pause after each question is sent so the API can inject the next human answer
    # before the next queued question is asked.
    interrupt_before=["await_patient_reply"],
)

# Non-interrupting version for testing
graph = builder.compile(checkpointer=checkpointer)