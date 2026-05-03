"""
NOVA_CORE — Invoice Handler
ConversationHandler para generar facturas via Telegram.
Flujo: /factura -> Nombre sala -> CIF -> Importe -> Fecha -> Confirmacion -> PDF
"""
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
)
from telegram.constants import ParseMode
from datetime import datetime
from bot_engine.services.legal_engine import InvoiceData, create_invoice, get_dj_profile, save_dj_profile
from bot_engine.services.verifactu_engine import generate_verifactu_xml, send_to_aeat
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.invoice")

# Estados de la conversacion
VENUE_NAME, VENUE_CIF, AMOUNT, DATE, CONFIRM, DJ_NAME, DJ_NIF, DJ_ADDRESS = range(8)


async def factura_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo de facturacion."""
    logger.info(f"/factura de {update.effective_user.first_name}")
    user_id = update.effective_user.id
    profile = get_dj_profile(user_id)
    if not profile:
        await update.message.reply_text(
            "*BIENVENIDO AL GENERADOR DE FACTURAS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Como es tu primera vez, necesito tus datos de facturación.\n\n"
            "Escribe tu *Nombre o Razón Social* (Emisor):",
            parse_mode=ParseMode.MARKDOWN,
        )
        return DJ_NAME
    else:
        context.user_data["dj_name"] = profile[0]
        context.user_data["dj_nif"] = profile[1]
        context.user_data["dj_address"] = profile[2]
        return await start_venue(update, context)

async def start_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*GENERADOR DE FACTURAS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Vamos a crear una factura profesional.\n\n"
        "Escribe el *nombre de la sala/cliente*:\n\n"
        "_Envía /cancelar para salir_",
        parse_mode=ParseMode.MARKDOWN,
    )
    return VENUE_NAME

async def dj_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dj_name"] = update.message.text.strip()
    await update.message.reply_text("Ahora escribe tu *CIF/NIF*:", parse_mode=ParseMode.MARKDOWN)
    return DJ_NIF

async def dj_nif_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dj_nif"] = update.message.text.strip().upper()
    await update.message.reply_text("Ahora escribe tu *Dirección fiscal*:", parse_mode=ParseMode.MARKDOWN)
    return DJ_ADDRESS

async def dj_address_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dj_address"] = update.message.text.strip()
    user_id = update.effective_user.id
    save_dj_profile(user_id, context.user_data["dj_name"], context.user_data["dj_nif"], context.user_data["dj_address"])
    await update.message.reply_text("✅ *Perfil guardado correctamente.*\n\n¡Vamos con tu primera factura!", parse_mode=ParseMode.MARKDOWN)
    return await start_venue(update, context)


async def venue_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["venue_name"] = update.message.text.strip()
    await update.message.reply_text(
        f"Sala: *{context.user_data['venue_name']}*\n\n"
        "Ahora escribe el *CIF/NIF* de la sala:",
        parse_mode=ParseMode.MARKDOWN,
    )
    return VENUE_CIF


async def venue_cif_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cif = update.message.text.strip().upper()
    context.user_data["venue_cif"] = cif
    await update.message.reply_text(
        f"CIF: *{cif}*\n\n"
        "Escribe el *importe bruto del bolo* (en EUR).\n"
        "Ejemplo: `500`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return AMOUNT


async def amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(",", ".").replace("€", "").replace("EUR", "").strip()
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Importe no valido. Escribe un numero, ejemplo: `500`",
            parse_mode=ParseMode.MARKDOWN)
        return AMOUNT

    context.user_data["amount"] = amount
    today = datetime.now().strftime("%d/%m/%Y")
    keyboard = [[today, "Otra fecha"]]
    await update.message.reply_text(
        f"Importe: *{amount:.2f} EUR*\n\n"
        f"Fecha de la factura?\n"
        f"Pulsa el boton o escribe en formato DD/MM/YYYY:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return DATE


async def date_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "Otra fecha":
        await update.message.reply_text(
            "Escribe la fecha en formato *DD/MM/YYYY*:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove(),
        )
        return DATE

    # Validar fecha
    try:
        datetime.strptime(text, "%d/%m/%Y")
    except ValueError:
        await update.message.reply_text("Formato invalido. Usa DD/MM/YYYY, ejemplo: 15/05/2026")
        return DATE

    context.user_data["date"] = text

    # Calcular preview
    from bot_engine.services.legal_engine import calculate_invoice
    calc = calculate_invoice(context.user_data["amount"])

    keyboard = [["CONFIRMAR", "CANCELAR"]]
    await update.message.reply_text(
        f"*RESUMEN DE FACTURA*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Sala: *{context.user_data['venue_name']}*\n"
        f"CIF: `{context.user_data['venue_cif']}`\n"
        f"Fecha: {text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Bruto: `{calc['gross']:.2f} EUR`\n"
        f"Base imponible: `{calc['base_imponible']:.2f} EUR`\n"
        f"IVA (21%): `+{calc['iva']:.2f} EUR`\n"
        f"IRPF (15%): `-{calc['irpf']:.2f} EUR`\n"
        f"Comision (10%): `-{calc['comision']:.2f} EUR`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*NETO: {calc['neto']:.2f} EUR*\n\n"
        f"Pulsa *CONFIRMAR* para generar el PDF:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CONFIRM


async def confirm_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    if text != "CONFIRMAR":
        await update.message.reply_text("Factura cancelada.",
            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    await update.message.reply_text(
        "Generando factura PDF...",
        reply_markup=ReplyKeyboardRemove(),
    )

    data = InvoiceData(
        venue_name=context.user_data["venue_name"],
        venue_cif=context.user_data["venue_cif"],
        gross_amount=context.user_data["amount"],
        date=context.user_data["date"],
        dj_name=context.user_data["dj_name"],
        dj_nif=context.user_data["dj_nif"],
        dj_address=context.user_data["dj_address"],
    )

    try:
        result = create_invoice(data, user_id=update.effective_user.id)
        
        # MODO SANDBOX: Generar XML VeriFactu local
        xml_path = generate_verifactu_xml(result, data.dj_name, data.dj_nif)
        send_to_aeat(xml_path)
        
    except Exception as e:
        logger.error(f"Error generando factura: {e}", exc_info=True)
        await update.message.reply_text(f"Error al generar: {e}")
        return ConversationHandler.END

    # Enviar PDF
    with open(result.pdf_path, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=f"{result.invoice_number}.pdf",
            caption=(
                f"*Factura {result.invoice_number}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Sala: {result.venue_name}\n"
                f"Bruto: {result.gross_amount:.2f} EUR\n"
                f"*Neto: {result.net_amount:.2f} EUR*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Hash: `{result.invoice_hash[:24]}...`\n"
                f"_Verifactu Ready_"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    logger.info(f"Factura {result.invoice_number} enviada a {update.effective_user.first_name}")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Factura cancelada.",
        reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_invoice_conversation() -> ConversationHandler:
    """Retorna el ConversationHandler listo para registrar en main.py"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("factura", factura_start),
            MessageHandler(filters.Regex("^🧾 Crear Factura$"), factura_start)
        ],
        states={
            VENUE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, venue_name_received)],
            VENUE_CIF: [MessageHandler(filters.TEXT & ~filters.COMMAND, venue_cif_received)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_received)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_received)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_received)],
            DJ_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, dj_name_received)],
            DJ_NIF: [MessageHandler(filters.TEXT & ~filters.COMMAND, dj_nif_received)],
            DJ_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, dj_address_received)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )
