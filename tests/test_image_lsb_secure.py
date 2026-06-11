"""Tests for stegano.image_lsb_secure — secure LSB with PBKDF2 + Fernet + scrambled pixels."""
import os
import tempfile
import unittest

from PIL import Image

from stegano.image_lsb_secure import encode_lsb_secure, decode_lsb_secure, _derive_secure_keys


class TestSecureKeyDerivation(unittest.TestCase):
    """Test PBKDF2 key derivation."""

    def test_same_passphrase_same_keys(self):
        salt = os.urandom(16)
        k1 = _derive_secure_keys("mypass", salt)
        k2 = _derive_secure_keys("mypass", salt)
        self.assertEqual(k1["fernet_key"], k2["fernet_key"])
        self.assertEqual(k1["seed_a"], k2["seed_a"])
        self.assertEqual(k1["seed_b"], k2["seed_b"])

    def test_different_passphrase_different_keys(self):
        salt = os.urandom(16)
        k1 = _derive_secure_keys("pass1", salt)
        k2 = _derive_secure_keys("pass2", salt)
        self.assertNotEqual(k1["fernet_key"], k2["fernet_key"])

    def test_different_salt_different_keys(self):
        k1 = _derive_secure_keys("mypass", os.urandom(16))
        k2 = _derive_secure_keys("mypass", os.urandom(16))
        self.assertNotEqual(k1["fernet_key"], k2["fernet_key"])


def make_test_image(name, size=(100, 100), mode="RGB"):
    """Create a test cover image with random pixels."""
    tmp_dir = tempfile.mkdtemp()
    path = os.path.join(tmp_dir, name)
    img = Image.new(mode, size)
    # Fill with non-zero random-looking data so LSB changes are undetectable
    import random
    rng = random.Random(42)
    pixels = [(rng.randint(0, 255) for _ in range(4 if mode == "RGBA" else 3)) for _ in range(size[0] * size[1])]
    if mode == "RGBA":
        pixels = [tuple(p) for p in pixels]
    else:
        pixels = [tuple(p) for p in pixels]
    img.putdata(pixels)
    img.save(path, format="PNG")
    return path


