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
            # Intentamos el modelo más reciente primero
            for model_name in ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-pro"]:
                try:
                    logger.info(f"Intentando inicializar modelo: {model_name}")
                    self._model = genai.GenerativeModel(model_name)
                    # No hacemos test aquí para evitar 404s en bucle, 
                    # lo probaremos en la primera llamada real.
                    return self._model
                except Exception as e:
                    logger.warning(f"No se pudo inicializar {model_name}: {e}")
                    continue
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
            logger.info(f"Generando bio para: {user_notes[:30]}...")
            response = self.model.generate_content(prompt)
            text = response.text
            logger.debug(f"Respuesta IA: {text}")

            # Parsear con más robustez
            esp = ""
            eng = ""
            
            if "ESP:" in text and "ENG:" in text:
                esp = text.split("ESP:")[1].split("ENG:")[0].strip()
                eng = text.split("ENG:")[1].strip()
            else:
                # Si no viene con los tags, intentamos partirlo por la mitad o usar el texto entero
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if len(lines) >= 2:
                    esp = lines[0]
                    eng = lines[1]
                else:
                    esp = text
                    eng = text

            return {"es": esp, "en": eng}
        except Exception as e:
            logger.error(f"Error crítico en AI Engine: {e}")
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
