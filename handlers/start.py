"""Handle /start command."""
from telegram import Update
from telegram.ext import ContextTypes

START_TEXT = """🔐 *StegaBot* — Hide secrets in plain sight

I use steganography to hide messages inside text and images. No AI, just pure math + cryptography.

*Three ways to hide:*

📝 *Text Steganography*
Hide secrets inside normal-looking text using 6 methods:
• ZWC — zero-width characters between letters
• SNOW — invisible whitespace/tabs at line ends
• Acrostic — first letters of each word spell your secret
• Homoglyph — swap similar-looking characters
• Variation Selector — invisible Unicode VS chars (8× capacity!)
• Emoji — hide data in emoji sequences

🖼️ *Image Steganography*
Hide text inside PNG images using LSB encoding:
• Standard mode — quick hide, no passphrase needed
• 🔒 *Secure mode* — AES-128 encryption + scrambled pixels + PBKDF2 key derivation
  No magic header, no detectable patterns, passphrase-protected
🎵 *Audio Steganography*
Hide text inside WAV audio files using LSB encoding:
• ~1KB capacity per second of audio
• Send as document to preserve hidden data

*Commands:*
/encode — Hide a secret in text
/decode — Extract a hidden text message
/detect — Scan text for hidden data
/imgencode — Hide text in an image
/imgdecode — Extract hidden text from image
/imgdetect — Scan image for hidden data
/audioencode — Hide text in audio (WAV)
/audiodecode — Extract hidden text from audio
/audiodetect — Scan audio for hidden data
/demo — Text steganography demo
/imgdemo — Image steganography demo
/methods — Learn about steganography methods
/encrypt on|off — Toggle AES encryption for text
/learn — 📚 Learning center (theory, deep dives)

*Quick example:*
The text "Hello world" can hide "hi" using zero-width characters — looks identical but carries hidden data!

Try /demo to see it in action 👇"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message."""
    await update.message.reply_text(START_TEXT, parse_mode="Markdown")
