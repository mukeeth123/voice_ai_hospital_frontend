"""
End-to-end test for LLM report generation via /json-intake endpoint.
Run from backend/: python test_llm_fields.py
"""
import urllib.request
import json

REQUIRED_FIELDS = [
    "patient_summary",
    "explanation",
    "possible_conditions",
    "ai_diagnostic_summary",
    "recommended_basic_tests",
    "doctor_recommendation",
    "lifestyle_recommendations",
    "precautions",
    "safety_precautions",
    "next_steps_checklist",
    "emergency_signs",
    "disclaimer",
]

# Simulate a fully-completed intake (payment already paid) so the endpoint
# skips the conversation loop and goes straight to LLM report generation.
payload = json.dumps({
    "collected_data": {
        "name": "Mukesh",
        "age": "32",
        "gender": "Male",
        "blood_group": "O+",
        "weight": "70",
        "symptoms": "severe chest pain radiating to left arm",
        "duration": "2 days",
        "bp_history": "Yes",
        "sugar_history": "No",
        "thyroid_history": "No",
        "surgeries": "None",
        "medications": "None",
        "email": "mukesh@test.com",
        "phone": "9999999999",
        "location": "Bangalore",
        "language": "English",
        "patient_relation": "Self",
        "assigned_doctor": "Dr. Aditi Sharma (Cardiologist)",
        "selected_slot": "Morning (9 AM - 12 PM)",
        "payment_status": "paid"
    },
    "latest_input": "paid",
    "last_field_key": "payment_status"
}).encode()

req = urllib.request.Request(
    "http://localhost:8000/api/v1/json-intake",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

print("=" * 65)
print("  AMRUTHA AI  -  LLM REPORT FIELD TEST")
print("  Patient: Mukesh | Symptoms: chest pain | POST /json-intake")
print("=" * 65)

try:
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.loads(r.read())

        is_complete = data.get("is_complete", False)
        report      = data.get("report") or {}
        analysis    = report.get("medical_analysis") or {}

        print(f"\n  is_complete : {is_complete}")
        print(f"  report keys : {list(report.keys())}")
        print()

        print("-" * 65)
        print("  FIELD VERIFICATION")
        print("-" * 65)

        all_pass = True
        for field in REQUIRED_FIELDS:
            val = analysis.get(field)
            empty = not val or (isinstance(val, (list, dict)) and len(val) == 0)
            if empty:
                print(f"\n  {field}:\n  MISSING / EMPTY")
                all_pass = False
            else:
                if isinstance(val, str):
                    preview = val[:80] + "..." if len(val) > 80 else val
                elif isinstance(val, list):
                    preview = f"[{len(val)} items]  first -> {str(val[0])[:60]}"
                elif isinstance(val, dict):
                    preview = f"keys = {list(val.keys())}"
                else:
                    preview = str(val)
                print(f"\n  {field}:\n  OK  {preview}")

        print("\n" + "=" * 65)
        if all_pass:
            print("  ALL FIELDS POPULATED  -  LLM is filling correctly!")
        else:
            print("  SOME FIELDS MISSING  -  Review output above.")
        print("=" * 65)

        print("\n\nFULL medical_analysis JSON:\n")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))

except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"\nHTTP {e.code}: {body[:600]}")
except Exception as e:
    print(f"\nERROR: {e}")
