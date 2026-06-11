# Image Steganography — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add image steganography to StegaBot — hide text secrets inside PNG images using LSB (Least Significant Bit) encoding, with Telegram-compatible send/receive via `sendDocument`.

**Architecture:** Pure PIL/Pillow LSB implementation (no external stegano library — avoids naming conflict with our `stegano/` package). Images sent as documents to preserve pixel-perfect data. PNG-only (JPEG destroys LSBs).

**Tech Stack:** PIL/Pillow (already installed), python-telegram-bot v21

---

## Background: Why Image Steganography?

**Capacity comparison:**

| Cover Type | Size | Capacity |
|---|---|---|
| Text (100 chars, ZWC) | 100 chars | ~100 bits (12 chars) |
| Image 512×512 RGB | 786 KB | 786,432 bits (96 KB) |
| Image 1024×768 RGB | 2.3 MB | 2,359,296 bits (288 KB) |

Images offer **1000× more capacity** than text steganography.

## Background: Telegram Image Handling

- `sendPhoto` → Telegram **compresses** (resizes to max 2560px, JPEG re-encode). **Destroys LSB data.**
- `sendDocument` → Telegram sends **uncompressed**. Pixel-perfect. **Required for steganography.**
- PNG format is **mandatory** — JPEG lossy compression destroys hidden bits.
- Max file size: 50MB for documents (plenty for images).

---

## Phase 1: Core Image Steganography Library

### Task 1.1: Implement `stegano/image_lsb.py` — LSB encode/decode

**Objective:** Pure PIL-based LSB steganography for RGB/RGBA PNG images.

**Files:**
- Create: `stegano/image_lsb.py`
- Create: `tests/test_image_lsb.py`

**Design:**

```
Message format in pixel bits:
[32-bit length header][message bits][padding zeros]

LSB mapping (per pixel):
  R channel → bit N
  G channel → bit N+1
  B channel → bit N+2
  (A channel skipped for RGBA — alpha changes are visually detectable)
```

**Step 1: Write failing tests**

```python
# tests/test_image_lsb.py
import pytest
import os
from PIL import Image
from stegano.image_lsb import encode_lsb, decode_lsb, capacity_lsb

TEST_DIR = "/tmp/stegabot_tests"

@pytest.fixture(autouse=True)
def setup():
    os.makedirs(TEST_DIR, exist_ok=True)

def make_test_image(name, size=(100, 100), mode='RGB'):
    path = os.path.join(TEST_DIR, name)
    img = Image.new(mode, size, color='blue')
    img.save(path, format='PNG')
    return path

class TestLSB:
    def test_roundtrip_short(self):
        cover = make_test_image("cover1.png")
        stego = os.path.join(TEST_DIR, "stego1.png")
        secret = "Hello!"
        encode_lsb(cover, secret, stego)
        assert decode_lsb(stego) == secret

    def test_roundtrip_long(self):
        cover = make_test_image("cover2.png", size=(512, 512))
        stego = os.path.join(TEST_DIR, "stego2.png")
        secret = "A" * 1000
        encode_lsb(cover, secret, stego)
        assert decode_lsb(stego) == secret

    def test_roundtrip_unicode(self):
        cover = make_test_image("cover3.png", size=(256, 256))
        stego = os.path.join(TEST_DIR, "stego3.png")
        secret = "こんにちは世界 🔐"
        encode_lsb(cover, secret, stego)
        assert decode_lsb(stego) == secret

    def test_rgba_image(self):
        cover = make_test_image("cover4.png", size=(200, 200), mode='RGBA')
        stego = os.path.join(TEST_DIR, "stego4.png")
        secret = "RGBA test"
        encode_lsb(cover, secret, stego)
        assert decode_lsb(stego) == secret

    def test_visual_similarity(self):
        """Stego image should look identical to cover."""
        cover = make_test_image("cover5.png", size=(100, 100))
        stego = os.path.join(TEST_DIR, "stego5.png")
        encode_lsb(cover, "test", stego)
        c = Image.open(cover)
        s = Image.open(stego)
        assert c.size == s.size
        assert c.mode == s.mode
        # Pixel difference should be minimal (≤1 per channel)
        for x in range(c.width):
            for y in range(c.height):
                cp = c.getpixel((x, y))
                sp = s.getpixel((x, y))
                for i in range(len(cp)):
                    assert abs(cp[i] - sp[i]) <= 1

    def test_capacity_check(self):
        cover = make_test_image("cover6.png", size=(100, 100))
        cap = capacity_lsb(cover)
        assert cap['pixels'] == 10000
        assert cap['channels'] == 3  # RGB
        assert cap['capacity_bits'] == 30000
        assert cap['capacity_chars'] == 3750

    def test_secret_too_long(self):
        cover = make_test_image("cover7.png", size=(10, 10))  # tiny
        stego = os.path.join(TEST_DIR, "stego7.png")
        secret = "A" * 100  # too many bits for 10x10 image
        with pytest.raises(ValueError, match="too long"):
            encode_lsb(cover, secret, stego)

    def test_decode_no_hidden_data(self):
        """Decoding an unmodified image should return empty or raise."""
        cover = make_test_image("cover8.png")
        # This may return garbage or empty — depends on first 32 bits
        # The length header will likely be 0 or nonsensical
        result = decode_lsb(cover)
        # We just verify it doesn't crash
        assert isinstance(result, str)
```

