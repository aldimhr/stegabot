# StegaBot — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a Telegram bot that hides and reveals secret messages using 4 classical text steganography methods — Zero-Width Characters, Whitespace/SNOW, Acrostic, and Unicode Homoglyph.

**Architecture:** Monolithic async Python bot (`python-telegram-bot` v21). Steganography logic in `stegano/` package (pure Python, zero deps). Bot handlers in `handlers/` package. In-memory session state per `chat_id`. Optional AES-128 encryption via `cryptography` lib.

**Tech Stack:** Python 3.11+, python-telegram-bot v21.6, python-dotenv, cryptography (for optional AES)

**Bot Token Env Var:** `TELEGRAM_BOT_KEY` (user convention, NOT `TELEGRAM_TOKEN`)

---

## Phase 1: Project Scaffold & Config

### Task 1.1: Initialize project structure

**Objective:** Create the directory tree, venv, `.gitignore`, and `requirements.txt`.

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `__init__.py` (empty, for package markers)

**Step 1: Create directory tree**

```bash
cd /opt/hermes/stegabot
mkdir -p handlers stegano tests
touch handlers/__init__.py stegano/__init__.py tests/__init__.py
```

**Step 2: Create requirements.txt**

```
python-telegram-bot==21.6
python-dotenv==1.0.0
cryptography==42.0.0
pytest==8.3.4
pytest-asyncio==0.24.0
```

**Step 3: Create .env.example**

```
TELEGRAM_BOT_KEY=REDACTED_TELEGRAM_BOT_TOKEN
```

**Step 4: Create .gitignore**

```
.env
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
build/
.pytest_cache/
```

**Step 5: Create venv and install deps**

```bash
cd /opt/hermes/stegabot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**Step 6: Create .env with provided token**

```
TELEGRAM_BOT_KEY=REDACTED_TELEGRAM_BOT_TOKEN
```

**Step 7: Initialize git**

```bash
cd /opt/hermes/stegabot
git init
git add .
git commit -m "chore: scaffold stegabot project structure"
```

---

## Phase 2: Core Steganography Library (stegano/)

### Task 2.1: Implement `stegano/utils.py` — bit conversion & capacity check

**Objective:** Build the foundational utilities shared by all 4 methods.

**Files:**
- Create: `stegano/utils.py`
- Create: `tests/test_utils.py`

**Step 1: Write failing tests**

```python
# tests/test_utils.py
import pytest
from stegano.utils import text_to_bits, bits_to_text, capacity_check

class TestBitConversion:
    def test_text_to_bits_ascii(self):
        bits = text_to_bits("A")
        assert bits == [0, 1, 0, 0, 0, 0, 0, 1]

    def test_text_to_bits_utf8_multibyte(self):
        bits = text_to_bits("€")
        assert len(bits) == 24  # 3 bytes × 8 bits

    def test_roundtrip_ascii(self):
        original = "hello world"
        bits = text_to_bits(original)
        recovered = bits_to_text(bits)
        assert recovered == original

    def test_roundtrip_unicode(self):
        original = "こんにちは"
        bits = text_to_bits(original)
        recovered = bits_to_text(bits)
        assert recovered == original

    def test_roundtrip_emoji(self):
        original = "🔐🗝️"
        bits = text_to_bits(original)
        recovered = bits_to_text(bits)
        assert recovered == original

    def test_bits_to_text_empty(self):
        assert bits_to_text([]) == ""

class TestCapacityCheck:
    def test_zwc_enough(self):
        result = capacity_check("A" * 100, "hello", "zwc")
        assert result["enough"] is True
        assert result["capacity_bits"] == 100
        assert result["needed_bits"] == 40  # 5 chars × 8 bits

    def test_zwc_not_enough(self):
        result = capacity_check("A" * 10, "hello", "zwc")
        assert result["enough"] is False

    def test_snow_capacity(self):
        cover = "line1\nline2\nline3\nline4\nline5"
        result = capacity_check(cover, "A", "snow")
        assert result["capacity_bits"] == 5  # 5 lines → 5 bits (but we need 8 for "A")
        assert result["enough"] is False

    def test_acrostic_capacity(self):
        cover = "one two three four five"
        result = capacity_check(cover, "abc", "acrostic")
        assert result["capacity_bits"] == 5  # 5 words → 5 chars
        assert result["enough"] is True  # 3 chars ≤ 5

    def test_homoglyph_capacity(self):
        cover = "aXeXoXpXcXx"  # 6 homoglyph-eligible letters
        result = capacity_check(cover, "A", "homoglyph")
        assert result["capacity_bits"] == 6
```

**Step 2: Run tests to verify failure**

```bash
cd /opt/hermes/stegabot
.venv/bin/python -m pytest tests/test_utils.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'stegano.utils'`

**Step 3: Implement utils.py**

```python
# stegano/utils.py
"""Core utilities: bit conversion, capacity checking."""

def text_to_bits(text: str) -> list[int]:
    """Convert UTF-8 text to list of bits (MSB first per byte)."""
    result = []
    for byte in text.encode('utf-8'):
        result.extend((byte >> (7 - i)) & 1 for i in range(8))
    return result


def bits_to_text(bits: list[int]) -> str:
    """Convert list of bits back to UTF-8 text."""
    if not bits:
        return ""
    chars = []
    for i in range(0, len(bits) - 7, 8):
        byte = int(''.join(str(b) for b in bits[i:i+8]), 2)
        chars.append(byte)
    try:
        return bytes(chars).decode('utf-8', errors='replace')
    except Exception:
        return ""


