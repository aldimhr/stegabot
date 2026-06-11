"""Tests for stegano.image_lsb — LSB image steganography."""
import pytest
import os
from PIL import Image
from stegano.image_lsb import encode_lsb, decode_lsb, capacity_lsb

TEST_DIR = "/tmp/stegabot_tests"


@pytest.fixture(autouse=True)
def setup():
    os.makedirs(TEST_DIR, exist_ok=True)


def make_test_image(name, size=(100, 100), mode='RGB'):
    path = os.path.join(TEST_DIR, name)
    img = Image.new(mode, size, color='blue')
    img.save(path, format='PNG')
    return path


class TestLSB:
    def test_roundtrip_short(self):
        cover = make_test_image("cover1.png")
        stego = os.path.join(TEST_DIR, "stego1.png")
        secret = "Hello!"
        encode_lsb(cover, secret, stego)
        assert decode_lsb(stego) == secret

    def test_roundtrip_long(self):
        cover = make_test_image("cover2.png", size=(512, 512))
        stego = os.path.join(TEST_DIR, "stego2.png")
        secret = "A" * 1000
        encode_lsb(cover, secret, stego)
        assert decode_lsb(stego) == secret

    def test_roundtrip_unicode(self):
        cover = make_test_image("cover3.png", size=(256, 256))
        stego = os.path.join(TEST_DIR, "stego3.png")
        secret = "こんにちは世界 🔐"
        encode_lsb(cover, secret, stego)
        assert decode_lsb(stego) == secret

    def test_rgba_image(self):
        cover = make_test_image("cover4.png", size=(200, 200), mode='RGBA')
        stego = os.path.join(TEST_DIR, "stego4.png")
        secret = "RGBA test"
        encode_lsb(cover, secret, stego)
        assert decode_lsb(stego) == secret

    def test_visual_similarity(self):
        """Stego image should look identical to cover."""
        cover = make_test_image("cover5.png", size=(100, 100))
        stego = os.path.join(TEST_DIR, "stego5.png")
        encode_lsb(cover, "test", stego)
        c = Image.open(cover)
        s = Image.open(stego)
        assert c.size == s.size
        assert c.mode == s.mode
        # Pixel difference should be minimal (<=1 per channel)
        for x in range(c.width):
            for y in range(c.height):
                cp = c.getpixel((x, y))
                sp = s.getpixel((x, y))
                for i in range(len(cp)):
                    assert abs(cp[i] - sp[i]) <= 1

    def test_capacity_check(self):
        cover = make_test_image("cover6.png", size=(100, 100))
        cap = capacity_lsb(cover)
        assert cap['pixels'] == 10000
        assert cap['channels'] == 3
        assert cap['capacity_bits'] == 30000
        assert cap['usable_bits'] == 29968  # 30000 - 32 (header)
        assert cap['capacity_chars'] == 3746  # 29968 // 8

    def test_secret_too_long(self):
        cover = make_test_image("cover7.png", size=(10, 10))
        stego = os.path.join(TEST_DIR, "stego7.png")
        secret = "A" * 100
        with pytest.raises(ValueError, match="too long"):
            encode_lsb(cover, secret, stego)

    def test_decode_empty_image(self):
        """Decoding an unmodified image should not crash."""
        cover = make_test_image("cover8.png")
        result = decode_lsb(cover)
        assert isinstance(result, str)

    def test_roundtrip_empty_secret(self):
        cover = make_test_image("cover9.png")
        stego = os.path.join(TEST_DIR, "stego9.png")
        encode_lsb(cover, "", stego)
        assert decode_lsb(stego) == ""
