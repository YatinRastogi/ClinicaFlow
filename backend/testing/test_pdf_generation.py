import sys
import os

# Add the parent directory to sys.path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pdf_generator import create_pdf_report

test_markdown = """
# Diagnostic Summary

## Probable Diagnosis
- **Condition:** Hypertension with suspected secondary complications
- **Confidence:** 85
- **Reasoning:** Patient presents with elevated BP 160/100 mmHg and other symptoms.

## Required Investigations
| Test | Reason |
|---|---|
| Basic Metabolic Panel | Check kidney function |

## Suggested Medications
- Adequate oral hydration (≥ 2 L water/day if tolerated).
- If BP remains ≥ 160/100 mmHg after 24 h, consider initiating an antihypertensive (e.g., low‑dose ACE inhibitor or calcium‑channel blocker) - to be prescribed by the treating physician.
- If bacterial sinusitis becomes likely (symptoms > 5‑7 days or worsening), consider amoxicillin‑clavulanate 875/125 mg PO BID for 5‑7 days - after clinical reassessment.
- If COVID‑19 test is positive, follow local treatment guidelines (e.g., antiviral therapy if indicated).
> Medication Disclaimer: A qualified human doctor must make the final prescribing decision and tailor therapy to the individual patient's full clinical picture.
"""

if __name__ == "__main__":
    output_filename = "test_output_report.pdf"
    print("Generating PDF...")
    result = create_pdf_report(test_markdown, filename=output_filename)
    if result:
        print(f"PDF successfully generated at: {result}")
    else:
        print("PDF generation failed.")
