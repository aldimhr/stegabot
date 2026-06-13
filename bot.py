"""StegaBot — Telegram bot for text steganography."""
import logging
from telegram import BotCommand, MenuButtonCommands, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import TELEGRAM_BOT_KEY
from state import SessionManager
from ratelimit import RateLimiter

from handlers.start import start_handler
from handlers.methods import methods_handler, method_callback
from handlers.encode import encode_handler, encode_method_callback, encode_message_handler
from handlers.decode import decode_handler, decode_message_handler
from handlers.detect import detect_handler, detect_message_handler
from handlers.demo import demo_handler, imgdemo_handler
from handlers.encrypt import encrypt_handler
from handlers.learn import learn_handler, learn_callback
from handlers.imgencode import (
    imgencode_handler, imgencode_photo_handler, imgencode_document_handler,
    imgencode_depth_callback, imgencode_encrypt_callback,
    imgencode_passphrase_handler, imgencode_secret_handler
)
from handlers.imgdecode import (
    imgdecode_handler, imgdecode_photo_handler, imgdecode_document_handler,
    imgdecode_decrypt_choice, imgdecode_passphrase_handler
)
from handlers.imgdetect import imgdetect_handler, imgdetect_photo_handler, imgdetect_document_handler
from handlers.audioencode import audioencode_handler, audioencode_document_handler, audioencode_secret_handler
from handlers.audiodecode import audiodecode_handler, audiodecode_document_handler
from handlers.audiodetect import audiodetect_handler, audiodetect_document_handler
from handlers.capacity import capacity_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

session_mgr = SessionManager()
rate_limiter = RateLimiter()


async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route text messages to the correct handler based on session state."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Rate limit check
    if not rate_limiter.is_allowed(user_id):
        remaining = rate_limiter.remaining(user_id)
        await update.message.reply_text(
            f"⏳ Please wait {remaining:.1f}s before trying again."
        )
        return

    session = session_mgr.get(chat_id)
    step = session.get("step")

    if step == "awaiting_decode":
        await decode_message_handler(update, context, session_mgr)
    elif step == "awaiting_detect":
        await detect_message_handler(update, context, session_mgr)
    elif step in ("awaiting_cover", "awaiting_secret"):
        await encode_message_handler(update, context, session_mgr)
    elif step == "awaiting_image_secret":
        await imgencode_secret_handler(update, context, session_mgr)
    elif step == "awaiting_image_passphrase":
        await imgencode_passphrase_handler(update, context, session_mgr)
    elif step == "awaiting_image_decrypt_passphrase":
        await imgdecode_passphrase_handler(update, context, session_mgr)
    elif step == "awaiting_secure_passphrase":
        await imgdecode_passphrase_handler(update, context, session_mgr)
    elif step == "awaiting_audio_secret":
        await audioencode_secret_handler(update, context, session_mgr)


async def post_init(app: Application) -> None:
    """Set bot commands menu after initialization."""
    commands = [
        BotCommand("start", "🔐 Welcome & overview"),
        BotCommand("encode", "📝 Hide a secret in text"),
        BotCommand("decode", "📝 Extract a hidden text message"),
        BotCommand("detect", "🔍 Scan text for hidden data"),
        BotCommand("imgencode", "🖼️ Hide text in an image"),
        BotCommand("imgdecode", "🖼️ Extract hidden text from image"),
        BotCommand("imgdetect", "🔍 Scan image for hidden data"),
        BotCommand("methods", "📖 Learn about steganography methods"),
        BotCommand("demo", "📝 Live text steganography demo"),
        BotCommand("imgdemo", "🖼️ Live image steganography demo"),
        BotCommand("encrypt", "🔒 Toggle AES-128 encryption"),
        BotCommand("learn", "📚 Learn steganography theory"),
        BotCommand("audioencode", "🎵 Hide text in audio (WAV)"),
        BotCommand("audiodecode", "🎵 Extract hidden text from audio"),
        BotCommand("audiodetect", "🔍 Scan audio for hidden data"),
        BotCommand("capacity", "📊 Capacity guide for all methods"),
    ]
    await app.bot.set_my_commands(commands)
    # Force menu button to show commands (not web app)
    await app.bot.set_chat_menu_button(
        chat_id=app.bot.id, menu_button=MenuButtonCommands()
    )
    logger.info("Bot commands menu + menu button registered")


