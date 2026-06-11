"""Handle /imgencode — hide text in images using LSB."""
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.image_lsb import encode_lsb, capacity_lsb
from stegano.utils import image_capacity_check
from config import MAX_SECRET_BYTES


async def imgencode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start image encode flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, method="image_lsb", step="awaiting_image")
    await update.message.reply_text(
        "🖼️ *Image Steganography — Encode*\n\n"
        "Send a *PNG image* to use as cover:\n\n"
        "💡 For best results, use PNG images. "
        "JPEG images will be converted to PNG but may lose quality.",
        parse_mode="Markdown",
    )


async def imgencode_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle photo upload in image encode flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_image":
        return False

    # Download the photo
    photo = update.message.photo[-1]  # Highest resolution
    file = await photo.get_file()

    # Save to temp directory
    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, "cover.png")
    await file.download_to_drive(input_path)

    # Convert to PNG (Telegram sends JPEG for photos)
    from PIL import Image
    img = Image.open(input_path)
    png_path = os.path.join(tmp_dir, "cover.png")
    img.save(png_path, format='PNG')

    # Check capacity
    cap = capacity_lsb(png_path)
    session_mgr.update(
        chat_id,
        cover_image=png_path,
        step="awaiting_image_secret",
    )

    await update.message.reply_text(
        f"✅ Image received! ({img.width}×{img.height})\n\n"
        f"📊 Capacity: {cap['capacity_chars']:,} characters\n\n"
        f"Now send your *SECRET MESSAGE* to hide:",
        parse_mode="Markdown",
    )
    return True


async def imgencode_secret_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle secret text in image encode flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_image_secret":
        return False

    secret = update.message.text
    cover_path = session.get("cover_image")

    if not cover_path or not os.path.exists(cover_path):
        await update.message.reply_text("❌ Cover image not found. Please /imgencode again.")
        session_mgr.reset(chat_id)
        return True

    # Check size
    if len(secret.encode('utf-8')) > MAX_SECRET_BYTES:
        await update.message.reply_text(
            f"⚠️ Secret too long ({len(secret.encode('utf-8'))} bytes). Max: {MAX_SECRET_BYTES} bytes."
        )
        return True

    # Check capacity
    cap = image_capacity_check(cover_path, secret)
    if not cap['enough']:
        await update.message.reply_text(
            f"⚠️ Secret too long for this image!\n\n"
            f"Need: {cap['needed_bits']:,} bits\n"
            f"Capacity: {cap['capacity_bits']:,} bits\n\n"
            f"Try a larger image or shorter secret."
        )
        return True

    # Encode
    stego_path = cover_path.replace("cover.png", "stego.png")
    try:
        encode_lsb(cover_path, secret, stego_path)
    except ValueError as e:
        await update.message.reply_text(f"❌ Error: {e}")
        session_mgr.reset(chat_id)
        return True

    # Send as document (preserves pixels!)
    await update.message.reply_document(
        document=open(stego_path, 'rb'),
        filename="stego_image.png",
        caption=(
            "✅ *Secret hidden in image!*\n\n"
            f"📊 Used: {len(secret):,}/{cap['capacity_chars']:,} chars\n"
            f"Method: LSB (Least Significant Bit)\n\n"
            "⚠️ *Important:* Download this image to decode. "
            "Screenshots will destroy the hidden data!"
        ),
        parse_mode="Markdown",
    )

    # Cleanup
    import shutil
    shutil.rmtree(os.path.dirname(cover_path), ignore_errors=True)
    session_mgr.reset(chat_id)
    return True
