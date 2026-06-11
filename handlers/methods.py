"""Handle /methods command — explain steganography methods."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

METHOD_INFO = {
    "zwc": {
        "name": "🔹 Zero-Width Characters",
        "desc": (
            "Hides data using invisible Unicode characters (U+200C, U+200D) "
            "inserted between letters of your cover text.\n\n"
            "*How it works:* Each bit of your secret becomes an invisible character.\n"
            "*Capacity:* ~1 bit per character of cover text\n"
            "*Robustness:* Survives copy-paste on Telegram, WhatsApp, web\n"
            "*Detection:* Can be found by scanning for U+200x characters\n\n"
            "✅ *Recommended method* — best balance of capacity and stealth."
        ),
    },
    "snow": {
        "name": "🔹 Whitespace / SNOW",
        "desc": (
            "Hides data in trailing spaces and tabs at the end of each line.\n\n"
            "*How it works:* Space = bit 0, Tab = bit 1\n"
            "*Capacity:* 1 bit per line\n"
            "*Robustness:* Fragile — many editors strip trailing whitespace\n"
            "*Telegram note:* ⚠️ Only works inside code blocks (```)\n\n"
            "Based on the SNOW algorithm (Matthew Kwan, 1999)."
        ),
    },
    "acrostic": {
        "name": "🔹 Acrostic / First-Letter",
        "desc": (
            "The first letter of each word spells out your secret message.\n\n"
            "*How it works:* Bot generates a sentence whose initials = your secret\n"
            "*Capacity:* 1 character per word\n"
            "*Robustness:* Survives any copy/reformat — purely structural\n"
            "*Limitation:* Cover text is generated, not user-provided\n\n"
            "Oldest steganography technique — used since ancient Greece."
        ),
    },
    "homoglyph": {
        "name": "🔹 Unicode Homoglyph",
        "desc": (
            "Replaces Latin letters with visually identical Cyrillic lookalikes.\n\n"
            "*How it works:* Normal 'a' = bit 0, Cyrillic 'а' = bit 1\n"
            "*Capacity:* 1 bit per substitutable letter (a, e, o, p, c, x)\n"
            "*Robustness:* Survives copy-paste; breaks if manually retyped\n"
            "*Detection:* Detectable by Unicode scanners\n\n"
            "Humans can't tell them apart. Machines can."
        ),
    },
    "image_lsb": {
        "name": "🖼️ Image LSB (Least Significant Bit)",
        "desc": (
            "Hides text in the least significant bits of pixel colors.\n\n"
            "*How it works:* Each pixel's R, G, B values have their "
            "last bit replaced with secret data bits.\n"
            "*Capacity:* 3 bits per pixel (huge!)\n"
            "*Robustness:* Survives exact copy-paste; destroyed by compression\n"
            "*Telegram:* ⚠️ Must send as document (not photo) to preserve data\n\n"
            "A 512×512 image can hide ~96 KB of text!\n\n"
            "Use /imgencode to hide, /imgdecode to extract."
        ),
    },
    "variation_selector": {
        "name": "🔹 Unicode Variation Selector",
        "desc": (
            "Hides data using invisible Unicode Variation Selectors "
            "(U+FE00–U+FE0F, U+E0100–U+E01EF).\n\n"
            "*How it works:* Each byte of the secret maps to one invisible "
            "VS character inserted after word boundaries.\n"
            "*Capacity:* 1 byte per word boundary — 8× higher than ZWC!\n"
            "*Robustness:* Survives copy-paste on Telegram, Discord, web\n"
            "*Detection:* Requires programmatic Unicode analysis\n\n"
            "The text looks completely normal but carries hidden data.\n\n"
            "✅ *Best balance of capacity and stealth.*"
        ),
    },
    "emoji_stego": {
        "name": "🔹 Emoji Steganography",
        "desc": (
            "Hides data in emoji sequences using a 64-emoji pool.\n\n"
            "*How it works:* Each emoji from a fixed pool encodes 6 bits. "
            "Skin tone modifiers add 2 extra bits per emoji.\n"
            "*Capacity:* ~8 bits per emoji (1 byte per emoji)\n"
            "*Robustness:* Platform-dependent rendering\n"
            "*Detection:* Looks like casual emoji usage\n\n"
            "Output is pure emoji — no visible text at all!\n\n"
            "Fun and visually innocuous."
        ),
    },
    "audio_lsb": {
        "name": "🎵 Audio LSB",
        "desc": (
            "Hides text in the least significant bits of audio samples.\n\n"
            "*How it works:* Each 16-bit audio sample gets its LSB "
            "replaced with one bit of the secret.\n"
            "*Capacity:* ~1000 bytes per second of audio\n"
            "*Robustness:* Fragile — lost on re-encoding\n"
            "*Telegram:* ⚠️ Send as document to preserve quality\n\n"
            "Works with WAV files. Great for hiding data in music or voice.\n\n"
            "Use /audioencode to hide, /audiodecode to extract."
        ),
    },
}


async def methods_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show method selection inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔹 Zero-Width", callback_data="method_zwc"),
            InlineKeyboardButton("🔹 SNOW", callback_data="method_snow"),
        ],
        [
            InlineKeyboardButton("🔹 Acrostic", callback_data="method_acrostic"),
            InlineKeyboardButton("🔹 Homoglyph", callback_data="method_homoglyph"),
        ],
        [
            InlineKeyboardButton("🔹 Variation Selector", callback_data="method_variation_selector"),
            InlineKeyboardButton("🔹 Emoji", callback_data="method_emoji_stego"),
        ],
        [
            InlineKeyboardButton("🖼️ Image LSB", callback_data="method_image_lsb"),
            InlineKeyboardButton("🎵 Audio LSB", callback_data="method_audio_lsb"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📚 *Steganography Methods*\n\nTap any method to learn how it works:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle method info button press."""
    query = update.callback_query
    await query.answer()

    method_key = query.data.replace("method_", "")
    info = METHOD_INFO.get(method_key)
    if info:
        await query.edit_message_text(
            f"{info['name']}\n\n{info['desc']}",
            parse_mode="Markdown",
        )
