# 🔐 StegaBot

A Telegram bot for steganography — hiding secrets in plain sight. No AI, just pure math + cryptography.

**[Try it on Telegram →](https://t.me/STEGANOGBOT)**

---

## Features

### 📝 Text Steganography (6 methods)

| Method | How It Works | Capacity | Stealth |
|--------|-------------|----------|---------|
| **Zero-Width Characters** | Invisible Unicode between letters | ~1 bit/char | Very High |
| **SNOW Whitespace** | Trailing spaces/tabs at line ends | ~1 bit/line | Medium |
| **Acrostic** | First letters spell your secret | 1 char/word | High |
| **Homoglyph** | Latin ↔ Cyrillic lookalikes | ~1 bit/char | High |
| **Variation Selector** | Invisible Unicode VS chars | **1 byte/word** | Very High |
| **Emoji Steganography** | Data in emoji sequences | ~1 byte/emoji | High |

### 🖼️ Image Steganography

| Mode | Capacity | Security |
|------|----------|----------|
| **Standard LSB** | 3 bits/pixel × depth | Basic (magic header) |
| **🔒 Secure LSB** | 3 bits/pixel × depth | AES-128 + PBKDF2 + scrambled pixels |

- Configurable LSB depth (1-3 bits per channel)
- Gzip compression for large secrets
- No magic header in secure mode
- Passphrase-derived pixel positions

### 🎵 Audio Steganography

| Method | Capacity | Format |
|--------|----------|--------|
| **Audio LSB** | ~1 KB/sec | WAV (16-bit PCM) |

### 🛡️ Security Features

- **AES-128 encryption** (Fernet) for text and images
- **PBKDF2 key derivation** (100,000 iterations)
- **Scrambled pixel order** in secure image mode
- **No magic headers** in secure mode — nothing to detect
- **Rate limiting** (1 request/user/5 seconds)

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome & overview |
| `/encode` | Hide a secret in text (6 methods) |
| `/decode` | Extract a hidden message (auto-detect) |
| `/detect` | Scan text for hidden data |
| `/imgencode` | Hide text in an image |
| `/imgdecode` | Extract hidden text from image |
| `/imgdetect` | Scan image for hidden data |
| `/methods` | Learn about each steganography method |
| `/learn` | 📚 Interactive learning center (20 topics) |
| `/demo` | Live text steganography demo |
| `/imgdemo` | Live image steganography demo |
| `/encrypt` | Toggle AES-128 encryption |

---

## Architecture

```
stegabot/
├── bot.py                      # Main entry point
├── config.py                   # Environment config
├── state.py                    # Per-chat session manager
├── ratelimit.py                # Rate limiter
│
├── stegano/                    # Core steganography modules
│   ├── zwc.py                  # Zero-width characters
│   ├── snow.py                 # SNOW whitespace
│   ├── acrostic.py             # Acrostic (first-letter)
│   ├── homoglyph.py            # Unicode homoglyphs
│   ├── variation_selector.py   # Unicode variation selectors
│   ├── emoji.py                # Emoji steganography
│   ├── image_lsb.py            # Standard image LSB
│   ├── image_lsb_secure.py     # Secure image LSB (AES+PBKDF2)
│   ├── audio_lsb.py            # Audio LSB
│   ├── detect.py               # Auto-detect method
│   ├── crypto.py               # AES-128 encryption
│   └── utils.py                # Shared utilities
│
├── handlers/                   # Telegram bot handlers
│   ├── start.py                # /start command
│   ├── encode.py               # /encode flow (6 methods)
│   ├── decode.py               # /decode flow (auto-detect)
│   ├── detect.py               # /detect command
│   ├── methods.py              # /methods info cards
│   ├── learn.py                # /learn education center
│   ├── encrypt.py              # /encrypt toggle
│   ├── demo.py                 # /demo + /imgdemo
│   ├── imgencode.py            # /imgencode flow
│   ├── imgdecode.py            # /imgdecode flow
│   └── imgdetect.py            # /imgdetect command
│
├── tests/                      # 12 test files, 116 tests
│   ├── test_zwc.py
│   ├── test_snow.py
│   ├── test_acrostic.py
│   ├── test_homoglyph.py
│   ├── test_variation_selector.py
│   ├── test_emoji.py
│   ├── test_image_lsb.py
│   ├── test_image_lsb_secure.py
│   ├── test_audio_lsb.py
│   ├── test_detect.py
│   ├── test_crypto.py
│   ├── test_state.py
│   └── test_utils.py
│
└── plans/                      # Implementation plans
```

---

## Setup

### Prerequisites

- Python 3.11+
- A Telegram bot token ([@BotFather](https://t.me/BotFather))

### Installation

```bash
git clone https://github.com/aldimhr/stegabot.git
cd stegabot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Create `.env` file:

```bash
TELEGRAM_BOT_KEY=your_bot_token_here
```

### Run

```bash
python bot.py
```

### Run Tests

```bash
python -m pytest tests/ -v
```

---

## How It Works

### Text Steganography

Each method encodes your secret message into the cover text differently:

**Zero-Width Characters** inserts invisible Unicode characters (U+200B, U+200C) between letters. Each character encodes one bit.

**Variation Selector** maps each byte of the secret to an invisible Unicode Variation Selector (U+FE00-U+FE0F, U+E0100-U+E01EF). One byte per word boundary — 8× the capacity of ZWC.

**Emoji** uses a 64-emoji pool where each emoji encodes 6 bits. Skin tone modifiers add 2 extra bits. Output is pure emoji.

### Image Steganography

Modifies the least significant bit(s) of each pixel's color channels:

```
Original pixel: R=142 (10001110)  G=85 (01010101)  B=200 (11001000)
Secret bit:     1                  0                  1
Stego pixel:    R=143 (10001111)  G=84 (01010100)  B=201 (11001001)
```

The change is ±1 per channel — invisible to the human eye.

**Secure mode** adds:
- PBKDF2 passphrase → Fernet key + pixel seeds
- No magic header (everything encrypted)
- Passphrase-derived start position
- Key-derived pixel shuffle order

### Audio Steganography

Modifies the LSB of 16-bit PCM audio samples. First 32 samples store the payload length as a header.

---

## Learn

Send `/learn` to the bot for an interactive education center with 20 topics:

- What is steganography? History & theory
- How each text method works (deep dive)
- Image LSB: pixels, bits, depth explained
- Secure mode: PBKDF2, Fernet, scrambled pixels
- Audio LSB: WAV samples, capacity
- Steganalysis: how detection works
- Best practices & common mistakes

---

## Stats

- **7 steganography methods** (6 text + 2 image + 1 audio)
- **116 unit tests** across 12 test files
- **~5,000 lines** of Python
- **20 interactive learn topics**

---

## License

MIT

---

Built by [@aldimhr](https://github.com/aldimhr)
