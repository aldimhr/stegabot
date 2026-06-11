"""Handle /imgdecode — extract hidden text from images."""
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.image_lsb import decode_lsb


async def imgdecode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start image decode flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, step="awaiting_stego_image")
    await update.message.reply_text(
        "🔍 *Image Steganography — Decode*\n\n"
        "Send a stego image to extract the hidden message:",
        parse_mode="Markdown",
    )


async def imgdecode_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle photo upload in image decode flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_stego_image":
        return False

    # Download the photo
    photo = update.message.photo[-1]
    file = await photo.get_file()

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, "stego.png")
    await file.download_to_drive(input_path)

    # Convert to PNG (Telegram may have compressed it)
    from PIL import Image
    img = Image.open(input_path)
    png_path = os.path.join(tmp_dir, "stego.png")
    img.save(png_path, format='PNG')

    # Try to decode
    try:
        decoded = decode_lsb(png_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to decode: {e}")
        session_mgr.reset(chat_id)
        return True

    if decoded:
        await update.message.reply_text(
            f"🔍 *Hidden message found!*\n\n"
            f"Method: LSB (Image)\n"
            f"Message:\n\n`{decoded}`",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "❌ *No hidden message found.*\n\n"
            "The image doesn't contain steganographic data, "
            "or it was compressed/modified after encoding.\n\n"
            "💡 Make sure to download the original image. "
            "Screenshots destroy hidden data.",
            parse_mode="Markdown",
        )

    # Cleanup
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    session_mgr.reset(chat_id)
    return True
