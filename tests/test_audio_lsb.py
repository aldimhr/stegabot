"""Tests for stegano.audio_lsb — Audio LSB steganography."""
import os
import tempfile
import unittest
import numpy as np
from scipy.io import wavfile

from stegano.audio_lsb import encode_audio, decode_audio, has_audio_data, audio_capacity


def make_test_audio(name, duration_sec=2.0, sample_rate=8000):
    """Create a test WAV file with sine wave audio."""
    tmp_dir = tempfile.mkdtemp()
    path = os.path.join(tmp_dir, name)
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    # 440Hz sine wave, int16
    audio = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.int16)
    wavfile.write(path, sample_rate, audio)
    return path


class TestAudioRoundtrip(unittest.TestCase):
    """Basic encode → decode roundtrip tests."""

    def test_short_secret(self):
        audio_path = make_test_audio("short.wav", duration_sec=3.0)
        secret = "Hi"
        stego_path = audio_path.replace("short.wav", "stego_short.wav")
        encode_audio(audio_path, secret, stego_path)
        result = decode_audio(stego_path)
        self.assertEqual(result, secret)

    def test_longer_secret(self):
        audio_path = make_test_audio("long.wav", duration_sec=5.0)
        secret = "Hello audio steganography!"
        stego_path = audio_path.replace("long.wav", "stego_long.wav")
        encode_audio(audio_path, secret, stego_path)
        result = decode_audio(stego_path)
        self.assertEqual(result, secret)

    def test_unicode_secret(self):
        audio_path = make_test_audio("unicode.wav", duration_sec=5.0)
        secret = "你好世界"
        stego_path = audio_path.replace("unicode.wav", "stego_unicode.wav")
        encode_audio(audio_path, secret, stego_path)
        result = decode_audio(stego_path)
        self.assertEqual(result, secret)

    def test_empty_secret(self):
        audio_path = make_test_audio("empty.wav", duration_sec=2.0)
        stego_path = audio_path.replace("empty.wav", "stego_empty.wav")
        encode_audio(audio_path, "", stego_path)
        # File should be identical to original
        result = decode_audio(stego_path)
        self.assertEqual(result, "")


class TestAudioDetection(unittest.TestCase):
    """Test has_audio_data detection."""

    def test_detect_header(self):
        audio_path = make_test_audio("detect.wav", duration_sec=3.0)
        stego_path = audio_path.replace("detect.wav", "stego_detect.wav")
        encode_audio(audio_path, "secret", stego_path)
        self.assertTrue(has_audio_data(stego_path))

    def test_detect_negative(self):
        audio_path = make_test_audio("clean.wav", duration_sec=2.0)
        self.assertFalse(has_audio_data(audio_path))


class TestAudioCapacity(unittest.TestCase):
    """Test capacity calculation."""

    def test_capacity(self):
        audio_path = make_test_audio("cap.wav", duration_sec=2.0, sample_rate=8000)
        cap = audio_capacity(audio_path)
        # 2 sec × 8000 samples/sec = 16000 samples
        # Header: 32 bits. Payload: (16000 - 32) / 8 = ~1999 bytes
        self.assertGreater(cap, 1000)
        self.assertLess(cap, 2000)


class TestAudioEdgeCases(unittest.TestCase):
    """Edge cases."""

    def test_secret_too_long(self):
        audio_path = make_test_audio("tooshort.wav", duration_sec=0.1)
        stego_path = audio_path.replace("tooshort.wav", "stego.wav")
        with self.assertRaises(ValueError):
            encode_audio(audio_path, "A" * 1000, stego_path)

    def test_stego_audio_similar_to_original(self):
        """LSB changes should be inaudible (±1 per sample)."""
        audio_path = make_test_audio("similar.wav", duration_sec=2.0)
        stego_path = audio_path.replace("similar.wav", "stego_similar.wav")
        encode_audio(audio_path, "Test", stego_path)

        _, original = wavfile.read(audio_path)
        _, stego = wavfile.read(stego_path)
        diff = np.abs(original.astype(int) - stego.astype(int))
        self.assertTrue(np.all(diff <= 1))


if __name__ == "__main__":
    unittest.main()
