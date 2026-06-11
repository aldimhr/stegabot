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


class TestLSBDepth1:
    def test_roundtrip_short(self):
        cover = make_test_image("d1_cover.png")
        stego = os.path.join(TEST_DIR, "d1_stego.png")
        secret = "Hello!"
        encode_lsb(cover, secret, stego, depth=1)
        assert decode_lsb(stego) == secret

    def test_roundtrip_long(self):
        cover = make_test_image("d1_long.png", size=(512, 512))
        stego = os.path.join(TEST_DIR, "d1_stego_long.png")
        secret = "A" * 1000
        encode_lsb(cover, secret, stego, depth=1)
        assert decode_lsb(stego) == secret

    def test_roundtrip_unicode(self):
        cover = make_test_image("d1_uni.png", size=(256, 256))
        stego = os.path.join(TEST_DIR, "d1_stego_uni.png")
        secret = "こんにちは世界 🔐"
        encode_lsb(cover, secret, stego, depth=1)
        assert decode_lsb(stego) == secret

    def test_rgba_image(self):
        cover = make_test_image("d1_rgba.png", size=(200, 200), mode='RGBA')
        stego = os.path.join(TEST_DIR, "d1_stego_rgba.png")
        secret = "RGBA test"
        encode_lsb(cover, secret, stego, depth=1)
        assert decode_lsb(stego) == secret

    def test_capacity(self):
        cover = make_test_image("d1_cap.png", size=(100, 100))
        cap = capacity_lsb(cover, depth=1)
        assert cap['pixels'] == 10000
        assert cap['channels'] == 3
        assert cap['depth'] == 1
        assert cap['capacity_bits'] == 30000

    def test_secret_too_long(self):
        cover = make_test_image("d1_err.png", size=(10, 10))
        stego = os.path.join(TEST_DIR, "d1_stego_err.png")
        # Use random-looking data that won't compress well
        import string, random
        random.seed(42)
        secret = ''.join(random.choices(string.ascii_letters + string.digits, k=200))
        with pytest.raises(ValueError, match="too long"):
            encode_lsb(cover, secret, stego, depth=1, compress=False)


class TestLSBDepth2:
    def test_roundtrip(self):
        cover = make_test_image("d2_cover.png")
        stego = os.path.join(TEST_DIR, "d2_stego.png")
        secret = "Depth 2 test!"
        encode_lsb(cover, secret, stego, depth=2)
        assert decode_lsb(stego) == secret

    def test_capacity_doubled(self):
        cover = make_test_image("d2_cap.png", size=(100, 100))
        cap1 = capacity_lsb(cover, depth=1)
        cap2 = capacity_lsb(cover, depth=2)
        assert cap2['capacity_bits'] == cap1['capacity_bits'] * 2


class TestLSBDepth3:
    def test_roundtrip(self):
        cover = make_test_image("d3_cover.png")
        stego = os.path.join(TEST_DIR, "d3_stego.png")
        secret = "Depth 3 test!"
        encode_lsb(cover, secret, stego, depth=3)
        assert decode_lsb(stego) == secret

    def test_capacity_tripled(self):
        cover = make_test_image("d3_cap.png", size=(100, 100))
        cap1 = capacity_lsb(cover, depth=1)
        cap3 = capacity_lsb(cover, depth=3)
        assert cap3['capacity_bits'] == cap1['capacity_bits'] * 3


class TestLSBCompression:
    def test_compressed_roundtrip(self):
        cover = make_test_image("comp_cover.png", size=(256, 256))
        stego = os.path.join(TEST_DIR, "comp_stego.png")
        secret = "A" * 2000
        encode_lsb(cover, secret, stego, depth=1, compress=True)
        assert decode_lsb(stego) == secret

    def test_uncompressed_roundtrip(self):
        cover = make_test_image("uncomp_cover.png")
        stego = os.path.join(TEST_DIR, "uncomp_stego.png")
        secret = "Short"
        encode_lsb(cover, secret, stego, depth=1, compress=False)
        assert decode_lsb(stego) == secret


class TestLSBVisual:
    def test_visual_similarity(self):
        """Stego image should look identical to cover at depth=1."""
        cover = make_test_image("vis_cover.png", size=(100, 100))
        stego = os.path.join(TEST_DIR, "vis_stego.png")
        encode_lsb(cover, "test", stego, depth=1)
        c = Image.open(cover)
        s = Image.open(stego)
        assert c.size == s.size
        for x in range(c.width):
            for y in range(c.height):
                cp = c.getpixel((x, y))
                sp = s.getpixel((x, y))
                for i in range(len(cp)):
                    assert abs(cp[i] - sp[i]) <= 1


class TestLSBDecode:
    def test_decode_empty(self):
        cover = make_test_image("dec_empty.png")
        result = decode_lsb(cover)
        assert result == ""
