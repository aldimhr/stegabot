"""Unicode Variation Selector steganography.

Hides data using invisible Unicode Variation Selectors (U+FE00-U+FE0F, U+E0100-U+E01EF).
Each variation selector encodes 1 byte (256 values) — 8x capacity vs zero-width characters.

The stego text looks identical to the cover text. Variation selectors are invisible
in all major platforms (Telegram, WhatsApp, Discord, browsers).

Algorithm:
  - Byte 0-15   → U+FE00 + byte   (VS1-VS16)
  - Byte 16-255 → U+E0100 + (byte - 16) (VS17-VS256)

VS characters are inserted after each word boundary (space) in the cover text.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Unicode ranges
VS_BASIC_START = 0xFE00      # VS1
VS_BASIC_END = 0xFE0F        # VS16  (16 selectors, encodes 0-15)
VS_EXTENDED_START = 0xE0100   # VS17
VS_EXTENDED_END = 0xE01EF     # VS256 (240 selectors, encodes 16-255)

# Regex to match all variation selectors
VS_PATTERN = re.compile(r'[\uFE00-\uFE0F]|[\U000E0100-\U000E01EF]')

# Separator used for inserting VS chars (after each space)
SEPARATOR = " "


def _byte_to_vs(b: int) -> str:
    """Convert a byte (0-255) to a variation selector character."""
    if b < 16:
        return chr(VS_BASIC_START + b)
    else:
        return chr(VS_EXTENDED_START + (b - 16))


def _vs_to_byte(ch: str) -> int | None:
    """Convert a variation selector character back to a byte. Returns None if not a VS."""
    cp = ord(ch)
    if VS_BASIC_START <= cp <= VS_BASIC_END:
        return cp - VS_BASIC_START
    elif VS_EXTENDED_START <= cp <= VS_EXTENDED_END:
        return (cp - VS_EXTENDED_START) + 16
    return None


def encode_vs(cover: str, secret: str) -> str:
    """Hide a secret message in cover text using Variation Selectors.

    VS characters are inserted after each space in the cover text.
    Each VS encodes 1 byte of the UTF-8 encoded secret.

    Args:
        cover: Cover text (must have enough word boundaries)
        secret: Secret message to hide

    Returns:
        Cover text with invisible VS characters inserted

    Raises:
        ValueError: If cover text doesn't have enough word boundaries
    """
    if not secret:
        return cover

    secret_bytes = secret.encode("utf-8")

    # Count available insertion points (spaces in cover text)
    spaces = [i for i, ch in enumerate(cover) if ch == SEPARATOR]
    if len(spaces) < len(secret_bytes):
        raise ValueError(
            f"Cover text needs at least {len(secret_bytes)} word boundaries, "
            f"but only has {len(spaces)}. Use a longer cover text or shorter secret."
        )

    # Build result: insert VS chars after spaces
    result = []
    byte_idx = 0
    for i, ch in enumerate(cover):
        result.append(ch)
        if ch == SEPARATOR and byte_idx < len(secret_bytes):
            result.append(_byte_to_vs(secret_bytes[byte_idx]))
            byte_idx += 1

    logger.info(f"VS encode: {len(secret_bytes)} bytes hidden in {len(spaces)} word boundaries")
    return "".join(result)


def decode_vs(text: str) -> str:
    """Extract hidden message from text containing Variation Selectors.

    Args:
        text: Text potentially containing VS-encoded secret

    Returns:
        Decoded secret message, or empty string if no VS data found
    """
    # Extract all VS characters and convert to bytes
    secret_bytes = bytearray()
    for ch in text:
        b = _vs_to_byte(ch)
        if b is not None:
            secret_bytes.append(b)

    if not secret_bytes:
        return ""

    try:
        return secret_bytes.decode("utf-8", errors="replace")
    except Exception:
        return ""


def has_vs_data(text: str) -> bool:
    """Check if text contains Variation Selector steganography data.

    Args:
        text: Text to check

    Returns:
        True if VS characters are found
    """
    return bool(VS_PATTERN.search(text))


def vs_capacity(cover: str) -> int:
    """Calculate how many bytes can be hidden in the cover text.

    Args:
        cover: Cover text to check

    Returns:
        Number of bytes that can be hidden (= number of spaces)
    """
    return cover.count(SEPARATOR)
