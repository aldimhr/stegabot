"""Emoji-based steganography.

Hides data in emoji sequences using an indexed emoji pool.
Each emoji encodes 6 bits (64 values from the pool).
Additional bits come from skin tone modifiers (5 values = ~2.3 extra bits).

The output is a sequence of emoji that looks like casual emoji usage.
No visible text — just emoji hiding data in plain sight.

Algorithm:
  1. Convert secret → bytes → stream of 6-bit chunks
  2. Each chunk selects an emoji from a 64-emoji pool
  3. Optionally add skin tone modifier for extra bits
  4. Output: emoji sequence

Capacity: ~6 bits per emoji → 10 emoji hide ~7 bytes
"""
import logging

logger = logging.getLogger(__name__)

# 64-emoji pool — common, distinct emoji that work across platforms
EMOJI_POOL = {
    0: "😀", 1: "😂", 2: "😍", 3: "🤔", 4: "😎", 5: "🥳", 6: "😱", 7: "🤩",
    8: "🐶", 9: "🐱", 10: "🐸", 11: "🦊", 12: "🐻", 13: "🐼", 14: "🦁", 15: "🐮",
    16: "🍎", 17: "🍊", 18: "🍋", 19: "🍇", 20: "🍓", 21: "🍒", 22: "🌽", 23: "🥕",
    24: "⚽", 25: "🏀", 26: "🎾", 27: "🏐", 28: "🎱", 29: "🎯", 30: "🎮", 31: "🎲",
    32: "🌹", 33: "🌻", 34: "🌸", 35: "🍄", 36: "⭐", 37: "🌙", 38: "☀️", 39: "❄️",
    40: "🚗", 41: "🚀", 42: "✈️", 43: "🚂", 44: "🏠", 45: "🗼", 46: "🎡", 47: "🎪",
    48: "❤️", 49: "💔", 50: "💯", 51: "✅", 52: "❌", 53: "⚡", 54: "🔥", 55: "💧",
    56: "🎵", 57: "🎸", 58: "🥁", 59: "🎺", 60: "📱", 61: "💻", 62: "📷", 63: "🔑",
}

# Reverse mapping: emoji → index
EMOJI_INDEX = {v: k for k, v in EMOJI_POOL.items()}

# Skin tone modifiers (Fitzpatrick scale) — encode extra bits
SKIN_TONES = [
    "\U0001F3FB",  # Light
    "\U0001F3FC",  # Medium-Light
    "\U0001F3FD",  # Medium
    "\U0001F3FE",  # Medium-Dark
    "\U0001F3FF",  # Dark
]
SKIN_TONE_INDEX = {t: i for i, t in enumerate(SKIN_TONES)}

POOL_BITS = 6  # 2^6 = 64 emoji
SKIN_BITS = 2  # 5 values ≈ 2.3 bits, we use 2


def encode_emoji(secret: str, max_emoji: int = 200) -> str:
    """Encode a secret message as an emoji sequence.

    Args:
        secret: Message to hide
        max_emoji: Maximum number of emoji in output

    Returns:
        Emoji sequence encoding the secret

    Raises:
        ValueError: If secret is too long for max_emoji
    """
    if not secret:
        return ""

    secret_bytes = secret.encode("utf-8")

    # Convert bytes to bit stream
    bits = []
    for byte in secret_bytes:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    # Calculate capacity: max_emoji * (POOL_BITS + SKIN_BITS) bits
    bits_per_emoji = POOL_BITS + SKIN_BITS
    max_bits = max_emoji * bits_per_emoji

    if len(bits) > max_bits:
        raise ValueError(
            f"Secret too long: need {len(bits)} bits, "
            f"max capacity is {max_bits} bits ({max_emoji} emoji)"
        )

    # Encode bits into emoji
    result = []
    for i in range(0, len(bits), bits_per_emoji):
        chunk = bits[i : i + bits_per_emoji]

        # Pool index: first POOL_BITS bits
        pool_bits = chunk[:POOL_BITS]
        while len(pool_bits) < POOL_BITS:
            pool_bits.append(0)
        pool_idx = 0
        for b in pool_bits:
            pool_idx = (pool_idx << 1) | b

        emoji = EMOJI_POOL[pool_idx]
        result.append(emoji)

        # Skin tone: next SKIN_BITS bits (if available)
        if len(chunk) > POOL_BITS:
            skin_bits = chunk[POOL_BITS:]
            if len(skin_bits) >= 2:
                skin_idx = (skin_bits[0] << 1) | skin_bits[1]
                if skin_idx < len(SKIN_TONES):
                    result.append(SKIN_TONES[skin_idx])

    # Add a terminator emoji (index 63 = 🔑) to mark end of data
    result.append(EMOJI_POOL[63])

    logger.info(f"Emoji encode: {len(secret_bytes)} bytes → {len(result)} emoji")
    return "".join(result)


def decode_emoji(text: str) -> str:
    """Extract hidden message from emoji sequence.

    Args:
        text: Emoji sequence from encode_emoji()

    Returns:
        Decoded secret message, or empty string if no data found
    """
    bits = []
    found_data = False

    i = 0
    chars = list(text)
    while i < len(chars):
        ch = chars[i]

        # Check if it's a pool emoji
        if ch in EMOJI_INDEX:
            idx = EMOJI_INDEX[ch]

            # Check for terminator
            if idx == 63 and found_data:
                break

            found_data = True

            # Extract 6 bits from pool index
            for bit_pos in range(POOL_BITS - 1, -1, -1):
                bits.append((idx >> bit_pos) & 1)

            # Check next char for skin tone modifier
            if i + 1 < len(chars) and chars[i + 1] in SKIN_TONE_INDEX:
                skin_idx = SKIN_TONE_INDEX[chars[i + 1]]
                bits.append((skin_idx >> 1) & 1)
                bits.append(skin_idx & 1)
                i += 1  # Skip skin tone

        i += 1

    if not bits:
        return ""

    # Convert bits to bytes
    secret_bytes = bytearray()
    for byte_start in range(0, len(bits), 8):
        byte_bits = bits[byte_start : byte_start + 8]
        if len(byte_bits) < 8:
            break
        byte_val = 0
        for b in byte_bits:
            byte_val = (byte_val << 1) | b
        secret_bytes.append(byte_val)

    try:
        return secret_bytes.decode("utf-8", errors="replace")
    except Exception:
        return ""


def has_emoji_data(text: str) -> bool:
    """Check if text contains emoji steganography data.

    Looks for sequences of pool emoji (not just any emoji).

    Args:
        text: Text to check

    Returns:
        True if emoji stego data is detected
    """
    pool_count = sum(1 for ch in text if ch in EMOJI_INDEX)
    # Require at least 2 pool emoji to be considered stego data
    return pool_count >= 2


def emoji_capacity(num_emoji: int) -> int:
    """Calculate how many bytes can be hidden in N emoji.

    Args:
        num_emoji: Number of emoji positions

    Returns:
        Number of bytes that can be hidden
    """
    total_bits = num_emoji * (POOL_BITS + SKIN_BITS)
    return total_bits // 8