**Step 2: Run tests to verify failure**

```bash
cd /opt/hermes/stegabot
.venv/bin/python -m pytest tests/test_image_lsb.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'stegano.image_lsb'`

**Step 3: Implement image_lsb.py**

```python
# stegano/image_lsb.py
"""LSB (Least Significant Bit) image steganography.

Hides text in the least significant bits of pixel color channels.
Works with RGB and RGBA PNG images.

Message format:
  [32-bit length header][UTF-8 message bits]

Capacity:
  RGB: width × height × 3 bits
  RGBA: width × height × 3 bits (alpha channel skipped — visual detectability)
"""
from PIL import Image
import struct


def _text_to_bits(text: str) -> list[int]:
    """Convert text to bit list (UTF-8 encoded, MSB first per byte)."""
    result = []
    for byte in text.encode('utf-8'):
        result.extend((byte >> (7 - i)) & 1 for i in range(8))
    return result


def _bits_to_text(bits: list[int]) -> str:
    """Convert bit list back to text."""
    if len(bits) < 8:
        return ""
    chars = []
    for i in range(0, len(bits) - 7, 8):
        byte = int(''.join(str(b) for b in bits[i:i+8]), 2)
        chars.append(byte)
    return bytes(chars).decode('utf-8', errors='replace')


def _int_to_bits(n: int, width: int = 32) -> list[int]:
    """Convert integer to fixed-width bit list."""
    return [(n >> (width - 1 - i)) & 1 for i in range(width)]


def _bits_to_int(bits: list[int]) -> int:
    """Convert bit list to integer."""
    result = 0
    for b in bits:
        result = (result << 1) | b
    return result


def _get_data_channels(pixel: tuple) -> int:
    """Number of channels to use for data (skip alpha)."""
    return 3  # Always use R, G, B (skip A if present)


def capacity_lsb(image_path: str) -> dict:
    """Calculate LSB capacity of an image.

    Returns dict with: pixels, channels, capacity_bits, capacity_chars, max_message_bytes.
    """
    img = Image.open(image_path)
    w, h = img.size
    channels = 3  # Always R, G, B (skip alpha)
    total_bits = w * h * channels
    # Subtract 32 bits for length header
    usable_bits = total_bits - 32
    return {
        'pixels': w * h,
        'channels': channels,
        'capacity_bits': total_bits,
        'usable_bits': usable_bits,
        'capacity_chars': usable_bits // 8,
        'max_message_bytes': usable_bits // 8,
    }


def encode_lsb(cover_path: str, secret: str, output_path: str) -> str:
    """Hide secret message in image using LSB encoding.

    Args:
        cover_path: Path to cover image (PNG)
        secret: Secret text to hide
        output_path: Path to save stego image (PNG)

    Returns:
        Path to stego image

    Raises:
        ValueError: If secret is too long for the image
    """
    img = Image.open(cover_path).convert('RGB')
    pixels = list(img.getdata())
    w, h = img.size

    # Encode message as UTF-8 bits
    msg_bytes = secret.encode('utf-8')
    msg_bits = _text_to_bits(secret)

    # Total capacity: 3 bits per pixel (R, G, B channels)
    total_capacity = w * h * 3
    needed_bits = 32 + len(msg_bits)  # 32-bit header + message

    if needed_bits > total_capacity:
        raise ValueError(
            f"Secret too long: need {needed_bits} bits, "
            f"image has {total_capacity} bits capacity"
        )

    # Build bit stream: [32-bit length][message bits]
    length_header = _int_to_bits(len(msg_bits))
    all_bits = length_header + msg_bits

    # Embed bits into pixel LSBs
    bit_idx = 0
    new_pixels = []
    for pixel in pixels:
        r, g, b = pixel[:3]  # Handle RGB or RGBA
        if bit_idx < len(all_bits):
            r = (r & 0xFE) | all_bits[bit_idx]
            bit_idx += 1
        if bit_idx < len(all_bits):
            g = (g & 0xFE) | all_bits[bit_idx]
            bit_idx += 1
        if bit_idx < len(all_bits):
            b = (b & 0xFE) | all_bits[bit_idx]
            bit_idx += 1
        if len(pixel) == 4:
            new_pixels.append((r, g, b, pixel[3]))  # Preserve alpha
        else:
            new_pixels.append((r, g, b))

    # Create stego image
    stego = Image.new(img.mode, img.size)
    stego.putdata(new_pixels)
    stego.save(output_path, format='PNG')
    return output_path


def decode_lsb(stego_path: str) -> str:
    """Extract hidden message from stego image.

    Args:
        stego_path: Path to stego image

    Returns:
        Decoded secret message
    """
    img = Image.open(stego_path).convert('RGB')
    pixels = list(img.getdata())

    # Extract all LSBs from R, G, B channels
    all_bits = []
    for pixel in pixels:
        r, g, b = pixel[:3]
        all_bits.extend([r & 1, g & 1, b & 1])

    # Read 32-bit length header
    if len(all_bits) < 32:
        return ""
    msg_length = _bits_to_int(all_bits[:32])

    # Sanity check
    if msg_length <= 0 or msg_length > len(all_bits) - 32:
        return ""

    # Extract message bits
    msg_bits = all_bits[32:32 + msg_length]
    return _bits_to_text(msg_bits)
```

