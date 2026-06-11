"""Tests for stegano.emoji — Emoji-based steganography."""
import unittest

from stegano.emoji import (
    encode_emoji,
    decode_emoji,
    has_emoji_data,
    emoji_capacity,
    EMOJI_POOL,
    EMOJI_INDEX,
    SKIN_TONE_INDEX,
)


class TestEmojiRoundtrip(unittest.TestCase):
    """Basic encode → decode roundtrip tests."""

    def test_short_secret(self):
        secret = "Hi"
        encoded = encode_emoji(secret)
        decoded = decode_emoji(encoded)
        self.assertEqual(decoded, secret)

    def test_single_char(self):
        secret = "A"
        encoded = encode_emoji(secret)
        decoded = decode_emoji(encoded)
        self.assertEqual(decoded, secret)

    def test_unicode_secret(self):
        secret = "你好"
        encoded = encode_emoji(secret)
        decoded = decode_emoji(encoded)
        self.assertEqual(decoded, secret)

    def test_empty_secret(self):
        encoded = encode_emoji("")
        self.assertEqual(encoded, "")
        self.assertEqual(decode_emoji(""), "")

    def test_all_ascii(self):
        secret = "Hello!"
        encoded = encode_emoji(secret)
        decoded = decode_emoji(encoded)
        self.assertEqual(decoded, secret)

    def test_long_secret(self):
        secret = "A" * 50
        encoded = encode_emoji(secret)
        decoded = decode_emoji(encoded)
        self.assertEqual(decoded, secret)


class TestEmojiVisibility(unittest.TestCase):
    """Verify output looks like emoji."""

    def test_output_is_emoji(self):
        encoded = encode_emoji("Test")
        # All characters should be pool emoji, skin tones, or terminator
        for ch in encoded:
            is_pool = ch in EMOJI_INDEX
            is_skin = ch in SKIN_TONE_INDEX
            self.assertTrue(
                is_pool or is_skin,
                f"U+{ord(ch):04X} ({ch!r}) is not an emoji character"
            )

    def test_different_secrets_different_emoji(self):
        e1 = encode_emoji("A")
        e2 = encode_emoji("B")
        self.assertNotEqual(e1, e2)


class TestEmojiDetection(unittest.TestCase):
    """Test has_emoji_data detection."""

    def test_detect_positive(self):
        encoded = encode_emoji("secret")
        self.assertTrue(has_emoji_data(encoded))

    def test_detect_negative(self):
        self.assertFalse(has_emoji_data("Hello world"))
        self.assertFalse(has_emoji_data("🎉 party"))


class TestEmojiCapacity(unittest.TestCase):
    """Test capacity calculation."""

    def test_capacity(self):
        cap = emoji_capacity(10)
        # 10 emoji × (6 pool + 2 skin) bits = 80 bits = 10 bytes
        self.assertEqual(cap, 10)

    def test_capacity_zero(self):
        self.assertEqual(emoji_capacity(0), 0)


class TestEmojiEdgeCases(unittest.TestCase):
    """Edge cases."""

    def test_decode_no_data(self):
        result = decode_emoji("Just normal text here for testing purposes")
        self.assertEqual(result, "")

    def test_secret_too_long(self):
        with self.assertRaises(ValueError):
            encode_emoji("A" * 1000, max_emoji=10)


if __name__ == "__main__":
    unittest.main()
