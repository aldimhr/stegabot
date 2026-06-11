"""LSB (Least Significant Bit) image steganography.

Hides text in the least significant bits of pixel color channels.
Works with RGB and RGBA PNG images.

Message format:
  [32-bit length header][UTF-8 message bits]

Capacity:
  RGB: width * height * 3 bits (minus 32 for header)
  RGBA: width * height * 3 bits (alpha skipped — visual detectability)
"""
from PIL import Image


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


def capacity_lsb(image_path: str) -> dict:
    """Calculate LSB capacity of an image.

    Returns dict with: pixels, channels, capacity_bits, usable_bits, capacity_chars.
    """
    img = Image.open(image_path)
    w, h = img.size
    channels = 3  # Always R, G, B (skip alpha)
    total_bits = w * h * channels
    usable_bits = total_bits - 32  # Subtract 32-bit header
    return {
        'pixels': w * h,
        'channels': channels,
        'capacity_bits': total_bits,
        'usable_bits': usable_bits,
        'capacity_chars': usable_bits // 8,
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

    # Encode message as bits
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
        r, g, b = pixel[:3]
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
        Decoded secret message (empty string if none found)
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