def main():
    """Start the bot."""
    if not TELEGRAM_BOT_KEY:
        logger.error("TELEGRAM_BOT_KEY not set in .env")
        return

    app = Application.builder().token(TELEGRAM_BOT_KEY).post_init(post_init).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("methods", methods_handler))
    app.add_handler(CommandHandler("demo", demo_handler))
    app.add_handler(CommandHandler("imgdemo", imgdemo_handler))
    app.add_handler(CommandHandler("encode",
        lambda u, c: encode_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("decode",
        lambda u, c: decode_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("detect",
        lambda u, c: detect_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("encrypt",
        lambda u, c: encrypt_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("learn", learn_handler))
    app.add_handler(CommandHandler("imgencode",
        lambda u, c: imgencode_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("imgdecode",
        lambda u, c: imgdecode_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("imgdetect",
        lambda u, c: imgdetect_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("audioencode",
        lambda u, c: audioencode_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("audiodecode",
        lambda u, c: audiodecode_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("audiodetect",
        lambda u, c: audiodetect_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("capacity", capacity_handler))

    # Callback query handlers (inline buttons)
    app.add_handler(CallbackQueryHandler(method_callback, pattern="^method_"))
    app.add_handler(CallbackQueryHandler(learn_callback, pattern="^learn_"))
    app.add_handler(CallbackQueryHandler(
        lambda u, c: encode_method_callback(u, c, session_mgr),
        pattern="^enc_method_"
    ))
    app.add_handler(CallbackQueryHandler(
        lambda u, c: imgencode_depth_callback(u, c, session_mgr),
        pattern="^lsb_depth_"
    ))
    app.add_handler(CallbackQueryHandler(
        lambda u, c: imgencode_encrypt_callback(u, c, session_mgr),
        pattern="^img_encrypt_"
    ))
    app.add_handler(CallbackQueryHandler(
        lambda u, c: imgdecode_decrypt_choice(u, c, session_mgr),
        pattern="^img_dec_"
    ))

    # Text message router (for multi-turn flows)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    # Photo router (for image steganography flows)
    async def photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route photo messages to the correct handler."""
        chat_id = update.effective_chat.id
        session = session_mgr.get(chat_id)
        step = session.get("step")

        if step == "awaiting_image":
            await imgencode_photo_handler(update, context, session_mgr)
        elif step == "awaiting_stego_image":
            await imgdecode_photo_handler(update, context, session_mgr)
        elif step == "awaiting_detect_image":
            await imgdetect_photo_handler(update, context, session_mgr)

    app.add_handler(MessageHandler(filters.PHOTO, photo_router))

    # Document router (for image and audio — documents preserve data!)
    async def document_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route document messages to the correct handler."""
        chat_id = update.effective_chat.id
        session = session_mgr.get(chat_id)
        step = session.get("step")

        if step == "awaiting_image":
            await imgencode_document_handler(update, context, session_mgr)
        elif step == "awaiting_stego_image":
            await imgdecode_document_handler(update, context, session_mgr)
        elif step == "awaiting_detect_image":
            await imgdetect_document_handler(update, context, session_mgr)
        elif step == "awaiting_audio":
            await audioencode_document_handler(update, context, session_mgr)
        elif step == "awaiting_stego_audio":
            await audiodecode_document_handler(update, context, session_mgr)
        elif step == "awaiting_detect_audio":
            await audiodetect_document_handler(update, context, session_mgr)

    app.add_handler(MessageHandler(filters.Document.ALL, document_router))

    logger.info("StegaBot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
