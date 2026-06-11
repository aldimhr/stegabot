"""Tests for stegano.variation_selector — Unicode Variation Selector steganography."""
import unittest

from stegano.variation_selector import (
    encode_vs,
    decode_vs,
    has_vs_data,
    vs_capacity,
)


class TestVariationSelectorRoundtrip(unittest.TestCase):
    """Basic encode → decode roundtrip tests."""

    def test_ascii_secret(self):
        cover = "Hello world, this is a normal sentence."
        secret = "Hi"
        encoded = encode_vs(cover, secret)
        # Should look like the original
        self.assertIn("Hello", encoded)
        # Should decode back
        self.assertEqual(decode_vs(encoded), secret)

    def test_unicode_secret(self):
        cover = "The quick brown fox jumps over the lazy dog near the river bank today."
        secret = "你好世界"
        encoded = encode_vs(cover, secret)
        self.assertEqual(decode_vs(encoded), secret)

    def test_emoji_secret(self):
        cover = "A sentence with enough words for the hidden secret message here now."
        secret = "🎉🔒"
        encoded = encode_vs(cover, secret)
        self.assertEqual(decode_vs(encoded), secret)

    def test_empty_secret(self):
        cover = "Hello world"
        encoded = encode_vs(cover, "")
        self.assertEqual(encoded, cover)
        self.assertEqual(decode_vs(encoded), "")

    def test_single_char_secret(self):
        cover = "Test sentence here."
        secret = "X"
        encoded = encode_vs(cover, secret)
        self.assertEqual(decode_vs(encoded), secret)

    def test_long_secret(self):
        cover = " ".join(["word"] * 200)  # 200 words
        secret = "A" * 100
        encoded = encode_vs(cover, secret)
        self.assertEqual(decode_vs(encoded), secret)

    def test_secret_with_newlines(self):
        cover = "This is a long enough cover text that has plenty of word boundaries for testing the secret data here."
        secret = "line1\nline2\nline3"
        encoded = encode_vs(cover, secret)
        self.assertEqual(decode_vs(encoded), secret)


class TestVariationSelectorVisibility(unittest.TestCase):
    """Verify the stego text looks identical to the original."""

    def test_visible_text_unchanged(self):
        cover = "Hello world, this is a test sentence for checking."
        secret = "S"
        encoded = encode_vs(cover, secret)
        # Strip all variation selectors — should look like original
        import re
        visible = re.sub(r'[\uFE00-\uFE0F]', '', encoded)
        visible = re.sub(r'[\U000E0100-\U000E01EF]', '', visible)
        self.assertEqual(visible, cover)

    def test_vs_characters_present(self):
        cover = "Test sentence for steganography."
        secret = "AB"
        encoded = encode_vs(cover, secret)
        # Should have variation selectors
        vs_count = sum(1 for c in encoded if '\uFE00' <= c <= '\uFE0F' or
                       (len(c) == 1 and 0xE0100 <= ord(c) <= 0xE01EF))
        self.assertGreater(vs_count, 0)


class TestVariationSelectorDetection(unittest.TestCase):
    """Test has_vs_data detection."""

    def test_detect_positive(self):
        cover = "Hello world test sentence here for checking."
        encoded = encode_vs(cover, "secret")
        self.assertTrue(has_vs_data(encoded))

    def test_detect_negative(self):
        self.assertFalse(has_vs_data("Hello world"))
        self.assertFalse(has_vs_data(""))
        self.assertFalse(has_vs_data("Normal text with emoji 🎉"))


class TestVariationSelectorCapacity(unittest.TestCase):
    """Test capacity calculation."""

    def test_capacity(self):
        cover = " ".join(["word"] * 50)
        cap = vs_capacity(cover)
        # 50 words = 49 spaces to insert VS chars
        self.assertEqual(cap, 49)

    def test_capacity_short(self):
        cap = vs_capacity("Hello")
        self.assertEqual(cap, 0)  # No spaces to insert between


class TestVariationSelectorEdgeCases(unittest.TestCase):
    """Edge cases."""

    def test_cover_too_short(self):
        """Cover must have enough word boundaries for the secret."""
        with self.assertRaises(ValueError):
            encode_vs("Hi", "This secret is way too long for this cover")

    def test_decode_no_data(self):
        result = decode_vs("Just normal text, nothing hidden here.")
        self.assertEqual(result, "")

    def test_roundtrip_all_bytes(self):
        """Test encoding every possible byte value."""
        # latin-1 chars 128-255 are 2 bytes in UTF-8, so 256 latin-1 → 384 UTF-8 bytes
        cover = " ".join(["word"] * 400)
        secret = bytes(range(256)).decode("latin-1")
        encoded = encode_vs(cover, secret)
        decoded = decode_vs(encoded)
        # latin-1 roundtrip
        self.assertEqual(decoded.encode("latin-1"), bytes(range(256)))


if __name__ == "__main__":
    unittest.main()
