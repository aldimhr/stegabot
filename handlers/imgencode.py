"""Handle /imgencode — hide text in images using LSB."""
import os
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        "Send a *cover image* (photo or file).\n\n"
        "💡 For best results, send as a *file/document* (📎) "
        "to avoid Telegram compression.",
        parse_mode="Markdown",
    )


async def _process_cover_image(update: Update, session_mgr: SessionManager, file, filename: str):
    """Common logic for processing cover image from photo or document."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_image":
        return False

    # Save to temp directory
    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, filename)
    await file.download_to_drive(input_path)

    # Convert to PNG
    from PIL import Image
    img = Image.open(input_path)
    png_path = os.path.join(tmp_dir, "cover.png")
    img.save(png_path, format='PNG')

    # Show capacity for all depths
    caps = {}
    for d in [1, 2, 3]:
        caps[d] = capacity_lsb(png_path, depth=d)

    session_mgr.update(
        chat_id,
        cover_image=png_path,
        step="awaiting_image_depth",
    )

    keyboard = [
        [
            InlineKeyboardButton(
                f"1️⃣ Safe ({caps[1]['capacity_chars']:,} chars)",
                callback_data="lsb_depth_1"
            ),
        ],
        [
            InlineKeyboardButton(
                f"2️⃣ Medium ({caps[2]['capacity_chars']:,} chars)",
                callback_data="lsb_depth_2"
            ),
        ],
        [
            InlineKeyboardButton(
                f"3️⃣ Max ({caps[3]['capacity_chars']:,} chars)",
                callback_data="lsb_depth_3"
            ),
        ],
    ]

    await update.message.reply_text(
        f"✅ Image received! ({img.width}×{img.height})\n\n"
        f"Choose LSB depth (bits per color channel):\n"
        f"• *Safe (1-bit)* — invisible, lower capacity\n"
        f"• *Medium (2-bit)* — 2× capacity, still hard to detect\n"
        f"• *Max (3-bit)* — 3× capacity, detectable by analysis",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return True


async def imgencode_depth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle LSB depth selection."""
    query = update.callback_query
    await query.answer()

    depth = int(query.data.replace("lsb_depth_", ""))
    chat_id = query.message.chat_id
    session_mgr.update(chat_id, lsb_depth=depth, step="awaiting_image_secret")

    await query.edit_message_text(
        f"✅ Depth set to *{depth}-bit*\n\n"
        f"Now send your *SECRET MESSAGE* to hide:",
        parse_mode="Markdown",
    )


async def imgencode_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle photo upload in image encode flow."""
    photo = update.message.photo[-1]
    file = await photo.get_file()
    return await _process_cover_image(update, session_mgr, file, "cover.jpg")


async def imgencode_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle document upload in image encode flow."""
    doc = update.message.document
    if not doc:
        return False
    if not doc.mime_type or not doc.mime_type.startswith('image/'):
        await update.message.reply_text("❌ Please send an image file (PNG, JPG, etc.)")
        return True
    file = await doc.get_file()
    return await _process_cover_image(update, session_mgr, file, doc.file_name or "cover.png")


async def imgencode_secret_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle secret text in image encode flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_image_secret":
        return False

    secret = update.message.text
    cover_path = session.get("cover_image")
    depth = session.get("lsb_depth", 1)

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
    cap = capacity_lsb(cover_path, depth=depth)
    secret_bits = len(secret.encode('utf-8')) * 8
    if secret_bits > cap['usable_bits']:
        await update.message.reply_text(
            f"⚠️ Secret too long for this image at {depth}-bit depth!\n\n"
            f"Need: {secret_bits:,} bits\n"
            f"Capacity: {cap['usable_bits']:,} bits\n\n"
            f"Try a larger image, shorter secret, or higher depth."
        )
        return True

    # Encode
    stego_path = cover_path.replace("cover.png", "stego.png")
    try:
        encode_lsb(cover_path, secret, stego_path, depth=depth, compress=True)
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
            f"Depth: {depth}-bit per channel\n"
            f"Method: LSB (Least Significant Bit)\n\n"
            "📥 *To decode later:*\n"
            "1. Download this image to your phone\n"
            "2. Send /imgdecode to the bot\n"
            "3. Tap 📎 (attachment) → select this file\n"
            "4. Send it\n\n"
            "⚠️ Do NOT use the camera/photo picker — "
            "Telegram compresses photos and destroys hidden data!"
        ),
        parse_mode="Markdown",
    )

    # Cleanup
    import shutil
    shutil.rmtree(os.path.dirname(cover_path), ignore_errors=True)
    session_mgr.reset(chat_id)
    return True