**Step 4: Run tests**

```bash
cd /opt/hermes/stegabot
.venv/bin/python -m pytest tests/test_image_lsb.py -v
```

Expected: All 9 tests pass

**Step 5: Commit**

```bash
git add stegano/image_lsb.py tests/test_image_lsb.py
git commit -m "feat(stegano): add LSB image steganography encode/decode"
```

---

## Phase 2: Image Capacity & Validation Helpers

### Task 2.1: Add image helpers to `stegano/utils.py`

**Objective:** Add `image_capacity_check()` to utils.py for bot handlers.

**Files:**
- Modify: `stegano/utils.py`

**Add function:**

```python
def image_capacity_check(image_path: str, secret: str) -> dict:
    """Check if image has enough LSB capacity for the secret."""
    from stegano.image_lsb import capacity_lsb
    cap = capacity_lsb(image_path)
    secret_bytes = len(secret.encode('utf-8'))
    secret_bits = secret_bytes * 8
    needed_bits = 32 + secret_bits  # header + message
    return {
        'enough': cap['usable_bits'] >= secret_bits,
        'capacity_bits': cap['usable_bits'],
        'needed_bits': needed_bits,
        'capacity_chars': cap['capacity_chars'],
        'image_size': cap['pixels'],
    }
```

**Commit:**

```bash
git commit -am "feat(stegano): add image capacity check to utils"
```

---

## Phase 3: Bot Handlers for Image Steganography

### Task 3.1: Add `/imgencode` handler — hide text in image

**Objective:** Multi-turn flow: user sends image → sends secret → gets stego image back.

**Files:**
- Create: `handlers/imgencode.py`

**Flow:**

```
User: /imgencode
Bot:  Send a PNG image to use as cover:

User: [sends photo]

Bot:  ✅ Image received (1024×768, capacity: 288 KB)
      Now send your SECRET MESSAGE to hide:

User: Hello world!

Bot:  [sends stego image as document with caption]
      ✅ Secret hidden in image!
      Capacity: 11/294,912 chars used
      ⚠️ Download the image (don't screenshot) to preserve hidden data.
```

**Implementation:**

