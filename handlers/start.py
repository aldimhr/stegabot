"""Handle /start command."""
from telegram import Update
from telegram.ext import ContextTypes

START_TEXT = """🔐 *StegaBot* — Hide secrets in plain sight

I use steganography to hide messages inside text and images. No AI, just pure math + cryptography.

*Two ways to hide:*

📝 *Text Steganography*
Hide secrets inside normal-looking text using 4 methods:
• ZWC — zero-width characters between letters
• SNOW — invisible whitespace/tabs at line ends
• Acrostic — first letters of each word spell your secret
• Homoglyph — swap similar-looking characters

🖼️ *Image Steganography*
Hide text inside PNG images using LSB encoding:
• Standard mode — quick hide, no passphrase needed
• 🔒 *Secure mode* — AES-128 encryption + scrambled pixels + PBKDF2 key derivation
  No magic header, no detectable patterns, passphrase-protected

*Commands:*
/encode — Hide a secret in text
/decode — Extract a hidden text message
/detect — Scan text for hidden data
/imgencode — Hide text in an image
/imgdecode — Extract hidden text from image
/imgdetect — Scan image for hidden data
/demo — Text steganography demo
/imgdemo — Image steganography demo
/methods — Learn about steganography methods
/encrypt on|off — Toggle AES encryption for text

*Quick example:*
The text "Hello world" can hide "hi" using zero-width characters — looks identical but carries hidden data!

Try /demo to see it in action 👇"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message."""
    await update.message.reply_text(START_TEXT, parse_mode="Markdown")
