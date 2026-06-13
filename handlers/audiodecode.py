"""Handle /audiodecode — extract hidden text from stego audio."""
import os
import tempfile
import shutil
import logging
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.audio_lsb import decode_audio, has_audio_data

logger = logging.getLogger(__name__)


async def audiodecode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start audio decode flow."""
    chat_id = update.effective_chat.id
    session_mgr.reset(chat_id)
    session_mgr.update(chat_id, step="awaiting_stego_audio")
    await update.message.reply_text(
        "🔍 *Audio Decode*\n\n"
        "Send a stego WAV file to extract hidden data:\n\n"
        "💡 Send as a *document* (📎) to preserve file integrity.",
        parse_mode="Markdown",
    )


async def audiodecode_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle uploaded stego WAV document."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_stego_audio":
        return False

    doc = update.message.document
    if not doc:
        return False

    if not doc.file_name or not doc.file_name.lower().endswith(".wav"):
        await update.message.reply_text("❌ Please send a WAV file (.wav).")
        return True

    # Download to temp dir
    tmp_dir = tempfile.mkdtemp(prefix="stegabot_decode_")
    audio_path = os.path.join(tmp_dir, "input.wav")
    file = await doc.get_file()
    await file.download_to_drive(audio_path)

    try:
        # Check for hidden data
        if not has_audio_data(audio_path):
            await update.message.reply_text(
                "🔍 *No hidden data detected* in this audio file.\n\n"
                "Make sure the file was encoded with /audioencode.",
                parse_mode="Markdown",
            )
            shutil.rmtree(tmp_dir, ignore_errors=True)
            session_mgr.reset(chat_id)
            return True

        # Decode
        secret = decode_audio(audio_path)

        if not secret:
            await update.message.reply_text(
                "🔍 Data header found but message is empty."
            )
        else:
            await update.message.reply_text(
                f"✅ *Hidden message found!*\n\n"
                f"Method: Audio LSB\n"
                f"Message:\n```\n{secret}\n```",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Audio decode error: {e}")
        await update.message.reply_text(f"❌ Decode failed: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        session_mgr.reset(chat_id)

    return True
