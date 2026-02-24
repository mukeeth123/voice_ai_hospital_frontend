"""
Quick test: verify all LLM fields are populated in the medical report.
Run from backend/ with: python test_llm_report.py
"""
import asyncio
import json
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(__file__))

async def main():
    from app.api.routes.json_intake import _generate_llm_report

    test_data = {
        "name": "Mukesh",
        "age": 32,
        "gender": "Male",
        "blood_group": "O+",
        "weight": 70,
        "symptoms": "severe chest pain and shortness of breath for the past 2 days",
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
    }

    print("=" * 60)
    print("TESTING LLM REPORT GENERATION")
    print("=" * 60)
    print(f"Patient: {test_data['name']}, {test_data['age']}y, {test_data['gender']}")
    print(f"Symptoms: {test_data['symptoms']}")
    print("-" * 60)

    result = await _generate_llm_report(test_data)
    analysis = result.get("medical_analysis", {})

    REQUIRED_FIELDS = [
        "patient_summary",
        "explanation",
        "possible_conditions",
        "ai_diagnostic_summary",
        "suggested_tests",
        "recommended_basic_tests",
        "doctor_recommendation",
        "lifestyle_recommendations",
        "precautions",
        "safety_precautions",
        "next_steps_checklist",
        "emergency_signs",
        "disclaimer",
    ]

    all_pass = True
    for field in REQUIRED_FIELDS:
        val = analysis.get(field)
        if not val or (isinstance(val, (list, dict)) and len(val) == 0):
            status = "❌ MISSING / EMPTY"
            all_pass = False
        else:
            if isinstance(val, str):
                preview = val[:80] + "..." if len(val) > 80 else val
            elif isinstance(val, list):
                preview = f"[{len(val)} items] " + str(val[0])[:60]
            elif isinstance(val, dict):
                preview = str(list(val.keys()))
            else:
                preview = str(val)
            status = f"✅ OK — {preview}"
        print(f"\n{field}:\n  {status}")

    print("\n" + "=" * 60)
    print("FULL JSON OUTPUT (medical_analysis):")
    print("=" * 60)
    print(json.dumps(analysis, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    if all_pass:
        print("✅ ALL FIELDS POPULATED — LLM report is working correctly!")
    else:
        print("⚠️  Some fields are missing. Check the output above.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
