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
