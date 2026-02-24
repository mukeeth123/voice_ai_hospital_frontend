import json
import logging
import re
from typing import Dict, Any, List
from groq import AsyncGroq
from app.core.config import settings

logger = logging.getLogger(__name__)

class IntakeService:
    """
    AI-driven voice intake service that manages conversational patient data collection.
    """
    
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama3-70b-8192"
        
    # Define the intake field schema
    INTAKE_FIELDS = [
        {"key": "name", "type": "string", "required": True, "question": "What is your full name?", "validation": "text_only"},
        {"key": "email", "type": "email", "required": True, "question": "What is your email address?", "validation": "email"},
        {"key": "phone", "type": "phone", "required": True, "question": "What is your phone number?", "validation": "phone"},
        {"key": "dob", "type": "date", "required": True, "question": "What is your date of birth?", "validation": "date"},
        {"key": "gender", "type": "choice", "required": True, "question": "What is your gender?", "choices": ["Male", "Female", "Other"], "validation": "choice"},
        {"key": "weight", "type": "number", "required": True, "question": "What is your weight in kilograms?", "validation": "positive_number"},
        {"key": "height", "type": "number", "required": True, "question": "What is your height in centimeters?", "validation": "positive_number"},
        {"key": "blood_group", "type": "choice", "required": True, "question": "What is your blood group?", "choices": ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "Unknown"], "validation": "choice"},
        {"key": "smoking_status", "type": "choice", "required": True, "question": "What is your smoking status?", "choices": ["Never", "Former", "Current"], "validation": "choice"},
        {"key": "alcohol_consumption", "type": "choice", "required": True, "question": "How often do you consume alcohol?", "choices": ["None", "Occasional", "Regular"], "validation": "choice"},
        {"key": "has_diabetes", "type": "choice", "required": True, "question": "Do you have diabetes?", "choices": ["Yes", "No"], "validation": "choice"},
        {"key": "has_bp_issues", "type": "choice", "required": True, "question": "Do you have blood pressure issues?", "choices": ["Yes", "No"], "validation": "choice"},
        {"key": "chronic_diseases", "type": "string", "required": False, "question": "Do you have any chronic diseases? (You can say 'None' if you don't have any)", "validation": "any"},
        {"key": "allergies", "type": "string", "required": False, "question": "Do you have any allergies? (You can say 'None' if you don't have any)", "validation": "any"},
        {"key": "medications", "type": "string", "required": False, "question": "Are you currently taking any medications? (You can say 'None' if you're not)", "validation": "any"},
        {"key": "recent_surgeries", "type": "string", "required": False, "question": "Have you had any recent surgeries? (You can say 'None' if you haven't)", "validation": "any"},
        {"key": "symptoms", "type": "string", "required": False, "question": "What symptoms are you experiencing today?", "validation": "any"},
        {"key": "symptom_duration", "type": "string", "required": False, "question": "How long have you been experiencing these symptoms?", "validation": "any"},
        {"key": "pain_level", "type": "number", "required": False, "question": "On a scale of 0 to 10, what is your pain level? (0 = no pain, 10 = worst pain)", "validation": "pain_scale"},
        {"key": "family_history", "type": "string", "required": False, "question": "Is there any relevant family medical history?", "validation": "any"},
        {"key": "medical_history", "type": "string", "required": False, "question": "Do you have any past medical history we should know about?", "validation": "any"},
        {"key": "emergency_contact", "type": "phone", "required": True, "question": "What is your emergency contact number?", "validation": "phone"},
        {"key": "doctor_acknowledgment", "type": "choice", "required": True, "question": "Do you want to proceed with the assigned doctor?", "choices": ["Proceed"], "validation": "choice"},
        {"key": "selected_slot", "type": "choice", "required": True, "question": "Please select a time slot:", "choices": [], "validation": "choice"},
        {"key": "payment_status", "type": "payment", "required": True, "question": "Please complete the payment to confirm your appointment.", "validation": "payment"}
    ]
    
    async def process_intake(self, history: List[Dict], user_input: str, language: str) -> Dict[str, Any]:
        """
        Processes the intake conversation and returns the next step.
        
        Args:
            history: Conversation history
            user_input: Latest user input
            language: Preferred language
            
        Returns:
            Dict containing message, field_key, expected_type, etc.
        """
        try:
            # Build conversation context
            collected_data = self._extract_collected_data(history)
            
            # Determine next field
            next_field = self._get_next_field(collected_data)
            
            # If all fields collected, return summary action
            if not next_field:
                return {
                    "message": self._get_summary_message(collected_data, language),
                    "field_key": "",
                    "expected_type": "string",
                    "validation_rules": {},
                    "is_intake_complete": True,
                    "collected_data": collected_data,
                    "next_action": "summary"
                }
            
            # If this is first call (no history), greet
            if not history or len(history) == 0:
                greeting = self._get_greeting(language)
                return {
                    "message": greeting,
                    "field_key": "name",
                    "expected_type": "string",
                    "validation_rules": {"pattern": "^[a-zA-Z ]+$"},
                    "is_intake_complete": False,
                    "collected_data": {},
                    "next_action": "ask"
                }
            
            # Validate last input if user provided one
            if user_input.strip():
                current_field = self._get_current_field(history)
                validation_result = self._validate_input(current_field, user_input, language)
                
                if not validation_result["valid"]:
                    # Return validation error
                    return {
                        "message": validation_result["error_message"],
                        "field_key": current_field,
                        "expected_type": self._get_field_type(current_field),
                        "validation_rules": self._get_validation_rules(current_field),
                        "options": self._get_validation_rules(current_field).get("options"), # Expose options
                        "is_intake_complete": False,
                        "collected_data": collected_data,
                        "next_action": "validate"
                    }
                
                # Valid input - store it
                collected_data[current_field] = user_input.strip()
            
            # Check if all required fields are collected
            next_field = self._get_next_field(collected_data)
            
            if not next_field:
                # Intake complete - generate summary
                summary_message = await self._generate_summary_message(collected_data, language)
                
                # Determine booking type based on symptoms
                booking_info = await self._determine_booking_type(collected_data, language)
                
                return {
                    "message": summary_message,
                    "field_key": "summary",
                    "expected_type": "string",
                    "validation_rules": {},
                    "is_intake_complete": True,
                    "collected_data": collected_data,
                    "next_action": "summary",
                    "booking_type": booking_info.get("booking_type"),
                    "available_slots": booking_info.get("available_slots")
                }
            
            # Ask next question
            question = self._generate_question(next_field, collected_data.get("name", ""), language, collected_data)
            
            return {
                "message": question,
                "field_key": next_field,
                "expected_type": self._get_field_type(next_field),
                "validation_rules": self._get_validation_rules(next_field, collected_data),
                "options": self._get_validation_rules(next_field, collected_data).get("options"), # Expose options
                "is_intake_complete": False,
                "collected_data": collected_data,
                "next_action": "ask"
            }
            
        except Exception as e:
            logger.error(f"Intake processing error: {e}")
            return self._get_fallback_response(language)
    
    def _extract_collected_data(self, history: List[Dict]) -> Dict[str, str]:
        """Extract collected data from conversation history."""
        data = {}
        i = 0
        while i < len(history):
            entry = history[i]
            if entry.get("role") == "assistant" and entry.get("field_key"):
                field = entry["field_key"]
                # Look for next user message
                if i + 1 < len(history) and history[i + 1].get("role") == "user":
                    user_response = history[i + 1].get("content", "")
                    
                    # Check if the next message after user response is a validation error
                    # If i+2 exists and is an assistant message with validation error, skip this
                    is_validation_error = False
                    if i + 2 < len(history) and history[i + 2].get("role") == "assistant":
                        next_message = history[i + 2].get("content", "")
                        if "Please enter a valid" in next_message or "Invalid" in next_message:
                            is_validation_error = True
                    
                    # Only store data if it wasn't followed by a validation error
                    if not is_validation_error and user_response.strip():
                        data[field] = user_response
            i += 1
        return data
    
    def _get_next_field(self, collected_data: Dict) -> str:
        """Get the next field to collect."""
        for field in self.INTAKE_FIELDS:
            field_key = field["key"]
            if field["required"] and (field_key not in collected_data or not collected_data[field_key]):
                return field_key
        # Check optional fields
        for field in self.INTAKE_FIELDS:
            field_key = field["key"]
            if not field["required"] and field_key not in collected_data:
                return field_key
        return ""
    
    def _get_current_field(self, history: List[Dict]) -> str:
        """Get the current field being asked."""
        # Look backwards through history to find the last field that was actually asked (not a validation error)
        # We need to find the field where a question was asked, not where validation failed
        for entry in reversed(history):
            if entry.get("role") == "assistant" and entry.get("field_key"):
                field_key = entry["field_key"]
                # Check if this is a validation error by looking at the message
                # Validation errors contain phrases like "Please enter a valid"
                message = entry.get("content", "")
                if "Please enter a valid" not in message and "Invalid" not in message:
                    return field_key
        return "name"
    
    def _validate_input(self, field: str, value: str, language: str) -> Dict[str, Any]:
        """Validate user input for a specific field."""
        value = value.strip()
        
        validations = {
            "name": {
                "check": lambda v: v.replace(" ", "").isalpha() and len(v) > 1,
                "error": {
                    "English": "Please enter a valid name using only alphabets.",
                    "Hindi": "कृपया केवल अक्षरों का उपयोग करके एक मान्य नाम दर्ज करें।",
                    "Kannada": "ದಯವಿಟ್ಟು ಅಕ್ಷರಗಳನ್ನು ಮಾತ್ರ ಬಳಸಿ ಮಾನ್ಯ ಹೆಸರನ್ನು ನಮೂದಿಸಿ."
                }
            },
            "email": {
                "check": lambda v: "@" in v and len(v) > 3,
                "error": {
                    "English": "Please enter a valid email address.",
                    "Hindi": "कृपया एक मान्य ईमेल पता दर्ज करें।",
                    "Kannada": "ದಯವಿಟ್ಟು ಮಾನ್ಯ ಇಮೇಲ್ ವಿಳಾಸವನ್ನು ನಮೂದಿಸಿ."
                }
            },
            "phone": {
                "check": lambda v: v.isdigit() and len(v) == 10,
                "error": {
                    "English": "Please enter a valid 10-digit phone number.",
                    "Hindi": "कृपया 10 अंकों का मान्य फ़ोन नंबर दर्ज करें।",
                    "Kannada": "ದಯವಿಟ್ಟು ಮಾನ್ಯ 10-ಅಂಕಿಯ ಫೋನ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ."
                }
            },
            "emergency_contact": {
                "check": lambda v: v.isdigit() and len(v) == 10,
                "error": {
                    "English": "Please enter a valid 10-digit emergency contact number.",
                    "Hindi": "कृपया 10 अंकों का मान्य आपातकालीन संपर्क नंबर दर्ज करें।",
                    "Kannada": "ದಯವಿಟ್ಟು ಮಾನ್ಯ 10-ಅಂಕಿಯ ತುರ್ತು ಸಂಪರ್ಕ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ."
                }
            },
            "weight": {
                "check": lambda v: v.replace(".", "").isdigit() and 1 <= float(v) <= 300,
                "error": {
                    "English": "Please enter a valid weight between 1 and 300 kg.",
                    "Hindi": "कृपया 1 से 300 किलो के बीच वजन दर्ज करें।",
                    "Kannada": "ದಯವಿಟ್ಟು 1 ಮತ್ತು 300 ಕೆಜಿ ನಡುವೆ ಮಾನ್ಯ ತೂಕವನ್ನು ನಮೂದಿಸಿ."
                }
            },
            "height": {
                "check": lambda v: v.replace(".", "").isdigit() and 30 <= float(v) <= 250,
                "error": {
                    "English": "Please enter a valid height between 30 and 250 cm.",
                    "Hindi": "कृपया 30 से 250 सेमी के बीच ऊंचाई दर्ज करें।",
                    "Kannada": "ದಯವಿಟ್ಟು 30 ಮತ್ತು 250 ಸೆಂ.ಮೀ ನಡುವೆ ಮಾನ್ಯ ಎತ್ತರವನ್ನು ನಮೂದಿಸಿ."
                }
            },
            "gender": {
                "check": lambda v: v.lower() in ["male", "female", "other"],
                "error": {
                    "English": "Please select Male, Female, or Other.",
                    "Hindi": "कृपया पुरुष, महिला या अन्य चुनें।",
                    "Kannada": "ದಯವಿಟ್ಟು ಪುರುಷ, ಮಹಿಳೆ ಅಥವಾ ಇತರೆ ಆಯ್ಕೆಮಾಡಿ."
                }
            },
            "has_diabetes": {
                "check": lambda v: v.lower() in ["yes", "no"],
                "error": {
                    "English": "Please answer Yes or No.",
                    "Hindi": "कृपया हां या नहीं उत्तर दें।",
                    "Kannada": "ದಯವಿಟ್ಟು ಹೌದು ಅಥವಾ ಇಲ್ಲ ಎಂದು ಉತ್ತರಿಸಿ."
                }
            },
            "has_bp_issues": {
                "check": lambda v: v.lower() in ["yes", "no"],
                "error": {
                    "English": "Please answer Yes or No.",
                    "Hindi": "कृपया हां या नहीं उत्तर दें।",
                    "Kannada": "ದಯವಿಟ್ಟು ಹೌದು ಅಥವಾ ಇಲ್ಲ ಎಂದು ಉತ್ತರಿಸಿ."
                }
            },
            "blood_group": {
                "check": lambda v: v.upper() in ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "UNKNOWN"],
                "error": {
                    "English": "Please select a valid blood group (A+, A-, B+, B-, O+, O-, AB+, AB-, Unknown).",
                    "Hindi": "कृपया एक मान्य रक्त समूह चुनें (A+, A-, B+, B-, O+, O-, AB+, AB-, Unknown)।",
                    "Kannada": "ದಯವಿಟ್ಟು ಮಾನ್ಯ ರಕ್ತ ಗುಂಪನ್ನು ಆಯ್ಕೆಮಾಡಿ (A+, A-, B+, B-, O+, O-, AB+, AB-, Unknown)."
                }
            },
            "smoking_status": {
                "check": lambda v: v.lower() in ["never", "former", "current"],
                "error": {
                    "English": "Please select Never, Former, or Current.",
                    "Hindi": "कृपया कभी नहीं, पूर्व या वर्तमान चुनें।",
                    "Kannada": "ದಯವಿಟ್ಟು ಎಂದಿಗೂ ಇಲ್ಲ, ಹಿಂದೆ, ಅಥವಾ ಪ್ರಸ್ತುತ ಆಯ್ಕೆಮಾಡಿ."
                }
            },
            "alcohol_consumption": {
                "check": lambda v: v.lower() in ["none", "occasional", "regular"],
                "error": {
                    "English": "Please select None, Occasional, or Regular.",
                    "Hindi": "कृपया कोई नहीं, कभी-कभी या नियमित चुनें।",
                    "Kannada": "ದಯವಿಟ್ಟು ಯಾವುದೂ ಇಲ್ಲ, ಸಾಂದರ್ಭಿಕ, ಅಥವಾ ನಿಯಮಿತ ಆಯ್ಕೆಮಾಡಿ."
                }
            },
            "pain_level": {
                "check": lambda v: v.replace(".", "").isdigit() and 0 <= float(v) <= 10,
                "error": {
                    "English": "Please enter a pain level between 0 and 10.",
                    "Hindi": "कृपया 0 से 10 के बीच दर्द का स्तर दर्ज करें।",
                    "Kannada": "ದಯವಿಟ್ಟು 0 ಮತ್ತು 10 ರ ನಡುವೆ ನೋವಿನ ಮಟ್ಟವನ್ನು ನಮೂದಿಸಿ."
                }
            },
            "doctor_acknowledgment": {
                "check": lambda v: True,  # Accepts any positive acknowledgment or button click
                "error": {"English": "Please confirm to proceed."}
            },
            "selected_slot": {
                "check": lambda v: True,  # Validation logic could be stricter against available slots
                "error": {"English": "Please select a valid slot."}
            },
            "payment_status": {
                "check": lambda v: True,  # Payment logic handled by frontend/payment gateway
                "error": {"English": "Payment required."}
            }
        }
        
        # Fields that allow free text
        if field in ["dob", "allergies", "medications", "symptoms", "medical_history", "chronic_diseases", "recent_surgeries", "symptom_duration", "family_history"]:
            return {"valid": True}
        
        if field in validations:
            rule = validations[field]
            try:
                if rule["check"](value):
                    return {"valid": True}
                else:
                    return {
                        "valid": False,
                        "error_message": rule["error"].get(language, rule["error"]["English"])
                    }
            except:
                return {
                    "valid": False,
                    "error_message": rule["error"].get(language, rule["error"]["English"])
                }
        
        return {"valid": True}
    
    def _get_field_type(self, field: str) -> str:
        """Get the expected input type for a field."""
        # Find field in INTAKE_FIELDS
        for f in self.INTAKE_FIELDS:
            if f["key"] == field:
                return f["type"]
        return "string"
    
    async def _determine_slots(self):
         """Helper to return slots"""
         return [
             "Morning (10:00 AM)", 
             "Afternoon (2:00 PM)", 
             "Evening (6:00 PM)"
         ]

    def _get_validation_rules(self, field: str, collected_data: Dict = None) -> Dict:
        """Get validation rules for a field."""
        # Find field in INTAKE_FIELDS and return choices if available
        for f in self.INTAKE_FIELDS:
            if f["key"] == field:
                if field == "selected_slot":
                     # Return dynamic slots (simplified for now)
                     return {"options": ["10:00 AM", "12:00 PM", "4:00 PM", "6:00 PM"]}
                if "choices" in f:
                    return {"options": f["choices"]}
                elif f["type"] == "number":
                    if field == "pain_level":
                        return {"min": 0, "max": 10}
                    elif field == "weight":
                        return {"min": 1, "max": 300}
                    elif field == "height":
                        return {"min": 30, "max": 250}
        return {}
    
    def _generate_question(self, field: str, name: str, language: str, collected_data: Dict = {}) -> str:
        """Generate the next question."""
        prefix = f"{name}, " if name else ""
        
        questions = {
            "English": {
                "name": "Hello! I am Arogya AI. What is your full name?",
                "email": f"{prefix}what is your email address?",
                "phone": "What is your phone number?",
                "dob": f"{prefix}what is your date of birth?",
                "gender": "What is your gender?",
                "weight": "What is your weight in kilograms?",
                "height": "What is your height in centimeters?",
                "has_diabetes": f"{prefix}do you have diabetes?",
                "has_bp_issues": "Do you have blood pressure issues?",
                "allergies": "Do you have any allergies? If none, please say 'None'.",
                "medications": "Are you currently taking any medications? If none, please say 'None'.",
                "symptoms": f"{prefix}what symptoms are you experiencing today?",
                "medical_history": "Please describe your past medical history or any other details."
            },
            "Hindi": {
                "name": "नमस्ते! मैं आरोग्य AI हूं। आपका पूरा नाम क्या है?",
                "email": f"{prefix}आपका ईमेल पता क्या है?",
                "phone": "आपका फोन नंबर क्या है?",
                "dob": f"{prefix}आपकी जन्म तिथि क्या है?",
                "gender": "आपका लिंग क्या है?",
                "weight": "आपका वजन किलोग्राम में क्या है?",
                "height": "आपकी ऊंचाई सेंटीमीटर में क्या है?",
                "has_diabetes": f"{prefix}क्या आपको मधुमेह है?",
                "has_bp_issues": "क्या आपको रक्तचाप की समस्या है?",
                "allergies": "क्या आपको कोई एलर्जी है? यदि नहीं, तो 'कोई नहीं' कहें।",
                "medications": "क्या आप वर्तमान में कोई दवाएं ले रहे हैं? यदि नहीं, तो 'कोई नहीं' कहें।",
                "symptoms": f"{prefix}आज आप किन लक्षणों का अनुभव कर रहे हैं?",
                "medical_history": "कृपया अपने पिछले चिकित्सा इतिहास या किसी अन्य विवरण का वर्णन करें।"
            },
            "Kannada": {
                "name": "ನಮಸ್ಕಾರ! ನಾನು ಆರೋಗ್ಯ AI. ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರು ಏನು?",
                "email": f"{prefix}ನಿಮ್ಮ ಇಮೇಲ್ ವಿಳಾಸ ಏನು?",
                "phone": "ನಿಮ್ಮ ಫೋನ್ ಸಂಖ್ಯೆ ಏನು?",
                "dob": f"{prefix}ನಿಮ್ಮ ಹುಟ್ಟಿದ ದಿನಾಂಕ ಏನು?",
                "gender": "ನಿಮ್ಮ ಲಿಂಗ ಏನು?",
                "weight": "ನಿಮ್ಮ ತೂಕ ಕಿಲೋಗ್ರಾಂಗಳಲ್ಲಿ ಎಷ್ಟು?",
                "height": "ನಿಮ್ಮ ಎತ್ತರ ಸೆಂಟಿಮೀಟರ್‌ಗಳಲ್ಲಿ ಎಷ್ಟು?",
                "has_diabetes": f"{prefix}ನಿಮಗೆ ಮಧುಮೇಹವಿದೆಯೇ?",
                "has_bp_issues": "ನಿಮಗೆ ರಕ್ತದೊತ್ತಡ ಸಮಸ್ಯೆಗಳಿವೆಯೇ?",
                "allergies": "ನಿಮಗೆ ಯಾವುದೇ ಅಲರ್ಜಿಗಳಿವೆಯೇ? ಇಲ್ಲದಿದ್ದರೆ, 'ಯಾವುದೂ ಇಲ್ಲ' ಎಂದು ಹೇಳಿ.",
                "medications": "ನೀವು ಪ್ರಸ್ತುತ ಯಾವುದೇ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳುತ್ತಿದ್ದೀರಾ? ಇಲ್ಲದಿದ್ದರೆ, 'ಯಾವುದೂ ಇಲ್ಲ' ಎಂದು ಹೇಳಿ.",
                "symptoms": f"{prefix}ಇಂದು ನೀವು ಯಾವ ರೋಗಲಕ್ಷಣಗಳನ್ನು ಅನುಭವಿಸುತ್ತಿದ್ದೀರಿ?",
                "medical_history": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಹಿಂದಿನ ವೈದ್ಯಕೀಯ ಇತಿಹಾಸ ಅಥವಾ ಯಾವುದೇ ಇತರ ವಿವರಗಳನ್ನು ವಿವರಿಸಿ."
            }
        }
        
        if field == "doctor_acknowledgment":
            doctor = self._assign_doctor(collected_data.get("symptoms", ""))
            
            # Localized doctor acknowledgment
            ack_messages = {
                "English": f"Based on your symptoms, I have assigned you to **{doctor}**. Consultation Fee: ₹499. Shall we proceed to book a slot?",
                "Hindi": f"आपके लक्षणों के आधार पर, मैंने आपको **{doctor}** को सौंपा है। परामर्श शुल्क: ₹499। क्या हम आगे बढ़ें?",
                "Kannada": f"ನಿಮ್ಮ ರೋಗಲಕ್ಷಣಗಳ ಆಧಾರದ ಮೇಲೆ, ನಾನು ನಿಮ್ಮನ್ನು **{doctor}** ಗೆ ನಿಯೋಜಿಸಿದ್ದೇನೆ. ಸಮಾಲೋಚನೆ ಶುಲ್ಕ: ₹499. ನಾವು ಮುಂದುವರಿಯೋಣವೇ?"
            }
            return ack_messages.get(language, ack_messages["English"])

        if field == "selected_slot":
            slot_messages = {
                "English": "Please select a suitable time for your consultation:",
                "Hindi": "कृपया अपने परामर्श के लिए उपयुक्त समय चुनें:",
                "Kannada": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಸಮಾಲೋಚನೆಗೆ ಸೂಕ್ತ ಸಮಯವನ್ನು ಆಯ್ಕೆಮಾಡಿ:"
            }
            return slot_messages.get(language, slot_messages["English"])

        if field == "payment_status":
            payment_messages = {
                "English": "Please complete the secure payment of ₹499 to confirm your appointment.",
                "Hindi": "कृपया अपनी नियुक्ति की पुष्टि करने के लिए ₹499 का सुरक्षित भुगतान पूरा करें।",
                "Kannada": "ನಿಮ್ಮ ನೇಮಕಾತಿಯನ್ನು ಖಚಿತಪಡಿಸಲು ದಯವಿಟ್ಟು ₹499 ಸುರಕ್ಷಿತ ಪಾವತಿಯನ್ನು ಪೂರ್ಣಗೊಳಿಸಿ."
            }
            return payment_messages.get(language, payment_messages["English"])

        lang_questions = questions.get(language, questions["English"])
        return lang_questions.get(field, f"Please provide your {field}.")
    
    def _assign_doctor(self, symptoms: str) -> str:
        """Assign a doctor based on symptoms."""
        symptoms = symptoms.lower()
        if any(x in symptoms for x in ["heart", "chest", "breath"]):
            return "Dr. Aditi Sharma (Cardiologist)"
        elif any(x in symptoms for x in ["skin", "rash", "itch"]):
            return "Dr. Rajesh Gupta (Dermatologist)"
        elif any(x in symptoms for x in ["child", "baby", "infant"]):
            return "Dr. Sneha Patil (Pediatrician)"
        else:
            return "Dr. Arun Kumar (General Physician)"
    
    def _get_greeting(self, language: str) -> str:
        """Get initial greeting."""
        greetings = {
            "English": "Hi 👋 Welcome to Arogya AI. I am your medical assistant. I will help you complete your health intake and guide you through booking your consultation. May I know your full name to begin your reservation?",
            "Hindi": "नमस्ते 👋 आरोग्य AI में आपका स्वागत है। मैं आपका चिकित्सा सहायक हूं। मैं आपके स्वास्थ्य इंटेक को पूरा करने और आपके परामर्श की बुकिंग में आपकी मदद करूंगा। अपना आरक्षण शुरू करने के लिए मुझे आपका पूरा नाम बता सकते हैं?",
            "Kannada": "ನಮಸ್ಕಾರ 👋 ಆರೋಗ್ಯ AI ಗೆ ಸುಸ್ವಾಗತ. ನಾನು ನಿಮ್ಮ ವೈದ್ಯಕೀಯ ಸಹಾಯಕ. ನಿಮ್ಮ ಆರೋಗ್ಯ ಸೇವನೆಯನ್ನು ಪೂರ್ಣಗೊಳಿಸಲು ಮತ್ತು ನಿಮ್ಮ ಸಮಾಲೋಚನೆಯನ್ನು ಬುಕ್ ಮಾಡಲು ನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ. ನಿಮ್ಮ ಕಾಯ್ದಿರಿಸುವಿಕೆಯನ್ನು ಪ್ರಾರಂಭಿಸಲು ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರು ತಿಳಿಸಬಹುದೇ?"
        }
        return greetings.get(language, greetings["English"])
    
    def _get_summary_message(self, data: Dict, language: str) -> str:
        """Generate summary message."""
        messages = {
            "English": "Thank you for providing all the information. Please review your details carefully before we proceed to the medical analysis.",
            "Hindi": "सभी जानकारी प्रदान करने के लिए धन्यवाद। कृपया चिकित्सा विश्लेषण के लिए आगे बढ़ने से पहले अपने विवरण की सावधानीपूर्वक समीक्षा करें।",
            "Kannada": "ಎಲ್ಲಾ ಮಾಹಿತಿಯನ್ನು ಒದಗಿಸಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು. ವೈದ್ಯಕೀಯ ವಿಶ್ಲೇಷಣೆಗೆ ಮುಂದುವರಿಯುವ ಮೊದಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಎಚ್ಚರಿಕೆಯಿಂದ ಪರಿಶೀಲಿಸಿ."
        }
        return messages.get(language, messages["English"])
    
    async def _generate_summary_message(self, data: Dict, language: str) -> str:
        """Generate personalized summary message using LLM."""
        try:
            name = data.get("name", "").split()[0] if data.get("name") else ""
            personalization = f"Address the patient as '{name}'" if name else "Be friendly and professional"
            
            system_prompt = f"""
            You are Arogya AI, a caring medical assistant.
            Generate a brief, warm message asking the patient to review their information before proceeding.
            
            Rules:
            1. {personalization}
            2. Keep it concise (2-3 sentences max)
            3. Be reassuring and professional
            4. Output ONLY the message text in {language}
            5. Mention that they can edit any field if needed
            """
            
            user_content = "Generate a message asking the patient to review their intake information."
            
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            # logger.error(f"Error generating summary message: {e}") # Commented out as logger is not defined in this snippet
            return self._get_summary_message(data, language)
    
    async def _determine_booking_type(self, data: Dict, language: str) -> Dict:
        """
        Determine booking type based on symptoms and urgency.
        Returns booking_type ('instant' or 'scheduled') and available_slots if scheduled.
        """
        try:
            # Extract relevant data
            symptoms = data.get("symptoms", "").lower()
            pain_level = int(data.get("pain_level", 0)) if data.get("pain_level", "").replace(".", "").isdigit() else 0
            symptom_duration = data.get("symptom_duration", "").lower()
            
            # Urgent keywords
            urgent_keywords = [
                "chest pain", "difficulty breathing", "severe pain", "bleeding", "unconscious",
                "stroke", "heart attack", "seizure", "severe headache", "high fever",
                "accident", "injury", "emergency", "critical", "urgent"
            ]
            
            # Check for urgent conditions
            is_urgent = False
            
            # High pain level
            if pain_level >= 8:
                is_urgent = True
            
            # Urgent keywords in symptoms
            for keyword in urgent_keywords:
                if keyword in symptoms:
                    is_urgent = True
                    break
            
            # Sudden onset (within hours)
            if any(word in symptom_duration for word in ["hour", "hours", "sudden", "just now", "minutes"]):
                if pain_level >= 6:
                    is_urgent = True
            
            if is_urgent:
                # Instant booking
                return {
                    "booking_type": "instant",
                    "available_slots": None
                }
            else:
                # Scheduled booking - provide time slots
                slots = [
                    "Morning (9 AM – 12 PM)",
                    "Afternoon (1 PM – 4 PM)",
                    "Evening (5 PM – 8 PM)"
                ]
                return {
                    "booking_type": "scheduled",
                    "available_slots": slots
                }
                
        except Exception as e:
            # logger.error(f"Error determining booking type: {e}") # Commented out as logger is not defined in this snippet
            # Default to scheduled booking
            return {
                "booking_type": "scheduled",
                "available_slots": [
                    "Morning (9 AM – 12 PM)",
                    "Afternoon (1 PM – 4 PM)",
                    "Evening (5 PM – 8 PM)"
                ]
            }
    
    def _get_fallback_response(self, language: str) -> Dict:
        """Fallback response on error."""
        messages = {
            "English": "I'm having trouble processing your request. Please try again.",
            "Hindi": "मुझे आपके अनुरोध को संसाधित करने में समस्या हो रही है। कृपया पुनः प्रयास करें।",
            "Kannada": "ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲು ನನಗೆ ತೊಂದರೆಯಾಗುತ್ತಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
        }
        return {
            "message": messages.get(language, messages["English"]),
            "field_key": "",
            "expected_type": "string",
            "validation_rules": {},
            "is_intake_complete": False,
            "collected_data": {},
            "next_action": "ask"
        }

# Singleton
intake_service = IntakeService()
