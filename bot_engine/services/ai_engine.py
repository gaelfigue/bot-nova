"""
NOVA_CORE — AI Engine (Google Gemini)
Centraliza las llamadas a la IA para generación de texto y consultoría.
"""

import google.generativeai as genai
from bot_engine.config import GEMINI_API_KEY
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.ai")

# Configurar el SDK
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("⚠️ GEMINI_API_KEY no configurada. Las funciones de IA estarán limitadas.")

class AIEngine:
    def __init__(self, model_name="gemini-1.5-flash"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None and GEMINI_API_KEY:
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    async def generate_press_kit_bio(self, user_notes: str) -> dict:
        """
        Genera una biografía profesional en español e inglés basada en notas.
        Retorna un diccionario con ambas versiones.
        """
        if not self.model:
            return None

        prompt = f"""
        Actúa como un experto en marketing musical y manager de artistas electrónicos de primer nivel.
        Tu tarea es redactar una biografía profesional para un DJ/Productor basada en estas notas: "{user_notes}".
        
        REGLAS:
        1. El tono debe ser épico, profesional y atractivo para promotores de clubs internacionales.
        2. Mantén la biografía concisa (máximo 150 palabras).
        3. No inventes datos que no estén en las notas, pero dales un giro profesional.
        4. Devuelve el resultado exactamente en este formato (JSON-like, sin bloques de código):
        ESP: [Biografía en español]
        ENG: [Biografía en inglés]
        """

        try:
            # Gemini Python SDK no es nativo async en todas las versiones, pero lo tratamos con cuidado
            response = self.model.generate_content(prompt)
            text = response.text

            # Parsear rudimentario pero efectivo
            esp = text.split("ESP:")[1].split("ENG:")[0].strip()
            eng = text.split("ENG:")[1].strip()

            return {"es": esp, "en": eng}
        except Exception as e:
            logger.error(f"Error generando Bio con IA: {e}")
            return None

    async def get_career_advice(self, user_question: str) -> str:
        """Responde dudas sobre la carrera musical."""
        if not self.model:
            return "Lo siento, mi 'cerebro' de IA no está configurado ahora mismo. Contacta con soporte."

        prompt = f"""
        Eres NOVA, el asistente inteligente de Nova Club. Eres un mentor experto en la industria de la música electrónica.
        Responde a esta pregunta de un DJ emergente: "{user_question}"
        
        REGLAS:
        1. Sé directo, motivador y usa lenguaje de la industria.
        2. Si la pregunta no tiene nada que ver con música o carrera DJ, dile amablemente que solo respondes sobre la industria.
        3. Mantén la respuesta corta y accionable (máximo 200 palabras).
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error en AI Chat: {e}")
            return "He tenido un cortocircuito mental al procesar eso. ¿Puedes repetirlo?"

# Instancia única para toda la app
ai_engine = AIEngine()
