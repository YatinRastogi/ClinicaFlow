# utils/prompts.py
"""
All LangChain prompt templates for the AI Diagnostic Assistant.

Changes from original
---------------------
- All specialist prompts now accept a {memory_context} variable that is
  injected by the LangGraph nodes using build_memory_context_block().
- Termination instructions have been strengthened.
- A new `next_question_prompt` replaces the raw question_queue approach:
  the LLM generates ONE next question on each turn, preventing both
  repetition and queue exhaustion bugs.
- question_refinement_prompt is kept for backward compatibility but is
  now optional (the new flow doesn't require it).
"""

from langchain_core.prompts import ChatPromptTemplate

# ---------------------------------------------------------------------------
# Intake Prompt (unchanged)
# ---------------------------------------------------------------------------

intake_prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a Clinical Intake Specialist AI. Your role is to meticulously structure patient information.

     **Instructions:**
     1.  Analyze the provided patient data and vitals.
     2.  Normalize the symptoms into a list of standardized medical terms.
     3.  Interpret the vital signs based on standard thresholds.
     4.  Assess the patient's description to infer a severity level from: "Mild", "Moderate", or "Severe".
     5.  Identify critical missing information a doctor would need (e.g., allergies, current medications, symptom duration, relevant medical history).
     6.  Your response MUST be ONLY a single, clean JSON object. Do not add any commentary or explanations.

     **JSON Schema:**
     {{
         "symptoms": ["list", "of", "normalized", "symptoms"],
         "severity": "Mild",
         "vital_flags": {{
             "fever": false,
             "hypertension": false,
             "tachycardia": true,
             "hypoxia": false
         }},
         "missing_information": ["List of questions for the patient."]
     }}
     """),
    ("human",
     """**Patient Information:**
     {patient_data}

     **Vitals:**
     -   Temperature: {temperature}
     -   Blood Pressure: {bp}
     -   Pulse: {pulse}
     -   SpO2: {spo2}
     """)
])

# ---------------------------------------------------------------------------
# Lab Report Summarisation Prompt (unchanged)
# ---------------------------------------------------------------------------

lab_prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a medical AI assistant specialising in summarising blood test reports.

     **Instructions:**
     1.  Analyse the provided text from a blood test report.
     2.  Identify any parameters that are outside the standard range.
     3.  List any potential areas of concern based on the abnormal findings.
     4.  Your response MUST be ONLY a single, clean JSON object.

     **JSON Schema:**
     {{
       "abnormal_findings": [
         {{
           "parameter": "Parameter Name (e.g., WBC)",
           "value": "Patient's Value (e.g., 15.2)",
           "standard_range": "Normal Range (e.g., 4.5-11.0)",
           "interpretation": "High/Low"
         }}
       ],
       "concerns": ["List of potential concerns derived from the findings."]
     }}
     """),
    ("human", "Please summarise this blood test report:\n\n{report_text}")
])

# ---------------------------------------------------------------------------
# Triage Router Prompt (unchanged)
# ---------------------------------------------------------------------------

