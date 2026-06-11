"""Handle /detect — scan text for hidden data."""
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.detect import ZWC_CHARS, CYRILLIC_LOOKALIKES


async def detect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start detect flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, step="awaiting_detect")
    await update.message.reply_text(
        "🔎 *Steganalysis Scanner*\n\nSend any text to scan for hidden data:",
        parse_mode="Markdown",
    )


async def detect_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle text submission for detection."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_detect":
        return False

    text = update.message.text
    findings = []

    # Check each method
    zwc_count = sum(1 for c in text if c in ZWC_CHARS)
    if zwc_count > 0:
        findings.append(f"🔹 *Zero-Width Chars:* {zwc_count} invisible characters found")

    homoglyph_count = sum(1 for c in text if c in CYRILLIC_LOOKALIKES)
    if homoglyph_count > 0:
        findings.append(f"🔹 *Homoglyph:* {homoglyph_count} Cyrillic lookalike characters found")

    lines = text.split('\n')
    snow_lines = sum(1 for line in lines if line.endswith('\t') or line.endswith('  '))
    if snow_lines > 0:
        findings.append(f"🔹 *SNOW:* {snow_lines} lines with trailing whitespace")

    if findings:
        report = "\n\n".join(findings)
        await update.message.reply_text(
            f"🔎 *Scan Results*\n\n{report}\n\n"
            f"Use /decode to extract the hidden message.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "✅ *Clean — no hidden data detected.*\n\n"
            "The text appears to be free of steganographic patterns.",
            parse_mode="Markdown",
        )

    session_mgr.reset(chat_id)
    return True
