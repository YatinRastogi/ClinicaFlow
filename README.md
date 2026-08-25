# ClinicaFlow 🩺

**ClinicaFlow** is an advanced, AI-powered Medical Diagnostic Assistant designed to simulate a real-world clinical workflow. Instead of acting as a simple Q&A chatbot, ClinicaFlow conducts a stateful, interactive patient interview, processes medical documents, grounds its reasoning in real clinical guidelines, and generates professional PDF diagnostic reports.

---

## 🚀 Key Features

* **Interactive Medical Interview (State Machine):** Uses an intelligent queue-based interview flow to generate a short set of 3-4 relevant follow-up questions, then asks them one by one without re-triggering the LLM after every reply.
* **Persistent Context Memory:** Keeps the raw conversation transcript and structured interview state, avoiding a separate per-reply extraction LLM call while preserving duplicate checks and known clinical facts.
* **Automated Triage & Specialist Routing:** Analyzes the patient's initial complaints and routes the case to a specialized AI persona (e.g., Cardiology, Dermatology, or General Medicine) for highly accurate analysis.
* **Retrieval-Augmented Generation (RAG):** Grounds the AI's diagnostic reasoning in verified clinical practice guidelines (using ChromaDB) rather than relying solely on the LLM's pre-trained knowledge.
* **Lab Report Processing:** Parses uploaded PDF lab results and health records to pre-inform the AI before the interview begins.
* **Professional PDF Generation:** Compiles the final diagnosis, required investigations, and suggested treatments into a beautifully formatted, printable PDF report using ReportLab.

---

## 🧠 System Architecture & Workflow

**App (Frontend)** → **Backend API (FastAPI)** → **AI Processing Layer (LangGraph)** → **Outputs (Dashboard + PDF Report)**

ClinicaFlow follows a strict, node-based workflow managed by LangGraph:

1. **Preprocess:** The patient signs in, provides their initial symptoms, and uploads any lab reports via the frontend app.
2. **Process Labs:** The backend extracts text from lab reports, and an AI summarises the findings.
3. **Interview Loop (`ask_one_question` + queued follow-ups):** The AI generates a compact batch of 3-4 relevant questions up front, asks them one by one, and only asks the LLM for a new batch when the queue is exhausted — reducing unnecessary LLM calls while preserving a structured patient interview.
4. **Triage Router:** The system decides which medical department is best suited to handle the final diagnosis.
5. **Context Retrieval (RAG):** The system searches local medical guidelines (e.g., AHA Cardiology Guidelines) for literature matching the patient's symptoms.
6. **Specialist Analysis:** The specialized AI (e.g., the "Cardiologist") reviews the entire memory state, lab reports, and RAG context to formulate a diagnosis and treatment plan.
7. **Generate Report:** The backend formats the final output and utilizes ReportLab to generate a clean, plain-English PDF report.

---

## 🛠️ Tech Stack

* **Frontend**: React and Tailwindcss
* **Backend**: FastAPI (Python), LangGraph / LangChain for AI orchestration
* **Vector Database (RAG):** ChromaDB
* **Document Processing:** PyMuPDF (`fitz`), ReportLab (PDF Generation)
* **AI/ML**: LLMs (OpenAI OSS via Groq) for NLP & Q&A
* **Database**: SQLAlchemy & SQLite (Patient Profiles & Auth)

---

## 📂 Project Structure (Suggested)

```text
/backend
  ├── main.py                # FastAPI entry point
  ├── langgraph_logic.py     # LangGraph workflow state machine
  ├── utils/                 # AI helpers (Memory, RAG, PDF Generator, Prompts)
  ├── database/              # SQLAlchemy schemas
  ├── data/                  # Source medical PDFs for RAG
  └── chroma_db/             # Vector database storage
/ai_doctor
  ├── src/                   # React Frontend App
```

---

## 💻 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/patient-ai-system.git
cd patient-ai-system
```

### 2. Setup backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Setup frontend

```bash
cd ../ai_doctor
npm install
npm run dev
```

### 4. Access the system

* **Frontend App** → `http://localhost:5173/`
* **Backend API** → `http://localhost:8000/docs`

### 5. Environment Variables
Create a `.env` file inside the `backend/` folder and add your API Keys and Base URL:
```env
GROQ_API_KEY=your_api_key_here
BASE_URL=http://127.0.0.1:8000
```

---
