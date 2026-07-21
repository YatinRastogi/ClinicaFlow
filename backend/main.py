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

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, staticfiles, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt

from database.models import SessionLocal, PatientProfile, engine

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
# Auth & DB setup
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

class PatientCreate(BaseModel):
    username: str
    password: str
    name: str
    age: int
    gender: str
    blood_group: str
    family_history: str = "None"
    pre_existing_conditions: str = "None"

class PatientLogin(BaseModel):
    username: str
    password: str

@app.post("/register")
def register_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    db_user = db.query(PatientProfile).filter(PatientProfile.username == patient.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_patient = PatientProfile(
        username=patient.username,
        hashed_password=get_password_hash(patient.password), 
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        blood_group=patient.blood_group,
        family_history=patient.family_history,
        pre_existing_conditions=patient.pre_existing_conditions
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return {"message": "Patient registered successfully", "patient_id": new_patient.id}

@app.post("/login")
def login_patient(patient: PatientLogin, db: Session = Depends(get_db)):
    db_user = db.query(PatientProfile).filter(PatientProfile.username == patient.username).first()
    if not db_user or not verify_password(patient.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    return {
        "message": "Login successful",
        "patient_id": db_user.id,
        "profile": {
            "name": db_user.name,
            "age": db_user.age,
            "gender": db_user.gender,
            "blood_group": db_user.blood_group,
            "family_history": db_user.family_history,
            "pre_existing_conditions": db_user.pre_existing_conditions
        }
    }


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
            print(f"--- START: Starting new conversation: {convo_id} ---")
            patient_data = user_input.get("patient_data", user_input)
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
            graph_input = {
                "raw_input": patient_data,
                "patient_profile": user_input.get("patient_profile")
            }

        # ------------------------------------------------------------------
        # Branch B: continuing an existing conversation
        else:
            print(f"--- MSG: Continuing conversation: {convo_id} ---")
            human_answer = user_input.get("answer", "")

            current_snapshot = await asyncio.to_thread(
                graph_with_checkpoint.get_state, config
            )
            if not current_snapshot or not current_snapshot.values:
                raise HTTPException(status_code=404, detail="Conversation not found.")

            current_values = dict(current_snapshot.values)
            messages = list(current_values.get("messages", []))
            messages.append({"role": "human", "content": human_answer})
            current_values["messages"] = messages

            await asyncio.to_thread(
                graph_with_checkpoint.update_state,
                config,
                current_values,
                as_node="extract_memory",
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
        tb=traceback.print_exc()
        print(f"--- ❌ FULL ERROR:\n{tb}")
        raise HTTPException(status_code=500, detail=f"Internal error: {type(e).__name__}: {e}")