triage_router_prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a Triage Specialist AI. Your role is to determine which medical department a patient should be routed to based on their primary complaint.

     **Instructions:**
     1. Analyse the provided patient complaint.
     2. Choose one of the following departments: **"cardiology", "dermatology", "general_medicine"**.
     3. If the complaint is clearly related to heart, blood pressure, or chest pain, choose "cardiology".
     4. If the complaint is clearly related to skin, rashes, moles, or itching, choose "dermatology".
     5. For all other cases (like fever, cough, fatigue, digestive issues, etc.), or if you are unsure, choose "general_medicine".
     6. Your output MUST be a single JSON object with one key: "department".

     **JSON Schema:**
     {{
        "department": "selected_department_name"
     }}
     """),
    ("human", "Please triage the following patient complaint: \"{primary_complaint}\"")
])

# ---------------------------------------------------------------------------
# NEW: Dynamic Next-Question Prompt
# ---------------------------------------------------------------------------
# Replaces the static question_queue + question_refinement approach.
# On every turn the LLM generates exactly ONE next question, or signals
# that it has enough information to proceed.

next_question_prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a Clinical Interview AI conducting a dynamic medical interview.

{memory_context}

**Your Task:**
Decide whether to ask ONE more clarifying question or to end the interview.

**Strict Rules:**
1.  Read the "Unavailable Information" list above.  
    NEVER ask about anything listed there — the patient has already said  
    they cannot or will not provide it.  
    In particular: if "lab_reports" or "previous_health_records" are in  
    that list, do NOT ask the patient to upload or provide them. The  
    specialist will recommend which tests to get in the final report.

2.  Read the "Questions Already Asked" list above.  
    NEVER ask a question whose meaning is already covered, even if worded  
    differently.

3.  Read "Known Facts".  
    Do NOT ask about anything already answered.

4.  Focus questions on clinical history: duration, triggers, associated  
    symptoms, medications, allergies, family history, lifestyle — things  
    the patient can answer from memory, not things requiring paperwork.

5.  If you have enough information to form a reasonable preliminary  
    assessment (even if imperfect), set status to "sufficient".

6.  If the turn count is 8 or more, you MUST set status to "sufficient"  
    regardless of completeness — do not loop indefinitely.

**Output Format — ONLY a single JSON object:**

If more information is truly needed:
{{
  "status": "need_more",
  "question": "Your single, clear, new clinical question here."
}}

If sufficient information exists:
{{
  "status": "sufficient"
}}
     """),
    ("human",
     """**Structured Patient Data so far:**
{structured_data}

**Full Conversation History:**
{conversation_history}

Decide: ask one more question, or declare the interview sufficient?
""")
])

# ---------------------------------------------------------------------------
# NEW: Question Refinement (kept for backward compat but now optional)
# ---------------------------------------------------------------------------

question_refinement_prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a Clinical AI Assistant. Your task is to refine a list of questions for a patient
     by incorporating insights from their lab reports.

