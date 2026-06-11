"""Optional AES-128 (Fernet) encryption for secrets before steganographic embedding."""
import base64
import hashlib
from cryptography.fernet import Fernet


def _derive_key(passphrase: str) -> bytes:
    """Derive a Fernet-compatible key from a passphrase."""
    key = hashlib.sha256(passphrase.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_secret(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext with passphrase. Returns base64-encoded ciphertext."""
    key = _derive_key(passphrase)
    f = Fernet(key)
    ciphertext = f.encrypt(plaintext.encode('utf-8'))
    return base64.urlsafe_b64encode(ciphertext).decode('ascii')


def decrypt_secret(ciphertext_b64: str, passphrase: str) -> str:
    """Decrypt base64-encoded ciphertext with passphrase."""
    key = _derive_key(passphrase)
    f = Fernet(key)
    ciphertext = base64.urlsafe_b64decode(ciphertext_b64.encode('ascii'))
    plaintext = f.decrypt(ciphertext)
    return plaintext.decode('utf-8')
