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
    if not secret:
        return cover
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