def capacity_check(cover: str, secret: str, method: str) -> dict:
    """Check if cover text has enough capacity for the secret.

    Returns dict with keys: enough, capacity_bits, needed_bits, utilization.
    """
    from stegano.homoglyph import HOMOGLYPHS

    secret_bits = len(text_to_bits(secret))
    cover_capacity = {
        'zwc': len(cover),
        'snow': cover.count('\n'),
        'acrostic': len(cover.split()),
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

**Step 4: Run tests to verify pass**

```bash
cd /opt/hermes/stegabot
.venv/bin/python -m pytest tests/test_utils.py -v
```

Expected: 8 passed

**Step 5: Commit**

```bash
git add stegano/utils.py tests/test_utils.py
git commit -m "feat(stegano): add utils.py with bit conversion and capacity check"
```

---

### Task 2.2: Implement `stegano/zwc.py` — Zero-Width Character method

**Objective:** Encode/decode using invisible Unicode zero-width characters (recommended default method).

**Files:**
- Create: `stegano/zwc.py`
- Create: `tests/test_zwc.py`

**Step 1: Write failing tests**

```python
# tests/test_zwc.py
import pytest
from stegano.zwc import encode_zwc, decode_zwc

class TestZWC:
    def test_encode_produces_same_length_visible(self):
        cover = "The weather in Jakarta is nice today."
        stego = encode_zwc(cover, "hi")
        # Visible length should be the same (ZWC are invisible)
        visible = ''.join(c for c in stego if c not in ('\u200B', '\u200C', '\u200D', '\uFEFF'))
        assert visible == cover

    def test_roundtrip_short(self):
        cover = "The weather in Jakarta is nice today."
        secret = "hi"
        stego = encode_zwc(cover, secret)
        decoded = decode_zwc(stego)
        assert decoded == secret

    def test_roundtrip_longer(self):
        cover = "A" * 200
        secret = "hello world this is a test"
        stego = encode_zwc(cover, secret)
        decoded = decode_zwc(stego)
        assert decoded == secret

    def test_roundtrip_unicode_secret(self):
        cover = "A" * 300
        secret = "こんにちは"
        stego = encode_zwc(cover, secret)
        decoded = decode_zwc(stego)
        assert decoded == secret

    def test_decode_no_hidden_data(self):
        result = decode_zwc("just plain text nothing hidden")
        assert result == ""

    def test_encode_inserts_zwc_chars(self):
        cover = "Hello world"
        stego = encode_zwc(cover, "A")
        zwc_chars = [c for c in stego if ord(c) in (0x200B, 0x200C, 0x200D)]
        assert len(zwc_chars) > 0
```

**Step 2: Run tests to verify failure**

```bash
.venv/bin/python -m pytest tests/test_zwc.py -v
```

Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement zwc.py**

```python
# stegano/zwc.py
"""Zero-Width Character steganography method.

Maps each bit of the secret to an invisible Unicode character:
  0 → U+200C (Zero-Width Non-Joiner)
  1 → U+200D (Zero-Width Joiner)
  Separator between bytes → U+200B (Zero-Width Space)
"""
from stegano.utils import text_to_bits, bits_to_text

ZWC_0 = '\u200C'    # Zero-Width Non-Joiner
ZWC_1 = '\u200D'    # Zero-Width Joiner
ZWC_SEP = '\u200B'  # Zero-Width Space (byte boundary)

ALL_ZWC = {ZWC_0, ZWC_1, ZWC_SEP}


def encode_zwc(cover: str, secret: str) -> str:
    """Hide secret inside cover text using zero-width characters."""
    bits = text_to_bits(secret)
    zwc_stream = ZWC_SEP.join(ZWC_1 if b else ZWC_0 for b in bits)
    # Insert after the first space (word boundary)
    idx = cover.index(' ') + 1 if ' ' in cover else len(cover) // 2
    return cover[:idx] + zwc_stream + cover[idx:]


def decode_zwc(stego: str) -> str:
    """Extract hidden message from stego text containing zero-width characters."""
    zwc_chars = [c for c in stego if c in (ZWC_0, ZWC_1)]
    if not zwc_chars:
        return ""
    bits = [1 if c == ZWC_1 else 0 for c in zwc_chars]
    return bits_to_text(bits)
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_zwc.py -v
```

Expected: 6 passed

**Step 5: Commit**

```bash
git add stegano/zwc.py tests/test_zwc.py
git commit -m "feat(stegano): add ZWC (zero-width character) encode/decode"
```

---

### Task 2.3: Implement `stegano/snow.py` — Whitespace/SNOW method

**Objective:** Encode/decode using trailing spaces and tabs (SNOW algorithm).

**Files:**
- Create: `stegano/snow.py`
- Create: `tests/test_snow.py`

**Step 1: Write failing tests**

```python
# tests/test_snow.py
import pytest
from stegano.snow import encode_snow, decode_snow

class TestSNOW:
    def test_roundtrip(self):
        cover = "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10"
        secret = "A"  # 8 bits → needs 8 lines
        stego = encode_snow(cover, secret)
        decoded = decode_snow(stego)
        assert decoded == secret

    def test_roundtrip_multichar(self):
        cover = "\n".join([f"line{i}" for i in range(30)])
        secret = "hi"
        stego = encode_snow(cover, secret)
        decoded = decode_snow(stego)
        assert decoded == secret

    def test_trailing_whitespace_present(self):
        cover = "line1\nline2\nline3"
        stego = encode_snow(cover, "A")
        lines = stego.split('\n')
        # At least some lines should end with space or tab
        has_trailer = any(line.endswith(' ') or line.endswith('\t') for line in lines)
        assert has_trailer

    def test_decode_no_hidden_data(self):
        result = decode_snow("just plain text\nnothing hidden")
        assert result == ""
```

**Step 2: Run tests to verify failure**

```bash
.venv/bin/python -m pytest tests/test_snow.py -v
```

**Step 3: Implement snow.py**

```python
# stegano/snow.py
"""Whitespace/SNOW steganography method.

Trailing spaces/tabs on each line encode bits:
  space (U+0020) → bit 0
  tab (U+0009)   → bit 1

NOTE: Telegram strips trailing whitespace. This method works only
when the stego text is wrapped in a code block (```).
"""
from stegano.utils import text_to_bits, bits_to_text


def encode_snow(cover: str, secret: str) -> str:
    """Hide secret in trailing whitespace of each line."""
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
    """Extract hidden bits from trailing whitespace."""
    lines = stego.split('\n')
    bits = []
    for line in lines:
        if line.endswith('\t'):
            bits.append(1)
        elif line.endswith(' '):
            bits.append(0)
    if not bits:
        return ""
    return bits_to_text(bits)
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_snow.py -v
```

**Step 5: Commit**

```bash
git add stegano/snow.py tests/test_snow.py
git commit -m "feat(stegano): add SNOW whitespace encode/decode"
```

---

### Task 2.4: Implement `stegano/acrostic.py` — First-letter method

**Objective:** Encode/decode using first letter of each word. Uses a word bank for cover generation.

**Files:**
- Create: `stegano/acrostic.py`
- Create: `tests/test_acrostic.py`

**Step 1: Write failing tests**

```python
# tests/test_acrostic.py
import pytest
from stegano.acrostic import encode_acrostic, decode_acrostic

class TestAcrostic:
    def test_decode_known(self):
        text = "Hello Everyone Look What I Found"
        assert decode_acrostic(text) == "HELWIF"

    def test_decode_ignores_nonalpha(self):
        text = "1Hello 2Everyone"
        assert decode_acrostic(text) == "HE"

    def test_roundtrip(self):
        secret = "HELLO"
        stego = encode_acrostic(secret)
        assert stego is not None  # May fail if word bank lacks letters
        decoded = decode_acrostic(stego)
        assert decoded == secret

    def test_encode_lowercase(self):
        secret = "test"
        stego = encode_acrostic(secret)
        assert stego is not None
        decoded = decode_acrostic(stego)
        assert decoded == "TEST"

    def test_encode_empty(self):
        assert encode_acrostic("") == ""
```

**Step 2: Run tests to verify failure**

**Step 3: Implement acrostic.py**

```python
# stegano/acrostic.py
"""Acrostic / First-Letter steganography.

