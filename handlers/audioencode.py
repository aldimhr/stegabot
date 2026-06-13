"""Handle /audioencode — hide text in audio using LSB."""
import os
import tempfile
import shutil
import logging
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.audio_lsb import encode_audio, audio_capacity

logger = logging.getLogger(__name__)


async def audioencode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start audio encode flow."""
    chat_id = update.effective_chat.id
    session_mgr.reset(chat_id)
    session_mgr.update(chat_id, method="audio", step="awaiting_audio")
    await update.message.reply_text(
        "🎵 *Audio LSB Steganography — Encode*\n\n"
        "Send a WAV audio file (16-bit PCM) as a *document* (📎):\n\n"
        "💡 Larger files hide more data — ~1KB per second of audio.\n"
        "⚠️ Must be WAV format. Other audio formats are not supported.",
        parse_mode="Markdown",
    )


async def audioencode_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle uploaded WAV document."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_audio":
        return False

    doc = update.message.document
    if not doc:
        return False

    if not doc.file_name or not doc.file_name.lower().endswith(".wav"):
        await update.message.reply_text(
            "❌ Please send a WAV file (.wav). Other audio formats are not supported."
        )
        return True

    # Download to temp dir
    tmp_dir = tempfile.mkdtemp(prefix="stegabot_audio_")
    input_path = os.path.join(tmp_dir, "input.wav")
    file = await doc.get_file()
    await file.download_to_drive(input_path)

    # Read audio info
    try:
        from scipy.io import wavfile
        sample_rate, data = wavfile.read(input_path)
        if data.ndim > 1:
            data = data[:, 0]
        duration = len(data) / sample_rate
    except Exception as e:
        await update.message.reply_text(f"❌ Cannot read audio file: {e}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        session_mgr.reset(chat_id)
        return True

    # Check capacity
    try:
        cap = audio_capacity(input_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Cannot calculate capacity: {e}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        session_mgr.reset(chat_id)
        return True

    session_mgr.update(
        chat_id,
        audio_path=input_path,
        audio_tmp_dir=tmp_dir,
        audio_capacity=cap,
        step="awaiting_audio_secret",
    )

    await update.message.reply_text(
        f"✅ Audio received!\n\n"
        f"🎵 Duration: {duration:.1f}s\n"
        f"📦 Capacity: {cap:,} bytes\n\n"
        f"Now send your *SECRET MESSAGE* to hide:",
        parse_mode="Markdown",
    )
    return True


async def audioencode_secret_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle secret message for audio encode."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_audio_secret":
        return False

    secret = update.message.text
    secret_bytes = secret.encode("utf-8")
    capacity = session.get("audio_capacity", 0)

    if len(secret_bytes) > capacity:
        await update.message.reply_text(
            f"⚠️ Secret too long! {len(secret_bytes):,} bytes > {capacity:,} bytes capacity.\n\n"
            f"Send a shorter secret or use a longer audio file."
        )
        return True

    input_path = session.get("audio_path")
    tmp_dir = session.get("audio_tmp_dir")

    if not input_path or not os.path.exists(input_path):
        await update.message.reply_text("❌ Audio file not found. Please /audioencode again.")
        session_mgr.reset(chat_id)
        return True

    output_path = os.path.join(tmp_dir, "stego.wav")

    try:
        encode_audio(input_path, secret, output_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Encoding failed: {e}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        session_mgr.reset(chat_id)
        return True

    # Send stego audio as document (preserves LSB data)
    await update.message.reply_document(
        document=open(output_path, "rb"),
        filename="stego_audio.wav",
        caption=(
            "✅ *Secret hidden in audio!*\n\n"
            f"Method: Audio LSB\n"
            f"Secret: {len(secret_bytes):,} bytes\n"
            f"Capacity: {len(secret_bytes):,}/{capacity:,} bytes "
            f"({len(secret_bytes)/capacity:.0%} used)\n\n"
            "📥 *To decode:*\n"
            "1. Download this file\n"
            "2. Send /audiodecode to the bot\n"
            "3. Tap 📎 → select this file → send\n\n"
            "⚠️ Send as 📎 document, NOT as voice message!"
        ),
        parse_mode="Markdown",
    )

    # Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)
    session_mgr.reset(chat_id)
    return True
