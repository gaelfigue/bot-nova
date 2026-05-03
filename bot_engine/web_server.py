"""
NOVA_CORE — Mini Servidor Web
Sirve las Landing Pages generadas para los DJs.
"""

from aiohttp import web
import aiohttp_jinja2
import jinja2
import json
import os
from pathlib import Path
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.web")

# Rutas
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / 'templates'
DATA_DIR = BASE_DIR.parent / 'data'
LANDING_DATA_FILE = DATA_DIR / 'landing_pages.json'

async def get_dj_landing(request: web.Request):
    """Manejador para la ruta /dj/{username}"""
    username = request.match_info.get('username', '')
    
    if not LANDING_DATA_FILE.exists():
        return web.Response(text="Servidor no inicializado.", status=404)

    with open(LANDING_DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    if username not in data:
        return web.Response(text="DJ no encontrado.", status=404)

    dj_data = data[username]
    
    # Renderizar la plantilla
    context = {'dj': dj_data}
    response = aiohttp_jinja2.render_template('landing.html', request, context)
    return response

async def start_web_server(host='0.0.0.0', port=None):
    """Inicia el servidor web de aiohttp."""
    if port is None:
        port = int(os.getenv("PORT", "8080"))

    # Asegurar que el archivo de datos existe
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LANDING_DATA_FILE.exists():
        with open(LANDING_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)

    app = web.Application()
    
    # Configurar Jinja2
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)))
    
    app.router.add_get('/dj/{username}', get_dj_landing)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    
    logger.info(f"🌐 Servidor web iniciado en http://{host}:{port}")
    await site.start()
    
    # Devolver el runner para poder cerrarlo de forma limpia si hiciera falta
    return runner