Each word's initial letter spells the secret message.
Uses a predefined word bank (no AI) to generate plausible cover sentences.
"""
import random
from typing import Optional

# Word bank grouped by first letter — common, neutral words
# that form plausible sentences
WORD_BANK = {
    'A': ['always', 'also', 'about', 'after', 'amazing', 'another', 'any', 'around', 'are', 'at'],
    'B': ['because', 'before', 'being', 'best', 'beyond', 'big', 'both', 'but', 'by', 'bring'],
    'C': ['can', 'come', 'could', 'carefully', 'certainly', 'clearly', 'create', 'current', 'cut', 'change'],
    'D': ['daily', 'deep', 'did', 'do', 'done', 'down', 'during', 'dark', 'day', 'dear'],
    'E': ['each', 'early', 'either', 'else', 'enough', 'even', 'every', 'evidence', 'exactly', 'example'],
    'F': ['far', 'fast', 'feel', 'few', 'find', 'first', 'for', 'found', 'from', 'full'],
    'G': ['get', 'give', 'go', 'good', 'got', 'great', 'group', 'growing', 'given', 'global'],
    'H': ['had', 'has', 'have', 'he', 'her', 'here', 'high', 'him', 'his', 'how'],
    'I': ['if', 'in', 'into', 'is', 'it', 'its', 'indeed', 'important', 'imagine', 'instead'],
    'J': ['just', 'join', 'joy', 'jump', 'judge', 'journey', 'job', 'june', 'july', 'january'],
    'K': ['keep', 'key', 'kind', 'knew', 'know', 'known', 'kindly', 'king', 'kitchen', 'kids'],
    'L': ['large', 'last', 'later', 'least', 'less', 'let', 'life', 'like', 'long', 'look'],
    'M': ['made', 'make', 'many', 'may', 'me', 'might', 'more', 'most', 'much', 'must'],
    'N': ['name', 'near', 'need', 'never', 'new', 'next', 'no', 'not', 'now', 'number'],
    'O': ['of', 'off', 'often', 'on', 'one', 'only', 'or', 'other', 'our', 'out'],
    'P': ['part', 'past', 'people', 'per', 'place', 'point', 'possible', 'present', 'problem', 'public'],
    'Q': ['quite', 'quiet', 'question', 'quickly', 'quality', 'quarter', 'queen', 'quest', 'quote', 'queue'],
    'R': ['real', 'really', 'right', 'run', 'rather', 'reason', 'result', 'room', 'rest', 'return'],
    'S': ['said', 'same', 'say', 'see', 'she', 'should', 'so', 'some', 'such', 'system'],
    'T': ['take', 'tell', 'than', 'that', 'the', 'their', 'them', 'then', 'there', 'these'],
    'U': ['under', 'up', 'upon', 'us', 'use', 'used', 'using', 'usually', 'until', 'unit'],
    'V': ['very', 'view', 'various', 'value', 'visit', 'voice', 'vital', 'visual', 'volume', 'version'],
    'W': ['was', 'we', 'well', 'were', 'what', 'when', 'which', 'who', 'will', 'with'],
    'X': ['xenon', 'xerox', 'xray', 'xeric', 'xylem', 'xenial', 'xeric', 'xmas', 'xenon', 'xerox'],
    'Y': ['year', 'yes', 'yet', 'you', 'your', 'young', 'yield', 'yesterday', 'youth', 'yours'],
    'Z': ['zero', 'zone', 'zoo', 'zeal', 'zenith', 'zigzag', 'zinc', 'zip', 'zoom', 'zodiac'],
}


def encode_acrostic(secret: str) -> Optional[str]:
    """Generate a cover sentence whose first letters spell the secret.

    Returns None if any letter lacks word bank coverage.
    """
    if not secret:
        return ""

    words = []
    for ch in secret.upper():
        bank = WORD_BANK.get(ch)
        if not bank:
            return None
        words.append(random.choice(bank))
    return ' '.join(words)


def decode_acrostic(stego: str) -> str:
    """Extract first letter of each word to reveal the secret."""
    words = stego.split()
    return ''.join(w[0].upper() for w in words if w and w[0].isalpha())
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_acrostic.py -v
```

**Step 5: Commit**

```bash
git add stegano/acrostic.py tests/test_acrostic.py
git commit -m "feat(stegano): add acrostic encode/decode with word bank"
```

---

### Task 2.5: Implement `stegano/homoglyph.py` — Unicode Homoglyph method

**Objective:** Encode/decode by substituting Latin letters with visually identical Cyrillic/Greek lookalikes.

**Files:**
- Create: `stegano/homoglyph.py`
- Create: `tests/test_homoglyph.py`

**Step 1: Write failing tests**

```python
# tests/test_homoglyph.py
import pytest
from stegano.homoglyph import encode_homoglyph, decode_homoglyph, HOMOGLYPHS, REVERSE

class TestHomoglyph:
    def test_roundtrip(self):
        cover = "access accepted success"  # has a, e, c, x
        secret = "A"  # 8 bits
        stego = encode_homoglyph(cover, secret)
        decoded = decode_homoglyph(stego)
        assert decoded == secret

    def test_no_eligible_chars(self):
        cover = "wxyz"  # no homoglyph-eligible letters
        stego = encode_homoglyph(cover, "A")
        assert stego == cover  # no changes

    def test_decode_plain_text(self):
        # Text with no homoglyphs returns empty
        result = decode_homoglyph("hello world")
        assert result == ""

    def test_replacement_invisible(self):
        cover = "aaa"
        stego = encode_homoglyph(cover, "A")
        # Visual text should look the same
        assert len(stego) == len(cover)
        for i, ch in enumerate(stego):
            if ch in REVERSE:
                # Looks like 'a' but is Cyrillic
                assert ch != cover[i]
                assert ch.lower() in REVERSE
```

**Step 2: Run tests to verify failure**

**Step 3: Implement homoglyph.py**

```python
# stegano/homoglyph.py
"""Unicode Homoglyph Substitution steganography.

