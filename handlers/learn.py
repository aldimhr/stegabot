"""Handle /learn command — interactive steganography education."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ─────────────────────────────────────────────
#  CONTENT LIBRARY
# ─────────────────────────────────────────────

MAIN_MENU = {
    "what": (
        "📖 *What is Steganography?*\n\n"
        "Steganography is the art of hiding a secret message inside something "
        "that looks completely ordinary. The word comes from Greek: "
        "*steganos* (covered) + *graphein* (to write).\n\n"
        "Unlike *cryptography* (which scrambles data so it looks random), "
        "steganography makes the data *invisible* — nobody knows there's "
        "a secret at all.\n\n"
        "💡 *Think of it this way:*\n"
        "• Cryptography = putting a letter in a locked box\n"
        "• Steganography = hiding the letter inside a book nobody would check\n\n"
        "The best approach? *Use both!* Encrypt first, then hide. "
        "That's exactly what our 🔒 Secure Image mode does."
    ),
    "history": (
        "📜 *History of Steganography*\n\n"
        "*Ancient Greece (440 BC):*\n"
        "Histiaeus tattooed a message on a slave's shaved head, "
        "waited for hair to regrow, then sent him as a messenger.\n\n"
        "*World War II:*\n"
        "Microdots — shrinking photographs to the size of a period. "
        "Invisible letters written between lines of innocent text.\n\n"
        "*Modern Digital:*\n"
        "• 1990s: LSB encoding in digital images\n"
        "• 1999: SNOW algorithm (whitespace steganography)\n"
        "• 2000s: Zero-width Unicode characters\n"
        "• 2010s: Steganography in social media, VoIP, blockchain\n\n"
        "StegaBot implements *multiple classical techniques* "
        "adapted for the Telegram era."
    ),
}

TOPICS = {
    # ── TEXT METHODS ──
    "text_overview": {
        "title": "📝 Text Steganography",
        "text": (
            "📝 *Text Steganography Overview*\n\n"
            "Text steganography hides data inside ordinary-looking text. "
            "StegaBot supports *6 methods*, each with different trade-offs.\n\n"
            "🔹 *Zero-Width Characters (ZWC)*\n"
            "Invisible Unicode characters between letters.\n"
            "Capacity: ~1 bit per cover character.\n\n"
            "🔹 *SNOW (Whitespace)*\n"
            "Spaces and tabs at line endings.\n"
            "Capacity: low, fragile but classic.\n\n"
            "🔹 *Acrostic*\n"
            "First letters of each word spell the secret.\n"
            "Capacity: 1 char per word, very robust.\n\n"
            "🔹 *Homoglyph*\n"
            "Swap Latin letters with identical Cyrillic twins.\n"
            "Capacity: 1 bit per swappable letter.\n\n"
            "🔹 *Variation Selector*\n"
            "Invisible Unicode VS chars after word boundaries.\n"
            "Capacity: 1 byte per word — 8× higher than ZWC!\n\n"
            "🔹 *Emoji Steganography*\n"
            "Data encoded in emoji sequences from a 64-emoji pool.\n"
            "Capacity: ~1 byte per emoji, pure emoji output.\n\n"
            "Tap any method below to learn the theory 👇"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔹 ZWC Deep Dive", callback_data="learn_zwc"),
                InlineKeyboardButton("🔹 SNOW Deep Dive", callback_data="learn_snow"),
            ],
            [
                InlineKeyboardButton("🔹 Acrostic Deep Dive", callback_data="learn_acrostic"),
                InlineKeyboardButton("🔹 Homoglyph Deep Dive", callback_data="learn_homoglyph"),
            ],
            [
                InlineKeyboardButton("🔹 Variation Selector", callback_data="learn_variation_selector"),
                InlineKeyboardButton("🔹 Emoji Steganography", callback_data="learn_emoji_stego"),
            ],
            [
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "zwc": {
        "title": "🔹 Zero-Width Characters — Theory",
        "text": (
            "🔹 *Zero-Width Characters (ZWC)*\n\n"
            "*The Idea:*\n"
            "Unicode has invisible characters that take up zero space on screen. "
            "Nobody can see them, but computers treat them as real characters.\n\n"
            "*Characters Used:*\n"
            "• `U+200B` — Zero-Width Space (bit 0)\n"
            "• `U+200C` — Zero-Width Non-Joiner (bit 1)\n"
            "• `U+200D` — Zero-Width Joiner (separator)\n"
            "• `U+FEFF` — Zero-Width No-Break Space (separator)\n\n"
            "*How Encoding Works:*\n"
            "1. Convert secret text → binary (UTF-8)\n"
            "2. Each `0` bit → U+200B\n"
            "3. Each `1` bit → U+200C\n"
            "4. Insert these between characters of your cover text\n\n"
            "*Example:*\n"
            "Cover: `Hello`\n"
            "Secret: `H` (binary: 01001000)\n"
            "Result: `H[0]e[1]l[0]l[0]o[1][0][0][0]`\n"
            "(The [brackets] represent invisible ZWC characters)\n\n"
            "*Capacity:*\n"
            "For a 100-character cover text, you can hide ~100 bits = 12 characters.\n\n"
            "*Why It Works on Telegram:*\n"
            "Telegram preserves all Unicode characters in messages, "
            "including invisible ones. The message looks completely normal."
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔬 Detection Methods", callback_data="learn_zwc_detect"),
                InlineKeyboardButton("⚡ Try It Now", callback_data="learn_zwc_try"),
            ],
            [
                InlineKeyboardButton("📝 Text Methods", callback_data="learn_text_overview"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "zwc_detect": {
        "title": "🔬 ZWC Detection",
        "text": (
            "🔬 *How ZWC Steganography Can Be Detected*\n\n"
            "While invisible to humans, ZWC can be found by machines:\n\n"
            "*1. Unicode Scanner*\n"
            "Simply search for U+200x characters. Any message with "
            "multiple zero-width characters is suspicious.\n\n"
            "*2. Character Frequency Analysis*\n"
            "Normal text has predictable character patterns. "
            "ZWC-encoded text has 'noise' between characters.\n\n"
            "*3. Byte-Level Inspection*\n"
            "Copy the text to a hex editor. ZWC characters show up "
            "as distinct byte sequences (E2 80 8B, E2 80 8C).\n\n"
            "*Countermeasures:*\n"
            "• Use fewer ZWC characters (shorter secrets)\n"
            "• Mix with other Unicode formatting characters\n"
            "• Combine with encryption (hide encrypted data)\n\n"
            "*Bottom line:* ZWC is stealthy against casual inspection "
            "but detectable with dedicated tools."
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔹 Back to ZWC", callback_data="learn_zwc"),
                InlineKeyboardButton("📝 Text Methods", callback_data="learn_text_overview"),
            ],
        ],
    },

    "zwc_try": {
        "title": "⚡ Try ZWC Encoding",
        "text": (
            "⚡ *Try Zero-Width Encoding Yourself*\n\n"
            "Ready to hide a message? Here's how:\n\n"
            "*Step 1:* Send /encode\n"
            "*Step 2:* Choose \"Zero-Width\" method\n"
            "*Step 3:* Type your cover text (the visible message)\n"
            "*Step 4:* Type your secret (the hidden message)\n"
            "*Step 5:* Send the result to anyone!\n\n"
            "*To decode:*\n"
            "Send /decode and paste the message with hidden data.\n\n"
            "*Pro tips:*\n"
            "• Longer cover text = longer secret capacity\n"
            "• Add /encrypt on for extra security\n"
            "• Works perfectly in Telegram, WhatsApp, most websites\n\n"
            "Try it now! 👉 /encode"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔹 Back to ZWC", callback_data="learn_zwc"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "snow": {
        "title": "🔹 SNOW — Whitespace Steganography",
        "text": (
            "🔹 *SNOW — Whitespace Steganography*\n\n"
            "*The Idea:*\n"
            "Trailing spaces and tabs at the end of lines are invisible. "
            "Most editors strip them, but in certain contexts (like "
            "code blocks or raw text), they survive.\n\n"
            "*SNOW Algorithm (Matthew Kwan, 1999):*\n"
            "• Space = bit `0`\n"
            "• Tab = bit `1`\n"
            "• Consecutive whitespace at line ends encodes the secret\n\n"
            "*How It Works:*\n"
            "1. Convert secret to binary\n"
            "2. At the end of each line, append spaces/tabs\n"
            "3. 7 spaces + tab + 3 spaces = `0000000 1 000`\n\n"
            "*Example:*\n"
            "```\n"
            "Hello world       \t  \n"
            "How are you?   \t \n"
            "```\n"
            "(The trailing whitespace after each line is the hidden data)\n\n"
            "*Capacity:* Very low — 1 bit per line.\n"
            "A 10-line text hides only 10 bits ≈ 1 character.\n\n"
            "*Limitations:*\n"
            "• ⚠️ On Telegram: only works inside ```code blocks```\n"
            "• Many editors strip trailing whitespace automatically\n"
            "• Destroyed by most text processing tools\n\n"
            "*Best for:* Short secrets in code/config file sharing."
        ),
        "buttons": [
            [
                InlineKeyboardButton("⚡ Try SNOW", callback_data="learn_snow_try"),
                InlineKeyboardButton("📝 Text Methods", callback_data="learn_text_overview"),
            ],
            [
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "snow_try": {
        "title": "⚡ Try SNOW Encoding",
        "text": (
            "⚡ *Try SNOW Encoding Yourself*\n\n"
            "*Step 1:* Send /encode\n"
            "*Step 2:* Choose \"SNOW / Whitespace\" method\n"
            "*Step 3:* Type your cover text\n"
            "*Step 4:* Type your secret\n\n"
            "⚠️ *Important:* The result will contain trailing whitespace. "
            "Send it inside a code block (```) for best results on Telegram.\n\n"
            "To decode: /decode and paste the text.\n\n"
            "Try it now! 👉 /encode"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔹 Back to SNOW", callback_data="learn_snow"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "acrostic": {
        "title": "🔹 Acrostic — First-Letter Encoding",
        "text": (
            "🔹 *Acrostic Steganography*\n\n"
            "*The Idea:*\n"
            "The first letter of each word in the cover text spells out "
            "your secret message. This is the *oldest* steganography "
            "technique — used since ancient Greece!\n\n"
            "*How It Works:*\n"
            "1. Take secret: `HI`\n"
            "2. Generate sentence where first letters = H, I\n"
            "3. Result: \"*H*appy *I*ndependence day!\"\n\n"
            "*The bot's approach:*\n"
            "StegaBot has a word bank and generates sentences where "
            "the first letter of each word matches your secret. "
            "It tries to make grammatically sensible text.\n\n"
            "*Capacity:* 1 character per word in the cover text.\n"
            "A 20-word sentence hides 20 characters.\n\n"
            "*Strengths:*\n"
            "• ✅ Survives ANY copy-paste, reformat, compression\n"
            "• ✅ Works everywhere — text, email, social media\n"
            "• ✅ Humans rarely notice unless they look for it\n\n"
            "*Weaknesses:*\n"
            "• Generated text may sound unnatural\n"
            "• Cover text is created by the bot, not user-provided\n"
            "• If someone reads first letters, they'll find the secret\n\n"
            "*Famous examples:*\n"
            "• Edgar Allan Poe used acrostics in poems\n"
            "• Medieval monks hid messages in hymn texts\n"
            "• Modern: used in song lyrics, book dedications"
        ),
        "buttons": [
            [
                InlineKeyboardButton("⚡ Try Acrostic", callback_data="learn_acrostic_try"),
                InlineKeyboardButton("📝 Text Methods", callback_data="learn_text_overview"),
            ],
            [
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "acrostic_try": {
        "title": "⚡ Try Acrostic Encoding",
        "text": (
            "⚡ *Try Acrostic Encoding Yourself*\n\n"
            "*Step 1:* Send /encode\n"
            "*Step 2:* Choose \"Acrostic\" method\n"
            "*Step 3:* The bot asks for your secret directly (no cover text needed)\n"
            "*Step 4:* Type your secret message\n"
            "*Step 5:* Bot generates a sentence!\n\n"
            "*Example:*\n"
            "Secret: `HELLO`\n"
            "Result: \"*H*appy *E*lephants *L*ove *L*arge *O*ranges\"\n\n"
            "The receiver reads the first letters of each word to find the secret.\n\n"
            "Try it now! 👉 /encode"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔹 Back to Acrostic", callback_data="learn_acrostic"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "homoglyph": {
        "title": "🔹 Homoglyph — Visual Substitution",
        "text": (
            "🔹 *Unicode Homoglyph Steganography*\n\n"
            "*The Idea:*\n"
            "Many Unicode characters look *identical* to Latin letters "
            "but are completely different characters. Humans can't tell "
            "them apart — machines can.\n\n"
            "*Homoglyph Pairs Used:*\n"
            "• `a` (Latin) ↔ `а` (Cyrillic) — U+0430\n"
            "• `e` (Latin) ↔ `е` (Cyrillic) — U+0435\n"
            "• `o` (Latin) ↔ `о` (Cyrillic) — U+043E\n"
            "• `p` (Latin) ↔ `р` (Cyrillic) — U+0440\n"
            "• `c` (Latin) ↔ `с` (Cyrillic) — U+0441\n"
            "• `x` (Latin) ↔ `х` (Cyrillic) — U+0445\n\n"
            "*How It Works:*\n"
            "1. Convert secret to binary\n"
            "2. For each eligible letter in the cover text:\n"
            "   • Bit `0` → keep Latin letter\n"
            "   • Bit `1` → replace with Cyrillic twin\n"
            "3. Result looks identical but encodes bits\n\n"
            "*Example:*\n"
            "Cover: `the cat`\n"
            "Secret: `hi` (binary: 01101000 01101001)\n"
            "Result: `thе саt` (е, с, а are Cyrillic!)\n\n"
            "*Capacity:* 1 bit per eligible letter.\n"
            "Only 6 letters (a, e, o, p, c, x) can carry data.\n\n"
            "*Detection:*\n"
            "• Unicode scanners can flag Cyrillic in Latin text\n"
            "• Some security tools specifically check for homoglyphs\n"
            "• Domain names use similar tricks (phishing!)"
        ),
        "buttons": [
            [
                InlineKeyboardButton("⚡ Try Homoglyph", callback_data="learn_homoglyph_try"),
                InlineKeyboardButton("📝 Text Methods", callback_data="learn_text_overview"),
            ],
            [
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "homoglyph_try": {
        "title": "⚡ Try Homoglyph Encoding",
        "text": (
            "⚡ *Try Homoglyph Encoding Yourself*\n\n"
            "*Step 1:* Send /encode\n"
            "*Step 2:* Choose \"Homoglyph\" method\n"
            "*Step 3:* Type cover text (must contain a, e, o, p, c, or x)\n"
            "*Step 4:* Type your secret\n\n"
            "⚠️ *Note:* The cover text needs eligible letters (a, e, o, p, c, x). "
            "If there aren't enough, the bot will tell you.\n\n"
            "To decode: /decode and paste the text.\n\n"
            "Try it now! 👉 /encode"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔹 Back to Homoglyph", callback_data="learn_homoglyph"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    # ── IMAGE METHODS ──
    "image_overview": {
        "title": "🖼️ Image & Audio Steganography",
        "text": (
            "🖼️ *Image & Audio Steganography Overview*\n\n"
            "Images and audio are made of *samples*. Each sample is a number "
            "we can modify at the bit level.\n\n"
            "*Images:* Pixels have R, G, B values (0-255). "
            "Changing the *last bit* is invisible to the eye.\n\n"
            "*Audio:* WAV samples are 16-bit integers. "
            "Changing the LSB is inaudible.\n\n"
            "StegaBot offers:\n"
            "• 🔓 *Image Standard LSB* — quick hide, no passphrase\n"
            "• 🔒 *Image Secure LSB* — AES-128 + scrambled pixels\n"
            "• 🎵 *Audio LSB* — hide data in WAV audio files\n\n"
            "Tap a topic below to learn more 👇"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔬 How LSB Works", callback_data="learn_lsb_how"),
                InlineKeyboardButton("📊 Depth & Capacity", callback_data="learn_lsb_depth"),
            ],
            [
                InlineKeyboardButton("🔒 Secure Mode", callback_data="learn_secure_mode"),
                InlineKeyboardButton("🎵 Audio LSB", callback_data="learn_audio_lsb"),
            ],
            [
                InlineKeyboardButton("⚠️ Common Mistakes", callback_data="learn_image_mistakes"),
            ],
            [
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "lsb_how": {
        "title": "🔬 How LSB Encoding Works",
        "text": (
            "🔬 *LSB Encoding — Step by Step*\n\n"
            "*The Pixel:*\n"
            "Each pixel = 3 bytes (R, G, B), each 0-255.\n"
            "A 100×100 image = 10,000 pixels = 30,000 bytes.\n\n"
            "*The Bit:*\n"
            "Each byte = 8 bits. The *last* bit (LSB) is the least important.\n"
            "Changing bit 0 of 142 (`10001110`) → 143 (`10001111`)\n"
            "Changing bit 0 of 143 (`10001111`) → 142 (`10001110`)\n\n"
            "*Encoding Process:*\n"
            "1. Take secret text → convert to binary\n"
            "2. For each pixel, for each channel (R, G, B):\n"
            "   • Clear the LSB: `value & 0xFE`\n"
            "   • Set it to the secret bit: `| secret_bit`\n"
            "3. Save as PNG (lossless!)\n\n"
            "*Decoding Process:*\n"
            "1. Read each pixel's R, G, B values\n"
            "2. Extract the LSB: `value & 1`\n"
            "3. Reassemble bits → bytes → text\n\n"
            "*Header Format (Standard Mode):*\n"
            "First 64 bits contain metadata:\n"
            "• Magic: `LS` (identifies stego data)\n"
            "• Version, flags (depth, compression)\n"
            "• Payload length (32 bits)\n\n"
            "The decoder reads the header first, then extracts exactly "
            "the right number of bits for the secret."
        ),
        "buttons": [
            [
                InlineKeyboardButton("📊 Depth & Capacity", callback_data="learn_lsb_depth"),
                InlineKeyboardButton("🔒 Secure Mode", callback_data="learn_secure_mode"),
            ],
            [
                InlineKeyboardButton("🖼️ Image Overview", callback_data="learn_image_overview"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "lsb_depth": {
        "title": "📊 LSB Depth & Capacity",
        "text": (
            "📊 *LSB Depth & Capacity*\n\n"
            "*Depth = how many bits per channel to use.*\n\n"
            "🔹 *Depth 1 (Safe)* — 1 bit per channel\n"
            "• Changes: ±1 per color value (invisible)\n"
            "• Capacity: `(width × height × 3) ÷ 8` bytes\n"
            "• 512×512 image → ~96 KB\n"
            "• Undetectable by visual inspection\n\n"
            "🔹 *Depth 2 (Medium)* — 2 bits per channel\n"
            "• Changes: ±3 per color value (still invisible)\n"
            "• Capacity: 2× depth 1 → ~192 KB\n"
            "• Very hard to detect\n\n"
            "🔹 *Depth 3 (Max)* — 3 bits per channel\n"
            "• Changes: ±7 per color value (barely visible)\n"
            "• Capacity: 3× depth 1 → ~288 KB\n"
            "• Detectable by statistical analysis\n\n"
            "*Capacity Table (pre-gzip):*\n"
            "• 200×200 @ depth 1 → ~15,000 chars\n"
            "• 200×200 @ depth 2 → ~30,000 chars\n"
            "• 200×200 @ depth 3 → ~45,000 chars\n"
            "• 512×512 @ depth 1 → ~98,000 chars\n\n"
            "*Gzip compression* is applied automatically for secrets "
            "over 50 bytes — text typically compresses 40-60%.\n\n"
            "*Rule of thumb:* Use depth 1 unless you need more space."
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔬 How LSB Works", callback_data="learn_lsb_how"),
                InlineKeyboardButton("🔒 Secure Mode", callback_data="learn_secure_mode"),
            ],
            [
                InlineKeyboardButton("🖼️ Image Overview", callback_data="learn_image_overview"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "secure_mode": {
        "title": "🔒 Secure Image Mode",
        "text": (
            "🔒 *Secure Image Mode — Deep Dive*\n\n"
            "Standard LSB has weaknesses:\n"
            "• Magic header `LS` = instant detection\n"
            "• Always starts at pixel 0\n"
            "• Sequential pixel modification (detectable pattern)\n\n"
            "*Secure mode fixes all three:*\n\n"
            "*1. PBKDF2 Key Derivation*\n"
            "Your passphrase + random salt → 100,000 rounds of SHA-256 → "
            "cryptographic keys. Resistant to brute-force.\n\n"
            "*2. No Magic Header*\n"
            "Everything (header + payload) is encrypted with Fernet "
            "(AES-128-CBC + HMAC). No plaintext markers at all.\n\n"
            "*3. Passphrase-Derived Start Position*\n"
            "PBKDF2 output determines which pixel to start from. "
            "Without the passphrase, you don't know where to look.\n\n"
            "*4. Scrambled Pixel Order*\n"
            "Key-derived PRNG shuffles which pixels get modified. "
            "Instead of sequential (0, 1, 2, 3...), data is spread "
            "across the image in a random-looking pattern.\n\n"
            "*Decode Strategy:*\n"
            "Tries all 6 combinations (depth 1/2/3 × RGB/RGBA) "
            "until Fernet decryption succeeds. First match wins.\n\n"
            "*Security Properties:*\n"
            "• Same image + different passphrases → completely different results\n"
            "• Wrong passphrase → HMAC fails → can't confirm data exists\n"
            "• No magic header → can't tell stego from normal image\n"
            "• Scrambled pixels → harder statistical detection"
        ),
        "buttons": [
            [
                InlineKeyboardButton("⚠️ Common Mistakes", callback_data="learn_image_mistakes"),
                InlineKeyboardButton("🔬 How LSB Works", callback_data="learn_lsb_how"),
            ],
            [
                InlineKeyboardButton("🖼️ Image Overview", callback_data="learn_image_overview"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "image_mistakes": {
        "title": "⚠️ Common Image Stegano Mistakes",
        "text": (
            "⚠️ *Common Mistakes & How to Avoid Them*\n\n"
            "*1. Sending as Photo (not Document)* 📸\n"
            "Telegram compresses photos → destroys LSB data!\n"
            "✅ *Always* send stego images as 📎 documents.\n\n"
            "*2. Using JPEG Format* 🖼️\n"
            "JPEG is lossy — it changes pixel values on save.\n"
            "✅ *Always* use PNG (lossless format).\n\n"
            "*3. Editing the Stego Image* ✂️\n"
            "Cropping, resizing, filters — all change pixels.\n"
            "✅ Never edit a stego image before decoding.\n\n"
            "*4. Screenshot Instead of Download* 📱\n"
            "Screenshots re-encode the image (usually JPEG).\n"
            "✅ Download the original file.\n\n"
            "*5. Not Sharing the Passphrase* 🔑\n"
            "If using secure mode, the recipient needs the passphrase.\n"
            "✅ Share it privately (separate channel, in person).\n\n"
            "*6. Using a Weak Passphrase* 📝\n"
            "\"password123\" can be brute-forced.\n"
            "✅ Use 12+ characters with mixed types.\n\n"
            "*The Golden Rule:*\n"
            "Ste → send as 📎 PNG → recipient downloads → decode\n"
            "Never compress, never screenshot, never edit."
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔒 Secure Mode", callback_data="learn_secure_mode"),
                InlineKeyboardButton("📊 Depth & Capacity", callback_data="learn_lsb_depth"),
            ],
            [
                InlineKeyboardButton("🖼️ Image Overview", callback_data="learn_image_overview"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    # ── SECURITY & DETECTION ──
    "security": {
        "title": "🔒 Security & Steganalysis",
        "text": (
            "🔒 *Security & Steganalysis*\n\n"
            "*Steganalysis* = the science of detecting hidden data.\n\n"
            "*Can someone detect steganography?*\n"
            "Yes — but it depends on the method and how it's used.\n\n"
            "*Detection Methods:*\n"
            "• *Visual inspection* — looking for artifacts\n"
            "• *Statistical analysis* — chi-square, RS analysis\n"
            "• *Unicode scanning* — finding zero-width characters\n"
            "• *Byte-level analysis* — hex editors, binary comparison\n\n"
            "*Our Security Layers:*\n"
            "• AES-128 encryption (before hiding)\n"
            "• PBKDF2 key derivation (100k iterations)\n"
            "• No magic headers (secure image mode)\n"
            "• Scrambled pixel order (statistical resistance)\n\n"
            "Tap a topic to learn more 👇"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔬 Steganalysis Explained", callback_data="learn_steganalysis"),
                InlineKeyboardButton("🛡️ Best Practices", callback_data="learn_best_practices"),
            ],
            [
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "steganalysis": {
        "title": "🔬 Steganalysis — How Detection Works",
        "text": (
            "🔬 *Steganalysis — How Detection Works*\n\n"
            "Steganalysis is the opposite of steganography — "
            "finding hidden data where it shouldn't be.\n\n"
            "*Statistical Methods for Images:*\n\n"
            "*1. Chi-Square Attack*\n"
            "LSB embedding changes the statistical distribution "
            "of pixel values. Chi-square test detects this shift.\n"
            "• Works best against depth ≥ 2\n"
            "• Depth 1 is much harder to detect\n\n"
            "*2. RS Analysis (Regular-Singular)*\n"
            "Analyzes pixel groups to estimate the percentage "
            "of modified pixels. Can detect even partial embedding.\n\n"
            "*3. Sample Pair Analysis*\n"
            "Looks at pairs of adjacent pixels for anomalies "
            "in their least significant bits.\n\n"
            "*What Our Secure Mode Does Against This:*\n"
            "• Scrambled pixels → changes are spread across image\n"
            "• No sequential pattern → harder for RS analysis\n"
            "• Depth 1 → below chi-square detection threshold\n"
            "• Encrypted payload → looks like random noise\n\n"
            "*For Text Methods:*\n"
            "• ZWC: detectable by Unicode scanning\n"
            "• SNOW: detectable by whitespace analysis\n"
            "• Acrostic: only if someone reads first letters\n"
            "• Homoglyph: detectable by Unicode comparison\n\n"
            "*Bottom line:* No steganography is 100% undetectable. "
            "The goal is to make detection *impractical*."
        ),
        "buttons": [
            [
                InlineKeyboardButton("🛡️ Best Practices", callback_data="learn_best_practices"),
                InlineKeyboardButton("🔒 Security Overview", callback_data="learn_security"),
            ],
            [
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "best_practices": {
        "title": "🛡️ Best Practices",
        "text": (
            "🛡️ *Steganography Best Practices*\n\n"
            "*1. Layer Your Security*\n"
            "Encrypt FIRST, then hide. If steganography is detected, "
            "the data is still encrypted. Our secure mode does this.\n\n"
            "*2. Use Appropriate Methods*\n"
            "• Quick message to a friend → ZWC (fast, easy)\n"
            "• Need to survive reformatting → Acrostic\n"
            "• Hiding large data → Image LSB\n"
            "• Maximum security → Image LSB Secure + strong passphrase\n\n"
            "*3. Don't Reuse Patterns*\n"
            "Using the same method repeatedly makes detection easier. "
            "Switch methods between messages.\n\n"
            "*4. Keep Secrets Short*\n"
            "Shorter secrets = less modification = harder to detect. "
            "Compress and encrypt before hiding.\n\n"
            "*5. Share Passphrases Securely*\n"
            "Never send the passphrase in the same channel as the "
            "stego content. Use a different app, meet in person, "
            "or use a pre-shared key.\n\n"
            "*6. Verify Before Sharing*\n"
            "Always decode your own stego message before sending. "
            "Make sure the roundtrip works!\n\n"
            "*7. Consider the Channel*\n"
            "• Telegram: compresses photos, preserves documents\n"
            "• Email: preserves attachments, may strip whitespace\n"
            "• WhatsApp: heavily compresses images\n"
            "• Social media: always compresses uploads"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔬 Steganalysis", callback_data="learn_steganalysis"),
                InlineKeyboardButton("🔒 Security Overview", callback_data="learn_security"),
            ],
            [
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    # ── NEW METHODS ──
    "variation_selector": {
        "title": "🔹 Unicode Variation Selector — Deep Dive",
        "text": (
            "🔹 *Unicode Variation Selector Steganography*\n\n"
            "*The Idea:*\n"
            "Unicode has invisible characters called Variation Selectors "
            "(VS1-VS256) that normally select emoji/text variants. "
            "They are completely invisible but preserved in text.\n\n"
            "*How It Works:*\n"
            "1. Convert secret → UTF-8 bytes\n"
            "2. Each byte (0-255) maps to one VS character:\n"
            "   • Byte 0-15 → U+FE00 to U+FE0F (VS1-16)\n"
            "   • Byte 16-255 → U+E0100 to U+E01EF (VS17-256)\n"
            "3. Insert VS characters after each space in cover text\n\n"
            "*Capacity:* 1 byte per word boundary\n"
            "A 50-word sentence hides 50 bytes!\n\n"
            "*Why It's Better Than ZWC:*\n"
            "• ZWC: ~1 bit per character (6 chars = 1 byte)\n"
            "• VS: 1 byte per word boundary (8× higher capacity!)\n"
            "• Both are invisible, but VS carries more data\n\n"
            "*Robustness:*\n"
            "Survives Telegram, Discord, most web forms. "
            "Destroyed by strict Unicode sanitizers.\n\n"
            "*Detection:*\n"
            "Requires scanning for U+FE00-U+FE0F and U+E0100-U+E01EF ranges. "
            "Invisible to casual inspection."
        ),
        "buttons": [
            [
                InlineKeyboardButton("⚡ Try It Now", callback_data="learn_vs_try"),
                InlineKeyboardButton("📝 Text Methods", callback_data="learn_text_overview"),
            ],
            [
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "vs_try": {
        "title": "⚡ Try Variation Selector Encoding",
        "text": (
            "⚡ *Try Variation Selector Encoding*\n\n"
            "Ready to hide a message with maximum text capacity?\n\n"
            "*Step 1:* Send /encode\n"
            "*Step 2:* Choose \"Variation Selector\" method\n"
            "*Step 3:* Type your cover text (needs enough words)\n"
            "*Step 4:* Type your secret message\n\n"
            "*Capacity:* 1 byte per word boundary\n"
            "A 100-word cover text hides 100 bytes!\n\n"
            "*Tips:*\n"
            "• Longer cover text = more capacity\n"
            "• The output looks exactly like your cover text\n"
            "• Add /encrypt on for extra security\n\n"
            "To decode: /decode and paste the text.\n\n"
            "Try it now! 👉 /encode"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔹 Back to VS Theory", callback_data="learn_variation_selector"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "emoji_stego": {
        "title": "🔹 Emoji Steganography — Deep Dive",
        "text": (
            "🔹 *Emoji Steganography*\n\n"
            "*The Idea:*\n"
            "Encode data in sequences of emoji from a fixed 64-emoji pool. "
            "Each emoji encodes 6 bits (64 values). "
            "Skin tone modifiers add 2 extra bits.\n\n"
            "*The Emoji Pool:*\n"
            "😀😂😍🤔😎🥳😱🤩🐶🐱🐸🦊🐻🐼🦁🐮"
            "🍎🍊🍋🍇🍓🍒🌽🥕⚽🏀🎾🏐🎱🎯🎮🎲"
            "🌹🌻🌸🍄⭐🌙☀️❄️🚗🚀✈️🚂🏠🗼🎡🎪"
            "❤️💔💯✅❌⚡🔥💧🎵🎸🥁🎺📱💻📷🔑\n\n"
            "*How It Works:*\n"
            "1. Convert secret → bytes → 6-bit chunks\n"
            "2. Each chunk selects an emoji from the pool\n"
            "3. Optionally add skin tone modifier (5 options)\n"
            "4. Terminator emoji marks end of data\n\n"
            "*Capacity:* ~1 byte per emoji\n"
            "20 emoji = 20 bytes hidden data\n\n"
            "*Output:* Pure emoji — no visible text at all!\n"
            "Looks like casual emoji usage.\n\n"
            "*Robustness:*\n"
            "Platform-dependent. Different platforms may render emoji differently."
        ),
        "buttons": [
            [
                InlineKeyboardButton("⚡ Try It Now", callback_data="learn_emoji_try"),
                InlineKeyboardButton("📝 Text Methods", callback_data="learn_text_overview"),
            ],
            [
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "emoji_try": {
        "title": "⚡ Try Emoji Encoding",
        "text": (
            "⚡ *Try Emoji Steganography*\n\n"
            "Hide a message in pure emoji!\n\n"
            "*Step 1:* Send /encode\n"
            "*Step 2:* Choose \"Emoji\" method\n"
            "*Step 3:* Type your secret message (no cover text needed)\n\n"
            "The bot generates an emoji sequence encoding your secret.\n\n"
            "*Example:*\n"
            "Secret: \"Hi\"\n"
            "Output: 😀🐶🐻🎉🔑 (example — actual emoji depend on data)\n\n"
            "*To decode:*\n"
            "Send /decode and paste the emoji sequence.\n\n"
            "Try it now! 👉 /encode"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🔹 Back to Emoji Theory", callback_data="learn_emoji_stego"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },

    "audio_lsb": {
        "title": "🎵 Audio LSB — Deep Dive",
        "text": (
            "🎵 *Audio LSB Steganography*\n\n"
            "*The Idea:*\n"
            "Audio files (WAV) contain thousands of 16-bit samples per second. "
            "Changing the last bit of each sample is inaudible to humans.\n\n"
            "*How It Works:*\n"
            "1. Load WAV audio (16-bit PCM)\n"
            "2. Convert secret → bits\n"
            "3. First 32 samples: store payload length (header)\n"
            "4. Remaining samples: embed 1 bit per sample in LSB\n"
            "5. Save modified WAV\n\n"
            "*Capacity:*\n"
            "8kHz audio: ~1000 bytes/sec\n"
            "10-second clip: ~10KB hidden\n"
            "1-minute clip: ~60KB hidden\n\n"
            "*Robustness:*\n"
            "Fragile — lost on re-encoding (MP3, Opus, AAC). "
            "Must send as WAV document on Telegram.\n\n"
            "*Detection:*\n"
            "Detectable by statistical analysis (chi-square, RS). "
            "Phase coding and spread spectrum are harder to detect.\n\n"
            "*Telegram Tip:*\n"
            "Send as 📎 document, NOT as voice message! "
            "Voice messages are re-encoded to Opus, destroying LSB data."
        ),
        "buttons": [
            [
                InlineKeyboardButton("🖼️ Image Methods", callback_data="learn_image_overview"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main"),
            ],
        ],
    },
}


# ─────────────────────────────────────────────
#  HANDLERS
# ─────────────────────────────────────────────

def _main_menu_keyboard():
    """Build the main /learn menu keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 What is Steganography?", callback_data="learn_what"),
            InlineKeyboardButton("📜 History", callback_data="learn_history"),
        ],
        [
            InlineKeyboardButton("📝 Text Methods", callback_data="learn_text_overview"),
            InlineKeyboardButton("🖼️ Image Methods", callback_data="learn_image_overview"),
        ],
        [
            InlineKeyboardButton("🔒 Security & Detection", callback_data="learn_security"),
            InlineKeyboardButton("🛡️ Best Practices", callback_data="learn_best_practices"),
        ],
    ])


