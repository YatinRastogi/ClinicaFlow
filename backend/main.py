# backend/main.py
"""
FastAPI backend for the AI Diagnostic Assistant.

Changes from original
~~~~~~~~~~~~~~~~~~~~~
- Continuation flow now calls extract_memory_node BEFORE resuming the graph,
  by updating state with both the new human message AND the updated interview_state.
- The interview_state is persisted inside LangGraph's MemorySaver automatically;
  no extra storage is needed.
- The hardcoded localhost URL is replaced by a configurable BASE_URL env variable.
"""

import asyncio
import json
import os
import shutil
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, staticfiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langgraph_logic import graph_with_checkpoint
from utils.interview_memory import make_interview_state

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Diagnostic Assistant API",
    version="2.0.0",
)

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

REPORTS_DIR = "generated_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)
app.mount("/reports", staticfiles.StaticFiles(directory=REPORTS_DIR), name="reports")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Pydantic response model
# ---------------------------------------------------------------------------

class ChatResponse(BaseModel):
    conversation_id: str
    ai_message: Optional[str] = None
    final_report_url: Optional[str] = None
    final_report_data: Optional[Dict[str, Any]] = None
    is_complete: bool = False
    # Optional diagnostics (helpful for frontend progress display)
    interview_turn: Optional[int] = None
    confidence_score: Optional[float] = None


# ---------------------------------------------------------------------------
# /diagnose/chat  — unified endpoint
# ---------------------------------------------------------------------------

@app.post("/diagnose/chat", response_model=ChatResponse)
async def chat(
    conversation_id: Optional[str] = Form(None),
    user_input_json: str = Form(...),
    lab_report: Optional[UploadFile] = File(None),
    health_record: Optional[UploadFile] = File(None),
):
    try:
        convo_id = conversation_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": convo_id}}
        user_input = json.loads(user_input_json)

        # ------------------------------------------------------------------
        # Branch A: new conversation
        # ------------------------------------------------------------------
        if not conversation_id:
            print(f"--- 🚀 Starting new conversation: {convo_id} ---")
            patient_data = user_input
            file_paths: Dict[str, str] = {}

            if lab_report:
                fp = os.path.join(UPLOAD_DIR, f"{convo_id}_{lab_report.filename}")
                with open(fp, "wb") as buf:
                    shutil.copyfileobj(lab_report.file, buf)
                file_paths["lab_report"] = fp

            if health_record:
                fp = os.path.join(UPLOAD_DIR, f"{convo_id}_{health_record.filename}")
                with open(fp, "wb") as buf:
                    shutil.copyfileobj(health_record.file, buf)
                file_paths["health_record"] = fp

            patient_data["files"] = file_paths
            graph_input = {"raw_input": patient_data}

        # ------------------------------------------------------------------
        # Branch B: continuing an existing conversation
        # ------------------------------------------------------------------
        else:
            print(f"--- 💬 Continuing conversation: {convo_id} ---")
            human_answer = user_input.get("answer", "")

            # Fetch current graph state
            current_snapshot = await asyncio.to_thread(
                graph_with_checkpoint.get_state, config
            )
            if not current_snapshot:
                raise HTTPException(status_code=404, detail="Conversation not found.")

            # With interrupt_before=["extract_memory"], the graph is paused
            # BEFORE extract_memory runs. We only need to inject the human
            # reply into the message history — extract_memory_node runs first
            # inside the graph on resume, so we do NOT extract here to avoid
            # double-processing.
            current_values = dict(current_snapshot.values)
            messages = list(current_values.get("messages", []))
            messages.append({"role": "human", "content": human_answer})
            current_values["messages"] = messages

            await asyncio.to_thread(
                graph_with_checkpoint.update_state, config, current_values
            )

            graph_input = None  # Resume from checkpoint

        # ------------------------------------------------------------------
        # Run / resume the graph
        # ------------------------------------------------------------------
        final_state = await asyncio.to_thread(
            graph_with_checkpoint.invoke, graph_input, config
        )
        final_state = final_state or {}

        ai_message = final_state.get("pending_question")
        report_path = final_state.get("report_path")
        report_json_path = final_state.get("report_json_path")
        is_complete = bool(report_path and report_json_path)
        interview_state_final = final_state.get("interview_state") or {}

        final_report_url = None
        final_report_data = None

        if is_complete:
            ai_message = None
            pdf_filename = os.path.basename(report_path)
            final_report_url = f"{BASE_URL}/reports/{pdf_filename}"
            try:
                with open(report_json_path, "r", encoding="utf-8") as f:
                    final_report_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"--- ❌ Error reading report JSON: {e} ---")

        return ChatResponse(
            conversation_id=convo_id,
            ai_message=ai_message,
            final_report_url=final_report_url,
            final_report_data=final_report_data,
            is_complete=is_complete,
            interview_turn=interview_state_final.get("turn_count"),
            confidence_score=interview_state_final.get("confidence_score"),
        )

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in user_input_json.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")