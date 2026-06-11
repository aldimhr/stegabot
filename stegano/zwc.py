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
