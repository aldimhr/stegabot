"""Handle /audiodetect — scan audio for hidden LSB data."""
import os
import tempfile
import shutil
import logging
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.audio_lsb import has_audio_data, audio_capacity

logger = logging.getLogger(__name__)


async def audiodetect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start audio detect flow."""
    chat_id = update.effective_chat.id
    session_mgr.reset(chat_id)
    session_mgr.update(chat_id, step="awaiting_detect_audio")
    await update.message.reply_text(
        "🔍 *Audio Analysis*\n\n"
        "Send a WAV file to scan for hidden data:",
        parse_mode="Markdown",
    )


async def audiodetect_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle uploaded WAV for detection."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_detect_audio":
        return False

    doc = update.message.document
    if not doc:
        return False

    if not doc.file_name or not doc.file_name.lower().endswith(".wav"):
        await update.message.reply_text("❌ Please send a WAV file (.wav).")
        return True

    # Download to temp dir
    tmp_dir = tempfile.mkdtemp(prefix="stegabot_detect_")
    audio_path = os.path.join(tmp_dir, "input.wav")
    file = await doc.get_file()
    await file.download_to_drive(audio_path)

    try:
        has_data = has_audio_data(audio_path)
        cap = audio_capacity(audio_path)

        # Get audio info
        duration_info = ""
        try:
            from scipy.io import wavfile
            sr, data = wavfile.read(audio_path)
            if data.ndim > 1:
                data = data[:, 0]
            duration = len(data) / sr
            duration_info = f"Duration: {duration:.1f}s\n"
        except Exception:
            pass

        if has_data:
            await update.message.reply_text(
                "🔍 *Audio Analysis Results*\n\n"
                "✅ *Hidden LSB data detected!*\n"
                "Method: Audio LSB\n"
                f"{duration_info}"
                f"File capacity: {cap:,} bytes\n\n"
                "Use /audiodecode to extract the hidden message.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "🔍 *Audio Analysis Results*\n\n"
                "❌ *No hidden data detected.*\n"
                f"{duration_info}"
                f"File capacity: {cap:,} bytes\n\n"
                "This file appears clean.",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Audio detect error: {e}")
        await update.message.reply_text(f"❌ Analysis failed: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        session_mgr.reset(chat_id)

    return True
