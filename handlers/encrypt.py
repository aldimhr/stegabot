"""Handle /encrypt on|off toggle."""
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager


async def encrypt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Toggle AES encryption mode."""
    chat_id = update.effective_chat.id
    args = context.args

    if not args or args[0].lower() not in ('on', 'off'):
        await update.message.reply_text(
            "🔐 *AES Encryption*\n\n"
            "Usage: `/encrypt on` or `/encrypt off`\n\n"
            "When enabled, your secret is encrypted with AES-128 before "
            "being hidden. Even if someone extracts the hidden data, "
            "they can't read it without your passphrase.",
            parse_mode="Markdown",
        )
        return

    mode = args[0].lower()
    if mode == "on":
        session_mgr.update(chat_id, encrypt=True)
        await update.message.reply_text(
            "🔐 AES encryption *enabled*.\n\n"
            "When you /encode, you'll be asked for a passphrase.\n"
            "The hidden message will be unreadable without it.",
            parse_mode="Markdown",
        )
    else:
        session_mgr.update(chat_id, encrypt=False, passphrase=None)
        await update.message.reply_text(
            "🔓 AES encryption *disabled*.",
            parse_mode="Markdown",
        )
