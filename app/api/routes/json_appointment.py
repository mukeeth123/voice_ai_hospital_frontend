from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.services.email_service import email_service
from app.services.tts_service import tts_service
from app.services.pdf_service import pdf_service
import logging
from datetime import datetime, timedelta

router = APIRouter()
logger = logging.getLogger(__name__)

class JsonAppointmentRequest(BaseModel):
    patient_data: Dict[str, Any]   # Any to support int/float age, weight etc.
    medical_analysis: Dict[str, Any]
    
class JsonAppointmentResponse(BaseModel):
    success: bool
    appointment_id: str
    appointment_details: Dict[str, Any]
    email_sent: bool
    tts_audio_base64: Optional[str] = None

@router.post("/json-appointment", response_model=JsonAppointmentResponse)
async def book_json_appointment(request: JsonAppointmentRequest):
    """
    Book appointment based on LLM-generated recommendations.
    Generate PDF and send email confirmation.
    """
    try:
        patient_data = request.patient_data
        medical_analysis = request.medical_analysis
        
        # Extract doctor recommendation
        doctor_rec = medical_analysis.get("doctor_recommendation", {})
        specialist_type = doctor_rec.get("specialist_type", "General Physician")
        urgency = doctor_rec.get("consultation_priority", doctor_rec.get("urgency", "Medium"))
        expertise = doctor_rec.get("doctor_expertise", specialist_type)

        # Use the doctor already assigned during intake; fall back to lookup
        doctor_name = (
            doctor_rec.get("doctor_name") or
            patient_data.get("assigned_doctor") or
            _get_indian_doctor_name(specialist_type)
        )

        # Use the slot the user selected; fall back to urgency-based calculation
        selected_slot = patient_data.get("selected_slot", "")
        appointment_time = (
            selected_slot if selected_slot and selected_slot != "To be confirmed"
            else _calculate_appointment_time(urgency)
        )

        # Generate appointment ID
        appointment_id = f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create appointment details
        appointment_details = {
            "appointment_id": appointment_id,
            "patient_name": patient_data.get("name", "N/A"),
            "patient_email": patient_data.get("email", "N/A"),
            "patient_phone": patient_data.get("phone", "N/A"),
            "doctor_name": doctor_name,
            "doctor_specialist": specialist_type,
            "expertise": expertise,
            "appointment_time": appointment_time,
            "urgency": urgency,
            "status": "Confirmed",
            "consultation_type": medical_analysis.get("appointment_details", {}).get("consultation_type", "Online Consultation")
        }
        
        # Generate premium PDF report (returns bytes)
        pdf_bytes = None
        try:
            pdf_bytes = pdf_service.generate_report(
                patient_data=patient_data,
                medical_analysis=medical_analysis,
                appointment_details=appointment_details,
            )
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")

        # Send email with appointment details and PDF attachment
        email_sent = False
        try:
            email_result = await email_service.send_appointment_email(
                patient_email=patient_data.get("email"),
                patient_name=patient_data.get("name", "Patient"),
                appointment_details=appointment_details,
                pdf_attachment=pdf_bytes,
            )
            email_sent = email_result.get("success", False)
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
        
        # Generate TTS confirmation message
        confirmation_message = f"Great news! Your appointment with {doctor_name} has been confirmed for {appointment_time}. A confirmation email with your detailed medical report has been sent to {patient_data.get('email')}."
        
        tts_audio = None
        try:
            tts_result = await tts_service.generate_speech(
                text=confirmation_message,
                language="English"
            )
            tts_audio = tts_result.get("audio_base64")
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
        
        return JsonAppointmentResponse(
            success=True,
            appointment_id=appointment_id,
            appointment_details=appointment_details,
            email_sent=email_sent,
            tts_audio_base64=tts_audio
        )
        
    except Exception as e:
        logger.error(f"Appointment booking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_indian_doctor_name(specialist_type: str) -> str:
    """Get appropriate Indian doctor name based on specialty."""
    import random
    
    doctor_names = {
        "Cardiologist": [
            "Dr. Rajesh Kumar (MD, DM Cardiology)",
            "Dr. Priya Sharma (MBBS, MD Cardiology)",
            "Dr. Amit Patel (MD, FACC)",
            "Dr. Sunita Reddy (DM Cardiology)"
        ],
        "Endocrinologist": [
            "Dr. Suresh Menon (MD, DM Endocrinology)",
            "Dr. Kavita Singh (MBBS, MD Endocrinology)",
            "Dr. Arun Desai (DM Endocrinology)"
        ],
        "Neurologist": [
            "Dr. Vikram Rao (MD, DM Neurology)",
            "Dr. Anjali Gupta (MBBS, MD Neurology)",
            "Dr. Ramesh Iyer (DM Neurology)"
        ],
        "Orthopedic": [
            "Dr. Karthik Nair (MS Orthopedics)",
            "Dr. Deepa Joshi (MS Orthopedics)",
            "Dr. Sanjay Verma (MS Orthopedics)"
        ],
        "Gastroenterologist": [
            "Dr. Mahesh Kulkarni (MD, DM Gastroenterology)",
            "Dr. Sneha Kapoor (DM Gastroenterology)",
            "Dr. Ravi Krishnan (MD Gastroenterology)"
        ],
        "Pulmonologist": [
            "Dr. Ashok Mehta (MD Pulmonology)",
            "Dr. Pooja Agarwal (MD Respiratory Medicine)",
            "Dr. Harish Pillai (DM Pulmonology)"
        ],
        "General Physician": [
            "Dr. Arjun Sharma (MBBS, MD)",
            "Dr. Meera Nambiar (MBBS, MD)",
            "Dr. Rahul Bansal (MBBS, MD)",
            "Dr. Lakshmi Iyer (MBBS, MD)"
        ]
    }
    
    # Find matching specialty or use General Physician as default
    for key in doctor_names.keys():
        if key.lower() in specialist_type.lower():
            return random.choice(doctor_names[key])
    
    return random.choice(doctor_names["General Physician"])

def _calculate_appointment_time(urgency: str) -> str:
    """Calculate appointment time based on urgency."""
    now = datetime.now()
    
    if urgency == "High":
        # Next available slot (within 24 hours)
        appointment_dt = now + timedelta(hours=2)
    elif urgency == "Medium":
        # Within 3 days
        appointment_dt = now + timedelta(days=2)
    else:
        # Within a week
        appointment_dt = now + timedelta(days=5)
    
    return appointment_dt.strftime("%Y-%m-%d %H:%M")

