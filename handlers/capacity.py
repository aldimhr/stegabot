"""Handle /capacity — show capacity guide for all methods."""
from telegram import Update
from telegram.ext import ContextTypes


async def capacity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show capacity info for all steganography methods."""
    text = (
        "📊 *Steganography Capacity Guide*\n\n"
        "*Text Methods:*\n"
        "1️⃣ Zero-Width — 1 bit per character\n"
        "   100-char text → 12 bytes secret\n"
        "2️⃣ SNOW — 1 bit per line\n"
        "   100 lines → 12 bytes secret\n"
        "3️⃣ Acrostic — 1 character per word\n"
        "   50 words → 50 chars secret\n"
        "4️⃣ Homoglyph — 1 bit per substitutable letter\n"
        "   100 chars → ~12 bytes (depends on a,e,o,p,c,x count)\n"
        "5️⃣ Variation Selector — 1 byte per word boundary\n"
        "   50 words → 50 bytes secret\n"
        "6️⃣ Emoji — ~1 byte per emoji\n"
        "   100 emojis → ~100 bytes secret\n\n"
        "*Image Methods:*\n"
        "🖼️ Image LSB — 3 bits × depth per pixel\n"
        "   200×200 @ depth 1 → 14,992 chars\n"
        "   512×512 @ depth 1 → 96,000 chars\n"
        "   1024×768 @ depth 1 → 288,000 chars\n\n"
        "*Audio Methods:*\n"
        "🎵 Audio LSB — ~1,000 bytes per second\n"
        "   10s audio → 10,000 bytes\n"
        "   60s audio → 60,000 bytes\n\n"
        "💡 *Tips:*\n"
        "• Use /encode for text methods\n"
        "• Use /imgencode for image LSB\n"
        "• Use /audioencode for audio LSB\n"
        "• Longer cover = more capacity\n"
        "• Use encryption for sensitive data"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
