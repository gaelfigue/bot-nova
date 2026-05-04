"""
NOVA_CORE — PDF Generator Premium
Renderizado de documentos profesionales usando HTML/CSS (WeasyPrint).
"""

import os
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from bot_engine.config import BASE_DIR
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.pdf_premium")

TEMPLATE_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = BASE_DIR / "data" / "riders"

def render_premium_rider(data: dict) -> Path:
    """Renderiza un Tech Rider premium en PDF usando una plantilla HTML."""
    try:
        # Asegurar directorios
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configurar Jinja2
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
        template = env.get_template("rider_template.html")
        
        # Mapeo de datos para la plantilla Premium
        template_vars = {
            "dj_name": data.get("artist_name", "ARTISTA NOVA"),
            "contacto_email": data.get("contact_email", "booking@novaclub.es"),
            "contacto_tel": data.get("contact_tel", "+34 600 000 000"),
            "equipo_cdjs": data.get("setup_cdjs", "3x Pioneer CDJ-3000"),
            "equipo_mixer": data.get("setup_mixer", "Pioneer DJM-V10"),
            "equipo_extras": data.get("setup_extras", "Pro DJ Link Hub + Ethernet."),
            "hospitality_bebidas": data.get("hospitality", "4x Aguas mineral, 2x Toallas negras."),
            "hospitality_extras": data.get("hosp_extras", "Sin extras.")
        }
            
        # Renderizar HTML
        html_content = template.render(**template_vars)
        
        # Generar PDF
        filename = f"RIDER_{template_vars['dj_name'].replace(' ', '_')}.pdf"
        output_path = OUTPUT_DIR / filename
        
        # WeasyPrint render con base_url para imágenes
        HTML(string=html_content, base_url=str(TEMPLATE_DIR)).write_pdf(str(output_path))
        
        logger.info(f"PDF Premium generado: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generando PDF Premium: {e}")
        raise e

# Función legacy por compatibilidad (opcional, para no romper el código existente)
def create_tech_rider_pdf(artist_name: str, rider_text: str) -> str:
    """Mantiene compatibilidad con el flujo antiguo pero usa el nuevo motor."""
    data = {
        "artist_name": artist_name,
        "setup_audio": rider_text,
        "monitors": "Refer to standard technical requirements.",
        "hospitality": "Standard hospitality rider applies.",
        "contact_info": "Nova Management"
    }
    return str(render_premium_rider(data))
