"""Handle /start command."""
from telegram import Update
from telegram.ext import ContextTypes

START_TEXT = """🔐 *StegaBot* — Hide secrets in plain text!

I use classical steganography to hide messages inside innocent-looking text. No AI, just pure math.

*How it works:*
Send me a cover text + your secret, and I'll embed the secret invisibly. Anyone with this bot can decode it.

*Available commands:*
/encode — Hide a secret message in text
/decode — Extract a hidden message
/detect — Scan text for hidden data
/demo — See a live example
/methods — Learn about steganography methods
/encrypt on|off — Toggle AES encryption

*Example:*
The text "Hello world" can hide the secret "hi" using zero-width characters — it still looks exactly like "Hello world" but carries hidden data!

Try /demo to see it in action 👇"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message."""
    await update.message.reply_text(START_TEXT, parse_mode="Markdown")
