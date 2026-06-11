"""Handle /imgdetect — scan images for hidden data."""
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.image_lsb import decode_lsb, capacity_lsb


async def imgdetect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start image detect flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, step="awaiting_detect_image")
    await update.message.reply_text(
        "🔎 *Image Steganalysis*\n\n"
        "Send an image to scan for hidden data:",
        parse_mode="Markdown",
    )


async def imgdetect_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle photo upload in image detect flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_detect_image":
        return False

    photo = update.message.photo[-1]
    file = await photo.get_file()

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, "scan.png")
    await file.download_to_drive(input_path)

    from PIL import Image
    img = Image.open(input_path)
    png_path = os.path.join(tmp_dir, "scan.png")
    img.save(png_path, format='PNG')

    cap = capacity_lsb(png_path)

    # Try to decode
    decoded = decode_lsb(png_path)

    if decoded:
        await update.message.reply_text(
            f"🔎 *Scan Results*\n\n"
            f"✅ *Hidden data detected!*\n\n"
            f"Image: {img.width}×{img.height}\n"
            f"LSB capacity: {cap['capacity_chars']:,} chars\n"
            f"Hidden message: `{decoded[:100]}`{'...' if len(decoded) > 100 else ''}\n\n"
            f"Use /imgdecode to extract the full message.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"🔎 *Scan Results*\n\n"
            f"✅ *Clean — no hidden data detected.*\n\n"
            f"Image: {img.width}×{img.height}\n"
            f"LSB capacity: {cap['capacity_chars']:,} chars\n\n"
            f"The image appears to be free of steganographic patterns.",
            parse_mode="Markdown",
        )

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    session_mgr.reset(chat_id)
    return True
