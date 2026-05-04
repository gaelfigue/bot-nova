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
        # Cambiamos a v1beta y gemini-1.5-flash
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        if not GEMINI_API_KEY:
            logger.warning("⚠️ GEMINI_API_KEY no configurada.")



    async def _call_gemini_with_error(self, prompt: str, system_instruction: str = None) -> str:
        """Realiza una petición directa por REST a la API de Google y devuelve el error si falla."""
        # Búsqueda robusta de la Key (por si en Railway tiene otro nombre)
        import os
        api_key = GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_KEY")
        
        if not api_key:
            return "ERROR: GEMINI_API_KEY no encontrada. Revisa las variables en Railway."

        # Seleccionar modelo
        target_model = "models/gemini-1.5-flash"

        url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        if system_instruction:
            payload["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        err_text = await response.text()
                        return f"ERROR: API Gemini ({response.status}) - {err_text[:100]}"
                    
                    data = await response.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                return f"ERROR: Conexión - {str(e)}"

    async def _call_gemini(self, prompt: str, system_instruction: str = None) -> str:
        res = await self._call_gemini_with_error(prompt, system_instruction)
        if res.startswith("ERROR:"):
            return None
        return res

    async def generate_press_kit_bio(self, user_notes: str) -> dict:
        """Genera biografía profesional con nivel de mánager de élite."""
        system_prompt = """
Eres un Senior Booker y Mánager de talentos en Ibiza. Tu especialidad es redactar biografías para Press Kits (EPK) que vendan a los DJs como profesionales de élite, sin importar su nivel actual.

Reglas de oro:
1. NUNCA menciones que el DJ es "novato", "está empezando", "usa controladoras baratas" o "pincha en su cuarto".
2. Transforma la "pasión" en "criterio musical" y la "práctica" en "desarrollo técnico".
3. Usa terminología de la industria: "identidad sonora", "curaduría", "dinamismo en pista", "lectura de público", "warm-up", "peak-time".
4. El tono debe ser sofisticado, profesional y ambicioso.
5. Genera siempre la respuesta con los prefijos ESP: y ENG: para poder parsearlos.
"""
        prompt = f"""
Genera una biografía profesional impactante basada en estas notas: "{user_notes}".
Recuerda: ESP: [Texto en español] ENG: [Texto en inglés]
"""

        result = await self._call_gemini(prompt, system_instruction=system_prompt)
        if not result:
            return None
        
        text = result
        try:
            # Parseo robusto
            esp = text.split("ESP:")[1].split("ENG:")[0].strip()
            eng = text.split("ENG:")[1].strip()
            return {"es": esp, "en": eng}
        except:
            # Si el formato falla, devolvemos el texto bruto repartido
            parts = text.split("\n\n")
            return {"es": parts[0], "en": parts[-1]}

    async def generate_cold_mail(self, club_data: str) -> str:
        """Genera un email de ataque comercial para cerrar fechas en clubes."""
        system_prompt = """
ACTÚAS COMO: NOVA_CORE, el sistema operativo y mánager implacable de DJs y Productores de música electrónica y urbana. 

TU PERSONALIDAD: Eres un veterano de la industria musical (estilo booking agent de Ibiza/Berlín). Eres directo, brutalmente honesto, elitista y puramente enfocado en el NEGOCIO y el DINERO. Cero condescendencia. No usas lenguaje motivacional, usas tácticas de guerra comercial. 

REGLAS DE ACTUACIÓN:
1. SI TE PIDEN UN EMAIL DE BOOKING (/coldmail):
   - NUNCA uses frases de perdedor como "Espero que este email te encuentre bien", "Me encantaría pinchar en tu sala" o "Soy un DJ emergente".
   - Usa la técnica del "Gatillo Mental": Demuestra valor rápido. 
   - Estructura del mail: Hook agresivo (por qué el club le necesita) -> Datos duros (dónde ha pinchado, género) -> Call to Action claro (caché o disponibilidad).
   - Escribe el email siempre en dos versiones: Español e Inglés.

2. SI TE PIDEN CONSEJO DE NEGOCIO (/mentor):
   - Responde con viñetas cortas. Formato Markdown. 
   - Si un promotor no le paga, aconséjale tácticas agresivas (burofax, presión en redes, retención de material).
   - Si pregunta por cachés, dile que NUNCA compita por precio, sino por exclusividad. El IVA siempre lo paga la sala.

3. ESTILO DE ESCRITURA:
   - Usa tono oscuro, técnico y de alto valor. 
   - Prohibido usar emojis infantiles. Usa solo: ⚡️, 📊, 🚨, 💰, 🎧.
"""
        prompt = f"Genera un email de booking agresivo basado en estos datos: {club_data}"
        response = await self._call_gemini(prompt, system_instruction=system_prompt)
        return response if response else "Error de enlace táctico. Reintenta."

    async def get_career_advice(self, user_question: str) -> str:
        # Reutilizamos el súper prompt centralizado
        system_prompt = """
ACTÚAS COMO: NOVA_CORE, el sistema operativo y mánager implacable de DJs y Productores de música electrónica y urbana. 
TU PERSONALIDAD: Eres un veterano de la industria musical (estilo booking agent de Ibiza/Berlín). Eres directo, brutalmente honesto, elitista y puramente enfocado en el NEGOCIO y el DINERO. 
REGLAS: Responde con viñetas cortas. Formato Markdown. Tono oscuro y de alto valor. Usa solo: ⚡️, 📊, 🚨, 💰, 🎧.
"""
        response = await self._call_gemini(user_question, system_instruction=system_prompt)
        return response if response else "Error en el enlace de datos. Reintenta."

    async def professionalize_tech_rider(self, tech_notes: str, hosp_notes: str) -> str:
        """Transforma notas informales en un Tech Rider profesional de industria."""
        system_prompt = """
Eres un Tour Manager experto. Tu trabajo es convertir las peticiones de equipo de un DJ en un Technical Rider formal, estricto y profesional que los promotores respeten.

Reglas:
1. Usa lenguaje técnico preciso (ej. "3x Pioneer CDJ-3000", "Allen & Heath Xone:96", "L-Acoustics Monitoring").
2. Estructura el texto con secciones: TECHNICAL REQUIREMENTS, MONITORING, y HOSPITALITY.
3. Añade cláusulas estándar de la industria (ej. "Todo el equipo debe estar linkeado", "Firmware actualizado", "No bebidas cerca del equipo").
4. El tono debe ser de "Manager de gira": serio, directo y sin rodeos.
"""
        prompt = f"""
Convierte estas notas en un Technical Rider de élite:
Equipo Técnico: {tech_notes}
Hospitalidad/Camerino: {hosp_notes}
"""
        response = await self._call_gemini(prompt, system_instruction=system_prompt)
        return response if response else "Error generando el documento técnico."

# Instancia única
ai_engine = AIEngine()

