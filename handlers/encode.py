"""Handle /encode multi-turn flow."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.zwc import encode_zwc
from stegano.snow import encode_snow
from stegano.acrostic import encode_acrostic
from stegano.homoglyph import encode_homoglyph
from stegano.variation_selector import encode_vs
from stegano.emoji import encode_emoji
from stegano.utils import text_to_bits, capacity_check
from stegano.crypto import encrypt_secret
from config import MAX_SECRET_BYTES, MAX_COVER_CHARS


async def encode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start encode flow — ask user to choose method."""
    chat_id = update.effective_chat.id
    session_mgr.reset(chat_id)

    keyboard = [
        [
            InlineKeyboardButton("1️⃣ Zero-Width", callback_data="enc_method_zwc"),
            InlineKeyboardButton("2️⃣ SNOW", callback_data="enc_method_snow"),
        ],
        [
            InlineKeyboardButton("3️⃣ Acrostic", callback_data="enc_method_acrostic"),
            InlineKeyboardButton("4️⃣ Homoglyph", callback_data="enc_method_homoglyph"),
        ],
        [
            InlineKeyboardButton("5️⃣ Variation Selector", callback_data="enc_method_variation_selector"),
            InlineKeyboardButton("6️⃣ Emoji", callback_data="enc_method_emoji"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔒 *Encode a secret message*\n\nChoose a steganography method:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def encode_method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle method selection in encode flow."""
    query = update.callback_query
    await query.answer()

    method = query.data.replace("enc_method_", "")
    chat_id = query.message.chat_id
    session_mgr.update(chat_id, method=method, step="awaiting_cover")

    method_names = {
        "zwc": "Zero-Width Characters",
        "snow": "Whitespace/SNOW",
        "acrostic": "Acrostic",
        "homoglyph": "Unicode Homoglyph",
        "variation_selector": "Unicode Variation Selector",
        "emoji": "Emoji Steganography",
    }

    if method in ("acrostic", "emoji"):
        await query.edit_message_text(
            f"✅ Method: *{method_names[method]}*\n\n"
            "Now send your *SECRET MESSAGE* to hide:\n\n"
            "(No cover text needed — I'll generate it automatically)",
            parse_mode="Markdown",
        )
        session_mgr.update(chat_id, step="awaiting_secret")
    else:
        await query.edit_message_text(
            f"✅ Method: *{method_names[method]}*\n\n"
            "Now send your *COVER TEXT* (the innocent-looking message):",
            parse_mode="Markdown",
        )


async def encode_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle text messages during encode flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session["step"] == "awaiting_cover":
        cover = update.message.text
        if len(cover) > MAX_COVER_CHARS:
            await update.message.reply_text(
                f"⚠️ Cover text too long ({len(cover)} chars). Max: {MAX_COVER_CHARS}"
            )
            return

        session_mgr.update(chat_id, cover=cover, step="awaiting_secret")
        await update.message.reply_text(
            "✅ Cover text saved!\n\nNow send your *SECRET MESSAGE* to hide:",
            parse_mode="Markdown",
        )

    elif session["step"] == "awaiting_secret":
        secret = update.message.text
        if len(secret.encode('utf-8')) > MAX_SECRET_BYTES:
            await update.message.reply_text(
                f"⚠️ Secret too long ({len(secret.encode('utf-8'))} bytes). Max: {MAX_SECRET_BYTES} bytes."
            )
            return

        method = session["method"]
        cover = session.get("cover", "")

        # Optional encryption
        if session.get("encrypt") and session.get("passphrase"):
            secret = encrypt_secret(secret, session["passphrase"])

        # Acrostic and Emoji: generate output from secret directly
        if method == "acrostic":
            stego = encode_acrostic(secret)
            if stego is None:
                await update.message.reply_text(
                    "❌ Secret contains characters I can't encode. Use letters A-Z only."
                )
                session_mgr.reset(chat_id)
                return
            cap_info = ""
        elif method == "emoji":
            try:
                stego = encode_emoji(secret)
            except ValueError as e:
                await update.message.reply_text(f"❌ {e}")
                session_mgr.reset(chat_id)
                return
            cap_info = ""
        else:
            # Check capacity
            cap = capacity_check(cover, secret, method)
            if not cap["enough"]:
                await update.message.reply_text(
                    f"⚠️ Cover text too short!\n\n"
                    f"Need: {cap['needed_bits']} bits ({cap['needed_bits'] // 8} chars)\n"
                    f"Capacity: {cap['capacity_bits']} bits\n\n"
                    f"Please send a longer cover text:",
                    parse_mode="Markdown",
                )
                session_mgr.update(chat_id, step="awaiting_cover")
                return

            # Encode
            encoders = {
                "zwc": encode_zwc,
                "snow": encode_snow,
                "homoglyph": encode_homoglyph,
                "variation_selector": encode_vs,
            }
            stego = encoders[method](cover, secret)
            cap_info = (
                f"\n📊 Capacity: {cap['needed_bits']}/{cap['capacity_bits']} bits "
                f"({cap['utilization']:.0%} used)"
            )

        session_mgr.reset(chat_id)

        method_names = {
            "zwc": "Zero-Width Chars",
            "snow": "Whitespace/SNOW",
            "acrostic": "Acrostic",
            "homoglyph": "Homoglyph",
            "variation_selector": "Variation Selector",
            "emoji": "Emoji Steganography",
        }

        if method == "snow":
            # Wrap in code block to preserve trailing whitespace
            display = f"```\n{stego}\n```"
        elif method == "emoji":
            display = stego
        else:
            display = stego

        await update.message.reply_text(
            f"✅ *Done!* Send this stego text — it looks normal but carries your secret:\n\n"
            f"{display}\n\n"
            f"Method: {method_names[method]}"
            f"{cap_info}\n\n"
            f"💡 Anyone with this bot can use /decode to read the hidden message.",
            parse_mode="Markdown",
        )
