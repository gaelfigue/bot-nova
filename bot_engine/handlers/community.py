"""
NOVA_CORE — Handlers de Comunidad (Skool)
Herramientas IA para Marca Personal y Promotores.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode
import asyncio

from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.community")

# Estados para Generador de Press Kit
BIO_INPUT = 1

# Estados para Simulador de Presupuestos
BUDGET_ATTENDEES = 1
BUDGET_COST = 2

# ─── MÓDULO 1: MARCA PERSONAL (Press Kit) ──────────────────────────

async def start_press_kit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el generador de biografía."""
    query = update.callback_query
    if query:
        await query.answer()
        msg = query.message
    else:
        msg = update.message

    await msg.reply_text(
        "💼 *Generador de Press Kit (Biografía)*\n\n"
        "Escribe un breve texto contándome:\n"
        "1. De dónde eres o cómo te llamas.\n"
        "2. Qué estilo musical pinchas.\n"
        "3. Cuáles son tus mayores influencias o experiencia.\n\n"
        "_Ejemplo: 'Soy Álex de Madrid, pincho Techno Peak Time y me encanta el sonido de Drumcode.'_\n\n"
        "O escribe /cancelar para salir.",
        parse_mode=ParseMode.MARKDOWN
    )
    return BIO_INPUT

async def process_bio_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa el input del usuario y genera la biografía."""
    user_text = update.message.text
    
    msg = await update.message.reply_text("🤖 *Analizando tu perfil con IA...*", parse_mode=ParseMode.MARKDOWN)
    
    # Simulamos el delay de una IA real (LLM)
    await asyncio.sleep(2)
    
    # Generamos una biografía falsa basada en su texto para la demo
    bio_es = f"🔥 DJ y Productor emergente con una visión clara de la pista de baile. Su sonido se caracteriza por energías contundentes y ritmos magnéticos. Como nos cuenta en sus propias palabras: '{user_text}'. Una apuesta segura para cualquier cabina que busque conectar de verdad con el público."
    
    bio_en = f"🔥 Emerging DJ and Producer with a clear vision for the dancefloor. Their sound is characterized by heavy hitting energy and magnetic grooves. In their own words: '{user_text}'. A solid bet for any booth looking to truly connect with the crowd."
    
    response = (
        "✅ *Press Kit Generado con Éxito*\n\n"
        "🇪🇸 *Versión Español (Copia y pega en Spotify/Soundcloud):*\n"
        f"_{bio_es}_\n\n"
        "🇬🇧 *Versión Inglés (Para Booking Internacional):*\n"
        f"_{bio_en}_\n\n"
        "💡 *Tip de Nova:* Acompaña esto con unas fotos de prensa en blanco y negro."
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="menu_principal")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await msg.edit_text(response, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    return ConversationHandler.END

# ─── MÓDULO 2: PROMOTORES (Calculadora Presupuestos) ──────────────────

async def start_budget_simulator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia la calculadora de break-even para fiestas."""
    query = update.callback_query
    if query:
        await query.answer()
        msg = query.message
    else:
        msg = update.message

    await msg.reply_text(
        "📊 *Simulador de Presupuestos para Eventos*\n\n"
        "Vamos a calcular el Break-Even (punto de rentabilidad) de tu próxima fiesta.\n\n"
        "¿Cuántas **personas** esperas de aforo total de forma realista? (Ej: 200)\n\n"
        "O escribe /cancelar para salir.",
        parse_mode=ParseMode.MARKDOWN
    )
    return BUDGET_ATTENDEES

