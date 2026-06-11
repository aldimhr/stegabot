"""Tests for stegano.acrostic — First-Letter steganography."""
import pytest
from stegano.acrostic import encode_acrostic, decode_acrostic


class TestAcrostic:
    def test_decode_known(self):
        text = "Hello Everyone Look What I Found"
        assert decode_acrostic(text) == "HELWIF"

    def test_decode_ignores_nonalpha_first_char(self):
        # Words starting with non-alpha chars are skipped
        text = "1Hello 2Everyone"
        assert decode_acrostic(text) == ""

    def test_decode_mixed_alpha_nonalpha(self):
        # Words with alpha first char are kept
        text = "Hello 123 Everyone"
        assert decode_acrostic(text) == "HE"

    def test_roundtrip(self):
        secret = "HELLO"
        stego = encode_acrostic(secret)
        assert stego is not None
        decoded = decode_acrostic(stego)
        assert decoded == secret

    def test_encode_lowercase(self):
        secret = "test"
        stego = encode_acrostic(secret)
        assert stego is not None
        decoded = decode_acrostic(stego)
        assert decoded == "TEST"

    def test_encode_empty(self):
        assert encode_acrostic("") == ""

    def test_decode_empty(self):
        assert decode_acrostic("") == ""

    def test_roundtrip_random_word(self):
        secret = "STEGO"
        stego = encode_acrostic(secret)
        assert stego is not None
        decoded = decode_acrostic(stego)
        assert decoded == secret