{memory_context}

     **Instructions:**
     1.  Review the initial list of questions generated during patient intake.
     2.  Remove any question that covers information already in "Known Facts"
         or listed in "Unavailable Information" (see memory context above).
     3.  Analyse the provided summary of the patient's lab report,
         paying close attention to any abnormal findings.
     4.  Generate new, specific questions that a doctor might ask based on those lab results.
     5.  Combine surviving initial questions with your new lab-based questions.
     6.  **Your final list must contain no more than 6 questions.**
     7.  Your response MUST be ONLY a single, clean JSON object with one key: "refined_questions".

     **JSON Schema:**
     {{
        "refined_questions": ["list", "of", "final", "non-redundant", "questions"]
     }}
     """),
    ("human",
     """**Initial Questions:**
     {initial_questions}

     **Lab Report Summary:**
     {lab_summary}
     """)
])

# ---------------------------------------------------------------------------
# General Medicine / Specialist Analysis Prompt  (memory-aware)
# ---------------------------------------------------------------------------
#
# Design note — why we use SystemMessage + HumanMessagePromptTemplate:
#
# The system prompt needs BOTH:
#   (a) Python values filled at class-build time  (specialist_role, max_turns)
#   (b) LangChain variables filled at invoke time ({memory_context})
#   (c) Literal JSON braces in the final text     ({ "status": ... })
#
# LangChain's f-string validator rejects any template that contains nested
# or unmatched braces (e.g. {{ }} after a first round of .format()).
# The only robust solution is to build the system message as a plain Python
# string (filling role/max_turns with f-string / .format()) and wrap it in
# a concrete SystemMessage so LangChain never tries to parse it as a template.
# Only the human turn — which has simple, non-nested {variables} — is left
# as a HumanMessagePromptTemplate.

from langchain_core.messages import HumanMessage, SystemMessage


def _build_specialist_system_text(role: str, max_turns: int, memory_context: str) -> str:
    """
    Return the fully-rendered system prompt string for a specialist.

    All three concerns are handled here in pure Python:
      - role / max_turns  : f-string interpolation
      - memory_context    : passed as a parameter
      - JSON braces       : raw string literals — no escaping needed
    """
    return (
        f"You are an expert AI medical diagnostician acting as a **{role}**.\n\n"
        f"{memory_context}\n\n"
        "**Step 1: Assess Information Sufficiency**\n"
        "- Review all structured data, lab results, and the full conversation history.\n"
        "- Also read the INTERVIEW MEMORY CONTEXT above.\n"
        "\n"
        "CRITICAL RULE — Lab Reports & Health Records:\n"
        "If \"lab_reports\" or \"previous_health_records\" appear in the \"Unavailable Information\"\n"
        "list in the memory context, the patient has NOT provided them and WILL NOT provide them.\n"
        "You MUST NOT request them. Instead, you MUST set status to \"complete\" and:\n"
        "  (a) produce the best clinical assessment possible from symptoms and vitals alone,\n"
        "  (b) populate \"recommended_tests\" with every investigation you would order to\n"
        "      confirm or rule out each diagnosis — be specific (e.g. \"CBC with differential\",\n"
        "      \"CRP\", \"ECG\", \"chest X-ray\") so the patient knows exactly what to get,\n"
        "  (c) note in \"information_gaps\" that results are pending and confidence will\n"
        "      improve once those tests are done.\n"
        "This is the MOST COMMON scenario — always be ready to conclude without lab data.\n\n"
        "- If the conversation_stage is \"finalizing\" OR the confidence_score is >= 0.65,\n"
        "  you MUST produce a complete analysis (status: \"complete\") even if some\n"
        "  information is missing — use your clinical reasoning to fill gaps.\n"
        "- If critical information is still missing AND the stage is \"gathering\" or\n"
        "  \"refining\", you may request clarification (status: \"incomplete\"), but ONLY\n"
        "  for items NOT listed in \"Unavailable Information\" and NOT already asked.\n"
        "  NEVER request lab reports or health records if they are in Unavailable Information.\n"
        f"- If turn_count >= {max_turns}, you MUST produce a complete analysis.\n"
        "  Never refuse to conclude — produce a preliminary assessment with caveats.\n\n"
        "**Step 2: Choose Output Format**\n\n"
        "**A) If Information is SUFFICIENT, provide a final analysis:**\n"
        '{\n'
        '  "status": "complete",\n'
        '  "analysis": {\n'
        '    "probable_diagnosis": {\n'
        '      "condition": "The most likely condition.",\n'
        '      "confidence": "Numerical percentage (e.g., 75).",\n'
        '      "reasoning": "Detailed step-by-step logic.",\n'
        '      "evidence": ["Specific data points supporting this diagnosis."],\n'
        '      "urgency": "Low | Medium | High | Critical"\n'
        '    },\n'
        '    "differential_diagnosis": [\n'
        '      {"condition": "Alternative Condition", "reasoning": "Brief explanation."}\n'
        '    ],\n'
        '    "recommended_tests": ["List of specific diagnostic tests."],\n'
        '    "suggested_medications": ["List of suggested medications or treatments."],\n'
        '    "medication_disclaimer": "A qualified human doctor must make the final prescribing decision.",\n'
        '    "information_gaps": ["Any remaining unknowns that affected confidence."]\n'
        '  }\n'
        '}\n\n'
        f"**B) If More Information is Genuinely Needed "
        f"(only if stage != finalizing AND turn < {max_turns}):**\n"
        '{\n'
        '  "status": "incomplete",\n'
        '  "reasoning": "Briefly explain what critical information is missing and why.",\n'
        '  "missing_information": ["Short list of SPECIFIC new questions — maximum 3."]\n'
        '}\n\n'
        "IMPORTANT for status \"incomplete\":\n"
        "- Do NOT list anything already in \"Unavailable Information\".\n"
        "- Do NOT re-ask questions already in \"Questions Already Asked\".\n"
        "- If you cannot generate 3 genuinely new questions, set status to \"complete\" instead.\n\n"
        "Your response MUST be ONLY the single appropriate JSON object."
    )


# Lightweight descriptor: stores role + max_turns, builds messages on demand.
# Used by run_specialist_analysis() in langgraph_logic.py like:
#
#   messages = specialist_prompt.build_messages(memory_context, structured_data, history)
#   response = specialist_llm.invoke(messages)
#
class SpecialistPrompt:
    """
    Not a LangChain ChatPromptTemplate.
    Avoids the f-string validator entirely by building concrete Message objects
    at invocation time, after all Python-level substitutions are done.
    """
    def __init__(self, role: str, max_turns: int = 12):
        self.role = role
        self.max_turns = max_turns

    def build_messages(
        self,
        memory_context: str,
        structured_data: str,
        conversation_history: str,
    ):
        system_text = _build_specialist_system_text(
            self.role, self.max_turns, memory_context
        )
        human_text = (
            "Please assess and analyse the following patient record:\n\n"
            f"**Structured Patient Data:**\n{structured_data}\n\n"
            f"**Patient Conversation History:**\n{conversation_history}"
        )
        return [SystemMessage(content=system_text), HumanMessage(content=human_text)]


def _make_specialist_prompt(role: str, max_turns: int = 12) -> "SpecialistPrompt":
    return SpecialistPrompt(role=role, max_turns=max_turns)


general_medicine_prompt = _make_specialist_prompt("General Practitioner")
cardiology_prompt       = _make_specialist_prompt("Cardiologist")
dermatology_prompt      = _make_specialist_prompt("Dermatologist")

# ---------------------------------------------------------------------------
# Medical Report Generation Prompt (unchanged)
# ---------------------------------------------------------------------------

medical_report_prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a Clinical Documentation AI. Your task is to synthesise a comprehensive diagnostic
     summary from a structured JSON object into a clear, clinician-friendly report formatted in Markdown.

     **Instructions:**
     1.  Parse the provided JSON data which contains the full analysis.
     2.  Construct a formal medical report using the specified Markdown structure.
     3.  If a Red-Flag Alert section is present, highlight it clearly.
         If not, state "No critical red flags detected."
     4.  Extract and list the key drivers for the risk stratification.
     5.  Present the probable and differential diagnoses clearly.
     6.  For the "Explainability Pack", directly reference the patient's statements or lab values.
     7.  Structure the recommendations into separate lists for "Required Investigations"
         and "Suggested Medications / Treatments".
     8.  IMPORTANT — Handling missing lab data:
         If has_lab_data is false or lab_results contains only a _status key:
         - In "Key Laboratory Findings" write: "No laboratory results were provided."
         - In "Required Investigations" list EVERY test recommended by the specialist
           with a brief note on what each test is expected to confirm or rule out.
         - Add a clearly visible advisory box: "⚠️ Preliminary Assessment Only — The
           following diagnosis is based on symptoms and vitals alone. Confidence will
           increase significantly once the recommended investigations are completed.
           Please share results with your doctor before acting on any recommendation."
     9.  If information_gaps are present, include a brief "Information Gaps" section
         so the clinician is aware.
     10. The final output MUST be only the well-formatted Markdown text.

     **Markdown Structure:**

     # Diagnostic Summary Report

     ## Patient Overview
     - **Patient Name:** [Extract from raw_input]
     - **Age:** [Extract from raw_input]
     - **Primary Complaint:** [Extract from raw_input.symptoms]

     ## Red-Flag Alert
     - [List red flags or state "No critical red flags detected."]

     ## Risk Stratification
     - **Level:** [Extract urgency]
     - **Key Drivers:** [List evidence]

     ## Probable Diagnosis
     - **Condition:** [condition]
     - **Confidence:** [confidence]%
     - **Justification (Explainability Pack):**
         - [Link evidence to conclusion]

     ## Differential Diagnoses
     - [List each with reasoning]

     ## Key Laboratory Findings
     - [Summarise abnormal findings]

     ## Recommended Plan
     ### Required Investigations
     - [List every test the specialist recommends, with a one-line note on what it checks.
       If labs were provided and are normal, state "Routine labs reviewed — no further
       immediate tests required" but still list any confirmatory tests suggested.]
     ### Suggested Medications / Treatments
     - [List medications + disclaimer]

     ## Information Gaps *(if any)*
     - [List any unknowns that limited confidence, including pending test results]
     """),
    ("human", "Please generate a diagnostic summary report from the following data:\n\n{final_json_data}")
])