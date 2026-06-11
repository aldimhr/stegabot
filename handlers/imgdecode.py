"""Handle /imgdecode — extract hidden text from images with optional decryption."""
import logging
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.image_lsb import decode_lsb
from stegano.crypto import decrypt_secret

logger = logging.getLogger(__name__)


async def imgdecode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start image decode flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, step="awaiting_stego_image")
    await update.message.reply_text(
        "🔍 *Image Steganography — Decode*\n\n"
        "Send the stego image to extract the hidden message.\n\n"
        "⚠️ Tap 📎 → select the image file. "
        "Do NOT use the camera/photo picker!",
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
        # Store decoded text and ask if they need to decrypt
        session_mgr.update(chat_id, decoded_payload=decoded, step="awaiting_decrypt_choice")

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("🔓 Not encrypted", callback_data="img_dec_plain"),
                InlineKeyboardButton("🔑 Enter passphrase", callback_data="img_dec_decrypt"),
            ],
        ]

        await update.message.reply_text(
            "🔍 *Data extracted from image!*\n\n"
            "Was this message encrypted with a passphrase?",
            reply_markup=InlineKeyboardMarkup(keyboard),
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
    # Don't reset session yet — need to handle decrypt choice
    if not decoded:
        session_mgr.reset(chat_id)
    return True


async def imgdecode_decrypt_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle decrypt choice after extraction."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    choice = query.data.replace("img_dec_", "")
    session = session_mgr.get(chat_id)

    if choice == "plain":
        decoded = session.get("decoded_payload", "")
        await query.edit_message_text(
            f"🔓 *Hidden message:*\n\n`{decoded}`",
            parse_mode="Markdown",
        )
        session_mgr.reset(chat_id)
    else:
        session_mgr.update(chat_id, step="awaiting_image_decrypt_passphrase")
        await query.edit_message_text(
            "🔑 Send the *passphrase* to decrypt the message:",
            parse_mode="Markdown",
        )


async def imgdecode_passphrase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle passphrase input for decryption."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_image_decrypt_passphrase":
        return False

    passphrase = update.message.text
    decoded = session.get("decoded_payload", "")

    try:
        plaintext = decrypt_secret(decoded, passphrase)
        await update.message.reply_text(
            f"🔓 *Decrypted message:*\n\n`{plaintext}`",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning(f"Decrypt failed: {e}")
        await update.message.reply_text(
            "❌ *Decryption failed!*\n\n"
            "Wrong passphrase or the message wasn't encrypted.\n"
            "Try again with /imgdecode.",
            parse_mode="Markdown",
        )

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
