"""
Secure LSB (Least Significant Bit) image steganography.

Security-hardened variant of image_lsb.py with:
  - NO magic header (everything encrypted — no plaintext markers)
  - Passphrase-derived start position (PBKDF2)
  - Scrambled pixel selection order (key-derived PRNG shuffle)
  - Full encryption of header + payload (Fernet/AES-128)

On disk layout (all in pixel LSBs, depth=1 for metadata):
  Pixels 0-4:  salt (16 bytes = 48 bits at depth=1, 3ch = 16 pixels)
  Pixels 5-7:  encrypted_blob_length (4 bytes = 32 bits at depth=1, 3ch = 11 pixels)
  Pixels 27+:  encrypted blob (at configured depth, in shuffled pixel order)

Decode strategy: try all depth×channel combos until Fernet decryption succeeds.
"""
import base64
import gzip
import logging
import os
import random as _random
from PIL import Image
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from stegano.image_lsb import (
    _bytes_to_bits, _bits_to_bytes, _embed_bits_into_pixels,
    _extract_bits_from_pixels, VERSION,
)

logger = logging.getLogger(__name__)

# Secure mode constants
SECURE_SALT_BYTES = 16
SECURE_LEN_BYTES = 4
SECURE_META_BYTES = SECURE_SALT_BYTES + SECURE_LEN_BYTES  # 20 bytes
SECURE_META_BITS = SECURE_META_BYTES * 8  # 160 bits
SECURE_PBKDF2_ITERATIONS = 100_000
SECURE_PBKDF2_KEY_LEN = 48  # 32 for Fernet + 16 for seeds


