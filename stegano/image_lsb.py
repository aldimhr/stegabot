"""LSB (Least Significant Bit) image steganography.

Hides text in the least significant bits of pixel color channels.
Works with RGB and RGBA PNG images.

Features:
  - Configurable LSB depth (1-3 bits per channel)
  - Gzip compression for large secrets
  - Alpha channel support for RGBA images

Message format (all bits encoded at the same depth):
  [8-byte header][payload bytes]

Header (8 bytes = 64 bits, always at depth=1 in first pixels):
  Byte 0-1: Magic "LS" (0x4C53)
  Byte 2:   Version (0x01)
  Byte 3:   Flags: bit 0=compressed, bit 1=alpha_used, bits 2-3=depth-1
  Byte 4-7: Payload bit length (32-bit big-endian)

After header pixels, payload is encoded at configured depth.
"""
import gzip
import logging
from PIL import Image

logger = logging.getLogger(__name__)

HEADER_SIZE_BYTES = 8
HEADER_SIZE_BITS = HEADER_SIZE_BYTES * 8  # 64 bits
MAGIC = b'LS'
VERSION = 1


def _bytes_to_bits(data: bytes) -> list[int]:
    """Convert bytes to bit list (MSB first per byte)."""
    result = []
    for byte in data:
        result.extend((byte >> (7 - i)) & 1 for i in range(8))
    return result


def _bits_to_bytes(bits: list[int]) -> bytes:
    """Convert bit list back to bytes."""
    if len(bits) < 8:
        return b''
    chars = []
    for i in range(0, len(bits) - 7, 8):
        byte = int(''.join(str(b) for b in bits[i:i+8]), 2)
        chars.append(byte)
    return bytes(chars)


def _int_to_bits(n: int, width: int = 32) -> list[int]:
    """Convert integer to fixed-width bit list."""
    return [(n >> (width - 1 - i)) & 1 for i in range(width)]


def _bits_to_int(bits: list[int]) -> int:
    """Convert bit list to integer."""
    result = 0
    for b in bits:
        result = (result << 1) | b
    return result


def _build_header(payload_bit_len: int, depth: int, compressed: bool, alpha_used: bool) -> bytes:
    """Build the 8-byte magic header."""
    flags = 0
    if compressed:
        flags |= 0x01
    if alpha_used:
        flags |= 0x02
    flags |= ((depth - 1) & 0x03) << 2
    return MAGIC + bytes([VERSION, flags]) + payload_bit_len.to_bytes(4, 'big')


def _parse_header(header_bytes: bytes) -> dict | None:
    """Parse the 8-byte magic header. Returns header info or None if invalid."""
    if len(header_bytes) < HEADER_SIZE_BYTES:
        return None
    if header_bytes[:2] != MAGIC:
        return None
    version = header_bytes[2]
    if version != VERSION:
        return None
    flags = header_bytes[3]
    compressed = bool(flags & 0x01)
    alpha_used = bool(flags & 0x02)
    depth = ((flags >> 2) & 0x03) + 1
    payload_bit_len = int.from_bytes(header_bytes[4:8], 'big')
    return {
        'depth': depth,
        'compressed': compressed,
        'alpha_used': alpha_used,
        'payload_bit_len': payload_bit_len,
    }


def _embed_bits_into_pixels(pixels: list[tuple], all_bits: list[int],
                            depth: int, num_channels: int) -> list[tuple]:
    """Embed bits into pixel LSBs at given depth."""
    lsb_mask = (0xFF << depth) & 0xFF  # e.g., depth=2 → 0xFC
    bit_idx = 0
    new_pixels = []
    for pixel in pixels:
        channels = list(pixel)
        for ch_idx in range(min(len(channels), num_channels)):
            if bit_idx >= len(all_bits):
                break
            val = 0
            for d in range(depth):
                if bit_idx < len(all_bits):
                    val = (val << 1) | all_bits[bit_idx]
                    bit_idx += 1
                else:
                    val = (val << 1)
            channels[ch_idx] = (channels[ch_idx] & lsb_mask) | val
        new_pixels.append(tuple(channels))
    return new_pixels


def _extract_bits_from_pixels(pixels: list[tuple], depth: int,
                              num_channels: int, max_bits: int) -> list[int]:
    """Extract LSBs from pixels at given depth."""
    bits = []
    for pixel in pixels:
        for ch_idx in range(min(len(pixel), num_channels)):
            # Extract bits MSB-first (depth-1 down to 0) to match embed order
            for d in range(depth - 1, -1, -1):
                bits.append((pixel[ch_idx] >> d) & 1)
                if len(bits) >= max_bits:
                    return bits
    return bits


def capacity_lsb(image_path: str, depth: int = 1, use_alpha: bool = False) -> dict:
    """Calculate LSB capacity of an image.

    Args:
        image_path: Path to image
        depth: Bits per channel (1-3)
        use_alpha: Whether to use alpha channel (RGBA only)
    """
    img = Image.open(image_path)
    w, h = img.size
    has_alpha = img.mode == 'RGBA'
    channels = 3 + (1 if use_alpha and has_alpha else 0)
    total_bits = w * h * channels * depth
    header_bits = HEADER_SIZE_BITS  # Header at depth=1
    usable_bits = total_bits - header_bits
    return {
        'pixels': w * h,
        'channels': channels,
        'depth': depth,
        'capacity_bits': total_bits,
        'usable_bits': usable_bits,
        'capacity_chars': usable_bits // 8,
    }


