"""
NOVA_CORE — AI Engine (REST Directo)
Comunicación directa con la API de Google Gemini para máxima compatibilidad.
"""

import aiohttp
import json
from bot_engine.config import GEMINI_API_KEY
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.ai")

class AIEngine:
    def __init__(self):
        # Usamos la versión estable v1 y el modelo gemini-pro
        self.api_url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
        if not GEMINI_API_KEY:
            logger.warning("⚠️ GEMINI_API_KEY no configurada.")


    async def _call_gemini(self, prompt: str) -> str:
        """Realiza una petición directa por REST a la API de Google."""
        if not GEMINI_API_KEY:
            return None

        url = f"{self.api_url}?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        err_text = await response.text()
                        logger.error(f"Error API Gemini ({response.status}): {err_text}")
                        return None
                    
                    data = await response.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                logger.error(f"Fallo en conexión REST con Gemini: {e}")
                return None

    async def generate_press_kit_bio(self, user_notes: str) -> dict:
        """Genera biografía profesional."""
        prompt = f"""
        Actúa como un experto en marketing musical. Genera una biografía profesional para un DJ basada en esto: "{user_notes}".
        
        FORMATO DE RESPUESTA (Obligatorio):
        ESP: [Biografía en español, tono profesional y épico]
        ENG: [Professional bio in English]
        """

        text = await self._call_gemini(prompt)
        if not text:
            return None

        try:
            # Parseo robusto
            esp = text.split("ESP:")[1].split("ENG:")[0].strip()
            eng = text.split("ENG:")[1].strip()
            return {"es": esp, "en": eng}
        except:
            # Si el formato falla, devolvemos el texto bruto repartido
            parts = text.split("\n\n")
            return {"es": parts[0], "en": parts[-1]}

    async def get_career_advice(self, user_question: str) -> str:
        """Responde dudas sobre la carrera musical."""
        prompt = f"""
        Eres NOVA, mentor experto en música electrónica. Responde de forma corta y motivadora: "{user_question}"
        """
        response = await self._call_gemini(prompt)
        return response if response else "Lo siento, mi conexión cerebral ha fallado."

# Instancia única
ai_engine = AIEngine()