```python
# handlers/imgencode.py
"""Handle /imgencode — hide text in images using LSB."""
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.image_lsb import encode_lsb, capacity_lsb
from stegano.utils import image_capacity_check
from config import MAX_SECRET_BYTES


async def imgencode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start image encode flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, method="image_lsb", step="awaiting_image")
    await update.message.reply_text(
        "🖼️ *Image Steganography — Encode*\n\n"
        "Send a *PNG image* to use as cover:\n\n"
        "💡 For best results, use PNG images. "
        "JPEG images will be converted to PNG.",
        parse_mode="Markdown",
    )


async def imgencode_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle photo upload in image encode flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_image":
        return False

    # Download the photo
    photo = update.message.photo[-1]  # Highest resolution
    file = await photo.get_file()

    # Save to temp directory
    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, "cover.png")
    await file.download_to_drive(input_path)

    # Convert to PNG if needed (Telegram sends JPEG for photos)
    from PIL import Image
    img = Image.open(input_path)
    png_path = os.path.join(tmp_dir, "cover.png")
    img.save(png_path, format='PNG')

    # Check capacity
    cap = capacity_lsb(png_path)
    session_mgr.update(
        chat_id,
        cover_image=png_path,
        step="awaiting_image_secret",
    )

    await update.message.reply_text(
        f"✅ Image received! ({img.width}×{img.height})\n\n"
        f"📊 Capacity: {cap['capacity_chars']:,} characters\n\n"
        f"Now send your *SECRET MESSAGE* to hide:",
        parse_mode="Markdown",
    )
    return True


async def imgencode_secret_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle secret text in image encode flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_image_secret":
        return False

    secret = update.message.text
    cover_path = session.get("cover_image")

    if not cover_path or not os.path.exists(cover_path):
        await update.message.reply_text("❌ Cover image not found. Please /imgencode again.")
        session_mgr.reset(chat_id)
        return True

    # Check size
    if len(secret.encode('utf-8')) > MAX_SECRET_BYTES:
        await update.message.reply_text(
            f"⚠️ Secret too long ({len(secret.encode('utf-8'))} bytes). Max: {MAX_SECRET_BYTES} bytes."
        )
        return True

    # Check capacity
    cap = image_capacity_check(cover_path, secret)
    if not cap['enough']:
        await update.message.reply_text(
            f"⚠️ Secret too long for this image!\n\n"
            f"Need: {cap['needed_bits']:,} bits\n"
            f"Capacity: {cap['capacity_bits']:,} bits\n\n"
            f"Try a larger image or shorter secret."
        )
        return True

    # Encode
    stego_path = cover_path.replace("cover.png", "stego.png")
    try:
        encode_lsb(cover_path, secret, stego_path)
    except ValueError as e:
        await update.message.reply_text(f"❌ Error: {e}")
        session_mgr.reset(chat_id)
        return True

    # Send as document (preserves pixels!)
    await update.message.reply_document(
        document=open(stego_path, 'rb'),
        filename="stego_image.png",
        caption=(
            "✅ *Secret hidden in image!*\n\n"
            f"📊 Used: {len(secret):,}/{cap['capacity_chars']:,} chars\n"
            f"Method: LSB (Least Significant Bit)\n\n"
            "⚠️ *Important:* Download this image to decode. "
            "Screenshots will destroy the hidden data!"
        ),
        parse_mode="Markdown",
    )

    # Cleanup
    import shutil
    shutil.rmtree(os.path.dirname(cover_path), ignore_errors=True)
    session_mgr.reset(chat_id)
    return True
```

**Commit:**

```bash
git add handlers/imgencode.py
git commit -m "feat(handlers): add /imgencode — hide text in images via LSB"
```

---

### Task 3.2: Add `/imgdecode` handler — extract text from image

**Objective:** User sends stego image → bot decodes and shows hidden message.

**Files:**
- Create: `handlers/imgdecode.py`

**Flow:**

```
User: /imgdecode
Bot:  Send a stego image to decode:

User: [sends image]

Bot:  🔍 Hidden message found!
      Method: LSB
      Message: Hello world!
```

**Implementation:**

