import json
import logging
from typing import Dict, Any
from groq import AsyncGroq
from app.core.config import settings
from app.models.medical import MedicalAssessment

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def analyze_symptoms(self, patient_data: Dict[str, Any]) -> MedicalAssessment:
        """
        Analyzes patient symptoms and vitals using Groq Llama 3 to generate a strictly structured medical assessment.
        Async implementation.

        Args:
            patient_data (dict): Contains name, age, gender, medical_history, symptoms, bp, sugar, language.
        
        Returns:
            MedicalAssessment: Structured Pydantic model response.
        """
        try:
            # Extract data with defaults
            name = patient_data.get("name", "Patient")
            age = patient_data.get("age", "Unknown")
            gender = patient_data.get("gender", "Unknown")
            history = patient_data.get("medical_history", "None")
            symptoms = patient_data.get("symptoms", "")
            bp = patient_data.get("bp", "Not Recorded")
            sugar = patient_data.get("sugar", "Not Recorded")
            language = patient_data.get("language", "English")

            # Validate vital signs for emergency override
            is_emergency = self._check_vitals_emergency(bp, sugar)
            emergency_instruction = ""
            if is_emergency:
                emergency_instruction = "CRITICAL: Vitals indicate a potential emergency. Urgency MUST be High or Critical."

            # Construct System Prompt
            system_prompt = f"""
            You are Arogya AI, a senior medical AI assistant.
            Your goal is to analyze patient symptoms and vitals to provide a structured JSON assessment.
            
            RULES:
            1. Output STRICT JSON only.
            2. Language: ALL output fields (except keys) MUST be in {language}.
            3. Personalization: Address the patient as "{name}" in the 'avatar_message'. Be polite and caring.
            4. Urgency: Assess carefully. {emergency_instruction}
            5. Structure: Ensure all new fields (doctor_advice, precautions, etc.) are populated with high-quality medical content.
            
            JSON Schema:
            {{
                "urgency_level": "Low" | "Medium" | "High" | "Critical",
                "possible_conditions": ["Condition 1", "Condition 2"],
                "suggested_tests": ["Test 1", "Test 2"],
                "recommended_specialist": "Specialist Name",
                "doctor_advice": "Short specialist advice...",
                "precautions": ["Precaution 1", "Precaution 2"],
                "lifestyle_recommendations": ["Tip 1", "Tip 2"],
                "follow_up_steps": ["Step 1", "Step 2"],
                "emergency_warning": "Warning text if high urgency, else empty",
                "explanation": "Detailed reasoning...",
                "disclaimer": "Standard medical disclaimer...",
                "avatar_message": "Hello {name}, ..."
            }}
            """

            # Construct User Content
            user_content = f"""
            Patient Profile:
            - Name: {name}
            - Age: {age}
            - Gender: {gender}
            - Language: {language}
            - Medical History: {history}
            
            Current Status:
            - Symptoms: {symptoms}
            - Blood Pressure: {bp}
            - Blood Sugar: {sugar}
            
            Generate the assessment JSON.
            """

            # Call Groq API
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            response_content = completion.choices[0].message.content
            
            # Parse and Validate
            try:
                data = json.loads(response_content)
                assessment = MedicalAssessment(**data)
                return assessment
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"JSON Parsing Error: {e}. Content: {response_content}")
                return self._get_fallback_assessment(language, "Error parsing AI response.")

        except Exception as e:
            logger.error(f"Groq API Error: {e}")
            return self._get_fallback_assessment(patient_data.get("language", "English"), str(e))

    def _check_vitals_emergency(self, bp: str, sugar: str) -> bool:
        """
        Simple heuristic check for vital signs.
        """
        try:
            # Basic BP check (Systolic > 180 or Diastolic > 120 is Hypertensive Crisis)
            if "/" in str(bp):
                sys, dia = map(int, bp.split('/'))
                if sys > 180 or dia > 120 or sys < 90 or dia < 60:
                    return True
            
            # Basic Sugar check ( < 70 or > 300 mg/dL)
            if str(sugar).isdigit():
                val = int(sugar)
                if val < 70 or val > 300:
                    return True
                    
        except Exception:
            pass # If parsing fails, assume not critical based on vitals alone
        return False

    def _get_fallback_assessment(self, language: str, error_msg: str) -> MedicalAssessment:
        """
        Returns a safe fallback response if the API fails.
        """
        logger.warning(f"Using fallback assessment due to error: {error_msg}")
        
        messages = {
            "English": "I am having trouble connecting to my medical brain right now. However, based on your request, I recommend seeing a General Physician to be safe.",
            "Hindi": "मुझे अभी अपने मेडिकल डेटाबेस से जुड़ने में समस्या हो रही है। हालांकि, सुरक्षित रहने के लिए, मैं आपको सामान्य चिकित्सक (General Physician) से मिलने की सलाह देता हूं।",
            "Kannada": "ನನ್ನ ವೈದ್ಯಕೀಯ ಡೇಟಾಬೇಸ್ ಅನ್ನು ಸಂಪರ್ಕಿಸಲು ನನಗೆ ತೊಂದರೆಯಾಗುತ್ತಿದೆ. ಆದರೂ, ಸುರಕ್ಷಿತವಾಗಿರಲು, ನೀವು ಸಾಮಾನ್ಯ ವೈದ್ಯರನ್ನು (General Physician) ಕಾಣುವಂತೆ ನಾನು ಶಿಫಾರಸು ಮಾಡುತ್ತೇನೆ."
        }
        
        msg = messages.get(language, messages["English"])

        return MedicalAssessment(
            urgency_level="Medium",
            possible_conditions=["Undetermined"],
            suggested_tests=["Routine Health Checkup"],
            recommended_specialist="General Physician",
            explanation="System limitation or connection error preventing detailed analysis. Defaulting to safe recommendation.",
            disclaimer="This is a fallback system message. Please consult a doctor immediately if you feel unwell.",
            avatar_message=msg
        )

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text completion using Groq LLM.
        Now supports partial updates via kwargs.
        """
        try:
            # Combine default args with kwargs
            completion_args = {
                "messages": [{"role": "user", "content": prompt}],
                "model": self.model,
                "temperature": 0.6,
                "max_tokens": 1024,
            }
            # Update with any passed arguments (e.g. response_format)
            completion_args.update(kwargs)

            chat_completion = await self.client.chat.completions.create(**completion_args)
            content = chat_completion.choices[0].message.content
            
            # Clean Markdown Code Blocks if present
            if "```json" in content:
                content = content.replace("```json", "").replace("```", "")
            elif "```" in content:
                content = content.replace("```", "")
                
            return content.strip()
            
        except Exception as e:
            logger.error(f"Groq text generation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Groq text generation error: {e}")
            raise

# Singleton
groq_service = GroqService()
