"""Tests for stegano.utils — bit conversion and capacity check."""
import pytest
from stegano.utils import text_to_bits, bits_to_text, capacity_check


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


class TestCapacityCheck:
    def test_zwc_enough(self):
        result = capacity_check("A" * 100, "hello", "zwc")
        assert result["enough"] is True
        assert result["capacity_bits"] == 100
        assert result["needed_bits"] == 40  # 5 chars × 8 bits

    def test_zwc_not_enough(self):
        result = capacity_check("A" * 10, "hello", "zwc")
        assert result["enough"] is False

    def test_snow_capacity(self):
        cover = "line1\nline2\nline3\nline4\nline5"
        result = capacity_check(cover, "A", "snow")
        assert result["capacity_bits"] == 4  # 4 newlines → 4 bits (need 8 for "A")
        assert result["enough"] is False

    def test_acrostic_capacity(self):
        cover = "one two three four five"
        result = capacity_check(cover, "abc", "acrostic")
        assert result["capacity_bits"] == 40  # 5 words × 8 bits per char
        assert result["enough"] is True  # 24 bits ≤ 40 bits

    def test_homoglyph_capacity(self):
        cover = "aXeXoXpXcXx"  # all 11 chars are homoglyph-eligible (case-insensitive)
        result = capacity_check(cover, "A", "homoglyph")
        assert result["capacity_bits"] == 11
        assert result["enough"] is True  # 8 bits ≤ 11
