"""
NOVA_CORE — Handler de Landing Pages
Generador paso a paso del EPK para DJs.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode
import json
import os
import re
from pathlib import Path

from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.landing")

# Estados
L_NAME = 1
L_BIO = 2
L_LINKS = 3
L_PHOTO = 4

DATA_DIR = Path(__file__).parent.parent.parent / 'data'
LANDING_DATA_FILE = DATA_DIR / 'landing_pages.json'

async def start_landing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        msg = query.message
    else:
        msg = update.message

    context.user_data['landing'] = {}

    await msg.reply_text(
        "🌐 *Creador de Landing Page (EPK)*\n\n"
        "Vamos a crear tu página web profesional en 4 pasos rápidos.\n\n"
        "1️⃣ **¿Cuál es tu nombre artístico?** (Esto definirá tu enlace único).\n"
        "_(Ejemplo: DJ Nova)_\n\n"
        "Escribe /cancelar para salir.",
        parse_mode=ParseMode.MARKDOWN
    )
    return L_NAME

async def process_l_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    context.user_data['landing']['name'] = name
    
    # Generar username limpio (dj-nova)
    username = re.sub(r'[^a-zA-Z0-9]', '-', name.lower())
    username = re.sub(r'-+', '-', username).strip('-')
    context.user_data['landing']['username'] = username

    await update.message.reply_text(
        f"Genial, tu enlace será: `.../dj/{username}`\n\n"
        "2️⃣ **Escribe tu biografía profesional.**\n"
        "_(Puedes pegar la que generamos antes en el Press Kit)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return L_BIO

async def process_l_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['landing']['bio'] = update.message.text.strip()

    await update.message.reply_text(
        "3️⃣ **Tus Enlaces (Instagram, SoundCloud, Spotify)**\n\n"
        "Escríbelos separados por comas o espacios. Si no tienes alguno, sáltalo.\n"
        "_(Ej: instagram.com/djnova, soundcloud.com/djnova)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return L_LINKS

async def process_l_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    
    ig = re.search(r'(https?://)?(www\.)?instagram\.com/[^\s,]+', text)
    sc = re.search(r'(https?://)?(www\.)?soundcloud\.com/[^\s,]+', text)
    sp = re.search(r'(https?://)?(open\.)?spotify\.com/[^\s,]+', text)

    context.user_data['landing']['ig_link'] = ig.group(0) if ig else ""
    context.user_data['landing']['sc_link'] = sc.group(0) if sc else ""
    context.user_data['landing']['sp_link'] = sp.group(0) if sp else ""

    await update.message.reply_text(
        "4️⃣ **¡Último paso! Envíame una FOTO** tuya para el perfil y el fondo.\n\n"
        "Sube una imagen directamente al chat.",
        parse_mode=ParseMode.MARKDOWN
    )
    return L_PHOTO

async def process_l_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text("❌ Por favor, envía una imagen válida (comprimida como foto, no como archivo).")
        return L_PHOTO

    # Obtener el archivo de foto más grande
    photo_file = await update.message.photo[-1].get_file()
    
    # En Telegram las URLs directas de get_file duran 1 hora.
    # Para producción, deberíamos descargarla, pero para la demo usaremos file_path
    photo_url = photo_file.file_path
    
    context.user_data['landing']['photo_url'] = photo_url
    
    # Para la demo, el cover será la misma foto o un fondo genérico oscuro
    context.user_data['landing']['cover_url'] = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=2000&auto=format&fit=crop"

    # Guardar en JSON
    save_landing_data(context.user_data['landing'])

    username = context.user_data['landing']['username']
    public_url = f"http://192.168.1.161:8080/dj/{username}" # Cambiar a la URL de Railway en prod

    response = (
        "✅ **¡TU LANDING PAGE ESTÁ LISTA!**\n\n"
        "Hemos construido tu web interactiva. Aquí tienes tu enlace exclusivo:\n\n"
        f"🌐 [**{public_url}**]({public_url})\n\n"
        "💡 *Ponlo en tu biografía de Instagram ahora mismo.*"
    )
    
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    
    return ConversationHandler.END


def save_landing_data(dj_data):
    """Guarda los datos en el JSON local"""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if not LANDING_DATA_FILE.exists():
        data = {}
    else:
        with open(LANDING_DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = {}

    username = dj_data['username']
    data[username] = dj_data

    with open(LANDING_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


async def cancel_landing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🚫 Operación cancelada.")
    return ConversationHandler.END

def get_landing_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🌐 Crear Landing Page \(EPK\)$"), start_landing),
            CallbackQueryHandler(start_landing, pattern="^community_landing$")
        ],
        states={
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_l_name)],
            L_BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_l_bio)],
            L_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_l_links)],
            L_PHOTO: [MessageHandler(filters.PHOTO, process_l_photo)],
        },
        fallbacks=[CommandHandler("cancelar", cancel_landing)],
    )
