# SPEC.md — Conceptual Steganography Telegram Bot (No-AI Stegano Edition)

## Overview

A Telegram bot for **hiding and revealing secret messages** using **classical, deterministic text steganography** — no AI involved in the encoding/decoding process. The bot is inspired by the paper *"Conceptual Steganography"* (Zhou & May, 2026) but deliberately replaces AI-based reasoning-behavior encoding with proven, rule-based steganography algorithms that work on any plain text.

Users paste (or type) a **cover text** + a **secret message**, choose a method, and get a **stego text** back. Others with the bot can decode it.

---

## Why No AI for Steganography?

The paper uses LLMs to encode bits into CoT reasoning *behaviors* — but this:
- Requires an LLM call per encode/decode
- Is non-deterministic (LLMs may hallucinate bits)
- Needs a shared "codebook" between sender and receiver

Classical methods are:
- **Deterministic** — same input always gives same output
- **Zero-cost** — pure string manipulation, no API calls
- **Instantly reversible** — decode is a mirror of encode
- **Battle-tested** — studied since the 1990s

---

## Steganography Methods Implemented

### Method 1: Zero-Width Character (ZWC) — *Recommended*
**How it works:**
Map each bit of the secret to an invisible Unicode character inserted between letters of the cover text.

| Bit | Character | Unicode | Visible? |
|-----|-----------|---------|---------|
| 0   | Zero-Width Non-Joiner | U+200C | No |
| 1   | Zero-Width Joiner | U+200D | No |
| separator | Zero-Width Space | U+200B | No |

**Capacity:** 1 bit per inter-character position → cover text of N chars can hide ~N bits  
**Robustness:** Survives copy-paste in most platforms (Telegram, WhatsApp, web). Stripped by some platforms (Twitter).  
**Detectability:** Invisible to human eye; detectable by steganalysis tools scanning for U+200x chars.

**References:**  
- Zaynalov et al., *A High Capacity Text Steganography Utilizing Unicode Zero-Width Characters* (2020)  
- Thompson, *Unicode Steganography with Zero-Width Characters* (2017)

```python
ZWC_0 = '\u200C'  # Zero-Width Non-Joiner
ZWC_1 = '\u200D'  # Zero-Width Joiner
ZWC_SEP = '\u200B'  # Zero-Width Space (byte boundary separator)

def encode_zwc(cover: str, secret: str) -> str:
    bits = text_to_bits(secret)
    zwc_stream = ZWC_SEP.join(ZWC_1 if b else ZWC_0 for b in bits)
    # Insert invisibly after the first word
    idx = cover.index(' ') if ' ' in cover else len(cover) // 2
    return cover[:idx] + zwc_stream + cover[idx:]

def decode_zwc(stego: str) -> str:
    zwc_chars = [c for c in stego if c in (ZWC_0, ZWC_1)]
    bits = [1 if c == ZWC_1 else 0 for c in zwc_chars]
    return bits_to_text(bits)
```

---

### Method 2: Whitespace / SNOW-style
**How it works:**
Trailing spaces and tabs are appended to lines of the cover text to encode bits. One space = bit 0, one tab = bit 1. Based on the SNOW algorithm (Matthew Kwan, 1999–2013).

| Bit | Character |
|-----|-----------|
| 0   | space ` ` (U+0020) |
| 1   | tab `\t` (U+0009) |