def encode_lsb(cover_path: str, secret: str, output_path: str,
               depth: int = 1, compress: bool = True, use_alpha: bool = False) -> str:
    """Hide secret message in image using LSB encoding.

    Args:
        cover_path: Path to cover image (PNG)
        secret: Secret text to hide
        output_path: Path to save stego image (PNG)
        depth: Bits per channel (1-3). Higher = more capacity, slightly more detectable.
        compress: Whether to gzip-compress the secret before encoding
        use_alpha: Whether to use alpha channel (RGBA images only)

    Returns:
        Path to stego image

    Raises:
        ValueError: If secret is too long for the image
    """
    if depth < 1 or depth > 3:
        raise ValueError("depth must be 1, 2, or 3")

    img = Image.open(cover_path)
    has_alpha = img.mode == 'RGBA'
    if has_alpha:
        img = img.convert('RGBA')
    else:
        img = img.convert('RGB')
        use_alpha = False

    pixels = list(img.getdata())
    w, h = img.size
    num_channels = 3 + (1 if use_alpha else 0)

    # Compress if requested
    raw_bytes = secret.encode('utf-8')
    is_compressed = False
    if compress and len(raw_bytes) > 50:
        compressed = gzip.compress(raw_bytes, compresslevel=9)
        if len(compressed) < len(raw_bytes):
            payload_bytes = compressed
            is_compressed = True
        else:
            payload_bytes = raw_bytes
    else:
        payload_bytes = raw_bytes

    payload_bits = _bytes_to_bits(payload_bytes)
    payload_bit_len = len(payload_bits)

    # Check capacity
    total_capacity = w * h * num_channels * depth
    needed_bits = HEADER_SIZE_BITS + payload_bit_len

    logger.info(f"Encode: depth={depth}, compressed={is_compressed}, alpha={use_alpha}")
    logger.info(f"Payload: {len(raw_bytes)} raw bytes → {len(payload_bytes)} encoded bytes → {payload_bit_len} bits")
    logger.info(f"Capacity: {total_capacity} bits, need {needed_bits} bits")

    if needed_bits > total_capacity:
        raise ValueError(
            f"Secret too long: need {needed_bits} bits, "
            f"image has {total_capacity} bits capacity"
        )

    # Step 1: Encode header at depth=1 in first pixels
    header_bytes = _build_header(payload_bit_len, depth, is_compressed, use_alpha)
    header_bits_list = _bytes_to_bits(header_bytes)  # 64 bits

    # How many pixels for header at depth=1, 3 channels?
    header_pixels_needed = (HEADER_SIZE_BITS + 2) // 3  # ceil(64/3) = 22 pixels

    # Embed header at depth=1
    header_pixels = pixels[:header_pixels_needed]
    new_header_pixels = _embed_bits_into_pixels(header_pixels, header_bits_list, depth=1, num_channels=3)

    # Step 2: Encode payload at configured depth in remaining pixels
    remaining_pixels = pixels[header_pixels_needed:]
    new_payload_pixels = _embed_bits_into_pixels(remaining_pixels, payload_bits, depth=depth, num_channels=num_channels)

    # Combine
    all_new_pixels = new_header_pixels + new_payload_pixels

    # Create stego image
    stego = Image.new(img.mode, img.size)
    stego.putdata(all_new_pixels)
    stego.save(output_path, format='PNG')
    return output_path


def decode_lsb(stego_path: str) -> str:
    """Extract hidden message from stego image.

    Automatically detects depth, compression, and alpha from the header.

    Args:
        stego_path: Path to stego image

    Returns:
        Decoded secret message (empty string if none found)
    """
    img = Image.open(stego_path)
    has_alpha = img.mode == 'RGBA'
    if has_alpha:
        img = img.convert('RGBA')
    else:
        img = img.convert('RGB')

    pixels = list(img.getdata())

    # Step 1: Extract header at depth=1 from first pixels (always 3 channels, depth=1)
    header_pixels_needed = (HEADER_SIZE_BITS + 2) // 3  # 22 pixels
    header_bits = _extract_bits_from_pixels(
        pixels[:header_pixels_needed], depth=1, num_channels=3, max_bits=HEADER_SIZE_BITS
    )
    header_bytes = _bits_to_bytes(header_bits)

    header = _parse_header(header_bytes)
    if header is None:
        logger.debug("No valid header found")
        return ""

    depth = header['depth']
    is_compressed = header['compressed']
    alpha_used = header['alpha_used']
    payload_bit_len = header['payload_bit_len']

    logger.info(f"Decode: depth={depth}, compressed={is_compressed}, alpha={alpha_used}, payload_bits={payload_bit_len}")

    num_channels = 3 + (1 if alpha_used and has_alpha else 0)

    # Step 2: Extract payload at configured depth from remaining pixels
    remaining_pixels = pixels[header_pixels_needed:]
    max_bits_needed = payload_bit_len + depth  # Extra bits for safety
    payload_bits = _extract_bits_from_pixels(
        remaining_pixels, depth=depth, num_channels=num_channels, max_bits=max_bits_needed
    )

    if len(payload_bits) < payload_bit_len:
        logger.warning(f"Not enough bits: got {len(payload_bits)}, need {payload_bit_len}")
        return ""

    payload_bits = payload_bits[:payload_bit_len]
    payload_bytes = _bits_to_bytes(payload_bits)

    if is_compressed:
        try:
            payload_bytes = gzip.decompress(payload_bytes)
        except Exception as e:
            logger.warning(f"Gzip decompress failed: {e}")
            return ""

    return payload_bytes.decode('utf-8', errors='replace')
