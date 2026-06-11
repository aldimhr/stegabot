"""StegaBot — Telegram bot for text steganography."""
import logging
from telegram import Update
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
from handlers.demo import demo_handler
from handlers.encrypt import encrypt_handler

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


def main():
    """Start the bot."""
    if not TELEGRAM_BOT_KEY:
        logger.error("TELEGRAM_BOT_KEY not set in .env")
        return

    app = Application.builder().token(TELEGRAM_BOT_KEY).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("methods", methods_handler))
    app.add_handler(CommandHandler("demo", demo_handler))
    app.add_handler(CommandHandler("encode",
        lambda u, c: encode_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("decode",
        lambda u, c: decode_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("detect",
        lambda u, c: detect_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("encrypt",
        lambda u, c: encrypt_handler(u, c, session_mgr)))

    # Callback query handlers (inline buttons)
    app.add_handler(CallbackQueryHandler(method_callback, pattern="^method_"))
    app.add_handler(CallbackQueryHandler(
        lambda u, c: encode_method_callback(u, c, session_mgr),
        pattern="^enc_method_"
    ))

    # Text message router (for multi-turn flows)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    logger.info("StegaBot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
