"""Tests for stegano.crypto — AES-128 encryption layer."""
import pytest
from stegano.crypto import encrypt_secret, decrypt_secret


class TestCrypto:
    def test_roundtrip(self):
        plaintext = "hello world"
        passphrase = "my-secret-key"
        ciphertext = encrypt_secret(plaintext, passphrase)
        assert ciphertext != plaintext
        recovered = decrypt_secret(ciphertext, passphrase)
        assert recovered == plaintext

    def test_wrong_passphrase(self):
        plaintext = "hello world"
        ciphertext = encrypt_secret(plaintext, "key1")
        with pytest.raises(Exception):
            decrypt_secret(ciphertext, "key2")

    def test_unicode(self):
        plaintext = "こんにちは世界"
        passphrase = "test"
        ciphertext = encrypt_secret(plaintext, passphrase)
        recovered = decrypt_secret(ciphertext, passphrase)
        assert recovered == plaintext
