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
