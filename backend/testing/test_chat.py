import requests
import json

res = requests.post("http://127.0.0.1:8001/diagnose/chat", data={
    "user_input_json": json.dumps({
        "patient_profile": {
            "name": "Test User",
            "age": 30,
            "blood_group": "O+",
            "family_history": "None",
            "pre_existing_conditions": "None"
        },
        "patient_data": {
            "gender": "male",
            "weight": 70,
            "symptoms": "Headache",
            "duration": "2 days",
            "vitals": {
                "temperature": "98.6",
                "bp": "120/80",
                "pulse": "72",
                "spo2": "99"
            }
        }
    })
})

print(res.status_code)
print(res.text)
