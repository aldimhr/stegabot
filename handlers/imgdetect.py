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
        "Send an image to scan for hidden data.\n\n"
        "💡 Send as a *file/document* (📎) for accurate results.",
        parse_mode="Markdown",
    )


async def _process_detect_image(update: Update, session_mgr: SessionManager, file, filename: str):
    """Common logic for photo and document detect handlers."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_detect_image":
        return False

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, filename)
    await file.download_to_drive(input_path)

    from PIL import Image
    img = Image.open(input_path)
    png_path = os.path.join(tmp_dir, "scan.png")
    img.save(png_path, format='PNG')

    cap = capacity_lsb(png_path)
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


async def imgdetect_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle photo upload in image detect flow."""
    photo = update.message.photo[-1]
    file = await photo.get_file()
    return await _process_detect_image(update, session_mgr, file, "scan.jpg")


async def imgdetect_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle document upload in image detect flow."""
    doc = update.message.document
    if not doc or not doc.mime_type or not doc.mime_type.startswith('image/'):
        return False
    file = await doc.get_file()
    return await _process_detect_image(update, session_mgr, file, doc.file_name or "scan.png")
