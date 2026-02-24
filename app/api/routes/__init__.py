from fastapi import APIRouter
from app.api.routes import json_intake, json_appointment, tts

router = APIRouter()

router.include_router(json_intake.router, tags=["JSON Intake"])
router.include_router(json_appointment.router, tags=["JSON Appointment"])
router.include_router(tts.router, tags=["TTS"])