MAIN_MENU_TEXT = (
    "📚 *Steganography Learning Center*\n\n"
    "Welcome! Choose a topic to learn the theory and practice "
    "of hiding secrets in plain sight.\n\n"
    "📖 *What is Steganography?* — The concept & history\n"
    "📝 *Text Methods* — ZWC, SNOW, Acrostic, Homoglyph, VS, Emoji\n"
    "🖼️ *Image & Audio* — LSB encoding, depth, secure mode, audio\n"
    "🔒 *Security* — Steganalysis, detection, countermeasures\n"
    "🛡️ *Best Practices* — How to stay safe\n\n"
    "Tap a topic to start learning 👇"
)


async def learn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the learning center main menu."""
    try:
        await update.message.reply_text(
            MAIN_MENU_TEXT,
            reply_markup=_main_menu_keyboard(),
            parse_mode="Markdown",
        )
    except Exception:
        await update.message.reply_text(
            MAIN_MENU_TEXT,
            reply_markup=_main_menu_keyboard(),
        )


async def learn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all learn-related callback queries."""
    query = update.callback_query
    await query.answer()

    topic_key = query.data.replace("learn_", "")

    # Main menu
    if topic_key == "main":
        try:
            await query.edit_message_text(
                MAIN_MENU_TEXT,
                reply_markup=_main_menu_keyboard(),
                parse_mode="Markdown",
            )
        except Exception:
            await query.edit_message_text(
                MAIN_MENU_TEXT,
                reply_markup=_main_menu_keyboard(),
            )
        return

    # Static content pages
    if topic_key in ("what", "history"):
        content = MAIN_MENU.get(topic_key)
        if content:
            try:
                await query.edit_message_text(
                    content,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main")]
                    ]),
                    parse_mode="Markdown",
                )
            except Exception:
                await query.edit_message_text(
                    content,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Main Menu", callback_data="learn_main")]
                    ]),
                )
        return

    # Topic pages with sub-buttons
    topic = TOPICS.get(topic_key)
    if topic:
        full_text = f"{topic['title']}\n\n{topic['text']}"
        try:
            await query.edit_message_text(
                full_text,
                reply_markup=InlineKeyboardMarkup(topic["buttons"]),
                parse_mode="Markdown",
            )
        except Exception:
            await query.edit_message_text(
                full_text,
                reply_markup=InlineKeyboardMarkup(topic["buttons"]),
            )
        return

    # Fallback
    await query.edit_message_text(
        "❓ Unknown topic. Send /learn to start over.",
        parse_mode="Markdown",
    )