Replace Latin letters with visually identical characters from Cyrillic/Greek:
  bit 0 → keep original ASCII letter
  bit 1 → substitute with Cyrillic lookalike

Only 6 letters have common homoglyphs: a, e, o, p, c, x
"""
from stegano.utils import text_to_bits, bits_to_text

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
    """Hide secret by selectively substituting letters with homoglyphs."""
    bits = text_to_bits(secret)
    result = []
    bit_idx = 0
    for ch in cover:
        if ch.lower() in HOMOGLYPHS and bit_idx < len(bits):
            if bits[bit_idx]:
                result.append(HOMOGLYPHS[ch.lower()])
            else:
                result.append(ch)
            bit_idx += 1
        else:
            result.append(ch)
    return ''.join(result)


def decode_homoglyph(stego: str) -> str:
    """Extract hidden bits from homoglyph-substituted text."""
    bits = []
    for ch in stego:
        if ch in REVERSE:
            bits.append(1)
        elif ch.lower() in HOMOGLYPHS:
            bits.append(0)
    if not bits:
        return ""
    return bits_to_text(bits)
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_homoglyph.py -v
```

**Step 5: Commit**

```bash
git add stegano/homoglyph.py tests/test_homoglyph.py
git commit -m "feat(stegano): add homoglyph substitution encode/decode"
```

---

### Task 2.6: Implement `stegano/detect.py` — Auto-detection

**Objective:** Auto-detect which steganography method was used on a given text.

**Files:**
- Create: `stegano/detect.py`
- Create: `tests/test_detect.py`

**Step 1: Write failing tests**

```python
# tests/test_detect.py
import pytest
from stegano.detect import detect_method
from stegano.zwc import encode_zwc
from stegano.snow import encode_snow
from stegano.homoglyph import encode_homoglyph

class TestDetectMethod:
    def test_detect_zwc(self):
        cover = "The weather in Jakarta is nice today."
        stego = encode_zwc(cover, "hi")
        assert detect_method(stego) == "zwc"

    def test_detect_snow(self):
        cover = "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9"
        stego = encode_snow(cover, "A")
        assert detect_method(stego) == "snow"

    def test_detect_homoglyph(self):
        cover = "access accepted success"
        stego = encode_homoglyph(cover, "A")
        assert detect_method(stego) == "homoglyph"

    def test_detect_none(self):
        assert detect_method("just plain text") is None

    def test_detect_empty(self):
        assert detect_method("") is None
```

**Step 2: Run tests to verify failure**

**Step 3: Implement detect.py**

```python
# stegano/detect.py
"""Auto-detect which steganography method is present in text."""
from typing import Optional

ZWC_CHARS = {'\u200B', '\u200C', '\u200D', '\uFEFF'}
CYRILLIC_LOOKALIKES = set('\u0430\u0435\u043E\u0440\u0441\u0445')


def detect_method(text: str) -> Optional[str]:
    """Scan text for hidden data and return the detected method name.

    Returns: 'zwc' | 'snow' | 'homoglyph' | None
    """
    if not text:
        return None

    # Check for zero-width characters
    if any(c in ZWC_CHARS for c in text):
        return 'zwc'

    # Check for Cyrillic homoglyphs
    if any(c in CYRILLIC_LOOKALIKES for c in text):
        return 'homoglyph'

    # Check for trailing whitespace (SNOW)
    lines = text.split('\n')
    if any(line.endswith('\t') or (line.endswith('  ') and len(line.rstrip()) < len(line))
           for line in lines):
        return 'snow'

    return None
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_detect.py -v
```

**Step 5: Commit**

```bash
git add stegano/detect.py tests/test_detect.py
git commit -m "feat(stegano): add auto-detection of steganography methods"
```

---

## Phase 3: Session State & Config

### Task 3.1: Implement `state.py` — In-memory session state

**Objective:** Per-chat session tracking for multi-turn encode flow.

**Files:**
- Create: `state.py`
- Create: `tests/test_state.py`

**Step 1: Write failing tests**

```python
# tests/test_state.py
import pytest
from state import SessionManager

class TestSessionManager:
    def test_get_creates_default(self):
        sm = SessionManager()
        s = sm.get(123)
        assert s["step"] is None
        assert s["method"] is None
        assert s["cover"] is None
        assert s["encrypt"] is False

    def test_update(self):
        sm = SessionManager()
        sm.update(123, step="awaiting_cover", method="zwc")
        s = sm.get(123)
        assert s["step"] == "awaiting_cover"
        assert s["method"] == "zwc"

    def test_reset(self):
        sm = SessionManager()
        sm.update(123, step="awaiting_secret")
        sm.reset(123)
        s = sm.get(123)
        assert s["step"] is None

    def test_is_encoding(self):
        sm = SessionManager()
        assert sm.is_encoding(123) is False
        sm.update(123, step="awaiting_cover")
        assert sm.is_encoding(123) is True
```

**Step 2: Run tests to verify failure**

**Step 3: Implement state.py**

```python
# state.py
"""In-memory per-chat session state for encode flow."""

from typing import Any


class SessionManager:
    def __init__(self):
        self._sessions: dict[int, dict[str, Any]] = {}

    def get(self, chat_id: int) -> dict[str, Any]:
        """Get session for chat_id, creating default if needed."""
        if chat_id not in self._sessions:
            self._sessions[chat_id] = {
                "step": None,        # 'awaiting_cover' | 'awaiting_secret' | None
                "method": None,      # 'zwc' | 'snow' | 'acrostic' | 'homoglyph'
                "cover": None,       # Cover text entered by user
                "encrypt": False,    # Whether AES encryption is enabled
                "passphrase": None,  # Optional AES key
            }
        return self._sessions[chat_id]

    def update(self, chat_id: int, **kwargs) -> None:
        """Update session fields."""
        session = self.get(chat_id)
        session.update(kwargs)

    def reset(self, chat_id: int) -> None:
        """Reset session to defaults."""
        if chat_id in self._sessions:
            del self._sessions[chat_id]

    def is_encoding(self, chat_id: int) -> bool:
        """Check if user is mid-encode flow."""
        session = self.get(chat_id)
        return session["step"] is not None
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_state.py -v
```

**Step 5: Commit**

```bash
git add state.py tests/test_state.py
git commit -m "feat: add in-memory session state manager"
```

---

### Task 3.2: Implement `config.py` — Environment config loader

**Objective:** Load `.env` and expose bot config values.

**Files:**
- Create: `config.py`

**Implementation:**

```python
# config.py
"""Environment configuration loader."""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_KEY = os.getenv("TELEGRAM_BOT_KEY", "")
MAX_SECRET_BYTES = 500
MAX_COVER_CHARS = 10_000
RATE_LIMIT_SECONDS = 5
```

**Commit:**

```bash
git add config.py
git commit -m "feat: add config loader with TELEGRAM_BOT_KEY"
```

---

## Phase 4: Optional AES Encryption

### Task 4.1: Implement `stegano/crypto.py` — AES-128 encryption layer

**Objective:** Optional Fernet (AES-128) encryption of secret before embedding.

**Files:**
- Create: `stegano/crypto.py`
- Create: `tests/test_crypto.py`

**Step 1: Write failing tests**

```python
# tests/test_crypto.py
import pytest
from stegano.crypto import encrypt_secret, decrypt_secret

class TestCrypto:
    def test_roundtrip(self):
        plaintext = "hello world"
        passphrase = "my-secret-key"
        ciphertext = encrypt_secret(plaintext, passphrase)
        assert ciphertext != plaintext
        recovered = decrypt_secret(ciphertext, passphrase)
        assert recovered == plaintext

    def test_wrong_passphrase(self):
        plaintext = "hello world"
        ciphertext = encrypt_secret(plaintext, "key1")
        with pytest.raises(Exception):
            decrypt_secret(ciphertext, "key2")

    def test_unicode(self):
        plaintext = "こんにちは世界"
        passphrase = "test"
        ciphertext = encrypt_secret(plaintext, passphrase)
        recovered = decrypt_secret(ciphertext, passphrase)
        assert recovered == plaintext
```

**Step 2: Run tests to verify failure**

**Step 3: Implement crypto.py**

```python
# stegano/crypto.py
"""Optional AES-128 (Fernet) encryption for secrets before steganographic embedding."""
import base64
import hashlib
from cryptography.fernet import Fernet


def _derive_key(passphrase: str) -> bytes:
    """Derive a Fernet-compatible key from a passphrase."""
    key = hashlib.sha256(passphrase.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_secret(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext with passphrase. Returns base64-encoded ciphertext."""
    key = _derive_key(passphrase)
    f = Fernet(key)
    ciphertext = f.encrypt(plaintext.encode('utf-8'))
    return base64.urlsafe_b64encode(ciphertext).decode('ascii')


