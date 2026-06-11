"""Handle /imgdecode — extract hidden text from images."""
import logging
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.image_lsb import decode_lsb, capacity_lsb

logger = logging.getLogger(__name__)


async def imgdecode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start image decode flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, step="awaiting_stego_image")
    await update.message.reply_text(
        "🔍 *Image Steganography — Decode*\n\n"
        "Send the stego image to extract the hidden message.\n\n"
        "⚠️ *CRITICAL:* Tap 📎 → select the image file. "
        "Do NOT use the camera/photo picker — Telegram compresses photos!",
        parse_mode="Markdown",
    )


async def _process_decode_image(update: Update, session_mgr: SessionManager, file, filename: str, is_document: bool):
    """Common logic for decoding image from photo or document."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_stego_image":
        return False

    logger.info(f"Decode attempt: chat={chat_id}, is_document={is_document}, filename={filename}")

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, filename)
    await file.download_to_drive(input_path)

    file_size = os.path.getsize(input_path)
    logger.info(f"Downloaded file: {input_path}, size={file_size}")

    # Convert to PNG
    from PIL import Image
    img = Image.open(input_path)
    logger.info(f"Image: {img.size}, mode={img.mode}, format={img.format}")

    png_path = os.path.join(tmp_dir, "stego.png")
    img.save(png_path, format='PNG')

    cap = capacity_lsb(png_path)
    logger.info(f"Capacity: {cap}")

    # Try to decode
    try:
        decoded = decode_lsb(png_path)
    except Exception as e:
        logger.error(f"Decode error: {e}")
        await update.message.reply_text(f"❌ Failed to decode: {e}")
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
        session_mgr.reset(chat_id)
        return True

    logger.info(f"Decoded result: '{decoded[:50] if decoded else '(empty)'}'")

    if decoded:
        await update.message.reply_text(
            f"🔍 *Hidden message found!*\n\n"
            f"Method: LSB (Image)\n"
            f"Message:\n\n`{decoded}`",
            parse_mode="Markdown",
        )
    else:
        if not is_document:
            await update.message.reply_text(
                "❌ *No hidden message found.*\n\n"
                "This is because Telegram *compressed your photo*, "
                "destroying the hidden data.\n\n"
                "✅ *How to fix:*\n"
                "1. Download the stego image to your phone\n"
                "2. Tap 📎 (attachment button)\n"
                "3. Select the image file\n"
                "4. Send it\n\n"
                "Do NOT use the camera/photo picker!",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "❌ *No hidden message found.*\n\n"
                "The image doesn't contain steganographic data.",
                parse_mode="Markdown",
            )

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    session_mgr.reset(chat_id)
    return True


async def imgdecode_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle photo upload in image decode flow (photo = compressed by Telegram!)."""
    photo = update.message.photo[-1]
    file = await photo.get_file()
    return await _process_decode_image(update, session_mgr, file, "stego.jpg", is_document=False)


async def imgdecode_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle document upload in image decode flow (document = pixel-perfect!)."""
    doc = update.message.document
    if not doc:
        return False
    if not doc.mime_type or not doc.mime_type.startswith('image/'):
        await update.message.reply_text("❌ Please send an image file (PNG, JPG, etc.)")
        return True
    file = await doc.get_file()
    return await _process_decode_image(update, session_mgr, file, doc.file_name or "stego.png", is_document=True)
