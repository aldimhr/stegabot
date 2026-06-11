"""Handle /demo — live steganography demonstration."""
from telegram import Update
from telegram.ext import ContextTypes

from stegano.zwc import encode_zwc, decode_zwc


async def demo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run a complete live demo of ZWC steganography."""
    cover = "The weather in Jakarta is nice today and everyone is happy."
    secret = "SECRET"

    # Encode
    stego = encode_zwc(cover, secret)

    # Decode
    decoded = decode_zwc(stego)

    # Show ZWC chars as visible symbols for education
    zwc_visual = stego
    zwc_visual = zwc_visual.replace('\u200B', '·')  # ZWSP
    zwc_visual = zwc_visual.replace('\u200C', '‹')  # ZWNJ
    zwc_visual = zwc_visual.replace('\u200D', '›')  # ZWJ

    await update.message.reply_text(
        "🎯 *Live Demo — Zero-Width Characters*\n\n"
        f"📝 *Cover text:*\n`{cover}`\n\n"
        f"🔒 *Secret:* `{secret}`\n\n"
        f"📦 *Stego text (looks identical):*\n`{stego}`\n\n"
        f"🔬 *ZWC characters made visible:*\n`{zwc_visual}`\n"
        f"(› = bit 1, ‹ = bit 0, · = separator)\n\n"
        f"🔓 *Decoded:* `{decoded}` ✅\n\n"
        f"The stego text looks exactly like the cover text, "
        f"but it secretly contains the word \"{secret}\"!\n\n"
        f"Try /encode to hide your own messages.",
        parse_mode="Markdown",
    )
