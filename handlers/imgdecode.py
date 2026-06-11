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
        "Send a stego image to extract the hidden message.\n\n"
        "⚠️ *Important:* Send as a *file/document* (📎), NOT as a photo! "
        "Photos get compressed by Telegram and destroy hidden data.",
        parse_mode="Markdown",
    )


async def imgdecode_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle photo upload in image decode flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_stego_image":
        return False

    # Download the photo (Telegram compressed this!)
    photo = update.message.photo[-1]
    file = await photo.get_file()

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, "stego.png")
    await file.download_to_drive(input_path)

    # Convert to PNG
    from PIL import Image
    img = Image.open(input_path)
    png_path = os.path.join(tmp_dir, "stego.png")
    img.save(png_path, format='PNG')

    # Try to decode
    try:
        decoded = decode_lsb(png_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to decode: {e}")
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
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
            "This might be because Telegram *compressed* your photo, "
            "destroying the hidden data.\n\n"
            "💡 *Fix:* Send the stego image as a *file/document* (📎), "
            "not as a photo. Use the 📎 button → select the image file.",
            parse_mode="Markdown",
        )

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    session_mgr.reset(chat_id)
    return True


async def imgdecode_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle document upload in image decode flow (preserves pixels!)."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_stego_image":
        return False

    doc = update.message.document
    if not doc:
        return False

    # Only accept image documents
    if not doc.mime_type or not doc.mime_type.startswith('image/'):
        await update.message.reply_text("❌ Please send an image file (PNG, JPG, etc.)")
        return True

    file = await doc.get_file()
    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, f"stego_{doc.file_name or 'image.png'}")
    await file.download_to_drive(input_path)

    # Convert to PNG
    from PIL import Image
    img = Image.open(input_path)
    png_path = os.path.join(tmp_dir, "stego.png")
    img.save(png_path, format='PNG')

    # Try to decode
    try:
        decoded = decode_lsb(png_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to decode: {e}")
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
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
            "The image doesn't contain steganographic data.",
            parse_mode="Markdown",
        )

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    session_mgr.reset(chat_id)
    return True
