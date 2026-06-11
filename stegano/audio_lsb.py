"""Audio LSB (Least Significant Bit) steganography.

Hides text data in the least significant bits of 16-bit PCM audio samples.
Works with WAV files — send as document on Telegram to preserve quality.

Capacity: ~1000 bytes per second of audio (8kHz mono).

Format:
  - First 32 samples: 32-bit length header (number of payload bits)
  - Remaining samples: payload bits in LSB of each sample
"""
import logging
import numpy as np
from scipy.io import wavfile

logger = logging.getLogger(__name__)

HEADER_BITS = 32  # 32-bit length header


def _bytes_to_bits(data: bytes) -> list[int]:
    """Convert bytes to bit list (MSB first)."""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def _bits_to_bytes(bits: list[int]) -> bytes:
    """Convert bit list to bytes."""
    result = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte_val = 0
        for j in range(8):
            byte_val = (byte_val << 1) | bits[i + j]
        result.append(byte_val)
    return bytes(result)


def encode_audio(input_path: str, secret: str, output_path: str) -> str:
    """Hide a secret message in audio using LSB encoding.

    Args:
        input_path: Path to input WAV file (16-bit PCM)
        secret: Secret message to hide
        output_path: Path to save stego WAV file

    Returns:
        Path to stego audio file

    Raises:
        ValueError: If secret is too long for the audio
    """
    sample_rate, audio = wavfile.read(input_path)

    # Ensure int16
    if audio.dtype != np.int16:
        audio = audio.astype(np.int16)

    # Flatten to mono if stereo
    if audio.ndim > 1:
        audio = audio[:, 0]

    total_samples = len(audio)
    logger.info(f"Audio: {total_samples} samples, {sample_rate}Hz, {total_samples/sample_rate:.1f}s")

    if not secret:
        # Write zero-length header to signal "no data"
        stego = audio.copy()
        for i in range(HEADER_BITS):
            stego[i] = stego[i] & np.int16(-2)  # Clear LSB
        wavfile.write(output_path, sample_rate, stego)
        return output_path

    secret_bytes = secret.encode("utf-8")
    payload_bits = _bytes_to_bits(secret_bytes)
    payload_bit_len = len(payload_bits)

    # Check capacity
    available_samples = total_samples - HEADER_BITS
    if payload_bit_len > available_samples:
        raise ValueError(
            f"Secret too long: need {payload_bit_len} bits, "
            f"audio has {available_samples} usable bits "
            f"({available_samples // 8} bytes)"
        )

    # Build all bits: header (32-bit length) + payload
    header_bits = []
    for i in range(31, -1, -1):
        header_bits.append((payload_bit_len >> i) & 1)
    all_bits = header_bits + payload_bits

    # Embed bits into audio samples using numpy operations
    stego = audio.copy()
    for i, bit in enumerate(all_bits):
        stego[i] = (stego[i] & np.int16(-2)) | np.int16(bit)

    wavfile.write(output_path, sample_rate, stego)
    logger.info(f"Audio encode: {len(secret_bytes)} bytes → {len(all_bits)} samples modified")
    return output_path


def decode_audio(audio_path: str) -> str:
    """Extract hidden message from stego audio.

    Args:
        audio_path: Path to stego WAV file

    Returns:
        Decoded secret message, or empty string if no data found
    """
    _, audio = wavfile.read(audio_path)

    if audio.dtype != np.int16:
        audio = audio.astype(np.int16)

    if audio.ndim > 1:
        audio = audio[:, 0]

    total_samples = len(audio)
    if total_samples < HEADER_BITS:
        return ""

    # Extract header (32-bit length)
    header_bits = []
    for i in range(HEADER_BITS):
        header_bits.append(audio[i] & 1)

    payload_bit_len = 0
    for bit in header_bits:
        payload_bit_len = (payload_bit_len << 1) | bit

    if payload_bit_len == 0 or payload_bit_len > total_samples - HEADER_BITS:
        return ""

    # Extract payload
    payload_bits = []
    for i in range(HEADER_BITS, HEADER_BITS + payload_bit_len):
        payload_bits.append(audio[i] & 1)

    payload_bytes = _bits_to_bytes(payload_bits)

    try:
        return payload_bytes.decode("utf-8", errors="replace")
    except Exception:
        return ""


def has_audio_data(audio_path: str) -> bool:
    """Check if audio file contains LSB steganography data.

    Reads the 32-bit header and validates the length field.
    Uses a simple heuristic: valid length should be > 8 and < available samples.

    Args:
        audio_path: Path to WAV file

    Returns:
        True if valid LSB header is found
    """
    try:
        _, audio = wavfile.read(audio_path)
        if audio.dtype != np.int16:
            audio = audio.astype(np.int16)
        if audio.ndim > 1:
            audio = audio[:, 0]

        if len(audio) < HEADER_BITS:
            return False

        # Extract header
        header_bits = []
        for i in range(HEADER_BITS):
            header_bits.append(audio[i] & 1)

        payload_bit_len = 0
        for bit in header_bits:
            payload_bit_len = (payload_bit_len << 1) | bit

        # Valid if length is reasonable (>8 for at least 1 byte, < available samples)
        # Also check that the decoded text looks like valid UTF-8
        if payload_bit_len < 8 or payload_bit_len > len(audio) - HEADER_BITS:
            return False

        # Try to decode the payload to verify it's real data
        payload_bits = []
        for i in range(HEADER_BITS, HEADER_BITS + min(payload_bit_len, 1000)):
            payload_bits.append(audio[i] & 1)
        payload_bytes = _bits_to_bytes(payload_bits)
        try:
            payload_bytes.decode("utf-8")
            return True
        except Exception:
            return False
    except Exception:
        return False


def audio_capacity(audio_path: str) -> int:
    """Calculate how many bytes can be hidden in the audio file.

    Args:
        audio_path: Path to WAV file

    Returns:
        Number of bytes that can be hidden
    """
    _, audio = wavfile.read(audio_path)
    if audio.ndim > 1:
        audio = audio[:, 0]
    total_samples = len(audio)
    usable_bits = total_samples - HEADER_BITS
    return max(0, usable_bits // 8)
