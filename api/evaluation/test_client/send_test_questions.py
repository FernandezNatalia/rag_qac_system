import requests
import json
from time import sleep
from .test_questions import test_questions

API_URL = "http://localhost:8000/chat"

results = []

for idx, q in enumerate(test_questions, start=1):
    session_id = f"test_q_{idx:03d}"
    payload = {"session_id": session_id, "question": q}

    print(f"Enviando pregunta {idx}/20 → {session_id}")
    res = requests.post(API_URL, json=payload)

    if res.status_code != 200:
        print(f"Error {res.status_code}: {res.text}")
        continue
    
    data = res.json()
    data["session_id"] = session_id
    data["question"] = q
    results.append(data)

    sleep(0.5)

with open("rag_test_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\nProceso completo!")
print("Resultados almacenados en rag_test_results.json")
