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
