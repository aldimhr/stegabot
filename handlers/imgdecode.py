"""Handle /imgdecode — extract hidden text from images with optional decryption."""
import logging
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.image_lsb import decode_lsb
from stegano.image_lsb_secure import decode_lsb_secure

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

    # Store the path for later use (passphrase decode needs it)
    session_mgr.update(chat_id, stego_image_path=png_path)

    # Try standard (non-secure) decode first
    try:
        decoded = decode_lsb(png_path)
    except Exception as e:
        logger.error(f"Standard decode error: {e}")
        decoded = ""

    logger.info(f"Standard decode result: '{decoded[:50] if decoded else '(empty)'}'")

    if decoded:
        # Standard LSB message found (not secure mode)
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
        # No standard LSB data → likely secure mode (or no data at all)
        # Ask user if they have a passphrase (secure mode requires one)
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("🔑 Yes, I have a passphrase", callback_data="img_dec_secure"),
                InlineKeyboardButton("🔓 No passphrase", callback_data="img_dec_nopass"),
            ],
        ]

        if not is_document:
            msg = (
                "❌ *No standard hidden message found.*\n\n"
                "This could be because:\n"
                "• Telegram compressed your photo (send as 📎 file)\n"
                "• The image uses *secure mode* (needs a passphrase)\n"
                "• The image has no hidden data\n\n"
                "Does this image have a passphrase?"
            )
        else:
            msg = (
                "🔍 *No standard LSB data found.*\n\n"
                "This image might use *secure mode* (encrypted + scrambled pixels). "
                "Or it might have no hidden data at all.\n\n"
                "Does this image have a passphrase?"
            )

        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # Don't reset session yet — need to handle decrypt choice or secure decode
    if decoded:
        # Standard message found — safe to clean up temp files
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
    else:
        # No standard message — keep temp files for potential secure decode
        # The secure decode handler will clean up after itself
        session_mgr.update(chat_id, step="awaiting_decrypt_choice")
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
    elif choice == "decrypt":
        # Old flow: standard LSB was found, user wants to decrypt with passphrase
        session_mgr.update(chat_id, step="awaiting_image_decrypt_passphrase")
        await query.edit_message_text(
            "🔑 Send the *passphrase* to decrypt the message:",
            parse_mode="Markdown",
        )
    elif choice == "secure":
        # No standard LSB data found → try secure decode
        session_mgr.update(chat_id, step="awaiting_secure_passphrase")
        await query.edit_message_text(
            "🔑 *Secure mode decode*\n\n"
            "Send the *passphrase* to decrypt the hidden message.\n\n"
            "The bot will try all depth combinations automatically.",
            parse_mode="Markdown",
        )
    elif choice == "nopass":
        await query.edit_message_text(
            "❌ *No hidden message found.*\n\n"
            "The image doesn't contain standard steganographic data.\n\n"
            "If you think there's a hidden message, the sender "
            "needs to give you the passphrase.",
            parse_mode="Markdown",
        )
        session_mgr.reset(chat_id)


async def imgdecode_passphrase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle passphrase input for decryption (both old and secure mode)."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)
    step = session.get("step")

    if step not in ("awaiting_image_decrypt_passphrase", "awaiting_secure_passphrase"):
        return False

    passphrase = update.message.text

    if step == "awaiting_secure_passphrase":
        # Secure mode: decode_lsb_secure handles everything
        stego_path = session.get("stego_image_path")
        if not stego_path or not os.path.exists(stego_path):
            await update.message.reply_text(
                "❌ Stego image not found. Please /imgdecode again.",
                parse_mode="Markdown",
            )
            session_mgr.reset(chat_id)
            return True

        try:
            plaintext = decode_lsb_secure(stego_path, passphrase)
            await update.message.reply_text(
                f"🔓 *Secure decode successful!*\n\n"
                f"*Hidden message:*\n\n`{plaintext}`",
                parse_mode="Markdown",
            )
        except ValueError as e:
            logger.warning(f"Secure decode failed: {e}")
            await update.message.reply_text(
                "❌ *Decryption failed!*\n\n"
                "Wrong passphrase or no hidden message in this image.\n\n"
                "Tried all depth combinations (1/2/3 bits) with both "
                "RGB and RGBA channels.",
                parse_mode="Markdown",
            )

        # Cleanup stego file
        try:
            import shutil
            shutil.rmtree(os.path.dirname(stego_path), ignore_errors=True)
        except Exception:
            pass

    else:
        # Old flow: standard LSB was found, user provides passphrase to decrypt
        decoded = session.get("decoded_payload", "")
        try:
            from stegano.crypto import decrypt_secret
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