async def process_budget_attendees(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda los asistentes y pide el coste de la sala."""
    try:
        attendees = int(update.message.text.strip())
        context.user_data['attendees'] = attendees
    except ValueError:
        await update.message.reply_text("❌ Por favor, escribe solo un número (ej: 200).")
        return BUDGET_ATTENDEES

    await update.message.reply_text(
        f"Entendido, esperamos aforo de {attendees} personas.\n\n"
        "¿Cuál es el **coste total del alquiler de la sala** y otros gastos fijos (seguridad, DJs, promo)?\n"
        "(Ej: 1500)\n\n"
        "Escribe solo el número en euros.",
        parse_mode=ParseMode.MARKDOWN
    )
    return BUDGET_COST

async def process_budget_cost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Calcula el break-even y devuelve el resultado."""
    try:
        cost = float(update.message.text.strip())
        attendees = context.user_data.get('attendees', 100)
    except ValueError:
        await update.message.reply_text("❌ Por favor, escribe solo un número (ej: 1500).")
        return BUDGET_COST

    msg = await update.message.reply_text("🧮 *Calculando viabilidad financiera...*", parse_mode=ParseMode.MARKDOWN)
    
    await asyncio.sleep(1) # Simular carga
    
    break_even_price = cost / attendees
    recommended_price = break_even_price * 1.3 # 30% margen beneficio
    
    profit_if_sold_out = (recommended_price * attendees) - cost

    response = (
        "📊 *REPORTE FINANCIERO DEL EVENTO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 *Aforo Estimado:* {attendees} personas\n"
        f"💸 *Costes Fijos:* {cost}€\n\n"
        f"📉 *Break-Even (Punto Muerto):* **{break_even_price:.2f}€ / entrada**\n"
        "_(A este precio no ganas ni pierdes dinero)_\n\n"
        f"📈 *Precio Recomendado:* **{recommended_price:.2f}€ / entrada**\n"
        "_(A este precio, si haces Sold Out, ganarás **" + f"{profit_if_sold_out:.2f}€" + "** limpios)_\n\n"
        "💡 *Tip de Nova:* Te sugiero crear dos tramos de entradas: 'Early Bird' un poco más baratas del Break-Even para hacer caja rápida, y 'General' al precio recomendado."
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="menu_principal")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await msg.edit_text(response, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela cualquier conversación actual."""
    keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="menu_principal")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🚫 *Operación cancelada.*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# ─── MÓDULO 3: PROMOTORES (Tech Rider) ─────────────────────────

RIDER_TECH = 1
RIDER_HOSP = 2

async def start_tech_rider(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        msg = query.message
    else:
        msg = update.message

    await msg.reply_text(
        "📄 *Generador de Tech & Rider*\n\n"
        "Vamos a crear el documento que enviarás a las salas.\n\n"
        "1️⃣ **¿Qué equipo técnico necesitas en cabina?**\n"
        "_(Ej: 3x CDJ-3000, 1x DJM-900NXS2, Monitores a la altura de la cabeza)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return RIDER_TECH

async def process_rider_tech(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['rider_tech'] = update.message.text.strip()
    await update.message.reply_text(
        "2️⃣ **¿Cuáles son tus requisitos de Hospitalidad (Camerino)?**\n"
        "_(Ej: 4 botellas de agua mineral, 6 cervezas, 1 botella de Vodka, toallas negras)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return RIDER_HOSP

async def process_rider_hosp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tech = context.user_data.get('rider_tech', '')
    hosp = update.message.text.strip()
    
    response = (
        "✅ *TU RIDER PROFESIONAL ESTÁ LISTO*\n"
        "_(Copia y pega este texto para enviarlo al promotor)_ \n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 **TECHNICAL & HOSPITALITY RIDER**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔊 **REQUISITOS TÉCNICOS (CABINA)**\n"
        f"• {tech}\n\n"
        "El equipo debe estar linkeado mediante cable de red (Pro DJ Link) y actualizado a su último firmware. Los monitores deben tener control de volumen independiente desde la mesa de mezclas.\n\n"
        "🥂 **HOSPITALIDAD (CAMERINO / CABINA)**\n"
        f"• {hosp}\n\n"
        "🎟 **ACCESOS**\n"
        "• Artista + 2 Acompañantes (Guestlist).\n\n"
        "Por favor, confirmar la disponibilidad de este equipo al menos 72h antes del evento.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


# ─── MÓDULO 4: MARCA PERSONAL (Visual Identity) ─────────────────────────

VISUAL_GENRE = 1

async def start_visual_identity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        msg = query.message
    else:
        msg = update.message

    await msg.reply_text(
        "🎨 *Asistente de Identidad Visual*\n\n"
        "Dime, **¿cuál es tu género musical principal?**\n"
        "_(Ej: Techno Peak Time, House, Tech House, Hardstyle, Melodic Techno)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return VISUAL_GENRE

async def process_visual_genre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    genre = update.message.text.lower()
    
    if "hard" in genre:
        palette = "🔴 Rojo Sangre (#FF0000) + ⚫ Negro Puro (#000000) + ⚪ Blanco Industrial (#FFFFFF)"
        font = "Tipografía: *Anton* o *Impact* (Letras mayúsculas, pesadas, sin serifas)."
        vibe = "Estética: Cadenas, humo, texturas de metal desgastado, luz estroboscópica, velocidad."
    elif "house" in genre and "tech" not in genre:
        palette = "🟡 Amarillo Mostaza (#FFCC00) + 🔵 Azul Cielo (#00A2FF) + ⚪ Blanco Roto (#F5F5F5)"
        font = "Tipografía: *Futura* o *Helvetica* (Limpia, elegante, minimalista)."
        vibe = "Estética: Verano, palmeras, colores pastel, texturas de vinilo, luz cálida."
    elif "melodic" in genre:
        palette = "🌌 Morado Neón (#8A2BE2) + 🔵 Cian (#00FFFF) + 🌑 Gris Oscuro (#1A1A1A)"
        font = "Tipografía: *Montserrat* o *Cinzel* (Elegante, espaciada, cinemática)."
        vibe = "Estética: Espacio, láseres, texturas líquidas, geometría abstracta, profundidad."
    else:
        # Default Techno/Tech House
        palette = "🟢 Verde Neón (#39FF14) + ⚫ Negro (#0A0A0A) + ⬜ Gris Cemento (#808080)"
        font = "Tipografía: *Space Grotesk* o *Inter* (Moderna, tecnológica, legible)."
        vibe = "Estética: Underground, flashazos, texturas de cemento, luz de neón, minimalismo oscuro."

    response = (
        "🤖 *INFORME DE DIRECCIÓN DE ARTE*\n"
        "Basado en tu sonido, esta debería ser tu estética en Instagram y Portadas:\n\n"
        f"🎨 **Paleta de Colores:**\n{palette}\n\n"
        f"✍️ **Fuentes Recomendadas:**\n{font}\n\n"
        f"📸 **Vibe & Moodboard:**\n{vibe}\n\n"
        "💡 *Tip:* Usa esto en Canva o pásaselo a un diseñador gráfico para mantener tu marca visual coherente."
    )
    
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


# ─── BUILDERS PARA EL MAIN ──────────────────────────────────────────────

def get_press_kit_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📝 Generador de Press Kit \(Bio\)$"), start_press_kit),
            CallbackQueryHandler(start_press_kit, pattern="^community_bio$")
        ],
        states={
            BIO_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_bio_input)],
        },
        fallbacks=[CommandHandler("cancelar", cancel_conversation)],
    )

def get_budget_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📊 Simulador de Presupuestos$"), start_budget_simulator),
            CallbackQueryHandler(start_budget_simulator, pattern="^community_budget$")
        ],
        states={
            BUDGET_ATTENDEES: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_budget_attendees)],
            BUDGET_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_budget_cost)],
        },
        fallbacks=[CommandHandler("cancelar", cancel_conversation)],
    )

def get_tech_rider_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📄 Generar Tech Rider$"), start_tech_rider),
            CallbackQueryHandler(start_tech_rider, pattern="^community_rider$")
        ],
        states={
            RIDER_TECH: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_rider_tech)],
            RIDER_HOSP: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_rider_hosp)],
        },
        fallbacks=[CommandHandler("cancelar", cancel_conversation)],
    )

def get_visual_identity_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🎨 Identidad Visual$"), start_visual_identity),
            CallbackQueryHandler(start_visual_identity, pattern="^community_visual$")
        ],
        states={
            VISUAL_GENRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_visual_genre)],
        },
        fallbacks=[CommandHandler("cancelar", cancel_conversation)],
    )
