"""
NOVA_CORE — Finance & Business Handlers
Implementación de /bolo, /finanzas, /radar y /coldmail.
"""

import os
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

from bot_engine.services.auth_service import add_gig, get_user_finances, check_radar
from bot_engine.handlers.auth_handler import restricted
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.finance")

# Estados para /bolo
BOLO_SALA = 1
BOLO_FECHA = 2
BOLO_CACHE = 3

# --- HANDLER /bolo ---
@restricted
async def start_bolo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "💰 *Registro de Bolo*\n\n"
        "Vamos a meter este ingreso en el sistema.\n\n"
        "1️⃣ **¿En qué sala o evento vas a pinchar?**",
        parse_mode=ParseMode.MARKDOWN
    )
    return BOLO_SALA

async def process_bolo_sala(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['bolo_sala'] = update.message.text.strip()
    await update.message.reply_text("2️⃣ **¿Qué fecha es el bolo?** (Ej: 15 Julio)", parse_mode=ParseMode.MARKDOWN)
    return BOLO_FECHA

async def process_bolo_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['bolo_fecha'] = update.message.text.strip()
    await update.message.reply_text("3️⃣ **¿Cuál es el caché acordado?** (Solo números, ej: 800)", parse_mode=ParseMode.MARKDOWN)
    return BOLO_CACHE

async def process_bolo_cache(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cache = float(update.message.text.strip().replace('€', '').replace(',', '.'))
        sala = context.user_data['bolo_sala']
        fecha = context.user_data['bolo_fecha']
        user_id = update.effective_user.id
        
        add_gig(user_id, sala, fecha, cache)
        
        await update.message.reply_text(
            f"✅ *Bolo Guardado*\n\n"
            f"📍 **Sala:** {sala}\n"
            f"📅 **Fecha:** {fecha}\n"
            f"💰 **Caché:** {cache}€\n\n"
            "Estado: *PENDIENTE DE COBRO*. Usa `/finanzas` para ver el total.",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Por favor, envía solo el número del caché (ej: 500).")
        return BOLO_CACHE

# --- HANDLER /finanzas ---
@restricted
async def finanzas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    fin = get_user_finances(user_id)
    
    total = fin['PAGADO'] + fin['PENDIENTE']
    
    msg = (
        "📊 *PANEL DE FINANZAS NOVA*\n\n"
        f"💰 **Total Acumulado:** {total}€\n"
        f"✅ **Cobrado:** {fin['PAGADO']}€\n"
        f"⏳ **Pendiente:** {fin['PENDIENTE']}€\n\n"
        "_El negocio no duerme. Sigue cerrando fechas._ 🎧"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# --- HANDLER /radar ---
@restricted
async def radar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("🚨 Usa: `/radar Nombre-de-la-Sala`", parse_mode=ParseMode.MARKDOWN)
        return
        
    sala = " ".join(context.args).strip()
    reportes = check_radar(sala)
    
    if reportes > 0:
        await update.message.reply_text(
            f"🚨 *ALERTA ROJA: {sala.upper()}*\n\n"
            f"⚠️ Esta sala tiene **{reportes} reportes** de impagos o problemas técnicos.\n\n"
            "**CONSEJO NOVA:** Exige el 100% por adelantado o no te subas a la cabina.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            f"✅ *RADAR LIMPIO: {sala.upper()}*\n\n"
            "No tenemos reportes negativos de esta sala en nuestra base de datos actual.\n"
            "Recuerda siempre firmar contrato. ⚡️",
            parse_mode=ParseMode.MARKDOWN
        )

# --- HANDLER /coldmail ---
@restricted
async def coldmail_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("✉️ Usa: `/coldmail Sala, Género, Experiencia`", parse_mode=ParseMode.MARKDOWN)
        return
        
    data = " ".join(context.args)
    msg = await update.message.reply_text("⚡️ *Generando ataque comercial...*")
    
    from bot_engine.services.ai_engine import ai_engine
    email = await ai_engine.generate_cold_mail(data)
    
    await msg.edit_text(email, parse_mode=ParseMode.MARKDOWN)

# --- CONSTRUCTORES ---
def get_bolo_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("bolo", start_bolo)],
        states={
            BOLO_SALA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_bolo_sala)],
            BOLO_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_bolo_fecha)],
            BOLO_CACHE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_bolo_cache)],
        },
        fallbacks=[CommandHandler("cancelar", lambda u, c: ConversationHandler.END)],
    )
