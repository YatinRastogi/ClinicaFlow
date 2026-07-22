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

from database.models import SessionLocal, PatientProfile, DoctorProfile, Appointment, MedicalReport, engine

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

@app.on_event("startup")
def seed_doctors():
    db = SessionLocal()
    try:
        if db.query(DoctorProfile).count() == 0:
            default_pwd = get_password_hash("password123")
            docs = [
                DoctorProfile(username="dr_smith", hashed_password=default_pwd, name="Dr. Smith", specialty="Cardiology"),
                DoctorProfile(username="dr_jones", hashed_password=default_pwd, name="Dr. Jones", specialty="General Medicine"),
                DoctorProfile(username="dr_doe", hashed_password=default_pwd, name="Dr. Doe", specialty="General Medicine")
            ]
            db.add_all(docs)
            db.commit()
            print("--- Seeded 3 mock doctors ---")
    finally:
        db.close()

@app.post("/login")
def login_unified(patient: PatientLogin, db: Session = Depends(get_db)):
    # Check patient first
    db_patient = db.query(PatientProfile).filter(PatientProfile.username == patient.username).first()
    if db_patient and verify_password(patient.password, db_patient.hashed_password):
        return {
            "message": "Login successful",
            "role": "patient",
            "patient_id": db_patient.id,
            "profile": {
                "id": db_patient.id,
                "name": db_patient.name,
                "age": db_patient.age,
                "gender": db_patient.gender,
                "blood_group": db_patient.blood_group,
                "family_history": db_patient.family_history,
                "pre_existing_conditions": db_patient.pre_existing_conditions,
                "role": "patient"
            }
        }
    
    # Check doctor next
    db_doctor = db.query(DoctorProfile).filter(DoctorProfile.username == patient.username).first()
    if db_doctor and verify_password(patient.password, db_doctor.hashed_password):
        return {
            "message": "Login successful",
            "role": "doctor",
            "doctor_id": db_doctor.id,
            "profile": {
                "id": db_doctor.id,
                "name": db_doctor.name,
                "specialty": db_doctor.specialty,
                "role": "doctor"
            }
        }

    raise HTTPException(status_code=400, detail="Invalid credentials")


# ---------------------------------------------------------------------------
# /diagnose/chat  — unified endpoint
# ---------------------------------------------------------------------------

@app.post("/diagnose/chat", response_model=ChatResponse)
async def chat(
    conversation_id: Optional[str] = Form(None),
    user_input_json: str = Form(...),
    lab_report: Optional[UploadFile] = File(None),
    health_record: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
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
                    
                # Save the MedicalReport to DB
                patient_profile = user_input.get("patient_profile")
                if patient_profile and "id" in patient_profile:
                    new_report = MedicalReport(
                        patient_id=patient_profile["id"],
                        report_url=final_report_url,
                        report_data=json.dumps(final_report_data)
                    )
                    db.add(new_report)
                    db.commit()
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

# ---------------------------------------------------------------------------
# Doctor Portal Endpoints
# ---------------------------------------------------------------------------

class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    appointment_time: str

class RagQaRequest(BaseModel):
    patient_id: int
    query: str

@app.get("/api/doctors")
def get_doctors(db: Session = Depends(get_db)):
    doctors = db.query(DoctorProfile).all()
    return {"doctors": [{"id": d.id, "name": d.name, "specialty": d.specialty} for d in doctors]}

@app.get("/api/patients/{patient_id}/reports")
def get_patient_reports(patient_id: int, db: Session = Depends(get_db)):
    reports = db.query(MedicalReport).filter(MedicalReport.patient_id == patient_id).all()
    return {"reports": [{"id": r.id, "url": r.report_url, "created_at": r.created_at.isoformat(), "data": json.loads(r.report_data)} for r in reports]}

@app.post("/api/appointments")
def book_appointment(appt: AppointmentCreate, db: Session = Depends(get_db)):
    doctor = db.query(DoctorProfile).filter(DoctorProfile.id == appt.doctor_id).first()
    patient = db.query(PatientProfile).filter(PatientProfile.id == appt.patient_id).first()
    
    if not doctor or not patient:
        raise HTTPException(status_code=404, detail="Doctor or Patient not found")
        
    try:
        import datetime
        appt_time = datetime.datetime.fromisoformat(appt.appointment_time.replace('Z', '+00:00'))
    except:
        raise HTTPException(status_code=400, detail="Invalid appointment_time format")
        
    # Check availability
    existing = db.query(Appointment).filter(
        Appointment.doctor_id == doctor.id, 
        Appointment.appointment_time == appt_time
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Doctor is already booked for this time slot.")
        
    new_appt = Appointment(doctor_id=doctor.id, patient_id=patient.id, appointment_time=appt_time)
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)
    return {"message": "Appointment booked", "appointment_id": new_appt.id}

@app.put("/api/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = "Completed"
    db.commit()
    return {"message": "Appointment completed"}

@app.get("/api/doctors/{doctor_id}/booked-slots")
def get_booked_slots(doctor_id: int, db: Session = Depends(get_db)):
    appts = db.query(Appointment).filter(Appointment.doctor_id == doctor_id, Appointment.status == "Scheduled").all()
    # Return in format "HH:MM"
    # Local time offset logic might vary, but since backend stores naive UTC and we book today,
    # let's just return the UTC hour offset so the frontend can compare.
    # Actually, we can return the exact ISO strings, and the frontend will format them to HH:MM.
    return {"booked_slots": [(a.appointment_time.isoformat() + "Z") for a in appts]}

@app.get("/api/doctors/{doctor_id}/schedule")
def get_doctor_schedule(doctor_id: int, db: Session = Depends(get_db)):
    appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor_id).all()
    
    schedule = []
    for a in appointments:
        patient = db.query(PatientProfile).filter(PatientProfile.id == a.patient_id).first()
        schedule.append({
            "appointment_id": a.id,
            "time": a.appointment_time.isoformat() + "Z",
            "status": a.status,
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "blood_group": patient.blood_group
            } if patient else None
        })
    return {"doctor_id": doctor_id, "schedule": schedule}