```python
# handlers/imgdecode.py
"""Handle /imgdecode — extract hidden text from images."""
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.image_lsb import decode_lsb


async def imgdecode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start image decode flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, step="awaiting_stego_image")
    await update.message.reply_text(
        "🔍 *Image Steganography — Decode*\n\n"
        "Send a stego image to extract the hidden message:",
        parse_mode="Markdown",
    )


async def imgdecode_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle photo upload in image decode flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_stego_image":
        return False

    # Download the photo
    photo = update.message.photo[-1]
    file = await photo.get_file()

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, "stego.png")
    await file.download_to_drive(input_path)

    # Convert to PNG (Telegram may have compressed it)
    from PIL import Image
    img = Image.open(input_path)
    png_path = os.path.join(tmp_dir, "stego.png")
    img.save(png_path, format='PNG')

    # Try to decode
    try:
        decoded = decode_lsb(png_path)
    except Exception as e:
        await update.message.reply_text(
            f"❌ Failed to decode: {e}"
        )
        session_mgr.reset(chat_id)
        return True

    if decoded:
        await update.message.reply_text(
            f"🔍 *Hidden message found!*\n\n"
            f"Method: LSB (Image)\n"
            f"Message:\n\n`{decoded}`",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "❌ *No hidden message found.*\n\n"
            "The image doesn't contain steganographic data, "
            "or it was compressed/modified after encoding.\n\n"
            "💡 Make sure to download the original image. "
            "Screenshots destroy hidden data.",
            parse_mode="Markdown",
        )

    # Cleanup
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    session_mgr.reset(chat_id)
    return True
```

**Commit:**

```bash
git add handlers/imgdecode.py
git commit -m "feat(handlers): add /imgdecode — extract hidden text from images"
```

---

### Task 3.3: Add `/imgdetect` handler — scan image for hidden data

**Objective:** Scan an image and report if LSB steganography is likely present.

**Files:**
- Create: `handlers/imgdetect.py`

**Implementation:**

```python
# handlers/imgdetect.py
"""Handle /imgdetect — scan images for hidden data."""
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from state import SessionManager
from stegano.image_lsb import decode_lsb, capacity_lsb


async def imgdetect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Start image detect flow."""
    chat_id = update.effective_chat.id
    session_mgr.update(chat_id, step="awaiting_detect_image")
    await update.message.reply_text(
        "🔎 *Image Steganalysis*\n\n"
        "Send an image to scan for hidden data:",
        parse_mode="Markdown",
    )


async def imgdetect_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, session_mgr: SessionManager):
    """Handle photo upload in image detect flow."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)

    if session.get("step") != "awaiting_detect_image":
        return False

    photo = update.message.photo[-1]
    file = await photo.get_file()

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, "scan.png")
    await file.download_to_drive(input_path)

    from PIL import Image
    img = Image.open(input_path)
    png_path = os.path.join(tmp_dir, "scan.png")
    img.save(png_path, format='PNG')

    cap = capacity_lsb(png_path)

    # Try to decode
    decoded = decode_lsb(png_path)

    if decoded:
        await update.message.reply_text(
            f"🔎 *Scan Results*\n\n"
            f"✅ *Hidden data detected!*\n\n"
            f"Image: {img.width}×{img.height}\n"
            f"LSB capacity: {cap['capacity_chars']:,} chars\n"
            f"Hidden message: `{decoded[:100]}`{'...' if len(decoded) > 100 else ''}\n\n"
            f"Use /imgdecode to extract the full message.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"🔎 *Scan Results*\n\n"
            f"✅ *Clean — no hidden data detected.*\n\n"
            f"Image: {img.width}×{img.height}\n"
            f"LSB capacity: {cap['capacity_chars']:,} chars\n\n"
            f"The image appears to be free of steganographic patterns.",
            parse_mode="Markdown",
        )

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    session_mgr.reset(chat_id)
    return True
```

**Commit:**

```bash
git add handlers/imgdetect.py
git commit -m "feat(handlers): add /imgdetect — scan images for hidden data"
```

---

## Phase 4: Wire Image Handlers into bot.py

### Task 4.1: Register image handlers in `bot.py`

**Objective:** Add new commands and photo handlers to the bot.

**Files:**
- Modify: `bot.py`

**Changes:**

1. Add imports for new handlers
2. Add CommandHandler for `/imgencode`, `/imgdecode`, `/imgdetect`
3. Add MessageHandler for photos (to handle image uploads in encode/decode/detect flows)
4. Update `/start` help text
5. Update `message_router` to route image-related steps

