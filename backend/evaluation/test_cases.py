"""
ClinicaFlow RAG Evaluation Test Cases

Each test case contains:

- id
- specialty
- question
- reference_answer

The reference answer is intentionally concise because
RAGAS compares semantic similarity rather than exact wording.
"""

TEST_CASES = [

# ==========================================================
# CARDIOLOGY
# ==========================================================

{
    "id": 1,
    "specialty": "cardiology",
    "question": "A 60-year-old man has crushing chest pain radiating to the left arm for 30 minutes. What is the most likely diagnosis and initial investigations?",
    "reference_answer": "Acute coronary syndrome should be suspected. Initial investigations include ECG and cardiac troponins."
},

{
    "id": 2,
    "specialty": "cardiology",
    "question": "A patient has orthopnea, leg swelling and elevated BNP. What condition is most likely?",
    "reference_answer": "Heart failure is likely. Echocardiography should be performed."
},

{
    "id": 3,
    "specialty": "cardiology",
    "question": "A patient develops sudden tearing chest pain radiating to the back. What emergency should be suspected?",
    "reference_answer": "Aortic dissection should be suspected."
},

{
    "id": 4,
    "specialty": "cardiology",
    "question": "A patient presents with swollen painful calf after prolonged immobilization. What is the likely diagnosis?",
    "reference_answer": "Deep venous thrombosis."
},

{
    "id": 5,
    "specialty": "cardiology",
    "question": "Sharp chest pain improves while sitting forward and worsens when lying down. What is the diagnosis?",
    "reference_answer": "Acute pericarditis."
},

{
    "id": 6,
    "specialty": "cardiology",
    "question": "Which investigation is considered the primary imaging modality for evaluating heart failure?",
    "reference_answer": "Echocardiography."
},

{
    "id": 7,
    "specialty": "cardiology",
    "question": "Persistent hypertension despite medication should prompt evaluation for what secondary cause?",
    "reference_answer": "Renovascular hypertension."
},

{
    "id": 8,
    "specialty": "cardiology",
    "question": "Fever with a new heart murmur raises suspicion for which cardiac disease?",
    "reference_answer": "Infective endocarditis."
},

# ==========================================================
# PULMONOLOGY
# ==========================================================

{
    "id": 9,
    "specialty": "pulmonology",
    "question": "A young patient presents with episodic wheezing and shortness of breath that improves with bronchodilators. What is the likely diagnosis?",
    "reference_answer": "Asthma."
},

{
    "id": 10,
    "specialty": "pulmonology",
    "question": "An elderly smoker has chronic productive cough for years. What chronic disease should be considered?",
    "reference_answer": "Chronic obstructive pulmonary disease."
},

{
    "id": 11,
    "specialty": "pulmonology",
    "question": "Fever, productive cough and lobar consolidation on chest imaging suggest which diagnosis?",
    "reference_answer": "Community-acquired pneumonia."
},

{
    "id": 12,
    "specialty": "pulmonology",
    "question": "Sudden dyspnea after prolonged travel should raise suspicion for which pulmonary emergency?",
    "reference_answer": "Pulmonary embolism."
},

{
    "id": 13,
    "specialty": "pulmonology",
    "question": "What symptom most commonly characterizes asthma exacerbation?",
    "reference_answer": "Shortness of breath with wheezing."
},

{
    "id": 14,
    "specialty": "pulmonology",
    "question": "What is an important investigation in suspected pulmonary embolism?",
    "reference_answer": "CT pulmonary angiography."
},

# ==========================================================
# GASTROENTEROLOGY
# ==========================================================

{
    "id": 15,
    "specialty": "gastroenterology",
    "question": "Burning retrosternal pain after meals is characteristic of which disease?",
    "reference_answer": "Gastroesophageal reflux disease."
},

{
    "id": 16,
    "specialty": "gastroenterology",
    "question": "Severe epigastric pain radiating to the back suggests which diagnosis?",
    "reference_answer": "Acute pancreatitis."
},

{
    "id": 17,
    "specialty": "gastroenterology",
    "question": "Right lower quadrant abdominal pain with rebound tenderness suggests which diagnosis?",
    "reference_answer": "Acute appendicitis."
},

{
    "id": 18,
    "specialty": "gastroenterology",
    "question": "Black tarry stools are most consistent with what condition?",
    "reference_answer": "Upper gastrointestinal bleeding."
},

{
    "id": 19,
    "specialty": "gastroenterology",
    "question": "Helicobacter pylori is commonly associated with which gastrointestinal disease?",
    "reference_answer": "Peptic ulcer disease."
},

# ==========================================================
# ENDOCRINOLOGY
# ==========================================================

{
    "id": 20,
    "specialty": "endocrinology",
    "question": "Polyuria, polydipsia and elevated blood glucose suggest which disease?",
    "reference_answer": "Diabetes mellitus."
},

{
    "id": 21,
    "specialty": "endocrinology",
    "question": "Confusion with very low blood glucose levels indicates what acute complication?",
    "reference_answer": "Hypoglycemia."
},

{
    "id": 22,
    "specialty": "endocrinology",
    "question": "Weight gain, cold intolerance and fatigue suggest which endocrine disorder?",
    "reference_answer": "Hypothyroidism."
},

{
    "id": 23,
    "specialty": "endocrinology",
    "question": "Weight loss, heat intolerance and tremors suggest which endocrine disorder?",
    "reference_answer": "Hyperthyroidism."
},

{
    "id": 24,
    "specialty": "endocrinology",
    "question": "Moon face, truncal obesity and purple striae are characteristic of which syndrome?",
    "reference_answer": "Cushing syndrome."
},

# ==========================================================
# NEUROLOGY
# ==========================================================

{
    "id": 25,
    "specialty": "neurology",
    "question": "Sudden unilateral weakness and slurred speech suggest what diagnosis?",
    "reference_answer": "Acute ischemic stroke."
},

{
    "id": 26,
    "specialty": "neurology",
    "question": "A patient experiences recurrent generalized tonic-clonic episodes. What condition is likely?",
    "reference_answer": "Seizure disorder."
},

{
    "id": 27,
    "specialty": "neurology",
    "question": "Severe unilateral throbbing headache with photophobia suggests which condition?",
    "reference_answer": "Migraine."
},

{
    "id": 28,
    "specialty": "neurology",
    "question": "Acute fever, neck stiffness and altered mental status suggest which neurological emergency?",
    "reference_answer": "Acute bacterial meningitis."
},

{
    "id": 29,
    "specialty": "neurology",
    "question": "Resting tremor, rigidity and bradykinesia are classic features of which disease?",
    "reference_answer": "Parkinson disease."
},

# ==========================================================
# DERMATOLOGY
# ==========================================================

{
    "id": 30,
    "specialty": "dermatology",
    "question": "Chronic itchy flexural rash is characteristic of which skin condition?",
    "reference_answer": "Atopic dermatitis."
},

{
    "id": 31,
    "specialty": "dermatology",
    "question": "Pruritic rash appearing after exposure to an allergen suggests what diagnosis?",
    "reference_answer": "Contact dermatitis."
},

{
    "id": 32,
    "specialty": "dermatology",
    "question": "Painful warm erythematous skin with fever suggests which skin infection?",
    "reference_answer": "Cellulitis."
},

# ==========================================================
# CRITICAL CARE
# ==========================================================

{
    "id": 33,
    "specialty": "critical_care",
    "question": "Persistent hypotension despite adequate fluid resuscitation in a patient with infection indicates what condition?",
    "reference_answer": "Septic shock."
},

{
    "id": 34,
    "specialty": "critical_care",
    "question": "Low blood pressure with signs of inadequate tissue perfusion defines what syndrome?",
    "reference_answer": "Shock."
},

{
    "id": 35,
    "specialty": "critical_care",
    "question": "Diffuse pulmonary infiltrates with severe hypoxemia are characteristic of which syndrome?",
    "reference_answer": "Acute respiratory distress syndrome."
}

]