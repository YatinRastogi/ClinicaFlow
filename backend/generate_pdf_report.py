import os
from fpdf import FPDF


def create_pdf(filename, title, content):
    pdf = FPDF()
    pdf.add_page()

    # We use a built-in font. Replacing special characters to avoid the "black box" issue!
    content = content.replace("°", " degrees ").replace("–", "-").replace("—", "-")

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 8, txt=content)

    pdf.output(filename)
    print(f"✅ Successfully created: {filename}")


# --- REPORT 1: GENERAL MEDICINE ---
report_1_text = """Patient Name: Michael Chang
Age: 34
Date of Collection: May 24, 2026
Primary Complaint: Persistent sore throat, fatigue, and chills for 48 hours.

Vitals at Triage:
- Temperature: 102.1 degrees F (Elevated)
- Blood Pressure: 118/76 mmHg
- Heart Rate: 92 bpm
- SpO2: 98%

Complete Blood Count (CBC) Results:
- White Blood Cells (WBC): 14.2 x10^3/uL (HIGH - Reference: 4.5-11.0)
- Red Blood Cells (RBC): 4.8 x10^6/uL (Normal)
- Hemoglobin (Hb): 14.5 g/dL (Normal)
- Hematocrit (Hct): 43% (Normal)
- Platelets: 210 x10^3/uL (Normal)

Throat Culture (Rapid Strep): POSITIVE

Clinical Notes: Patient reports difficulty swallowing. No known allergies to medications."""

# --- REPORT 2: CARDIOLOGY ---
report_2_text = """Patient Name: Sarah Jenkins
Age: 58
Date of Collection: May 22, 2026
Primary Complaint: Intermittent chest tightness when walking up stairs, accompanied by mild shortness of breath.

Vitals at Triage:
- Temperature: 98.4 degrees F
- Blood Pressure: 152/94 mmHg (Elevated)
- Heart Rate: 88 bpm
- SpO2: 96%

Comprehensive Lipid Panel & Cardiac Markers:
- Total Cholesterol: 245 mg/dL (HIGH - Reference: < 200)
- LDL (Bad) Cholesterol: 165 mg/dL (HIGH - Reference: < 100)
- HDL (Good) Cholesterol: 42 mg/dL (LOW - Reference: > 50)
- Triglycerides: 190 mg/dL (HIGH - Reference: < 150)
- Troponin I (hs-cTnI): 12 ng/L (Normal - Reference: < 14)
- hs-CRP (Inflammation): 3.1 mg/L (HIGH - Reference: < 2.0)

Clinical Notes: Patient has a family history of premature coronary artery disease. Non-smoker. Currently not on any statin therapy."""

if __name__ == "__main__":
    # Make sure your data directories exist
    os.makedirs("data/general_medicine", exist_ok=True)
    os.makedirs("data/cardiology", exist_ok=True)

    print("Generating mock medical reports...")

    # Generate and save the PDFs directly into your data folders!
    create_pdf("data/general_medicine/mock_fever_report.pdf", "HEALTH RECORD & LAB REPORT", report_1_text)
    create_pdf("data/cardiology/mock_chest_pain_report.pdf", "HEALTH RECORD & LAB REPORT", report_2_text)