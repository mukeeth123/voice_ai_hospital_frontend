from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from app.services.groq_service import groq_service
from app.services.tts_service import tts_service
from app.services.validator import InputValidator
import logging
import json
from datetime import datetime
from enum import Enum

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response Models
class IntakeFieldType(str, Enum):
    text = "text"
    number = "number"
    date = "date"
    options = "options"
    payment = "payment"  # <--- Added payment type

class JsonIntakeRequest(BaseModel):
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    latest_input: str = Field(default="")
    last_field_key: Optional[str] = None  # To validate the previous answer

class JsonIntakeResponse(BaseModel):
    field_key: str
    question: str
    expected_type: IntakeFieldType
    options: Optional[List[str]] = None
    is_complete: bool = False
    report: Optional[Dict[str, Any]] = None
    tts_audio_base64: Optional[str] = None
    error_message: Optional[str] = None # If validation fails

@router.post("/json-intake", response_model=JsonIntakeResponse)
async def json_intake(request: JsonIntakeRequest):
    """
    Dynamic Intake:
    1. Validate latest_input based on last_field_key.
    2. If valid -> Update collected_data.
    3. If invalid -> Return error + same question.
    4. Call LLM to determined NEXT field.
    5. Return JSON with next question & type.
    """
    try:
        collected_data = request.collected_data
        latest_input = request.latest_input.strip()
        last_field = request.last_field_key

        # --- 1. VALIDATION PHASE ---
        if last_field and latest_input:
            # Determine expected type for validation (heuristic or stored)
            # For MVP, we can infer type from the field name or store it in frontend and pass back.
            # Ideally, backend should know. But since we are dynamic, we rely on the Validator's logic.
            field_type = "text"
            if "phone" in last_field.lower(): field_type = "phone"
            elif "email" in last_field.lower(): field_type = "email"
            elif "age" in last_field.lower(): field_type = "age"
            elif "date" in last_field.lower() or "dob" in last_field.lower(): field_type = "date"
            elif "blood" in last_field.lower(): field_type = "blood_group"
            elif "weight" in last_field.lower(): field_type = "weight"
            
            is_valid, error = InputValidator.validate(field_type, latest_input)
            
            if not is_valid:
                # Validation Failed: Ask user to retry
                return JsonIntakeResponse(
                    question=f"I'm sorry, that doesn't look like a valid {field_type.replace('_', ' ')}. {error}",
                    field_key=last_field, # Repeat same field
                    expected_type=field_type, # Should be consistent
                    is_complete=False,
                    error_message=error
                    # No TTS for validation error to keep it fast, or add if needed
                )
            
            # Validation Passed: Update Data
            # collected_data[last_field] = latest_input # This line is replaced by the new extraction logic below

        # --- 2. UPDATE COLLECTED DATA ---
        updated_data = collected_data.copy()
        
        if last_field and latest_input:
            # Simple direct assignment for payment to avoid LLM overhead/error
            if "payment" in str(last_field).lower() or "pay" in str(latest_input).lower():
                if "paid" in latest_input.lower() or "done" in latest_input.lower():
                    updated_data["payment_status"] = "paid"
            
            # Use LLM for other fields to extract structured data
            extraction_prompt = f"""
            EXTRACT info from user input into JSON.
            CONTEXT: Question was about "{last_field}". User said "{latest_input}".
            EXISTING DATA: {json.dumps(collected_data)}
            
            RULES:
            1. Update the relevant field key (e.g., name, age, symptoms).
            2. Normalize values (Age -> number, Gender -> Male/Female).
            3. If user says "Paid" for payment, set "payment_status": "paid".
            
            OUTPUT JSON: {{ "field_key": value }}
            """
            try:
                extracted_json = await groq_service.generate_text(extraction_prompt, response_format={"type": "json_object"})
                extracted_data = json.loads(extracted_json)
                updated_data.update(extracted_data)
                
                # Debug Log
                logger.info(f"🔹 Extraction Success. Extracted: {extracted_data}")
                logger.info(f"🔸 Updated Data: {updated_data}")
                
            except Exception as e:
                logger.error(f"Extraction Failed: {e}")
                updated_data[last_field] = latest_input

        # --- 3. DETERMINE NEXT STEP ---
        # Deterministic check for Payment Success
        if updated_data.get("payment_status") == "paid":
             # Force Completion if paid immediately
             next_step = {"is_complete": True}
        else:
             # Debug Log
             logger.info(f"🧠 Determining next step with data: {updated_data}")
             next_step = await _determine_next_step(updated_data) 
        
        # --- 3. COMPLETION CHECK ---
        if next_step.get("is_complete"):
            # Generate Report
            report = await _generate_llm_report(updated_data) # Use updated_data here
            completion_msg = "Thank you. I have collected all necessary details. I am generating your medical appointment report now. A copy will be sent to your email."
            
            # --- Generate PDF & Send Email ---
            try:
                from app.services.pdf_service import pdf_service
                from app.services.email_service import email_service

                dr_rec = report.get("medical_analysis", {}).get("doctor_recommendation", {})
                appt_details_inline = {
                    "appointment_id": f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "doctor_name": dr_rec.get("doctor_name", updated_data.get("assigned_doctor", "Specialist")),
                    "doctor_specialist": dr_rec.get("specialist_type", "General Physician"),
                    "appointment_time": updated_data.get("selected_slot", "To be confirmed"),
                    "urgency": dr_rec.get("consultation_priority", "Routine"),
                    "status": "Confirmed",
                    "consultation_type": "Online Consultation",
                }

                # 1. Generate PDF
                pdf_bytes = pdf_service.generate_report(
                    patient_data=updated_data,
                    medical_analysis=report.get("medical_analysis", {}),
                    appointment_details=appt_details_inline,
                )

                # 2. Send Email
                recipient = updated_data.get("email", "patient@example.com")
                logger.info(f"📧 Sending Appointment Email to: {recipient}")
                await email_service.send_appointment_email(
                    patient_email=recipient,
                    patient_name=updated_data.get("name", "Patient"),
                    appointment_details=appt_details_inline,
                    pdf_attachment=pdf_bytes,
                )
            except Exception as e:
                logger.error(f"Post-Intake Action Failed (PDF/Email): {e}")

            tts_audio = await _generate_tts(completion_msg, updated_data.get("language", "English"))
            
            return JsonIntakeResponse(
                question=completion_msg,
                field_key="complete",
                expected_type="text", # Fix validation error
                is_complete=True,
                report=report,
                tts_audio_base64=tts_audio
            )

        # --- 4. NEXT QUESTION ---
        question = next_step.get("question")
        field_key = next_step.get("field_key")
        
        # The question_bank already includes the welcome greeting for the first question
            
        expected_type = next_step.get("expected_type", "text")
        options = next_step.get("options")
        
        tts_audio = await _generate_tts(question, updated_data.get("language", "English"))

        return JsonIntakeResponse(
            question=question,
            field_key=field_key,
            expected_type=expected_type,
            options=options,
            is_complete=False,
            tts_audio_base64=tts_audio
        )

    except Exception as e:
        logger.error(f"Intake Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from app.services.question_bank import QUESTION_BANK

# Helper to get translated question
def _get_question(key: str, language: str, **kwargs) -> str:
    lang_map = {
        "English": "English",
        "Hindi": "Hindi",
        "Kannada": "Kannada"
    }
    target_lang = lang_map.get(language, "English")
    
    # Get template
    q_data = QUESTION_BANK.get(key, {})
    template = q_data.get(target_lang, q_data.get("English", "Question not found."))
    
    # Format with kwargs (e.g. name)
    try:
        return template.format(**kwargs)
    except Exception:
        return template

def _assign_doctor(symptoms: str) -> str:
    """Assign a specialist doctor based on symptoms."""
    symptoms = symptoms.lower()
    if any(x in symptoms for x in ["chest", "heart", "palpitation", "breath", "breathing"]):
        return "Dr. Aditi Sharma (Cardiologist)"
    elif any(x in symptoms for x in ["skin", "rash", "itch", "acne", "allergy"]):
        return "Dr. Rajesh Gupta (Dermatologist)"
    elif any(x in symptoms for x in ["child", "baby", "infant", "kid", "fever in child"]):
        return "Dr. Sneha Patil (Pediatrician)"
    elif any(x in symptoms for x in ["sugar", "diabetes", "thyroid", "weight gain", "fatigue"]):
        return "Dr. Meera Rao (Endocrinologist)"
    elif any(x in symptoms for x in ["bone", "joint", "knee", "back pain", "spine", "fracture"]):
        return "Dr. Sanjay Mehta (Orthopedic)"
    elif any(x in symptoms for x in ["stomach", "abdomen", "digestion", "vomiting", "diarrhea", "nausea"]):
        return "Dr. Priya Nair (Gastroenterologist)"
    elif any(x in symptoms for x in ["headache", "migraine", "brain", "nerves", "seizure", "memory"]):
        return "Dr. Kiran Kumar (Neurologist)"
    elif any(x in symptoms for x in ["eye", "vision", "blur", "sight"]):
        return "Dr. Ananya Joshi (Ophthalmologist)"
    elif any(x in symptoms for x in ["ear", "nose", "throat", "ent", "hearing", "tonsil"]):
        return "Dr. Ravi Verma (ENT Specialist)"
    else:
        return "Dr. Arun Kumar (General Physician)"


# Strict Prompt for Extraction
def _get_extraction_prompt(last_field: str, user_input: str, collected_data: dict) -> str:
    return f"""
    You are a medical data assistant.
    Extract the value for '{last_field}' from: "{user_input}".
    
    Rules:
    1. Return valid JSON only. Structure: {{ "{last_field}": "extracted_value" }}
    2. If user mentions other fields (e.g. duration), extract them too.
    3. If input is simple (e.g. "John"), just map it.
    4. Normalize 'age' to number.
    5. 'patient_relation': Extract 'Self', 'Parent', 'Child', 'Friend', 'Wife', 'Husband'.
    
    Current Data: {json.dumps(collected_data)}
    """

async def _determine_next_step(collected_data: dict) -> dict:
    """
    ADVANCED CONDITIONAL FLOW:
    1. Relation
    2. Demographics (Name, Age, Gender, Phone, Email, Location)
    3. Vitals (Weight, Blood Group)
    4. Symptoms & Duration
    5. Conditional History (BP, Sugar, Thyroid - Age/Gender dependent)
    6. General History (Surgeries, Medications)
    7. Payment
    """
    
    # 1. Personalization Context
    name = collected_data.get("name", "").strip()
    calling_name = name.split()[0] if name else "there"
    language = collected_data.get("language", "English")
    
    # helper for checks
    def is_missing(k): return not collected_data.get(k)

    # 2. Logic Tree
    
    # Step 0: Relation
    if is_missing("patient_relation"):
        return {"field_key": "patient_relation", "question": _get_question("patient_relation", language), "expected_type": "options", "options": ["Self", "Parent", "Child", "Other"]}
    
    # Determine Context (Self vs Other)
    relation = collected_data.get("patient_relation", "Self")
    suffix = "_self" if relation == "Self" else "_other"
    
    # Step 1: Basic Demographics
    if is_missing("name"):
        return {"field_key": "name", "question": _get_question(f"name{suffix}", language), "expected_type": "text"}
    
    if is_missing("age"):
        return {"field_key": "age", "question": _get_question(f"age{suffix}", language, name=calling_name), "expected_type": "number"}
        
    if is_missing("gender"):
        return {"field_key": "gender", "question": _get_question(f"gender{suffix}", language), "expected_type": "options", "options": ["Male", "Female", "Other"]}

    if is_missing("phone"):
        return {"field_key": "phone", "question": _get_question("phone", language), "expected_type": "text"} 
        
    if is_missing("email"):
        return {"field_key": "email", "question": _get_question("email", language), "expected_type": "text"}

    if is_missing("location"):
        return {"field_key": "location", "question": _get_question("location", language), "expected_type": "text"}

    # Step 2: Vitals
    if is_missing("weight"):
        return {"field_key": "weight", "question": _get_question(f"weight{suffix}", language, name=calling_name), "expected_type": "number"}
        
    if is_missing("blood_group"):
        return {"field_key": "blood_group", "question": _get_question(f"blood_group{suffix}", language), "expected_type": "text"}

    # Step 3: Clinical
    if is_missing("symptoms"):
        return {"field_key": "symptoms", "question": _get_question(f"symptoms{suffix}", language, name=calling_name), "expected_type": "text"}
        
    if is_missing("duration"):
        return {"field_key": "duration", "question": _get_question("duration", language), "expected_type": "text"}

    # Step 4: Conditional Medical History
    # Extract numeric age
    try:
        age_val = int(str(collected_data.get("age", "0")).lower().replace("years", "").replace("yrs", "").strip())
    except:
        age_val = 25 # Default to adult if unclear

    gender_val = str(collected_data.get("gender", "")).lower()
    is_female = "female" in gender_val or "woman" in gender_val
    is_child = age_val < 12

    # Skip specific history for children
    if not is_child:
        if is_missing("bp_history"):
            return {"field_key": "bp_history", "question": _get_question(f"bp_history{suffix}", language), "expected_type": "options", "options": ["Yes", "No", "Don't Know"]}
            
        if is_missing("sugar_history"):
            return {"field_key": "sugar_history", "question": _get_question(f"sugar_history{suffix}", language), "expected_type": "options", "options": ["Yes", "No", "Don't Know"]}
        
        if is_female and is_missing("thyroid_history"):
            return {"field_key": "thyroid_history", "question": _get_question(f"thyroid_history{suffix}", language), "expected_type": "options", "options": ["Yes", "No", "Don't Know"]}

    # General History for ALL
    if is_missing("surgeries"):
        return {"field_key": "surgeries", "question": _get_question(f"surgeries{suffix}", language), "expected_type": "text"}
        
    if is_missing("medications"):
        return {"field_key": "medications", "question": _get_question(f"medications{suffix}", language), "expected_type": "text"}

    # Step 5: Doctor Assignment — shown right after clinical data is collected
    doctor_name = _assign_doctor(collected_data.get("symptoms", ""))
    if is_missing("assigned_doctor"):
        return {
            "field_key": "assigned_doctor",
            "question": _get_question("assigned_doctor", language, doctor_name=doctor_name),
            "expected_type": "options",
            "options": ["Yes, proceed", "Choose another time"]
        }

    # Step 6: Appointment Slot Selection
    if is_missing("selected_slot"):
        return {
            "field_key": "selected_slot",
            "question": _get_question("selected_slot", language),
            "expected_type": "options",
            "options": ["Morning (9 AM – 12 PM)", "Afternoon (1 PM – 4 PM)", "Evening (5 PM – 8 PM)"]
        }

    # Step 7: Payment (now includes the assigned doctor's name)
    if collected_data.get("payment_status") != "paid":
        return {
            "field_key": "payment_status",
            "question": _get_question("payment_status", language, name=calling_name, doctor_name=doctor_name),
            "expected_type": "payment"
        }

    # All Done
    return {"is_complete": True}

async def _generate_tts(text: str, language: str = "English"):
    try:
        res = await tts_service.generate_speech(text, language)
        return res.get("audio_base64")
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return None

async def _generate_llm_report(collected_data: Dict) -> Dict[str, Any]:
    """
    Generate comprehensive patient intake report using LLM with strict JSON schema.
    All fields are populated based on patient symptoms and history.
    """
    try:
        assigned_doctor = _assign_doctor(collected_data.get("symptoms", ""))
        selected_slot   = collected_data.get("selected_slot", "To be confirmed")
        patient_name    = collected_data.get("name", "Patient")

        prompt = f"""
You are a Senior Medical AI Consultant. Analyze the patient profile below and generate a fully structured, clinically accurate medical assessment report.

PATIENT PROFILE:
- Name: {collected_data.get('name', 'N/A')}
- Age: {collected_data.get('age')} | Gender: {collected_data.get('gender')}
- Location: {collected_data.get('location')}
- Weight: {collected_data.get('weight')} kg | Blood Group: {collected_data.get('blood_group')}
- Relation: {collected_data.get('patient_relation', 'Self')}

CLINICAL DATA:
- Primary Symptoms: {collected_data.get('symptoms')}
- Duration: {collected_data.get('duration')}
- BP / Hypertension history: {collected_data.get('bp_history', 'N/A')}
- Diabetes / Sugar history: {collected_data.get('sugar_history', 'N/A')}
- Thyroid history: {collected_data.get('thyroid_history', 'N/A')}
- Past Surgeries: {collected_data.get('surgeries', 'None')}
- Current Medications: {collected_data.get('medications', 'None')}
- Assigned Doctor: {assigned_doctor}
- Appointment Slot: {selected_slot}

STRICT INSTRUCTIONS:
1. Every field MUST be filled with real, clinically relevant content based on the patient's symptoms.
2. Do NOT leave any array empty. Provide at least 2–3 items per list.
3. Output ONLY valid JSON — no markdown, no commentary.
4. Use simple, patient-friendly language (no unnecessary jargon).

OUTPUT JSON SCHEMA (fill ALL fields):
{{
  "patient_summary": "2-3 sentence clinical summary of the patient's condition, named after {patient_name}.",
  "explanation": "Detailed clinical reasoning for the diagnosis and treatment approach (3-5 sentences).",
  "possible_conditions": ["Condition 1", "Condition 2", "Condition 3"],
  "ai_diagnostic_summary": {{
    "explanation": "AI analysis of the symptoms and probable diagnosis (2-3 sentences).",
    "possible_conditions": ["Differential 1", "Differential 2", "Differential 3"],
    "risk_interpretation": "Risk level explanation (e.g., Moderate risk – requires prompt evaluation)."
  }},
  "suggested_tests": {{
    "blood_tests": [
      {{"test_name": "Test Name", "reason": "Why needed"}}
    ],
    "imaging": [
      {{"test_name": "Test Name", "reason": "Why needed"}}
    ],
    "special_tests": [
      {{"test_name": "Test Name", "reason": "Why needed"}}
    ]
  }},
  "recommended_basic_tests": [
    {{"test_name": "Test Name", "category": "Category (e.g., FASTING / AMBULATORY / URINE)"}},
    {{"test_name": "Test Name", "category": "Category"}}
  ],
  "doctor_recommendation": {{
    "specialist_type": "Specialist type (e.g., Cardiologist)",
    "doctor_name": "{assigned_doctor}",
    "doctor_expertise": "Area of expertise matching symptoms",
    "consultation_priority": "Routine / Urgent / Emergency",
    "reason": "Why this specialist is recommended for these symptoms."
  }},
  "lifestyle_recommendations": [
    "Specific recommendation 1",
    "Specific recommendation 2",
    "Specific recommendation 3"
  ],
  "precautions": [
    "Immediate precaution 1",
    "Immediate precaution 2",
    "Immediate precaution 3"
  ],
  "safety_precautions": [
    "Safety guideline 1",
    "Safety guideline 2",
    "Safety guideline 3"
  ],
  "next_steps_checklist": [
    "Complete required blood tests before appointment",
    "Share full medical history with {assigned_doctor} via the portal",
    "Monitor and log symptoms daily until appointment",
    "Avoid strenuous activity until evaluation is complete"
  ],
  "emergency_signs": [
    "Emergency warning sign 1 specific to the symptoms",
    "Emergency warning sign 2 specific to the symptoms"
  ],
  "disclaimer": "This AI-generated report is for preliminary informational purposes only and does not replace professional medical advice. Please consult {assigned_doctor} for a complete clinical evaluation."
}}
"""

        response = await groq_service.generate_text(prompt, temperature=0.3, max_tokens=2000)

        try:
            clean = response.strip().replace("```json", "").replace("```", "").strip()
            # Handle cases where LLM wraps in extra text before/after
            start = clean.find('{')
            end   = clean.rfind('}') + 1
            if start >= 0 and end > start:
                clean = clean[start:end]
            llm_report = json.loads(clean)
        except Exception as parse_err:
            logger.warning(f"LLM JSON parse error: {parse_err}. Using fallback.")
            llm_report = {
                "patient_summary": f"Medical assessment for {patient_name} based on reported symptoms.",
                "explanation": "Please consult your assigned doctor for detailed analysis.",
                "possible_conditions": ["Further evaluation required"],
                "ai_diagnostic_summary": {
                    "explanation": f"Symptoms reported: {collected_data.get('symptoms', 'N/A')}.",
                    "possible_conditions": ["See doctor for diagnosis"],
                    "risk_interpretation": "Risk level to be determined by physician."
                },
                "suggested_tests": {"blood_tests": [], "imaging": [], "special_tests": []},
                "recommended_basic_tests": [{"test_name": "Complete Blood Count (CBC)", "category": "BLOOD"}],
                "doctor_recommendation": {
                    "specialist_type": assigned_doctor,
                    "doctor_name": assigned_doctor,
                    "doctor_expertise": "General Medicine",
                    "consultation_priority": "Routine",
                    "reason": "Assigned based on reported symptoms."
                },
                "lifestyle_recommendations": ["Stay hydrated", "Rest adequately", "Monitor symptoms"],
                "precautions": ["Avoid self-medication", "Consult doctor if symptoms worsen"],
                "safety_precautions": ["Avoid strenuous activity", "Keep emergency contact handy"],
                "next_steps_checklist": [
                    "Complete blood work before appointment",
                    f"Share medical history with {assigned_doctor}",
                    "Monitor symptoms and log daily"
                ],
                "emergency_signs": ["High fever (>104°F)", "Severe difficulty breathing"],
                "disclaimer": "This AI-generated report is for informational purposes only."
            }

        # Always inject known fields so PDF is never blank
        llm_report.setdefault("doctor_recommendation", {})
        llm_report["doctor_recommendation"]["doctor_name"]     = assigned_doctor
        llm_report["doctor_recommendation"]["appointment_slot"] = selected_slot

        return {
            "title": "Medical Assessment Report",
            "generated_by": "Amrutha AI",
            "patient_data": collected_data,
            "medical_analysis": llm_report,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Report Gen Error: {e}")
        return {"title": "Error Report", "error": str(e)}

