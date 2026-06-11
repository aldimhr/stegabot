"""Handle /demo — live steganography demonstration."""
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from stegano.zwc import encode_zwc, decode_zwc
from stegano.image_lsb import encode_lsb, decode_lsb
from PIL import Image


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


async def imgdemo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run a live demo of image LSB steganography."""
    tmp_dir = tempfile.mkdtemp()
    cover_path = os.path.join(tmp_dir, "demo_cover.png")
    stego_path = os.path.join(tmp_dir, "demo_stego.png")

    # Create a gradient test image
    img = Image.new('RGB', (200, 200))
    for x in range(200):
        for y in range(200):
            img.putpixel((x, y), (x % 256, y % 256, (x + y) % 256))
    img.save(cover_path, format='PNG')

    # Hide secret
    secret = "DEMO"
    encode_lsb(cover_path, secret, stego_path)
    decoded = decode_lsb(stego_path)

    # Send cover image
    await update.message.reply_text(
        "🖼️ *Live Demo — Image LSB Steganography*\n\n"
        f"🔒 Secret: `{secret}`\n\n"
        "Sending cover image, then stego image...\n"
        "They look identical but the stego image hides the secret!",
        parse_mode="Markdown",
    )

    await update.message.reply_document(
        document=open(cover_path, 'rb'),
        filename="demo_cover.png",
        caption="📝 Cover image (original)",
    )

    await update.message.reply_document(
        document=open(stego_path, 'rb'),
        filename="demo_stego.png",
        caption=(
            f"📦 Stego image (contains hidden \"{secret}\")\n\n"
            f"🔓 Decoded: `{decoded}` ✅\n\n"
            "⚠️ Download the image — screenshots destroy hidden data!\n"
            "Try /imgencode to hide your own messages in images."
        ),
        parse_mode="Markdown",
    )

    # Cleanup
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
