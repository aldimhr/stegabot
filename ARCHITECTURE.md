# StegaBot Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram User                         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 StegaBot (bot.py)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │  Commands    │  │  Message     │  │  Callback      │ │
│  │  Router      │  │  Router      │  │  Router        │ │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘ │
│         │                │                   │          │
│  ┌──────▼────────────────▼───────────────────▼────────┐ │
│  │              Session Manager (state.py)             │ │
│  │         Per-chat_id in-memory state dict            │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────┐  ┌──────────────────────────┐ │
│  │   handlers/          │  │   stegano/                │ │
│  │   ├── start.py       │  │   ├── utils.py            │ │
│  │   ├── encode.py      │  │   ├── zwc.py              │ │
│  │   ├── decode.py      │  │   ├── snow.py             │ │
│  │   ├── detect.py      │  │   ├── acrostic.py         │ │
│  │   ├── demo.py        │  │   ├── homoglyph.py        │ │
│  │   ├── methods.py     │  │   ├── image_lsb.py        │ │
│  │   ├── encrypt.py     │  │   ├── detect.py           │ │
│  │   ├── imgencode.py   │  │   └── crypto.py           │ │
│  │   ├── imgdecode.py   │  │                            │ │
│  │   └── imgdetect.py   │  │                            │ │
│  └─────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Text Steganography (Encode)

```
User → /encode → choose method → enter cover text → enter secret
  → capacity_check() → encode_{method}() → reply with stego text
```

### Text Steganography (Decode)

```
User → /decode → paste stego text
  → detect_method() → decode_{method}() → reply with hidden message
```

### Image Steganography (Encode)

```
User → /imgencode → send PNG photo
  → download photo → convert to PNG → show capacity
  → enter secret → encode_lsb() → sendDocument(stego.png)
```

**Critical:** Bot uses `sendDocument` (not `sendPhoto`) to preserve pixel-perfect data.

### Image Steganography (Decode)

```
User → /imgdecode → send stego image
  → download photo → convert to PNG → decode_lsb()
  → reply with hidden message
```

## Package Structure

```
stegabot/
├── bot.py                  # Entry point, handler registration, message routing
├── config.py               # Environment config (TELEGRAM_BOT_KEY, limits)
├── state.py                # Per-chat session state manager
├── ratelimit.py            # In-memory rate limiter (token bucket)
├── requirements.txt
├── .env                    # TELEGRAM_BOT_KEY=...
├── SPEC.md                 # Full specification
├── ARCHITECTURE.md         # This file
│
├── handlers/               # Telegram command handlers
│   ├── start.py            # /start — welcome message
│   ├── methods.py          # /methods — explain all methods
│   ├── encode.py           # /encode — text steganography flow
│   ├── decode.py           # /decode — text decode flow
│   ├── detect.py           # /detect — text steganalysis
│   ├── demo.py             # /demo — live text demo
│   ├── encrypt.py          # /encrypt on|off — AES toggle
│   ├── imgencode.py        # /imgencode — image LSB encode
│   ├── imgdecode.py        # /imgdecode — image LSB decode
│   └── imgdetect.py        # /imgdetect — image steganalysis
│
├── stegano/                # Steganography algorithms
│   ├── utils.py            # Bit conversion, capacity check
│   ├── zwc.py              # Zero-Width Characters (U+200C/U+200D)
│   ├── snow.py             # Whitespace/SNOW (trailing spaces/tabs)
│   ├── acrostic.py         # First-Letter/Acrostic (word bank)
│   ├── homoglyph.py        # Unicode Homoglyph (Cyrillic lookalikes)
│   ├── image_lsb.py        # Image LSB (PIL-based)
│   ├── detect.py           # Auto-detection (text methods)
│   └── crypto.py           # AES-128 Fernet encryption
│
└── tests/                  # Pytest test suite
    ├── test_utils.py
    ├── test_zwc.py
    ├── test_snow.py
    ├── test_acrostic.py
    ├── test_homoglyph.py
    ├── test_image_lsb.py
    ├── test_detect.py
    ├── test_crypto.py
    └── test_state.py
```

## Key Design Decisions

### 1. Custom LSB Implementation (not Stegano PyPI library)

Our `stegano/` package name shadows the PyPI `Stegano` library. Rather than renaming our package, we implement LSB directly using PIL/Pillow (~80 lines). This gives us full control over the encoding format (32-bit length header, RGB-only channels).

### 2. Images Sent as Documents

Telegram's `sendPhoto` compresses images (resize to max 2560px, JPEG re-encode). This destroys LSB data. We use `sendDocument` which preserves the original file byte-for-byte.

| Method | Compression | Max Size | Preserves LSB? |
|--------|------------|----------|----------------|
| `sendPhoto` | Yes (JPEG) | 10 MB | ❌ No |
| `sendDocument` | No | 50 MB | ✅ Yes |

### 3. PNG-Only Format

JPEG uses lossy compression that modifies pixel values, destroying LSB data. PNG is lossless — pixel values are preserved exactly.

### 4. 32-bit Length Header

The first 32 LSBs encode the message bit-length as a big-endian integer. This allows the decoder to extract exactly the right number of bits without scanning the entire image.

### 5. Alpha Channel Skipped

For RGBA images, we only use R, G, B channels (skip alpha). Modifying alpha values is visually detectable (transparency changes) and some image processing tools normalize alpha.

### 6. Rate Limiting

1 operation per user per 5 seconds (in-memory token bucket). Prevents abuse without persistent storage.

## State Machine

### Text Encode Flow

```
┌─────────┐    /encode     ┌──────────────┐   method    ┌──────────────┐
│  Idle   │ ──────────────→│ Choose Method│ ──────────→ │ Awaiting     │
│         │                │ (callback)   │             │ Cover Text   │
└─────────┘                └──────────────┘             └──────┬───────┘
                                                               │ text
                                                               ▼
┌─────────┐    text        ┌──────────────┐                    │
│  Idle   │ ←──────────────│ Awaiting     │ ←─────────────────┘
│         │    encode+reply │ Secret Text  │
└─────────┘                └──────────────┘

Exception: Acrostic method skips "Awaiting Cover Text"
```

### Image Encode Flow

```
┌─────────┐   /imgencode   ┌──────────────┐   photo    ┌──────────────┐
│  Idle   │ ──────────────→│ Awaiting     │ ─────────→ │ Awaiting     │
│         │                │ Image        │            │ Image Secret │
└─────────┘                └──────────────┘            └──────┬───────┘
                                                               │ text
                                                               ▼
┌─────────┐    document    ┌──────────────┐
│  Idle   │ ←──────────────│ Encode +     │
│         │    send         │ Send Document│
└─────────┘                └──────────────┘
```

## Telegram-Specific Considerations

1. **Photo compression:** `sendPhoto` compresses. Use `sendDocument` for stego output.
2. **Received photos:** When users send photos via Telegram, they may already be compressed. LSB decode may fail on compressed photos. Warn users.
3. **File size limits:** Documents up to 50 MB (plenty for images).
4. **Markdown escaping:** Stego text may contain special characters. Use `parse_mode="Markdown"` carefully.
5. **Code blocks:** SNOW method requires code blocks to preserve trailing whitespace.

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| python-telegram-bot | 21.6 | Telegram Bot API |
| python-dotenv | 1.0.0 | .env loading |
| cryptography | 42.0.0 | AES-128 encryption |
| Pillow | 12.2.0 | Image processing (LSB) |
| pytest | 8.3.4 | Testing |
