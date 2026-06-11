"""Tests for stegano.detect — Auto-detection of steganography methods."""
import pytest
from stegano.detect import detect_method
from stegano.zwc import encode_zwc
from stegano.snow import encode_snow
from stegano.homoglyph import encode_homoglyph


class TestDetectMethod:
    def test_detect_zwc(self):
        cover = "The weather in Jakarta is nice today."
        stego = encode_zwc(cover, "hi")
        assert detect_method(stego) == "zwc"

    def test_detect_snow(self):
        cover = "\n".join([f"line{i}" for i in range(10)])
        stego = encode_snow(cover, "A")
        assert detect_method(stego) == "snow"

    def test_detect_homoglyph(self):
        cover = "access accepted success"
        stego = encode_homoglyph(cover, "A")
        assert detect_method(stego) == "homoglyph"

    def test_detect_none(self):
        assert detect_method("just plain text") is None

    def test_detect_empty(self):
        assert detect_method("") is None
