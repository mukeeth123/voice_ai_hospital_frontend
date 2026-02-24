from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional

class PatientData(BaseModel):
    """
    Input data model for patient assessment.
    """
    name: str = Field(..., description="Patient's name")
    age: str = Field(..., description="Patient's age")
    gender: str = Field(..., description="Patient's gender")
    email: Optional[str] = Field(None, description="Patient's email address for reports")
    phone: Optional[str] = Field(None, description="Patient's phone number for SMS")
    medical_history: Optional[str] = Field("None", description="Previous medical history")
    symptoms: str = Field(..., description="Current symptoms reported by patient")
    bp: Optional[str] = Field("Not Recorded", description="Blood Pressure")
    sugar: Optional[str] = Field("Not Recorded", description="Blood Sugar level")
    language: str = Field("English", description="Preferred language (English, Hindi, Kannada)")

class MedicalAssessment(BaseModel):
    """
    Structured response from Arogya AI Medical Architect.
    """
    urgency_level: Literal["Low", "Medium", "High", "Critical"] = Field(
        ..., 
        description="Assessed urgency level based on symptoms and vitals."
    )
    possible_conditions: List[str] = Field(
        ..., 
        description="List of 1-3 possible medical conditions."
    )
    suggested_tests: List[str] = Field(
        ..., 
        description="List of suggested diagnostic tests."
    )
    recommended_specialist: str = Field(
        ..., 
        description="The type of specialist doctor recommended (e.g., Cardiologist, Neurologist, General Physician)."
    )
    explanation: str = Field(
        ..., 
        description="Detailed medical reasoning for the assessment."
    )
    disclaimer: str = Field(
        default="This is an AI-generated assessment and not a substitute for professional medical advice. Please consult a doctor.",
        description="Mandatory medical disclaimer."
    )
    avatar_message: str = Field(
        ..., 
        description="A short, friendly, comforting message for the patient (2-4 sentences) IN THE PATIENT'S PREFERRED LANGUAGE. Address them by name if known."
    )
    doctor_advice: str = Field(
        ...,
        description="Short advice from a specialist perspective (in the preferred language)."
    )
    precautions: List[str] = Field(
        ...,
        description="Bullet-style list of precautions (in the preferred language)."
    )
    lifestyle_recommendations: List[str] = Field(
        ...,
        description="Diet, rest, hydration, and exercise suggestions (in the preferred language)."
    )
    follow_up_steps: List[str] = Field(
        ...,
        description="Step-by-step guidance after appointment (basic tests, when to consult again) (in the preferred language)."
    )
    emergency_warning: str = Field(
        default="",
        description="Clear warning instructions if urgency is High/Critical. Empty string otherwise (in the preferred language)."
    )

    @field_validator('possible_conditions', 'suggested_tests', 'precautions', 'lifestyle_recommendations', 'follow_up_steps', mode='before')
    def split_string(cls, v):
        if isinstance(v, str):
            # Handle potential markdown bullets issues if the LLM outputs them despite JSON instruction
            cleaned = v.replace('*', '').replace('-', '')
            return [x.strip() for x in cleaned.split(',') if x.strip()]
        return v

class AnalysisResponse(BaseModel):
    """
    Combined response with Medical Data and TTS Audio.
    """
    medical_data: MedicalAssessment
    tts_audio_base64: Optional[str] = Field(None, description="Base64 encoded MP3 audio of the avatar message")

class BookingRequest(BaseModel):
    patient_data: PatientData
    medical_report: MedicalAssessment
    selected_doctor: str = Field(..., description="Name of the selected doctor")
    appointment_time: str = Field(..., description="Scheduled time for appointment")
    confirm_booking: bool = Field(..., description="Whether the user confirmed the booking")

class BookingResponse(BaseModel):
    status: Optional[str] = None
    appointment_status: Optional[str] = None
    email_status: Optional[str] = None
    sms_status: Optional[str] = None
    reason: Optional[str] = None
    tts_audio_base64: Optional[str] = None

class VoiceIntakeRequest(BaseModel):
    """
    Request model for voice intake conversation.
    """
    conversation_history: List[dict] = Field(default_factory=list, description="Full chat history with role and content")
    latest_user_input: str = Field(default="", description="Most recent user message")
    language: str = Field(default="English", description="User's preferred language")
    editing_field: Optional[str] = Field(None, description="Field key being edited from summary screen")
    current_field: Optional[str] = Field(None, description="Current field being validated")

class VoiceIntakeResponse(BaseModel):
    """
    Response model for voice intake conversation.
    """
    message: str = Field(..., description="What the Avatar should say next")
    field_key: str = Field(..., description="Which field is being collected")
    expected_type: Literal["string", "number", "date", "email", "phone", "choice"] = Field(..., description="Input type for dynamic rendering")
    validation_rules: dict = Field(default_factory=dict, description="Validation rules for the field")
    is_intake_complete: bool = Field(default=False, description="Whether all required fields are collected")
    collected_data: dict = Field(default_factory=dict, description="All validated data collected so far")
    next_action: Literal["ask", "validate", "summary", "complete"] = Field(..., description="What the frontend should do next")
    validation_error: Optional[str] = Field(None, description="Error message if validation failed")
    tts_audio_base64: Optional[str] = Field(None, description="Base64 encoded TTS audio")
    booking_type: Optional[Literal["instant", "scheduled"]] = Field(None, description="Type of booking based on urgency")
    available_slots: Optional[List[str]] = Field(None, description="Available time slots for scheduled bookings")
    choices: Optional[List[str]] = Field(None, description="Options for choice-type fields")