def decrypt_secret(ciphertext_b64: str, passphrase: str) -> str:
    """Decrypt base64-encoded ciphertext with passphrase."""
    key = _derive_key(passphrase)
    f = Fernet(key)
    ciphertext = base64.urlsafe_b64decode(ciphertext_b64.encode('ascii'))
    plaintext = f.decrypt(ciphertext)
    return plaintext.decode('utf-8')
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_crypto.py -v
```

**Step 5: Commit**

```bash
git add stegano/crypto.py tests/test_crypto.py
git commit -m "feat(stegano): add optional AES-128 encryption layer"
```

---

## Phase 5: Rate Limiting

### Task 5.1: Implement `ratelimit.py` — In-memory token bucket

**Objective:** 1 encode/decode per user per 5 seconds.

**Files:**
- Create: `ratelimit.py`

**Implementation:**

```python
# ratelimit.py
"""In-memory rate limiter (token bucket per user)."""
import time
from config import RATE_LIMIT_SECONDS


class RateLimiter:
    def __init__(self, cooldown: float = RATE_LIMIT_SECONDS):
        self._last_call: dict[int, float] = {}
        self._cooldown = cooldown

    def is_allowed(self, user_id: int) -> bool:
        """Check if user can make a request."""
        now = time.monotonic()
        last = self._last_call.get(user_id, 0)
        if now - last >= self._cooldown:
            self._last_call[user_id] = now
            return True
        return False

    def remaining(self, user_id: int) -> float:
        """Seconds until user can make another request."""
        now = time.monotonic()
        last = self._last_call.get(user_id, 0)
        elapsed = now - last
        return max(0, self._cooldown - elapsed)
```

**Commit:**

```bash
git add ratelimit.py
git commit -m "feat: add in-memory rate limiter"
```

---

## Phase 6: Bot Handlers

### Task 6.1: Implement `handlers/start.py` — /start command

**Objective:** Welcome message with bot explanation and command list.

**Files:**
- Create: `handlers/start.py`

**Implementation:**

```python
# handlers/start.py
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
```

**Commit:**

```bash
git add handlers/start.py
git commit -m "feat(handlers): add /start welcome handler"
```

---

### Task 6.2: Implement `handlers/methods.py` — /methods command

**Objective:** Explain all 4 methods with inline keyboard.

**Files:**
- Create: `handlers/methods.py`

**Implementation:**

```python
# handlers/methods.py
"""Handle /methods command — explain steganography methods."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

METHOD_INFO = {
    "zwc": {
        "name": "🔹 Zero-Width Characters",
        "desc": (
            "Hides data using invisible Unicode characters (U+200C, U+200D) "
            "inserted between letters of your cover text.\n\n"
            "*How it works:* Each bit of your secret becomes an invisible character.\n"
            "*Capacity:* ~1 bit per character of cover text\n"
            "*Robustness:* Survives copy-paste on Telegram, WhatsApp, web\n"
            "*Detection:* Can be found by scanning for U+200x characters\n\n"
            "✅ *Recommended method* — best balance of capacity and stealth."
        ),
    },
    "snow": {
        "name": "🔹 Whitespace / SNOW",
        "desc": (
            "Hides data in trailing spaces and tabs at the end of each line.\n\n"
            "*How it works:* Space = bit 0, Tab = bit 1\n"
            "*Capacity:* 1 bit per line\n"
            "*Robustness:* Fragile — many editors strip trailing whitespace\n"
            "*Telegram note:* ⚠️ Only works inside code blocks (```)\n\n"
            "Based on the SNOW algorithm (Matthew Kwan, 1999)."
        ),
    },
    "acrostic": {
        "name": "🔹 Acrostic / First-Letter",
        "desc": (
            "The first letter of each word spells out your secret message.\n\n"
            "*How it works:* Bot generates a sentence whose initials = your secret\n"
            "*Capacity:* 1 character per word\n"
            "*Robustness:* Survives any copy/reformat — purely structural\n"
            "*Limitation:* Cover text is generated, not user-provided\n\n"
            "Oldest steganography technique — used since ancient Greece."
        ),
    },
    "homoglyph": {
        "name": "🔹 Unicode Homoglyph",
        "desc": (
            "Replaces Latin letters with visually identical Cyrillic lookalikes.\n\n"
            "*How it works:* Normal 'a' = bit 0, Cyrillic 'а' = bit 1\n"
            "*Capacity:* 1 bit per substitutable letter (a, e, o, p, c, x)\n"
            "*Robustness:* Survives copy-paste; breaks if manually retyped\n"
            "*Detection:* Detectable by Unicode scanners\n\n"
            "Humans can't tell them apart. Machines can."
        ),
    },
}


async def methods_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show method selection inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔹 Zero-Width", callback_data="method_zwc"),
            InlineKeyboardButton("🔹 SNOW", callback_data="method_snow"),
        ],
        [
            InlineKeyboardButton("🔹 Acrostic", callback_data="method_acrostic"),
            InlineKeyboardButton("🔹 Homoglyph", callback_data="method_homoglyph"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📚 *Steganography Methods*\n\nTap any method to learn how it works:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle method info button press."""
    query = update.callback_query
    await query.answer()

    method_key = query.data.replace("method_", "")
    info = METHOD_INFO.get(method_key)
    if info:
        await query.edit_message_text(
            f"{info['name']}\n\n{info['desc']}",
            parse_mode="Markdown",
        )
