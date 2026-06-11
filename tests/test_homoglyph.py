"""Tests for stegano.homoglyph — Unicode Homoglyph steganography."""
import pytest
from stegano.homoglyph import encode_homoglyph, decode_homoglyph, HOMOGLYPHS, REVERSE


class TestHomoglyph:
    def test_roundtrip(self):
        cover = "access accepted success"  # has a, e, c, x
        secret = "A"  # 8 bits
        stego = encode_homoglyph(cover, secret)
        decoded = decode_homoglyph(stego)
        assert decoded == secret

    def test_no_eligible_chars(self):
        cover = "wxyz"  # no homoglyph-eligible letters
        stego = encode_homoglyph(cover, "A")
        assert stego == cover  # no changes

    def test_decode_plain_text(self):
        result = decode_homoglyph("hello world")
        assert result == ""

    def test_replacement_looks_same(self):
        cover = "aaa"
        stego = encode_homoglyph(cover, "A")
        assert len(stego) == len(cover)
        for i, ch in enumerate(stego):
            if ch in REVERSE:
                assert ch != cover[i]
                assert ch.lower() in REVERSE

    def test_roundtrip_longer_secret(self):
        # Need enough eligible chars for longer secrets
        cover = "access access access access access"
        secret = "hi"
        stego = encode_homoglyph(cover, secret)
        decoded = decode_homoglyph(stego)
        assert decoded == secret
