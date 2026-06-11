"""Handle /decode flow — auto-detect and decode hidden messages."""
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.detect import detect_method
from stegano.zwc import decode_zwc
from stegano.snow import decode_snow
from stegano.homoglyph import decode_homoglyph
from stegano.variation_selector import decode_vs
from stegano.emoji import decode_emoji


async def decode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start decode flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, step="awaiting_decode")
    await update.message.reply_text(
        "🔍 *Decode a hidden message*\n\nSend the stego text to decode:",
        parse_mode="Markdown",
    )


async def decode_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle stego text submission for decoding."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_decode":
        return False  # Not in decode flow

    stego = update.message.text
    method = detect_method(stego)

    if method is None:
        await update.message.reply_text(
            "❌ *No hidden data detected.*\n\n"
            "The text doesn't contain any recognizable steganographic patterns.\n"
            "Supported: ZWC, SNOW, Homoglyph, Variation Selector, Emoji.",
            parse_mode="Markdown",
        )
    else:
        decoders = {
            "zwc": decode_zwc,
            "snow": decode_snow,
            "homoglyph": decode_homoglyph,
            "variation_selector": decode_vs,
            "emoji": decode_emoji,
        }
        decoded = decoders[method](stego)

        method_names = {
            "zwc": "Zero-Width Chars",
            "snow": "Whitespace/SNOW",
            "homoglyph": "Homoglyph",
            "variation_selector": "Unicode Variation Selector",
            "emoji": "Emoji Steganography",
        }

        await update.message.reply_text(
            f"🔍 *Hidden data found!*\n\n"
            f"Method: {method_names[method]}\n"
            f"Message:\n\n`{decoded}`",
            parse_mode="Markdown",
        )

    session_mgr.reset(chat_id)
    return True  # Handled