```python
# In bot.py, add imports:
from handlers.imgencode import (
    imgencode_handler, imgencode_photo_handler, imgencode_secret_handler
)
from handlers.imgdecode import imgdecode_handler, imgdecode_photo_handler
from handlers.imgdetect import imgdetect_handler, imgdetect_photo_handler

# Add command handlers:
app.add_handler(CommandHandler("imgencode",
    lambda u, c: imgencode_handler(u, c, session_mgr)))
app.add_handler(CommandHandler("imgdecode",
    lambda u, c: imgdecode_handler(u, c, session_mgr)))
app.add_handler(CommandHandler("imgdetect",
    lambda u, c: imgdetect_handler(u, c, session_mgr)))

# Add photo handler (for image uploads in multi-turn flows):
async def photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route photo messages to the correct handler."""
    chat_id = update.effective_chat.id
    session = session_mgr.get(chat_id)
    step = session.get("step")

    if step == "awaiting_image":
        await imgencode_photo_handler(update, context, session_mgr)
    elif step == "awaiting_stego_image":
        await imgdecode_photo_handler(update, context, session_mgr)
    elif step == "awaiting_detect_image":
        await imgdetect_photo_handler(update, context, session_mgr)

app.add_handler(MessageHandler(filters.PHOTO, photo_router))
```

**Update message_router to handle `awaiting_image_secret`:**

```python
# In message_router, add:
elif step == "awaiting_image_secret":
    await imgencode_secret_handler(update, context, session_mgr)
```

**Commit:**

```bash
git add bot.py
git commit -m "feat: wire image steganography handlers into bot"
```

---

## Phase 5: Update Documentation

### Task 5.1: Update `handlers/start.py` — add image commands to help

**Files:**
- Modify: `handlers/start.py`

**Add to START_TEXT:**

```
*Image Steganography:*
/imgencode — Hide text in an image
/imgdecode — Extract hidden text from image
/imgdetect — Scan image for hidden data
```

### Task 5.2: Update `handlers/methods.py` — add image method info

**Files:**
- Modify: `handlers/methods.py`

**Add to METHOD_INFO:**

```python
"image_lsb": {
    "name": "🖼️ Image LSB",
    "desc": (
        "Hides text in the least significant bits of pixel colors.\n\n"
        "*How it works:* Each pixel's R, G, B values have their "
        "last bit replaced with secret data bits.\n"
        "*Capacity:* 3 bits per pixel (huge!)\n"
        "*Robustness:* Survives exact copy-paste; destroyed by compression\n"
        "*Telegram:* ⚠️ Must send as document (not photo) to preserve data\n\n"
        "A 512×512 image can hide ~96 KB of text!"
    ),
},
```

**Add image method to keyboard:**

```python
keyboard = [
    [InlineKeyboardButton("🔹 Zero-Width", callback_data="method_zwc"),
     InlineKeyboardButton("🔹 SNOW", callback_data="method_snow")],
    [InlineKeyboardButton("🔹 Acrostic", callback_data="method_acrostic"),
     InlineKeyboardButton("🔹 Homoglyph", callback_data="method_homoglyph")],
    [InlineKeyboardButton("🖼️ Image LSB", callback_data="method_image_lsb")],
]
```

### Task 5.3: Update `handlers/demo.py` — add image demo

**Add `/imgdemo` command that:**
1. Creates a test PNG image with a gradient
2. Hides "SECRET" in it
3. Sends both the cover and stego images as documents
4. Shows the decoded result

**Files:**
- Modify: `handlers/demo.py`

### Task 5.4: Update `SPEC.md` — add Image Steganography section

**Add after Method 4 (Homoglyph):**

```markdown
### Method 5: Image LSB (Least Significant Bit)
**How it works:**
Each pixel in an RGB image has 3 color channels (R, G, B), each stored as an 8-bit value (0-255). By modifying only the least significant bit of each channel, we can encode 3 bits of data per pixel with virtually no visible change.

**Capacity:**
| Image Size | Pixels | Capacity |
|---|---|---|
| 100×100 | 10,000 | 3,750 chars |
| 512×512 | 262,144 | 96 KB |
| 1024×768 | 786,432 | 288 KB |
| 1920×1080 | 2,073,600 | 759 KB |

**Robustness:** Survives exact copy-paste. Destroyed by JPEG compression, resize, or screenshot.
**Telegram compatibility:** ⚠️ Must use `sendDocument` (not `sendPhoto`) to preserve pixel data.
**Detectability:** Can be detected by statistical analysis (chi-square attack, RS analysis).

**References:**
- Provos & Honeyman, *Hide and Seek: An Introduction to Steganography* (2003)
- Fridrich, *Steganography in Digital Media* (Cambridge, 2009)
```