def _derive_secure_keys(passphrase: str, salt: bytes) -> dict:
    """Derive Fernet key + pixel seeds from passphrase and salt using PBKDF2.

    Returns dict with:
      - fernet_key: base64-encoded 32-byte key for Fernet
      - seed_a: 8 bytes → start position seed
      - seed_b: 8 bytes → PRNG seed for pixel shuffle
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=SECURE_PBKDF2_KEY_LEN,
        salt=salt,
        iterations=SECURE_PBKDF2_ITERATIONS,
    )
    derived = kdf.derive(passphrase.encode("utf-8"))
    return {
        "fernet_key": base64.urlsafe_b64encode(derived[:32]),
        "seed_a": derived[32:40],
        "seed_b": derived[40:48],
    }


def _derive_pixel_indices(seed_a: bytes, seed_b: bytes,
                          total_pixels: int, count: int,
                          skip_start: int = 0) -> list[int]:
    """Generate deterministic shuffled pixel indices from key seeds.

    1. Derive a start offset from seed_a
    2. Build a sequential list of pixel indices (wrapping around)
    3. Fisher-Yates shuffle using seed_b as PRNG seed
    4. Skip the first `skip_start` pixels (used for metadata)
    """
    # Start position derived from passphrase
    start = int.from_bytes(seed_a[:4], "big") % max(1, total_pixels - count)

    # Build candidate indices (avoiding metadata region)
    indices = []
    i = 0
    while len(indices) < count:
        idx = (start + i) % total_pixels
        if idx >= skip_start:  # Don't overwrite metadata pixels
            indices.append(idx)
        i += 1
        # Safety: if we looped through all pixels without finding enough
        if i > total_pixels * 2:
            raise ValueError("Not enough pixels for secure encoding")

    # Deterministic shuffle
    rng = _random.Random(seed_b)
    rng.shuffle(indices)
    return indices


def encode_lsb_secure(cover_path: str, secret: str, output_path: str,
                      passphrase: str, depth: int = 1,
                      compress: bool = True, use_alpha: bool = False) -> str:
    """Securely hide a secret in an image.

    Security features:
    - NO magic header → no plaintext markers to detect
    - PBKDF2 key derivation (100k iterations) → brute-force resistant
    - Passphrase-derived start position → data not at pixel 0
    - Scrambled pixel order → statistical analysis harder
    - Fernet AES-128 encryption of header+payload → everything encrypted

    Args:
        cover_path: Path to cover image (PNG)
        secret: Secret text to hide
        output_path: Path to save stego image (PNG)
        passphrase: Encryption passphrase (required)
        depth: Bits per channel (1-3)
        compress: Whether to gzip before encrypting
        use_alpha: Whether to use alpha channel (RGBA only)

    Returns:
        Path to stego image
    """
    if not passphrase:
        raise ValueError("Passphrase is required for secure mode")
    if depth < 1 or depth > 3:
        raise ValueError("depth must be 1, 2, or 3")

    img = Image.open(cover_path)
    has_alpha = img.mode == "RGBA"
    if has_alpha:
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")
        use_alpha = False

    pixels = list(img.getdata())
    w, h = img.size
    total_pixels = w * h
    num_channels = 3 + (1 if use_alpha else 0)

    # --- Build internal header (6 bytes, will be encrypted) ---
    raw_bytes = secret.encode("utf-8")
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

    flags = 0
    if is_compressed:
        flags |= 0x01
    if use_alpha:
        flags |= 0x02
    flags |= ((depth - 1) & 0x03) << 2

    internal_header = bytes([VERSION, flags]) + len(payload_bytes).to_bytes(4, "big")
    plaintext = internal_header + payload_bytes  # 6 + N bytes

    # --- Encrypt entire stream ---
    salt = os.urandom(SECURE_SALT_BYTES)
    keys = _derive_secure_keys(passphrase, salt)
    fernet = Fernet(keys["fernet_key"])
    encrypted_blob = fernet.encrypt(plaintext)
    blob_bits = _bytes_to_bits(encrypted_blob)
    blob_bit_len = len(blob_bits)

    # --- Capacity check ---
    meta_pixels_needed = (SECURE_META_BITS + 2) // 3  # ceil(160/3) = 54 pixels
    payload_bits_per_pixel = num_channels * depth
    payload_pixels_needed = (blob_bit_len + payload_bits_per_pixel - 1) // payload_bits_per_pixel

    if meta_pixels_needed + payload_pixels_needed > total_pixels:
        raise ValueError(
            f"Secret too long for image at depth={depth}: "
            f"need {meta_pixels_needed + payload_pixels_needed} pixels, "
            f"have {total_pixels}"
        )

    logger.info(
        f"Secure encode: depth={depth}, compressed={is_compressed}, "
        f"alpha={use_alpha}, salt_len={len(salt)}, "
        f"blob={len(encrypted_blob)} bytes, "
        f"payload_pixels={payload_pixels_needed}"
    )

    # --- Step 1: Embed metadata (salt + blob length) in first pixels at depth=1 ---
    meta_bytes = salt + len(encrypted_blob).to_bytes(SECURE_LEN_BYTES, "big")
    meta_bits = _bytes_to_bits(meta_bytes)
    new_meta_pixels = list(
        _embed_bits_into_pixels(pixels[:meta_pixels_needed], meta_bits, depth=1, num_channels=3)
    )

    # --- Step 2: Embed encrypted blob in shuffled pixel positions ---
    pixel_indices = _derive_pixel_indices(
        keys["seed_a"], keys["seed_b"],
        total_pixels, payload_pixels_needed,
        skip_start=meta_pixels_needed,
    )

    # Build the new pixel list (copy all pixels, then modify selected ones)
    all_new_pixels = list(pixels)
    # Overwrite metadata region
    for i in range(meta_pixels_needed):
        all_new_pixels[i] = new_meta_pixels[i]

    # Embed payload bits into shuffled pixels
    lsb_mask = (0xFF << depth) & 0xFF
    bit_idx = 0
    for pidx in pixel_indices:
        if bit_idx >= len(blob_bits):
            break
        channels = list(all_new_pixels[pidx])
        for ch_idx in range(min(len(channels), num_channels)):
            if bit_idx >= len(blob_bits):
                break
            val = 0
            for d in range(depth):
                if bit_idx < len(blob_bits):
                    val = (val << 1) | blob_bits[bit_idx]
                    bit_idx += 1
                else:
                    val = (val << 1)
            channels[ch_idx] = (channels[ch_idx] & lsb_mask) | val
        all_new_pixels[pidx] = tuple(channels)

    # --- Save ---
    stego = Image.new(img.mode, img.size)
    stego.putdata(all_new_pixels)
    stego.save(output_path, format="PNG")
    return output_path


def decode_lsb_secure(stego_path: str, passphrase: str) -> str:
    """Extract and decrypt a secret hidden with encode_lsb_secure.

    Automatically tries all depth×channel combinations until Fernet
    decryption succeeds (or all combinations are exhausted).

    Args:
        stego_path: Path to stego image
        passphrase: Decryption passphrase

    Returns:
        Decoded and decrypted secret message

    Raises:
        ValueError: If no valid message found or wrong passphrase
    """
    if not passphrase:
        raise ValueError("Passphrase is required for secure decode")

    img = Image.open(stego_path)
    has_alpha = img.mode == "RGBA"
    if has_alpha:
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    pixels = list(img.getdata())
    total_pixels = len(pixels)

    # --- Step 1: Extract metadata from first pixels at depth=1 ---
    meta_pixels_needed = (SECURE_META_BITS + 2) // 3  # 54 pixels
    meta_bits = _extract_bits_from_pixels(
        pixels[:meta_pixels_needed], depth=1, num_channels=3, max_bits=SECURE_META_BITS
    )
    meta_bytes = _bits_to_bytes(meta_bits)

    if len(meta_bytes) < SECURE_META_BYTES:
        raise ValueError("No secure message found (metadata too short)")

    salt = meta_bytes[:SECURE_SALT_BYTES]
    encrypted_len = int.from_bytes(meta_bytes[SECURE_SALT_BYTES:SECURE_META_BYTES], "big")

    if encrypted_len == 0 or encrypted_len > total_pixels * 4:
        raise ValueError("No secure message found (invalid encrypted length)")

    logger.info(f"Secure decode: salt={salt.hex()[:16]}..., encrypted_len={encrypted_len}")

    # --- Step 2: Derive keys ---
    keys = _derive_secure_keys(passphrase, salt)
    fernet = Fernet(keys["fernet_key"])

    # --- Step 3: Try all depth × channel combinations ---
    channel_options = [3]
    if has_alpha:
        channel_options.append(4)

    errors = []
    for try_depth in [1, 2, 3]:
        for num_channels in channel_options:
            payload_bits_per_pixel = num_channels * try_depth
            payload_pixels_needed = (encrypted_len * 8 + payload_bits_per_pixel - 1) // payload_bits_per_pixel

            if meta_pixels_needed + payload_pixels_needed > total_pixels:
                continue

            try:
                pixel_indices = _derive_pixel_indices(
                    keys["seed_a"], keys["seed_b"],
                    total_pixels, payload_pixels_needed,
                    skip_start=meta_pixels_needed,
                )

                # Extract bits from shuffled pixels
                extracted_bits = []
                bits_needed = encrypted_len * 8
                for pidx in pixel_indices:
                    if len(extracted_bits) >= bits_needed:
                        break
                    pixel = pixels[pidx]
                    for ch_idx in range(min(len(pixel), num_channels)):
                        for d in range(try_depth - 1, -1, -1):
                            extracted_bits.append((pixel[ch_idx] >> d) & 1)
                            if len(extracted_bits) >= bits_needed:
                                break

                extracted_bits = extracted_bits[:bits_needed]
                encrypted_blob = _bits_to_bytes(extracted_bits)

                # Try Fernet decryption (includes HMAC verification)
                plaintext = fernet.decrypt(encrypted_blob)

                # Success! Parse internal header
                if len(plaintext) < 6:
                    continue

                version = plaintext[0]
                flags = plaintext[1]
                is_compressed = bool(flags & 0x01)
                alpha_used = bool(flags & 0x02)
                actual_depth = ((flags >> 2) & 0x03) + 1

                # Verify depth matches what we extracted with
                if actual_depth != try_depth:
                    logger.debug(f"Depth mismatch: header={actual_depth}, tried={try_depth}")
                    continue

                payload_len = int.from_bytes(plaintext[2:6], "big")
                payload_bytes = plaintext[6 : 6 + payload_len]

                if is_compressed:
                    payload_bytes = gzip.decompress(payload_bytes)

                result = payload_bytes.decode("utf-8", errors="replace")
                logger.info(
                    f"Secure decode success: depth={try_depth}, "
                    f"channels={num_channels}, compressed={is_compressed}"
                )
                return result

            except InvalidToken:
                errors.append(f"depth={try_depth},ch={num_channels}: wrong passphrase or no data")
                continue
            except Exception as e:
                errors.append(f"depth={try_depth},ch={num_channels}: {e}")
                continue

    raise ValueError(
        "Decryption failed — wrong passphrase or no hidden message.\n"
        f"Tried {len(errors)} combinations."
    )