```

**Commit:**

```bash
git add handlers/methods.py
git commit -m "feat(handlers): add /methods with inline keyboard"
```

---

### Task 6.3: Implement `handlers/encode.py` — /encode multi-turn flow

**Objective:** Multi-step encode: choose method → enter cover → enter secret → receive stego text.

**Files:**
- Create: `handlers/encode.py`

**Implementation:**

```python
# handlers/encode.py
"""Handle /encode multi-turn flow."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.zwc import encode_zwc
from stegano.snow import encode_snow
from stegano.acrostic import encode_acrostic
from stegano.homoglyph import encode_homoglyph
from stegano.utils import text_to_bits, capacity_check
from stegano.crypto import encrypt_secret
from config import MAX_SECRET_BYTES, MAX_COVER_CHARS


async def encode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start encode flow — ask user to choose method."""
    chat_id = update.effective_chat.id
    session_mgr.reset(chat_id)

    keyboard = [
        [
            InlineKeyboardButton("1️⃣ Zero-Width", callback_data="enc_method_zwc"),
            InlineKeyboardButton("2️⃣ SNOW", callback_data="enc_method_snow"),
        ],
        [
            InlineKeyboardButton("3️⃣ Acrostic", callback_data="enc_method_acrostic"),
            InlineKeyboardButton("4️⃣ Homoglyph", callback_data="enc_method_homoglyph"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔒 *Encode a secret message*\n\nChoose a steganography method:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def encode_method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle method selection in encode flow."""
    query = update.callback_query
    await query.answer()

    method = query.data.replace("enc_method_", "")
    chat_id = query.message.chat_id
    session_mgr.update(chat_id, method=method, step="awaiting_cover")

    method_names = {
        "zwc": "Zero-Width Characters",
        "snow": "Whitespace/SNOW",
        "acrostic": "Acrostic",
        "homoglyph": "Unicode Homoglyph",
    }

    if method == "acrostic":
        await query.edit_message_text(
            f"✅ Method: *{method_names[method]}*\n\n"
            "Now send your *SECRET MESSAGE* to hide:\n\n"
            "(I'll generate a cover sentence automatically)",
            parse_mode="Markdown",
        )
        session_mgr.update(chat_id, step="awaiting_secret")
    else:
        await query.edit_message_text(
            f"✅ Method: *{method_names[method]}*\n\n"
            "Now send your *COVER TEXT* (the innocent-looking message):",
            parse_mode="Markdown",
        )


async def encode_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle text messages during encode flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session["step"] == "awaiting_cover":
        cover = update.message.text
        if len(cover) > MAX_COVER_CHARS:
            await update.message.reply_text(
                f"⚠️ Cover text too long ({len(cover)} chars). Max: {MAX_COVER_CHARS}"
            )
            return

        session_mgr.update(chat_id, cover=cover, step="awaiting_secret")
        await update.message.reply_text(
            "✅ Cover text saved!\n\nNow send your *SECRET MESSAGE* to hide:",
            parse_mode="Markdown",
        )

    elif session["step"] == "awaiting_secret":
        secret = update.message.text
        if len(secret.encode('utf-8')) > MAX_SECRET_BYTES:
            await update.message.reply_text(
                f"⚠️ Secret too long ({len(secret.encode('utf-8'))} bytes). Max: {MAX_SECRET_BYTES} bytes."
            )
            return

        method = session["method"]
        cover = session.get("cover", "")

        # Optional encryption
        if session.get("encrypt") and session.get("passphrase"):
            secret = encrypt_secret(secret, session["passphrase"])

        # Acrostic: generate cover from secret
        if method == "acrostic":
            stego = encode_acrostic(secret)
            if stego is None:
                await update.message.reply_text(
                    "❌ Secret contains characters I can't encode. Use letters A-Z only."
                )
                session_mgr.reset(chat_id)
                return
            cap_info = ""
        else:
            # Check capacity
            cap = capacity_check(cover, secret, method)
            if not cap["enough"]:
                await update.message.reply_text(
                    f"⚠️ Cover text too short!\n\n"
                    f"Need: {cap['needed_bits']} bits ({cap['needed_bits'] // 8} chars)\n"
                    f"Capacity: {cap['capacity_bits']} bits\n\n"
                    f"Please send a longer cover text:",
                    parse_mode="Markdown",
                )
                session_mgr.update(chat_id, step="awaiting_cover")
                return

            # Encode
            encoders = {
                "zwc": encode_zwc,
                "snow": encode_snow,
                "homoglyph": encode_homoglyph,
            }
            stego = encoders[method](cover, secret)
            cap_info = (
                f"\n📊 Capacity: {cap['needed_bits']}/{cap['capacity_bits']} bits "
                f"({cap['utilization']:.0%} used)"
            )

        session_mgr.reset(chat_id)

        method_names = {
            "zwc": "Zero-Width Chars",
            "snow": "Whitespace/SNOW",
            "acrostic": "Acrostic",
            "homoglyph": "Homoglyph",
        }

        if method == "snow":
            # Wrap in code block to preserve trailing whitespace
            display = f"```\n{stego}\n```"
        else:
            display = stego

        await update.message.reply_text(
            f"✅ *Done!* Send this stego text — it looks normal but carries your secret:\n\n"
            f"{display}\n\n"
            f"Method: {method_names[method]}"
            f"{cap_info}\n\n"
            f"💡 Anyone with this bot can use /decode to read the hidden message.",
            parse_mode="Markdown",
        )
```

**Commit:**

```bash
git add handlers/encode.py
git commit -m "feat(handlers): add /encode multi-turn flow"
```

---

### Task 6.4: Implement `handlers/decode.py` — /decode flow

**Objective:** Auto-detect method and decode hidden message.

**Files:**
- Create: `handlers/decode.py`

**Implementation:**

```python
# handlers/decode.py
"""Handle /decode flow — auto-detect and decode hidden messages."""
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.detect import detect_method
from stegano.zwc import decode_zwc
from stegano.snow import decode_snow
from stegano.homoglyph import decode_homoglyph
from stegano.acrostic import decode_acrostic


async def decode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start decode flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, step="awaiting_decode")
    await update.message.reply_text(
        "🔍 *Decode a hidden message*\n\nSend the stego text to decode:",
        parse_mode="Markdown",
    )


async def decode_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle stego text submission for decoding."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_decode":
        return False  # Not in decode flow

    stego = update.message.text
    method = detect_method(stego)

    if method is None:
        await update.message.reply_text(
            "❌ *No hidden data detected.*\n\n"
            "The text doesn't contain any recognizable steganographic patterns.\n"
            "Supported methods: Zero-Width Chars, SNOW, Homoglyph.",
            parse_mode="Markdown",
        )
    else:
        decoders = {
            "zwc": decode_zwc,
            "snow": decode_snow,
            "homoglyph": decode_homoglyph,
        }
        decoded = decoders[method](stego)

        method_names = {
            "zwc": "Zero-Width Chars",
            "snow": "Whitespace/SNOW",
            "homoglyph": "Homoglyph",
        }

        await update.message.reply_text(
            f"🔍 *Hidden data found!*\n\n"
            f"Method: {method_names[method]}\n"
            f"Message:\n\n`{decoded}`",
            parse_mode="Markdown",
        )

    session_mgr.reset(chat_id)
    return True  # Handled
```

**Commit:**

```bash
git add handlers/decode.py
git commit -m "feat(handlers): add /decode with auto-detection"
```

---

### Task 6.5: Implement `handlers/detect.py` — /detect scan

**Objective:** Scan text and report which methods are present.

**Files:**
- Create: `handlers/detect.py`

**Implementation:**

```python
# handlers/detect.py
"""Handle /detect — scan text for hidden data."""
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.detect import detect_method, ZWC_CHARS, CYRILLIC_LOOKALIKES


async def detect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start detect flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, step="awaiting_detect")
    await update.message.reply_text(
        "🔎 *Steganalysis Scanner*\n\nSend any text to scan for hidden data:",
        parse_mode="Markdown",
    )


async def detect_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle text submission for detection."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_detect":
        return False

    text = update.message.text
    findings = []

    # Check each method
    zwc_count = sum(1 for c in text if c in ZWC_CHARS)
    if zwc_count > 0:
        findings.append(f"🔹 *Zero-Width Chars:* {zwc_count} invisible characters found")

    homoglyph_count = sum(1 for c in text if c in CYRILLIC_LOOKALIKES)
    if homoglyph_count > 0:
        findings.append(f"🔹 *Homoglyph:* {homoglyph_count} Cyrillic lookalike characters found")

    lines = text.split('\n')
    snow_lines = sum(1 for line in lines if line.endswith('\t') or line.endswith('  '))
    if snow_lines > 0:
        findings.append(f"🔹 *SNOW:* {snow_lines} lines with trailing whitespace")

    if findings:
        report = "\n\n".join(findings)
        await update.message.reply_text(
            f"🔎 *Scan Results*\n\n{report}\n\n"
            f"Use /decode to extract the hidden message.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "✅ *Clean — no hidden data detected.*\n\n"
            "The text appears to be free of steganographic patterns.",
            parse_mode="Markdown",
        )

    session_mgr.reset(chat_id)
    return True
```

**Commit:**

```bash
git add handlers/detect.py
git commit -m "feat(handlers): add /detect steganalysis scanner"
```

---

### Task 6.6: Implement `handlers/demo.py` — /demo command

**Objective:** Live example: encode → show → decode, all in one message.

**Files:**
- Create: `handlers/demo.py`

**Implementation:**

```python
# handlers/demo.py
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
```

**Commit:**

```bash
git add handlers/demo.py
git commit -m "feat(handlers): add /demo live demonstration"
```

---

### Task 6.7: Implement `handlers/encrypt.py` — /encrypt toggle

**Objective:** Toggle AES encryption mode and set passphrase.

**Files:**
- Create: `handlers/encrypt.py`

**Implementation:**

```python
# handlers/encrypt.py
"""Handle /encrypt on|off toggle."""
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager


async def encrypt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Toggle AES encryption mode."""
    chat_id = update.effective_chat.id
    args = context.args

    if not args or args[0].lower() not in ('on', 'off'):
        await update.message.reply_text(
            "🔐 *AES Encryption*\n\n"
            "Usage: `/encrypt on` or `/encrypt off`\n\n"
            "When enabled, your secret is encrypted with AES-128 before "
            "being hidden. Even if someone extracts the hidden data, "
            "they can't read it without your passphrase.",
            parse_mode="Markdown",
        )
        return

    mode = args[0].lower()
    if mode == "on":
        session_mgr.update(chat_id, encrypt=True)
        await update.message.reply_text(
            "🔐 AES encryption *enabled*.\n\n"
            "When you /encode, you'll be asked for a passphrase.\n"
            "The hidden message will be unreadable without it.",
            parse_mode="Markdown",
        )
    else:
        session_mgr.update(chat_id, encrypt=False, passphrase=None)
        await update.message.reply_text(
            "🔓 AES encryption *disabled*.",
            parse_mode="Markdown",
        )
```

**Commit:**

```bash
git add handlers/encrypt.py
git commit -m "feat(handlers): add /encrypt toggle"
```

---

## Phase 7: Main Bot Entry Point

### Task 7.1: Implement `bot.py` — Wire everything together

**Objective:** Main entry point that registers all handlers and starts polling.

**Files:**
- Create: `bot.py`

**Implementation:**

```python
# bot.py
"""StegaBot — Telegram bot for text steganography."""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import TELEGRAM_BOT_KEY
from state import SessionManager
from ratelimit import RateLimiter

from handlers.start import start_handler
from handlers.methods import methods_handler, method_callback
from handlers.encode import encode_handler, encode_method_callback, encode_message_handler
from handlers.decode import decode_handler, decode_message_handler
from handlers.detect import detect_handler, detect_message_handler
from handlers.demo import demo_handler
from handlers.encrypt import encrypt_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

session_mgr = SessionManager()
rate_limiter = RateLimiter()


async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route text messages to the correct handler based on session state."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Rate limit check
    if not rate_limiter.is_allowed(user_id):
        remaining = rate_limiter.remaining(user_id)
        await update.message.reply_text(
            f"⏳ Please wait {remaining:.1f}s before trying again."
        )
        return

    session = session_mgr.get(chat_id)
    step = session.get("step")

    if step == "awaiting_decode":
        await decode_message_handler(update, context, session_mgr)
    elif step == "awaiting_detect":
        await detect_message_handler(update, context, session_mgr)
    elif step in ("awaiting_cover", "awaiting_secret"):
        await encode_message_handler(update, context, session_mgr)


def main():
    """Start the bot."""
    if not TELEGRAM_BOT_KEY:
        logger.error("TELEGRAM_BOT_KEY not set in .env")
        return

    app = Application.builder().token(TELEGRAM_BOT_KEY).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("methods", methods_handler))
    app.add_handler(CommandHandler("demo", demo_handler))
    app.add_handler(CommandHandler("encode",
        lambda u, c: encode_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("decode",
        lambda u, c: decode_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("detect",
        lambda u, c: detect_handler(u, c, session_mgr)))
    app.add_handler(CommandHandler("encrypt",
        lambda u, c: encrypt_handler(u, c, session_mgr)))

    # Callback query handlers (inline buttons)
    app.add_handler(CallbackQueryHandler(method_callback, pattern="^method_"))
    app.add_handler(CallbackQueryHandler(
        lambda u, c: encode_method_callback(u, c, session_mgr),
        pattern="^enc_method_"
    ))

    # Text message router (for multi-turn flows)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    logger.info("StegaBot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
```

**Step 2: Verify the bot starts**

```bash
cd /opt/hermes/stegabot
.venv/bin/python bot.py
# Should see "StegaBot starting..." and polling begins
# Ctrl+C to stop
```

**Step 3: Commit**

```bash
git add bot.py
git commit -m "feat: add bot.py main entry point with all handlers"
```

---

## Phase 8: Systemd Service & Deployment

### Task 8.1: Create systemd service file

**Objective:** Auto-start bot on boot, auto-restart on crash.

**Files:**
- Create: `/etc/systemd/system/stegabot.service`

**Implementation:**

```ini
[Unit]
Description=StegaBot - Telegram Steganography Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hermes/stegabot
ExecStart=/opt/hermes/stegabot/.venv/bin/python bot.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

**Commands:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable stegabot
sudo systemctl start stegabot
sudo systemctl status stegabot
```

**Commit:**

```bash
git add -A
git commit -m "feat: add systemd service for stegabot"
```

---

## Phase 9: Integration Testing

### Task 9.1: Run full test suite

**Objective:** Verify all modules work together.

```bash
cd /opt/hermes/stegabot
.venv/bin/python -m pytest tests/ -v --tb=short
```

Expected: All tests pass (utils, zwc, snow, acrostic, homoglyph, detect, crypto, state).

### Task 9.2: Manual bot testing

Test each command in Telegram:
1. `/start` — Welcome message appears
2. `/demo` — Live demo shows encode/decode
3. `/methods` — Inline keyboard shows 4 methods
4. `/encode` → pick ZWC → enter cover → enter secret → get stego text
5. Copy stego text → `/decode` → paste → get original secret
6. `/detect` → paste stego text → shows detected method
7. `/encrypt on` → encode with passphrase → decode (should fail without passphrase)
8. Rate limiting: rapid requests should be throttled

---

## Summary: File Tree After Implementation

```
stegabot/
├── .env                    # TELEGRAM_BOT_KEY=...
├── .env.example
├── .gitignore
├── SPEC.md                 # (existing)
├── bot.py                  # Main entry point
├── config.py               # Environment config
├── state.py                # Session state manager
├── ratelimit.py            # Rate limiter
├── requirements.txt
├── handlers/
│   ├── __init__.py
│   ├── start.py            # /start
│   ├── encode.py           # /encode flow
│   ├── decode.py           # /decode flow
│   ├── detect.py           # /detect scanner
│   ├── demo.py             # /demo
│   ├── methods.py          # /methods + callbacks
│   └── encrypt.py          # /encrypt toggle
├── stegano/
│   ├── __init__.py
│   ├── utils.py            # Bit conversion, capacity check
│   ├── zwc.py              # Zero-width method
│   ├── snow.py             # SNOW/whitespace method
│   ├── acrostic.py         # Acrostic method
│   ├── homoglyph.py        # Homoglyph method
│   ├── detect.py           # Auto-detection
│   └── crypto.py           # Optional AES encryption
├── tests/
│   ├── __init__.py
│   ├── test_utils.py
│   ├── test_zwc.py
│   ├── test_snow.py
│   ├── test_acrostic.py
│   ├── test_homoglyph.py
│   ├── test_detect.py
│   ├── test_crypto.py
│   └── test_state.py
└── plans/
    └── 2026-06-10-stegabot-implementation.md  ← this file
```

---

## Commit Convention

Follows conventional commits:
- `feat(scope):` — new feature
- `chore:` — scaffold, config, non-functional
- `fix:` — bug fixes
- `test:` — test-only changes

## Task Execution Order

Tasks are strictly sequential (each depends on the prior):
1.1 → 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6 → 3.1 → 3.2 → 4.1 → 5.1 → 6.1 → 6.2 → 6.3 → 6.4 → 6.5 → 6.6 → 6.7 → 7.1 → 8.1 → 9.1 → 9.2
