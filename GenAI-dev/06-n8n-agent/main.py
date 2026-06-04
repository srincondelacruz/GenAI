# main.py — punto de entrada del bot de Telegram
# Gestiona los mensajes entrantes y el flujo de human-in-the-loop:
# recibe mensaje → ejecuta agente → si usó SerpAPI, pregunta si enviar email

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from agent import run_agent
from email_sender import send_email
from dotenv import load_dotenv
import os

load_dotenv()

# Almacena temporalmente los datos del email pendiente de confirmación por chat_id.
# Se elimina en cuanto el usuario pulsa Sí o No.
_pending: dict = {}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recibe cada mensaje de texto del usuario y lo procesa con el agente."""
    chat_id = update.effective_chat.id
    user_message = update.message.text

    result = await run_agent(user_message, str(chat_id))
    response = result["output"]

    if result["used_serpapi"]:
        # Guarda la pregunta y respuesta para usarlas si el usuario confirma el envío
        _pending[chat_id] = {"question": user_message, "answer": response}

        # Botones inline de confirmación (human-in-the-loop)
        keyboard = [[
            InlineKeyboardButton("✅ Sí, enviar informe al correo", callback_data="email_si"),
            InlineKeyboardButton("❌ No", callback_data="email_no"),
        ]]

        await update.message.reply_text(
            f"{response}\n\n---\n¿Quieres que te mande un informe al correo?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        # Respuesta normal sin búsqueda web
        await update.message.reply_text(response)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestiona el clic en los botones inline de confirmación de email."""
    query = update.callback_query
    await query.answer()  # Elimina el estado de carga del botón en Telegram

    chat_id = update.effective_chat.id

    if query.data == "email_si" and chat_id in _pending:
        data = _pending.pop(chat_id)
        send_email(data["question"], data["answer"])
        # Elimina los botones del mensaje original para evitar clics duplicados
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✅ Informe enviado a tu correo.")

    elif query.data == "email_no":
        _pending.pop(chat_id, None)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("Ok, no envío el informe.")


def main() -> None:
    """Arranca el bot en modo polling."""
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("Bot arrancado...")
    # ALL_TYPES es necesario para recibir callback_query además de mensajes normales
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
