from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.tts_service import tts_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class TTSRequest(BaseModel):
    text: str
    language: str = "English"

class TTSResponse(BaseModel):
    audio_base64: Optional[str] = None   # None when TTS is temporarily unavailable

@router.post("/tts", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """
    Generate TTS audio from text.
    Returns base64-encoded MP3 on success, or {audio_base64: null} when
    the TTS service is temporarily unavailable — never returns 500.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    result = await tts_service.generate_speech(request.text, request.language)
    return TTSResponse(audio_base64=result.get("audio_base64"))
