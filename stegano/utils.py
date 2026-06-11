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
        'zwc': len(cover),                          # 1 bit per char position
        'snow': cover.count('\n'),                   # 1 bit per line
        'acrostic': len(cover.split()) * 8,          # 1 char (8 bits) per word
        'homoglyph': sum(1 for c in cover if c.lower() in HOMOGLYPHS),  # 1 bit per eligible letter
    }
    cap = cover_capacity.get(method, 0)
    return {
        'enough': cap >= secret_bits,
        'capacity_bits': cap,
        'needed_bits': secret_bits,
        'utilization': secret_bits / cap if cap > 0 else float('inf'),
    }


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
        'image_pixels': cap['pixels'],
    }
