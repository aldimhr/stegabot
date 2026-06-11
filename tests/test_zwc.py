"""Tests for stegano.zwc — Zero-Width Character steganography."""
import pytest
from stegano.zwc import encode_zwc, decode_zwc, ALL_ZWC


class TestZWC:
    def test_encode_produces_same_visible_length(self):
        cover = "The weather in Jakarta is nice today."
        stego = encode_zwc(cover, "hi")
        visible = ''.join(c for c in stego if c not in ALL_ZWC)
        assert visible == cover

    def test_roundtrip_short(self):
        cover = "The weather in Jakarta is nice today."
        secret = "hi"
        stego = encode_zwc(cover, secret)
        decoded = decode_zwc(stego)
        assert decoded == secret

    def test_roundtrip_longer(self):
        cover = "A" * 200
        secret = "hello world this is a test"
        stego = encode_zwc(cover, secret)
        decoded = decode_zwc(stego)
        assert decoded == secret

    def test_roundtrip_unicode_secret(self):
        cover = "A" * 300
        secret = "こんにちは"
        stego = encode_zwc(cover, secret)
        decoded = decode_zwc(stego)
        assert decoded == secret

    def test_decode_no_hidden_data(self):
        result = decode_zwc("just plain text nothing hidden")
        assert result == ""

    def test_encode_inserts_zwc_chars(self):
        cover = "Hello world"
        stego = encode_zwc(cover, "A")
        zwc_chars = [c for c in stego if c in ALL_ZWC]
        assert len(zwc_chars) > 0