**Capacity:** Limited to number of lines × bits per line (typically 8–16 bits per line)  
**Robustness:** Fragile — many editors strip trailing whitespace. Best for raw `.txt` transmission.  
**Note:** Telegram strips trailing spaces, so this method works only when the stego text is wrapped in a code block (` ``` `).

**References:**  
- Kwan, *SNOW: Steganographic Nature Of Whitespace* (1999)  
- Innamark whitespace replacement survey (2025, arXiv:2502.12710)

```python
def encode_snow(cover: str, secret: str) -> str:
    bits = text_to_bits(secret)
    lines = cover.split('\n')
    result = []
    bit_idx = 0
    for line in lines:
        if bit_idx < len(bits):
            trailer = '\t' if bits[bit_idx] else ' '
            result.append(line + trailer)
            bit_idx += 1
        else:
            result.append(line)
    return '\n'.join(result)

def decode_snow(stego: str) -> str:
    lines = stego.split('\n')
    bits = []
    for line in lines:
        if line.endswith('\t'):
            bits.append(1)
        elif line.endswith(' '):
            bits.append(0)
    return bits_to_text(bits)
```

---

### Method 3: First-Letter / Acrostic
**How it works:**
The first letter of each word (or sentence) in the cover text spells out the secret message. This is the oldest steganography technique — used since ancient Greece and in WWI null ciphers.

**Capacity:** 1 character per word (using initials). A 26-word cover text hides 26 chars.  
**Robustness:** Survives any copy/reformat — purely structural.  
**Limitation:** The cover text must be crafted to match the secret, so the bot helps generate a plausible cover sentence whose initials spell the secret.

**References:**  
- Wikipedia, *Acrostic* — null cipher steganography  
- Chang & Clark, *Practical Linguistic Steganography* (MIT Press, 2014)

```python
def decode_acrostic(stego: str) -> str:
    words = stego.split()
    return ''.join(w[0].upper() for w in words if w[0].isalpha())
```

For encoding, the bot uses a **predefined word bank** grouped by first letter (no AI), so it can construct a plausible cover sentence letter-by-letter from the secret message.

---

### Method 4: Unicode Homoglyph Substitution
**How it works:**
Replace standard Latin letters in the cover text with visually identical Unicode lookalikes from Cyrillic, Greek, or other scripts. The substitution pattern encodes bits.

| Bit | Character | Example |
|-----|-----------|---------|
| 0   | Normal ASCII `a` | `a` (U+0061) |
| 1   | Cyrillic `а` | `а` (U+0430) |

Visually identical — humans can't tell them apart. Machines can.

**Capacity:** 1 bit per substitutable letter  
**Robustness:** Survives copy-paste perfectly. Breaks if text is manually retyped.  
**Detectability:** Detectable by Unicode scanners.

```python
HOMOGLYPHS = {
    'a': '\u0430',  # Cyrillic а
    'e': '\u0435',  # Cyrillic е
    'o': '\u043E',  # Cyrillic о
    'p': '\u0440',  # Cyrillic р
    'c': '\u0441',  # Cyrillic с
    'x': '\u0445',  # Cyrillic х
}
REVERSE = {v: k for k, v in HOMOGLYPHS.items()}

def encode_homoglyph(cover: str, secret: str) -> str:
    bits = text_to_bits(secret)
    result = []
    bit_idx = 0
    for ch in cover:
        if ch.lower() in HOMOGLYPHS and bit_idx < len(bits):
            result.append(HOMOGLYPHS[ch.lower()] if bits[bit_idx] else ch)
            bit_idx += 1
        else:
            result.append(ch)
    return ''.join(result)

def decode_homoglyph(stego: str) -> str:
    bits = []
    for ch in stego:
        if ch in REVERSE:
            bits.append(1)
        elif ch.lower() in HOMOGLYPHS:
            bits.append(0)
    return bits_to_text(bits)
```

---

## Method Comparison

| Method | Capacity | Robustness | Invisible? | Works on Telegram? | Complexity |
|--------|----------|------------|------------|-------------------|------------|
| ZWC (Zero-Width) | High | Medium | ✅ Yes | ✅ Yes | Low |
| SNOW (Whitespace) | Low | Fragile | ✅ Yes | ⚠️ Code block only | Low |
| Acrostic | Low | High | ❌ No | ✅ Yes | Medium |
| Homoglyph | Medium | Medium | ✅ Yes | ✅ Yes | Low |

**Default method: ZWC** — best balance of capacity, invisibility, and Telegram compatibility.

---

## Bot Architecture

```
User (Telegram)
      │
      ▼
Telegram Bot (Python, python-telegram-bot v21)
      │
      ├── /encode  → pure Python stegano (no API call)
      ├── /decode  → pure Python stegano (no API call)
      ├── /detect  → scan text for hidden data
      ├── /methods → explain all 4 methods
      └── /demo    → live example encode + decode
```

No external API calls for steganography. 100% offline capable.

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.11+ |
| Telegram library | `python-telegram-bot` v21+ (async) |
| Steganography | Pure Python (zero dependencies) |
| Encryption (optional) | `cryptography` library (Fernet AES-128) |
| Config | `.env` (`TELEGRAM_TOKEN` only) |
| State | In-memory dict per `chat_id` |

---

## File Structure

```
stego-bot/
├── bot.py                  # Entry point, registers all handlers
├── handlers/
│   ├── encode.py           # /encode multi-turn flow
│   ├── decode.py           # /decode flow
│   ├── detect.py           # /detect scan
│   ├── demo.py             # /demo
│   └── methods.py          # /methods education
├── stegano/
│   ├── zwc.py              # Zero-width character method
│   ├── snow.py             # Whitespace/SNOW method
│   ├── acrostic.py         # First-letter/acrostic method
│   ├── homoglyph.py        # Unicode homoglyph method
│   └── utils.py            # text_to_bits, bits_to_text, encrypt, decrypt
├── state.py                # Per-user session (encode in progress)
├── config.py               # .env loader
├── requirements.txt
└── .env.example
```

---

## Bot Commands

### `/start`
Welcome message. Brief explanation of what the bot does. Shows a quick example of text before and after ZWC encoding (they look identical). Lists commands.

---

### `/encode`
Multi-turn flow:

```
Bot:  Choose a method:
      [1] Zero-Width Chars  [2] Whitespace/SNOW
      [3] Acrostic          [4] Homoglyph

User: [taps 1]

Bot:  Send your COVER TEXT (the innocent-looking message):

User: The weather in Jakarta is nice today.

Bot:  Now send your SECRET MESSAGE to hide:

User: hello

Bot:  ✅ Done! Send this stego text — it looks normal but carries your secret:

      The weather‌‍‌‌‍‍‌‌‍‌‍‍‌‌‌‌‍‍‍‌‌ in Jakarta is nice today.

      Method: Zero-Width Chars
      Secret size: 5 chars → 40 bits
      Cover capacity used: 40/38 chars
      ⚠️ Secret too long for cover — truncated to 4 chars.
      Tip: Use a longer cover text for longer secrets.
```

---

### `/decode`
```
Bot:  Send the stego text to decode:

User: [pastes stego text]

Bot:  🔍 Scanning for hidden data...

      Method detected: Zero-Width Chars
      Hidden message: "hello"
```

Auto-detects the method by scanning for ZWC characters, trailing whitespace patterns, or homoglyphs.

---

### `/detect`
Scan any text and report:
- Which steganography methods are present
- Estimated hidden payload size
- Raw hidden bits (as hex) if found

Useful for the "Eve" (defender) role from the paper.

---

### `/demo`
Runs a complete live example:
1. Shows a cover text
2. Encodes "SECRET" into it using ZWC
3. Shows the stego text (looks identical)
4. Decodes it back
5. Shows the raw ZWC characters as visible symbols for educational purposes

---

### `/methods`
Inline keyboard menu — tap any method to get:
- How it works (plain English)
- Capacity formula
- Robustness against attacks
- Real historical examples
- Python pseudocode snippet

---

### `/encrypt on|off`
Toggle optional AES-128 (Fernet) encryption of the secret before steganographic embedding. When on, the bot asks for a passphrase. The hidden payload becomes ciphertext — even if extracted, it's unreadable without the key.

---

## Core Utilities (`stegano/utils.py`)

```python
def text_to_bits(text: str) -> list[int]:
    """Convert UTF-8 text to list of bits."""
    result = []
    for byte in text.encode('utf-8'):
        result.extend((byte >> (7 - i)) & 1 for i in range(8))
    return result

def bits_to_text(bits: list[int]) -> str:
    """Convert list of bits back to UTF-8 text."""
    chars = []
    for i in range(0, len(bits) - 7, 8):
        byte = int(''.join(str(b) for b in bits[i:i+8]), 2)
        chars.append(byte)
    try:
        return bytes(chars).decode('utf-8', errors='replace')
    except Exception:
        return ''

def capacity_check(cover: str, secret: str, method: str) -> dict:
    """Check if cover text has enough capacity for the secret."""
    secret_bits = len(text_to_bits(secret))
    cover_capacity = {
        'zwc': len(cover),           # 1 bit per char position
        'snow': cover.count('\n'),   # 1 bit per line
        'acrostic': len(cover.split()),  # 1 char per word
        'homoglyph': sum(1 for c in cover if c.lower() in HOMOGLYPHS),
    }
    cap = cover_capacity.get(method, 0)
    return {
        'enough': cap >= secret_bits,
        'capacity_bits': cap,
        'needed_bits': secret_bits,
        'utilization': secret_bits / cap if cap > 0 else float('inf'),
    }
```

---

## Auto-Detection Logic (`handlers/decode.py`)

```python
ZWC_CHARS = {'\u200B', '\u200C', '\u200D', '\uFEFF'}
CYRILLIC_LOOKALIKES = set('\u0430\u0435\u043E\u0440\u0441\u0445')

def detect_method(text: str) -> str | None:
    if any(c in ZWC_CHARS for c in text):
        return 'zwc'
    if any(c in CYRILLIC_LOOKALIKES for c in text):
        return 'homoglyph'
    lines = text.split('\n')
    if any(line.endswith('\t') or line.endswith('  ') for line in lines):
        return 'snow'
    return None  # No hidden data detected
```

---

## Session State (per `chat_id`)

```python
{
    "step": str,          # 'awaiting_cover' | 'awaiting_secret' | None
    "method": str,        # 'zwc' | 'snow' | 'acrostic' | 'homoglyph'
    "cover": str,         # Cover text entered by user
    "encrypt": bool,      # Whether AES encryption is enabled
    "passphrase": str,    # Optional AES key
}
```

---

## Capacity Guidelines (shown to user)

| Secret length | Min cover text length (ZWC) |
|---------------|----------------------------|
| 5 chars (hello) | 40 characters |
| 10 chars | 80 characters |
| 50 chars | 400 characters |
| 140 chars (tweet) | 1,120 characters |

Bot warns the user if the cover text is too short and suggests padding options.

---

## Rate Limiting

- 1 encode/decode per user per 5 seconds (in-memory token bucket)
- Max secret size: 500 bytes (4,000 bits)
- Max cover text: 10,000 characters

---

## requirements.txt

```
python-telegram-bot==21.6
python-dotenv==1.0.0
cryptography==42.0.0
```

---

## .env.example

```
TELEGRAM_TOKEN=REDACTED_TELEGRAM_BOT_TOKEN
```

No `ANTHROPIC_API_KEY` needed — zero AI calls for steganography.

---

## Running the Bot

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in TELEGRAM_TOKEN
python bot.py
```

---

## Connection to the Original Paper

The paper (*Conceptual Steganography*, Zhou & May 2026) argued that steganography can survive AI-based paraphrase defenses by encoding at the *concept* level rather than the word level. This bot takes the opposite, simpler approach:

| Paper's approach | This bot's approach |
|-----------------|---------------------|
| Encode bits into LLM reasoning *behaviors* | Encode bits into invisible Unicode chars / whitespace |
| Requires LLM (Alice, Bob, Eve) | Pure deterministic Python |
| Survives paraphrase via semantic preservation | Survives copy-paste via invisibility |
| ~4–6 bits per CoT step | ~1 bit per character (ZWC) |
| Non-deterministic, may hallucinate | 100% deterministic |
| Educational about AI alignment risk | Educational about classical stegano |

Both approaches demonstrate the same core idea: **information can hide in plain sight**.

---

## References

1. Kwan, M. (1999). *SNOW: Steganographic Nature Of Whitespace*. darkside.com.au  
2. Zaynalov et al. (2020). *A High Capacity Text Steganography Utilizing Unicode Zero-Width Characters*. ResearchGate  
3. Thompson (2017). *Unicode Steganography with Zero-Width Characters*. 330k.github.io  
4. Chang & Clark (2014). *Practical Linguistic Steganography using Contextual Synonym Substitution*. Computational Linguistics, MIT Press  
5. Por et al. (2012). *UniSpaCh: A Text-Based Data Hiding Method Using Unicode Space Characters*  
6. Innamark whitespace survey (2025). arXiv:2502.12710  
7. Zhou & May (2026). *Conceptual Steganography*. arXiv:2605.26537 *(inspiration only)*