class TestSecureEncodeDecode(unittest.TestCase):
    """Roundtrip tests for secure LSB."""

    def test_basic_roundtrip_depth1(self):
        cover = make_test_image("sec_d1.png")
        secret = "Hello, secure steganography!"
        stego = cover.replace("sec_d1.png", "stego_sec_d1.png")

        encode_lsb_secure(cover, secret, stego, passphrase="testpass", depth=1)
        result = decode_lsb_secure(stego, passphrase="testpass")
        self.assertEqual(result, secret)

    def test_basic_roundtrip_depth2(self):
        cover = make_test_image("sec_d2.png", size=(200, 200))
        secret = "Depth 2 secure test message with more data!"
        stego = cover.replace("sec_d2.png", "stego_sec_d2.png")

        encode_lsb_secure(cover, secret, stego, passphrase="testpass", depth=2)
        result = decode_lsb_secure(stego, passphrase="testpass")
        self.assertEqual(result, secret)

    def test_basic_roundtrip_depth3(self):
        cover = make_test_image("sec_d3.png", size=(200, 200))
        secret = "Depth 3 maximum capacity test!"
        stego = cover.replace("sec_d3.png", "stego_sec_d3.png")

        encode_lsb_secure(cover, secret, stego, passphrase="testpass", depth=3)
        result = decode_lsb_secure(stego, passphrase="testpass")
        self.assertEqual(result, secret)

    def test_wrong_passphrase_fails(self):
        cover = make_test_image("sec_wrong.png")
        secret = "Secret message"
        stego = cover.replace("sec_wrong.png", "stego_sec_wrong.png")

        encode_lsb_secure(cover, secret, stego, passphrase="correct_pass", depth=1)
        with self.assertRaises(ValueError):
            decode_lsb_secure(stego, passphrase="wrong_pass")

    def test_unicode_secret(self):
        cover = make_test_image("sec_uni.png", size=(256, 256))
        secret = "Unicode: 你好世界 🔒🎉 مرحبا"
        stego = cover.replace("sec_uni.png", "stego_sec_uni.png")

        encode_lsb_secure(cover, secret, stego, passphrase="unicode_pass", depth=1)
        result = decode_lsb_secure(stego, passphrase="unicode_pass")
        self.assertEqual(result, secret)

    def test_long_secret_with_compression(self):
        cover = make_test_image("sec_long.png", size=(512, 512))
        secret = "A" * 5000  # Should trigger gzip compression
        stego = cover.replace("sec_long.png", "stego_sec_long.png")

        encode_lsb_secure(cover, secret, stego, passphrase="long_pass", depth=1, compress=True)
        result = decode_lsb_secure(stego, passphrase="long_pass")
        self.assertEqual(result, secret)

    def test_rgba_image(self):
        cover = make_test_image("sec_rgba.png", size=(200, 200), mode="RGBA")
        secret = "RGBA secure test"
        stego = cover.replace("sec_rgba.png", "stego_sec_rgba.png")

        encode_lsb_secure(cover, secret, stego, passphrase="rgba_pass", depth=1)
        result = decode_lsb_secure(stego, passphrase="rgba_pass")
        self.assertEqual(result, secret)

    def test_secret_too_long(self):
        cover = make_test_image("sec_toolong.png", size=(10, 10))
        secret = "X" * 1000
        stego = cover.replace("sec_toolong.png", "stego_sec_toolong.png")

        with self.assertRaises(ValueError):
            encode_lsb_secure(cover, secret, stego, passphrase="pass", depth=1)

    def test_no_magic_header_in_pixels(self):
        """Verify there's no 'LS' magic bytes at the start of pixel LSBs."""
        cover = make_test_image("sec_nomagic.png", size=(200, 200))
        secret = "No magic header test"
        stego = cover.replace("sec_nomagic.png", "stego_sec_nomagic.png")

        encode_lsb_secure(cover, secret, stego, passphrase="nomagic_pass", depth=1)

        # Extract first 16 raw bits from stego (depth=1, 3 channels)
        img = Image.open(stego)
        pixels = list(img.getdata())
        first_bits = []
        for pixel in pixels[:6]:
            for ch in range(3):
                first_bits.append(pixel[ch] & 1)

        # First 16 bits should NOT be the ASCII for 'L' (0x4C = 01001100)
        # and 'S' (0x53 = 01010011) → 01001100 01010011
        magic_bits = [0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1]
        # The salt is random, so it should almost never match magic
        self.assertNotEqual(first_bits[:16], magic_bits,
                            "First 16 bits should not be 'LS' magic!")

    def test_different_passphrase_different_stego(self):
        """Same image + same secret + different passphrases → different stego images."""
        cover = make_test_image("sec_diff.png", size=(200, 200))
        secret = "Same secret"

        stego1 = cover.replace("sec_diff.png", "stego1.png")
        stego2 = cover.replace("sec_diff.png", "stego2.png")

        encode_lsb_secure(cover, secret, stego1, passphrase="pass_A", depth=1)
        encode_lsb_secure(cover, secret, stego2, passphrase="pass_B", depth=1)

        # The stego images should be different (different salt, different pixel positions)
        img1 = list(Image.open(stego1).getdata())
        img2 = list(Image.open(stego2).getdata())
        # They should differ in at least some pixels
        diffs = sum(1 for a, b in zip(img1, img2) if a != b)
        self.assertGreater(diffs, 0, "Different passphrases should produce different stego images")

        # But both should decode correctly with their respective passphrases
        self.assertEqual(decode_lsb_secure(stego1, "pass_A"), secret)
        self.assertEqual(decode_lsb_secure(stego2, "pass_B"), secret)


if __name__ == "__main__":
    unittest.main()
