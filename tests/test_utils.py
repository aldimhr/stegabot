"""Tests for stegano.utils — bit conversion and capacity check."""
import pytest
from stegano.utils import text_to_bits, bits_to_text


class TestBitConversion:
    def test_text_to_bits_ascii(self):
        bits = text_to_bits("A")
        assert bits == [0, 1, 0, 0, 0, 0, 0, 1]

    def test_text_to_bits_utf8_multibyte(self):
        bits = text_to_bits("€")
        assert len(bits) == 24  # 3 bytes × 8 bits

    def test_roundtrip_ascii(self):
        original = "hello world"
        bits = text_to_bits(original)
        recovered = bits_to_text(bits)
        assert recovered == original

    def test_roundtrip_unicode(self):
        original = "こんにちは"
        bits = text_to_bits(original)
        recovered = bits_to_text(bits)
        assert recovered == original

    def test_roundtrip_emoji(self):
        original = "🔐🗝️"
        bits = text_to_bits(original)
        recovered = bits_to_text(bits)
        assert recovered == original

    def test_bits_to_text_empty(self):
        assert bits_to_text([]) == ""

    def test_text_to_bits_empty(self):
        assert text_to_bits("") == []

    def test_bits_to_text_partial_byte_ignored(self):
        # 5 bits (not a full byte) should produce empty string
        assert bits_to_text([1, 0, 1, 0, 1]) == ""