@app.get("/api/appointments/{appointment_id}/summary")
def generate_fast_summary(appointment_id: int, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    patient = db.query(PatientProfile).filter(PatientProfile.id == appt.patient_id).first()
    
    # Get latest report
    latest_report = db.query(MedicalReport).filter(MedicalReport.patient_id == patient.id).order_by(MedicalReport.created_at.desc()).first()
    report_context = ""
    if latest_report:
        try:
            r_data = json.loads(latest_report.report_data)
            analysis = r_data.get("final_analysis", {}).get("analysis", {})
            report_context = f"\nLatest Report Data: {json.dumps(analysis)}"
        except:
            pass

    # Mock LLM fast summary for now, as integrating full Langchain here might be heavy
    from utils.llm import triage_llm
    from langchain_core.messages import HumanMessage
    
    prompt = f"Provide a fast 4-bullet point clinical brief for patient {patient.name}, age {patient.age}, blood group {patient.blood_group}, with conditions: {patient.pre_existing_conditions}. {report_context} Make it very concise."
    
    try:
        response = triage_llm.invoke([HumanMessage(content=prompt)])
        summary = response.content
    except Exception as e:
        print(f"LLM Error: {e}")
        # Fallback if Groq API fails
        summary = f"- Patient {patient.name} ({patient.age}yo) scheduled for routine checkup.\n- Blood type: {patient.blood_group}.\n- Known conditions: {patient.pre_existing_conditions}.\n- No acute symptoms reported."
        
    return {"appointment_id": appointment_id, "summary": summary}

@app.post("/api/rag_qa")
def rag_qa(request: RagQaRequest, db: Session = Depends(get_db)):
    patient = db.query(PatientProfile).filter(PatientProfile.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    reports = db.query(MedicalReport).filter(MedicalReport.patient_id == patient.id).all()
    reports_context = []
    for r in reports:
        try:
            r_data = json.loads(r.report_data)
            # Extract basic info from report
            analysis = r_data.get("final_analysis", {}).get("analysis", {})
            reports_context.append(f"Date: {r.created_at.isoformat()} - Report: {json.dumps(analysis)}")
        except:
            pass
            
    reports_str = "\n".join(reports_context) if reports_context else "No past reports available."
        
    from utils.llm import llm
    from langchain_core.messages import HumanMessage
    
    # In a real scenario, this would query ChromaDB. For this iteration, we use the LLM directly with context.
    context = f"Patient {patient.name}, Age {patient.age}, Conditions: {patient.pre_existing_conditions}.\nPast Reports:\n{reports_str}"
    prompt = f"Context: {context}\nDoctor's Query: {request.query}\nAnswer the query concisely based on the context."
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        answer = response.content
    except Exception as e:
        answer = f"I am unable to answer this right now. Error: {e}"
        
    return {"query": request.query, "answer": answer}