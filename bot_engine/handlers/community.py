"""
NOVA_CORE — Handlers de Comunidad (Skool)
Herramientas IA para Marca Personal y Promotores.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode
import asyncio

from bot_engine.utils.logger import setup_logger
from bot_engine.handlers.auth_handler import restricted

logger = setup_logger("nova.community")

# Estados para Generador de Press Kit
BIO_INPUT = 1

# Estados para Simulador de Presupuestos
BUDGET_ATTENDEES = 1
BUDGET_COST = 2

# Estados para Generador de Tech Rider (Premium)
RIDER_TECH = 1
RIDER_MONITORS = 2
RIDER_HOSP = 3
CONT_FEE = 3

# Estados para Generador de Contratos
CONT_VENUE = 1
CONT_DATE = 2
CONT_FEE = 3

# ─── MÓDULO 1: MARCA PERSONAL (Press Kit) ──────────────────────────

@restricted
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
    
    # Importar y usar el motor de IA real
    from bot_engine.services.ai_engine import ai_engine
    try:
        result = await ai_engine.generate_press_kit_bio(user_text)
    except Exception as e:
        result = None
        error_msg = str(e)
    
    if result:
        bio_es = result['es']
        bio_en = result['en']
    else:
        # Fallback con DEBUG
        error_info = error_msg if 'error_msg' in locals() else "Error desconocido"
        bio_es = f"⚠️ Error IA: {error_info}\n\nNotas: {user_text}"
        bio_en = f"⚠️ AI Error: {error_info}\n\nNotes: {user_text}"

    
    response = (
        "✅ *Press Kit Generado con IA*\n\n"
        "🇪🇸 *Versión Español:*\n"
        f"_{bio_es}_\n\n"
        "🇬🇧 *Versión Inglés:*\n"
        f"_{bio_en}_\n\n"
        "💡 *Tip de Nova:* Copia estos textos en tu perfil de SoundCloud para dar una imagen profesional."
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

@restricted
async def start_tech_rider(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        msg = query.message
    else:
        msg = update.message

    await msg.reply_text(
        "📄 *Generador de Tech Rider Premium*\n\n"
        "Voy a entrevistarte para crear un documento de nivel agencia.\n\n"
        "1️⃣ **¿Qué equipo de audio necesitas?**\n"
        "_(Ej: 2x CDJ-3000, Mesa DJM-V10...)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return RIDER_TECH

async def process_rider_tech(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['rider_tech'] = update.message.text.strip()
    await update.message.reply_text(
        "2️⃣ **¿Qué necesitas de Monitorización?**\n"
        "_(Ej: 2x Monitores autoamplificados de 15' controlables desde mesa)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return RIDER_MONITORS

async def process_rider_monitors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['rider_monitors'] = update.message.text.strip()
    await update.message.reply_text(
        "3️⃣ **Hospitalidad y Camerino**\n"
        "_(Ej: 4 aguas, 2 toallas negras, 1 botella de Gin)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return RIDER_HOSP

async def process_rider_hosp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tech = context.user_data.get('rider_tech', '')
    monitors = context.user_data.get('rider_monitors', 'Refer to standard technical requirements.')
    hosp = update.message.text.strip()
    
    user = update.effective_user
    artist_name = user.first_name
    
    msg = await update.message.reply_text("💎 *Diseñando Tech Rider en formato Modo Noche...*", parse_mode=ParseMode.MARKDOWN)
    
    from bot_engine.utils.pdf_generator import render_premium_rider
    
    data = {
        "artist_name": artist_name,
        "setup_audio": tech,
        "monitors": monitors,
        "hospitality": hosp,
        "contact_info": f"{user.username or user.first_name} | Nova Hub System"
    }
    
    try:
        pdf_path = render_premium_rider(data)
        
        with open(pdf_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=os.path.basename(pdf_path),
            )
    else:
        await update.message.reply_text("⚠️ No se pudo generar el PDF, pero arriba tienes el texto.", reply_markup=reply_markup)

    return ConversationHandler.END

import os # Asegurar que os está disponible para la comprobación del path


# ─── MÓDULO 4: MARCA PERSONAL (Visual Identity) ─────────────────────────

VISUAL_GENRE = 1

@restricted
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


# ─── MÓDULO 5: CONTRATOS (Performance Agreement) ─────────────────────────

@restricted
async def start_contract(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        msg = query.message
    else:
        msg = update.message

    await msg.reply_text(
        "📜 *Generador de Contrato de Actuación*\n\n"
        "Vamos a blindar legalmente tu próximo bolo.\n\n"
        "1️⃣ **¿Cómo se llama la sala o el promotor?**",
        parse_mode=ParseMode.MARKDOWN
    )
    return CONT_VENUE

async def process_contract_venue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['cont_venue'] = update.message.text.strip()
    await update.message.reply_text(
        "2️⃣ **¿Cuál es la fecha del evento?**\n"
        "_(Ej: 24 de Junio de 2026)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return CONT_DATE

async def process_contract_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['cont_date'] = update.message.text.strip()
    await update.message.reply_text(
        "3️⃣ **¿Cuál es el Fee (honorarios) pactado?**\n"
        "_(Escribe solo el número en euros, ej: 600)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return CONT_FEE

async def process_contract_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    venue = context.user_data.get('cont_venue', 'Cliente')
    date = context.user_data.get('cont_date', 'Fecha TBD')
    try:
        fee = float(update.message.text.replace("€", "").strip())
    except:
        fee = 0.0
        
    dj_name = update.effective_user.first_name
    
    msg = await update.message.reply_text("⚖️ *Redactando cláusulas de protección y generando PDF...*", parse_mode=ParseMode.MARKDOWN)
    
    from bot_engine.services.contract_engine import generate_performance_contract
    
    try:
        contract_path = generate_performance_contract(dj_name, venue, date, fee)
    except Exception as e:
        logger.error(f"Error en contrato: {e}")
        contract_path = None

    if contract_path and os.path.exists(contract_path):
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="menu_principal")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        with open(contract_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=os.path.basename(contract_path),
                caption=f"📜 Contrato de Actuación: {dj_name} vs {venue}\n\n*Nova Tip:* Envía esto firmado antes de cualquier desplazamiento.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        await msg.delete()
    else:
        await msg.edit_text("⚠️ Error al generar el contrato. Reintenta más tarde.")

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
            RIDER_MONITORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_rider_monitors)],
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

def get_contract_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📜 Generar Contrato$"), start_contract),
            CallbackQueryHandler(start_contract, pattern="^community_contract$")
        ],
        states={
            CONT_VENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_contract_venue)],
            CONT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_contract_date)],
            CONT_FEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_contract_fee)],
        },
        fallbacks=[CommandHandler("cancelar", cancel_conversation)],
    )
