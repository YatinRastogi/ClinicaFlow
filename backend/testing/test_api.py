import requests

# 1. Register
res = requests.post("http://127.0.0.1:8001/register", json={
    "username": "testuser_99",
    "password": "testpass_99",
    "name": "Test User 99",
    "age": 40,
    "blood_group": "AB+",
    "family_history": "Mother: Asthma",
    "pre_existing_conditions": "Diabetes"
})
print("Register:", res.status_code, res.text)

# 2. Login
res = requests.post("http://127.0.0.1:8001/login", json={
    "username": "testuser_99",
    "password": "testpass_99"
})
print("Login:", res.status_code, res.text)
