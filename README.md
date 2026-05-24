# ClinicaFlow 🩺

**ClinicaFlow** is an advanced, AI-powered Medical Diagnostic Assistant designed to simulate a real-world clinical workflow. Instead of acting as a simple Q&A chatbot, ClinicaFlow conducts a stateful, interactive patient interview, processes medical documents, grounds its reasoning in real clinical guidelines, and generates professional PDF diagnostic reports.

---

## 🚀 Key Features

* **Interactive Medical Interview (State Machine):** Uses an intelligent state graph (LangGraph) to ask targeted follow-up questions one at a time, just like a real physician.
* **Persistent Context Memory:** Dynamically extracts and remembers "known facts" and "unavailable information" during the chat, preventing duplicate questions and ensuring the AI never loses track of the patient's history.
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
3. **Interview Loop (`ask_one_question` & `extract_memory`):** The AI asks a highly targeted question. When the patient replies, the system extracts the medical facts, updates its internal memory state, and loops back to ask the next question until it has sufficient data.
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

## 🔮 Future Enhancements

* Multi-language support for patient interaction
* Integration with wearable devices (IoT vitals)
* Advanced disease prediction models
* Blockchain-based medical record security

---

## 👥 Contributors

* Vasu Tyagi
* Yatin Rastogi
* Shubh 
* Raman