import re
from datetime import datetime
from typing import Optional, Tuple

class InputValidator:
    """
    Strict validation for patient intake fields.
    Returns (is_valid, error_message)
    """
    
    @staticmethod
    def validate_phone(value: str) -> Tuple[bool, Optional[str]]:
        """Expects 10 digit number. Ignores spaces/dashes."""
        clean_num = re.sub(r'[\s\-]', '', str(value))
        if not re.match(r'^\d{10}$', clean_num):
            return False, "Please provide a valid 10-digit phone number."
        return True, None

    @staticmethod
    def validate_email(value: str) -> Tuple[bool, Optional[str]]:
        """Basic email regex."""
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            return False, "Please provide a valid email address."
        return True, None

    @staticmethod
    def validate_age(value: str) -> Tuple[bool, Optional[str]]:
        """Expects numeric age between 1 and 120."""
        try:
            age = int(value)
            if 1 <= age <= 120:
                return True, None
            return False, "Please provide a realistic age (1-120)."
        except ValueError:
            return False, "Please provide your age as a number."

    @staticmethod
    def validate_date(value: str) -> Tuple[bool, Optional[str]]:
        """Expects YYYY-MM-DD or standard formats. (Simplified for MVP)"""
        # For MVP, we might accept dynamic date strings if we use an LLM parser,
        # but for strict mode, we'd want YYYY-MM-DD.
        # Let's assume the frontend sends YYYY-MM-DD for 'date' type inputs.
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True, None
        except ValueError:
            return False, "Please use the date picker or format YYYY-MM-DD."

    @staticmethod
    def validate_blood_group(value: str) -> Tuple[bool, Optional[str]]:
        """Strict Blood Group Regex (A, B, AB, O with + or -)."""
        # Case insensitive match, e.g. A+, o-, AB +, etc.
        clean = value.strip().upper().replace(" ", "")
        if not re.match(r"^(A|B|AB|O)[+-]$", clean) and "KNOW" not in clean: # Allow 'Don't Know'
            return False, "Please enter a valid Blood Group (e.g., A+, O-)."
        return True, None

    @staticmethod
    def validate_weight(value: str) -> Tuple[bool, Optional[str]]:
        """Weight in Kg (1-300)."""
        try:
            w = float(value)
            if 1 <= w <= 300:
                return True, None
            return False, "Please provide a realistic weight in kg."
        except ValueError:
            return False, "Please enter weight as a number."

    @staticmethod
    def validate(field_type: str, value: str) -> Tuple[bool, Optional[str]]:
        """Generic entry point."""
        if not value or not str(value).strip():
             return False, "This field cannot be empty."

        if field_type == 'phone':
            return InputValidator.validate_phone(value)
        elif field_type == 'email':
            return InputValidator.validate_email(value)
        elif field_type == 'age':
            return InputValidator.validate_age(value)
        elif field_type == 'date':
            return InputValidator.validate_date(value)
        elif field_type == 'blood_group':
            return InputValidator.validate_blood_group(value)
        elif field_type == 'weight':
            return InputValidator.validate_weight(value)
        elif field_type == 'number':
             # General number check
             if not str(value).replace(".", "", 1).isdigit():
                 return False, "Please enter a valid number."
        
        return True, None

validator = InputValidator()
