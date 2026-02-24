import edge_tts
import asyncio
import tempfile
import base64
import os
import logging
import uuid

logger = logging.getLogger(__name__)

class EdgeTTSService:
    def __init__(self):
        self.VOICE_MAP = {
            "English": "en-IN-NeerjaNeural",
            "Hindi": "hi-IN-SwaraNeural",
            "Kannada": "kn-IN-SapnaNeural"
        }
        self.DEFAULT_VOICE = "en-IN-NeerjaNeural"

    async def generate_speech(self, text: str, language: str = "English") -> dict:
        """
        Generates speech audio. Returns {"audio_base64": "..."} on success
        or {"audio_base64": None} if TTS is unavailable (network issue etc.)
        — never raises, so callers always get a clean dict back.
        """
        if not text:
            return {"audio_base64": None}

        temp_file_path = None
        try:
            voice = self.VOICE_MAP.get(language, self.DEFAULT_VOICE)
            logger.info(f"Generating TTS: lang={language}, voice={voice}")

            filename = f"tts_{uuid.uuid4().hex}.mp3"
            temp_file_path = os.path.join(tempfile.gettempdir(), filename)

            communicate = edge_tts.Communicate(text, voice)
            # Add a 15-second timeout so a dead network doesn't hang the request
            await asyncio.wait_for(communicate.save(temp_file_path), timeout=15)

            if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
                raise RuntimeError("TTS produced an empty file.")

            with open(temp_file_path, "rb") as f:
                audio_base64 = base64.b64encode(f.read()).decode("utf-8")

            logger.info("TTS generated successfully.")
            return {"audio_base64": audio_base64}

        except asyncio.TimeoutError:
            logger.warning("TTS timed out — network may be slow. Returning null audio.")
            return {"audio_base64": None}
        except Exception as e:
            logger.warning(f"TTS unavailable: {e}")
            return {"audio_base64": None}
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass

# Singleton instance
tts_service = EdgeTTSService()
