"""Auto-detect which steganography method is present in text."""
from typing import Optional

ZWC_CHARS = {'\u200B', '\u200C', '\u200D', '\uFEFF'}
CYRILLIC_LOOKALIKES = set('\u0430\u0435\u043E\u0440\u0441\u0445')

# Variation Selector ranges
VS_BASIC = range(0xFE00, 0xFE0F + 1)
VS_EXTENDED = range(0xE0100, 0xE01EF + 1)

# Emoji pool from stegano.emoji (lazy import to avoid circular)
_EMOJI_POOL_EMOJI = None


def _get_emoji_pool():
    global _EMOJI_POOL_EMOJI
    if _EMOJI_POOL_EMOJI is None:
        from stegano.emoji import EMOJI_INDEX
        _EMOJI_POOL_EMOJI = set(EMOJI_INDEX.keys())
    return _EMOJI_POOL_EMOJI


def detect_method(text: str) -> Optional[str]:
    """Scan text for hidden data and return the detected method name.

    Returns: 'zwc' | 'snow' | 'homoglyph' | 'variation_selector' | 'emoji' | None
    """
    if not text:
        return None

    # Check for zero-width characters
    if any(c in ZWC_CHARS for c in text):
        return 'zwc'

    # Check for Variation Selectors
    if any(ord(c) in VS_BASIC or ord(c) in VS_EXTENDED for c in text):
        return 'variation_selector'

    # Check for emoji steganography (2+ pool emoji)
    pool = _get_emoji_pool()
    emoji_count = sum(1 for c in text if c in pool)
    if emoji_count >= 2:
        return 'emoji'

    # Check for Cyrillic homoglyphs
    if any(c in CYRILLIC_LOOKALIKES for c in text):
        return 'homoglyph'

    # Check for trailing whitespace (SNOW)
    lines = text.split('\n')
    if any(line.endswith('\t') or (line.endswith('  ') and len(line.rstrip()) < len(line))
           for line in lines):
        return 'snow'

    return None
