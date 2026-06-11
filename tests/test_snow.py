"""Tests for stegano.snow — Whitespace/SNOW steganography."""
import pytest
from stegano.snow import encode_snow, decode_snow


class TestSNOW:
    def test_roundtrip_single_char(self):
        cover = "\n".join([f"line{i}" for i in range(10)])
        secret = "A"  # 8 bits → needs 8 lines
        stego = encode_snow(cover, secret)
        decoded = decode_snow(stego)
        assert decoded == secret

    def test_roundtrip_multichar(self):
        cover = "\n".join([f"line{i}" for i in range(30)])
        secret = "hi"
        stego = encode_snow(cover, secret)
        decoded = decode_snow(stego)
        assert decoded == secret

    def test_trailing_whitespace_present(self):
        cover = "line1\nline2\nline3"
        stego = encode_snow(cover, "A")
        lines = stego.split('\n')
        has_trailer = any(line.endswith(' ') or line.endswith('\t') for line in lines)
        assert has_trailer

    def test_decode_no_hidden_data(self):
        result = decode_snow("just plain text\nnothing hidden")
        assert result == ""

    def test_roundtrip_empty_secret(self):
        cover = "line1\nline2"
        stego = encode_snow(cover, "")
        assert stego == cover