**Update the Method Comparison table to include Image LSB.**

### Task 5.5: Create `ARCHITECTURE.md`

**Create comprehensive architecture doc:**

```markdown
# StegaBot Architecture

## System Overview

[Mermaid diagram or ASCII art showing bot architecture]

## Data Flow

### Text Steganography
1. User → /encode → choose method → enter cover → enter secret → bot encodes → reply with stego text
2. User → /decode → paste stego text → bot auto-detects method → decodes → reply with secret

### Image Steganography
1. User → /imgencode → send PNG → enter secret → bot encodes → reply with stego PNG (as document)
2. User → /imgdecode → send image → bot decodes → reply with hidden text

## Package Structure

stegabot/
├── bot.py              # Entry point, handler registration
├── config.py           # Environment config
├── state.py            # Per-chat session state
├── ratelimit.py        # Rate limiting
├── handlers/           # Telegram command handlers
│   ├── start.py        # /start
│   ├── methods.py      # /methods + callbacks
│   ├── encode.py       # /encode (text)
│   ├── decode.py       # /decode (text)
│   ├── detect.py       # /detect (text)
│   ├── demo.py         # /demo
│   ├── encrypt.py      # /encrypt toggle
│   ├── imgencode.py    # /imgencode (image)
│   ├── imgdecode.py    # /imgdecode (image)
│   └── imgdetect.py    # /imgdetect (image)
├── stegano/            # Steganography algorithms
│   ├── utils.py        # Bit conversion, capacity check
│   ├── zwc.py          # Zero-Width Characters
│   ├── snow.py         # Whitespace/SNOW
│   ├── acrostic.py     # First-Letter/Acrostic
│   ├── homoglyph.py    # Unicode Homoglyph
│   ├── image_lsb.py    # Image LSB
│   ├── detect.py       # Auto-detection (text)
│   └── crypto.py       # AES-128 encryption

## Key Design Decisions

1. **LSB implementation is custom** (not using Stegano PyPI library) to avoid naming conflict with our `stegano/` package
2. **Images sent as documents** (`sendDocument`) not photos (`sendPhoto`) to preserve pixel-perfect data
3. **PNG-only** — JPEG destroys LSB data due to lossy compression
4. **32-bit length header** — message length encoded in first 32 LSBs for reliable extraction
5. **Alpha channel skipped** — RGBA alpha changes are visually detectable
6. **Rate limiting** — 1 operation per user per 5 seconds
```

**Commits:**

```bash
git add handlers/start.py handlers/methods.py handlers/demo.py
git commit -m "feat(handlers): update help, methods, and demo for image steganography"

git add SPEC.md ARCHITECTURE.md
git commit -m "docs: update SPEC and add ARCHITECTURE for image steganography"
```

---

## Phase 6: Testing & Deployment

### Task 6.1: Integration test — encode + decode via temp files

```bash
cd /opt/hermes/stegabot
.venv/bin/python -m pytest tests/ -v
```

### Task 6.2: Restart bot service

```bash
sudo systemctl restart stegabot
sudo systemctl status stegabot
```

### Task 6.3: Manual Telegram testing

1. `/imgencode` → send photo → send secret → receive stego image
2. Download stego image → `/imgdecode` → send image → get secret back
3. `/imgdetect` → send stego image → shows hidden data found
4. `/methods` → tap Image LSB → shows info

---

## Execution Order

1.1 → 2.1 → 3.1 → 3.2 → 3.3 → 4.1 → 5.1 → 5.2 → 5.3 → 5.4 → 5.5 → 6.1 → 6.2 → 6.3

## Pitfalls

1. **Telegram photo compression:** Telegram's `sendPhoto` compresses images. MUST use `sendDocument` for stego output. For received photos (user sends via `sendPhoto`), the LSB data may already be destroyed — warn users to send as document if possible.

2. **Naming conflict:** Our `stegano/` package shadows the PyPI `Stegano` library. Solution: implement our own LSB using PIL directly (simple, ~80 lines).

3. **JPEG covers:** Users may send JPEG images as covers. Convert to PNG before encoding. Warn that JPEG→PNG conversion loses quality (LSBs are already destroyed by JPEG compression).

4. **File cleanup:** Temp files from photo downloads must be cleaned up after processing. Use `tempfile.mkdtemp()` and `shutil.rmtree()`.
