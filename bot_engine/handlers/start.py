"""
NOVA_CORE — Handler de Inicio
Comandos /start, /help y /status del bot. Menús interactivos Inline y ReplyKeyboardMarkup.
"""

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.cmd")

WELCOME_MSG = """
🎧 *NOVA PROMO HUB* 🎧
━━━━━━━━━━━━━━━━━━━━━━━━
Bienvenido al motor asistente de *Nova Club*.

Selecciona una categoría del menú interactivo, o usa los atajos rápidos del teclado inferior:
"""

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Devuelve el teclado principal permanente (Atajos rápidos)."""
    keyboard = [
        ["📜 Generar Contrato", "📝 Generador de Press Kit (Bio)"],
        ["🎨 Identidad Visual", "📊 Simulador de Presupuestos"],
        ["📄 Generar Tech Rider", "🧾 Crear Factura"],
        ["📥 Descargar Track Sencillo", "🎛 Analizar LUFS"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Devuelve el teclado del menú principal (Inline)."""
    keyboard = [
        [InlineKeyboardButton("🎪 Promotores (Fiestas)", callback_data="menu_promotores")],
        [InlineKeyboardButton("💼 Marca Personal (DJ)", callback_data="menu_marca")],
        [InlineKeyboardButton("🎵 Música y Audio", callback_data="menu_musica")],
        [InlineKeyboardButton("🧾 Facturación", callback_data="menu_factura")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_promotores_menu() -> InlineKeyboardMarkup:
    """Devuelve el submenú de Promotores."""
    keyboard = [
        [InlineKeyboardButton("📊 Simulador de Presupuestos", callback_data="community_budget")],
        [InlineKeyboardButton("📄 Generar Tech Rider", callback_data="community_rider")],
        [InlineKeyboardButton("📜 Generar Contrato", callback_data="community_contract")],
        [InlineKeyboardButton("🔙 Volver", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_marca_menu() -> InlineKeyboardMarkup:
    """Devuelve el submenú de Marca Personal."""
    keyboard = [
        [InlineKeyboardButton("🌐 Crear Landing Page (EPK)", callback_data="community_landing")],
        [InlineKeyboardButton("📝 Generador de Press Kit (Bio)", callback_data="community_bio")],
        [InlineKeyboardButton("🎨 Identidad Visual", callback_data="community_visual")],
        [InlineKeyboardButton("🔙 Volver", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_musica_menu() -> InlineKeyboardMarkup:
    """Devuelve el submenú de Música."""
    keyboard = [
        [InlineKeyboardButton("📥 Descargar Track Sencillo", callback_data="music_track")],
        [InlineKeyboardButton("🎛 Analizar LUFS", callback_data="music_lufs")],
        [InlineKeyboardButton("🔙 Volver", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para el comando /start. Muestra el teclado principal y el menú inline."""
    user = update.effective_user
    logger.info(f"▶ /start de {user.first_name} ({user.id})")
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            WELCOME_MSG,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # Enviar mensaje de bienvenida con el teclado de atajos integrado
        await update.message.reply_text(
            WELCOME_MSG,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_reply_keyboard()
        )
        # Enviar el menú interactivo principal (Inline) justo después
        await update.message.reply_text(
            "Selecciona una categoría para más opciones:",
            reply_markup=get_main_menu_keyboard()
        )


# ─── HANDLERS DE CALLBACKS DE NAVEGACIÓN ───────────────────────────

async def handle_menu_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja la navegación por los submenús."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_principal":
        await query.message.edit_text(
            WELCOME_MSG,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
    elif data == "menu_promotores":
        await query.message.edit_text(
            "🎪 *MENÚ DE PROMOTORES*\n\n"
            "Herramientas para ayudarte a montar y rentabilizar tus eventos.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_promotores_menu()
        )
    elif data == "menu_marca":
        await query.message.edit_text(
            "💼 *MENÚ DE MARCA PERSONAL*\n\n"
            "Construye tu identidad como artista profesional.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_marca_menu()
        )
    elif data == "menu_musica":
        await query.message.edit_text(
            "🎵 *MENÚ DE MÚSICA Y AUDIO*\n\n"
            "Herramientas clásicas de Nova Engine.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_musica_menu()
        )
    elif data == "menu_factura":
        # Simular que le decimos que use el atajo o lanzamos el invoice handler
        await query.message.edit_text(
            "🧾 *FACTURACIÓN*\n\n"
            "Para crear una factura, usa el botón *🧾 Crear Factura* del teclado inferior o escribe /factura.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="menu_principal")]])
        )
    elif data == "music_track":
        await query.message.edit_text(
            "🎧 *MODO DESCARGA SIMPLE ACTIVADO*\n\n"
            "Pega directamente en el chat el enlace de *YouTube, Spotify o SoundCloud* que quieras descargar y procesar en calidad de cabina.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="menu_musica")]])
        )
    elif data == "music_lufs":
        await query.message.edit_text(
            "🎛 *ANALIZADOR DE LUFS ACTIVADO*\n\n"
            "Esta función permite analizar el volumen percibido de tus producciones.\n\n"
            "Para usarlo, envíame el archivo de audio directamente al chat.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="menu_musica")]])
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Usa el menú interactivo o el teclado inferior para navegar. Escribe /start si no los ves.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Esta función ha sido deshabilitada del menú principal, pero el bot está operativo.")

async def music_track_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎧 *MODO DESCARGA SIMPLE ACTIVADO*\n\n"
        "Pega directamente en el chat el enlace de *YouTube, Spotify o SoundCloud* que quieras descargar.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_reply_keyboard()
    )

async def lufs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎛 *ANALIZADOR DE LUFS ACTIVADO*\n\n"
        "Envíame un archivo de audio (.mp3 o .wav) para analizar sus picos y volumen.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_reply_keyboard()
    )

