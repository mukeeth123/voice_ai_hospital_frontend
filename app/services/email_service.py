import aiosmtplib
import logging
from email.message import EmailMessage
from app.core.config import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host     = settings.SMTP_HOST
        self.smtp_port     = settings.SMTP_PORT
        self.smtp_user     = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email    = settings.FROM_EMAIL

    async def send_appointment_email(
        self,
        patient_email: str,
        patient_name: str,
        appointment_details: Dict[str, Any],
        pdf_attachment: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Send appointment confirmation email with optional PDF attachment (bytes).

        Args:
            patient_email:       Recipient email address.
            patient_name:        Patient's display name.
            appointment_details: Dict with doctor_name, appointment_time, etc.
            pdf_attachment:      Raw PDF bytes to attach (optional).

        Returns:
            {"success": True/False, "status": "sent"/"failed", ...}
        """
        message = EmailMessage()
        message["From"]    = self.from_email
        message["To"]      = patient_email
        message["Subject"] = "Your Amrutha AI Medical Report & Appointment Confirmation"

        doctor_name      = appointment_details.get("doctor_name", "a Specialist")
        appointment_time = appointment_details.get("appointment_time", "Pending Confirmation")
        appointment_id   = appointment_details.get("appointment_id", "N/A")
        specialist       = appointment_details.get("doctor_specialist", "")

        body = f"""Dear {patient_name},

Your appointment has been successfully confirmed with Amrutha AI.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
APPOINTMENT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Appointment ID : {appointment_id}
  Doctor         : {doctor_name}
  Specialty      : {specialist}
  Date & Time    : {appointment_time}
  Status         : Confirmed ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please find your detailed medical report attached to this email.
Share it with your doctor during the consultation.

DISCLAIMER:
This report is AI-generated for informational purposes only.
It is not a substitute for professional medical advice.

Stay Healthy,
Amrutha AI Team
"""
        message.set_content(body)

        # Attach PDF bytes if provided
        if pdf_attachment:
            filename = f"Amrutha_AI_Appointment_Report_{appointment_id}.pdf"
            message.add_attachment(
                pdf_attachment,
                maintype="application",
                subtype="pdf",
                filename=filename,
            )

        # Send via SMTP
        try:
            logger.info(f"Sending appointment email to {patient_email} via {self.smtp_host}:{self.smtp_port}")
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=False,
                start_tls=True,
            )
            logger.info("Appointment email sent successfully.")
            return {"success": True, "status": "sent"}

        except aiosmtplib.SMTPAuthenticationError:
            logger.error("SMTP Authentication failed. Check credentials.")
            return {"success": False, "status": "failed", "reason": "Authentication failed"}
        except Exception as e:
            logger.error(f"SMTP Error: {e}")
            return {"success": False, "status": "failed", "reason": str(e)}

    async def send_welcome_email(self, patient_email: str, patient_name: str) -> Dict[str, Any]:
        """Send a welcome email to the patient upon registration."""
        message = EmailMessage()
        message["From"]    = self.from_email
        message["To"]      = patient_email
        message["Subject"] = "Welcome to Amrutha AI – Your Health Companion"

        body = f"""Dear {patient_name},

Welcome to Amrutha AI!

Thank you for trusting us with your health journey. Our AI-powered assistant is here to help you understand your symptoms and guide you to the right care.

You can now:
  • Describe your symptoms using voice or text.
  • Get instant AI-powered medical assessments.
  • Book appointments with specialists effortlessly.

Stay Healthy,
Amrutha AI Team
"""
        message.set_content(body)

        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=False,
                start_tls=True,
            )
            logger.info("Welcome email sent successfully.")
            return {"success": True, "status": "sent"}
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return {"success": False, "status": "failed", "reason": str(e)}


# Singleton
email_service = EmailService()
