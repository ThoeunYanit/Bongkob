"""Encryption layer for Bongkob.

Password -> key:   PBKDF2-HMAC-SHA256, 600,000 rounds, random 16-byte salt
Encryption:        AES-256-GCM, random 12-byte nonce, 16-byte authentication tag

Payload layout (bytes):
    MAGIC "BONGKOB2" (8) | salt (16) | nonce (12) | ciphertext + tag

Plaintext inside the ciphertext:
    kind (1: 0 = text, 1 = file) | name length (1) | name (UTF-8) | data

The filename sits inside the ciphertext, so an attacker who extracts the
payload learns nothing except its size. MAGIC is passed to GCM as associated
data, so changing the header also breaks the tag.
"""

import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

MAGIC = b"BONGKOB2"
SALT_SIZE = 16
NONCE_SIZE = 12
TAG_SIZE = 16               # GCM authentication tag
KEY_SIZE = 32                # 256-bit AES key
KDF_ITERATIONS = 600_000     # OWASP recommendation for PBKDF2-HMAC-SHA256
MIN_PASSWORD_LENGTH = 8

KIND_TEXT = 0
KIND_FILE = 1


class DecryptionError(Exception):
    """Wrong password, or the data was modified (GCM tag check failed)."""


class NotBongkobPayload(Exception):
    """The bytes do not start with the Bongkob header."""


@dataclass
class Secret:
    """What the user wants to hide: a text message or a file."""

    kind: int
    data: bytes
    name: str = ""

    @classmethod
    def from_text(cls, text: str) -> "Secret":
        return cls(KIND_TEXT, text.encode("utf-8"))

    @classmethod
    def from_file(cls, data: bytes, name: str) -> "Secret":
        return cls(KIND_FILE, data, name)

    @property
    def text(self) -> str:
        return self.data.decode("utf-8")


def check_password(password: str) -> str | None:
    """Return a problem description, or None if the password is acceptable."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Use at least {MIN_PASSWORD_LENGTH} characters."
    if password.isdigit() or password.isalpha():
        return "Mix letters with numbers or symbols."
    return None


def payload_size(secret: Secret) -> int:
    """Exact size of the encrypted payload, without encrypting (used for capacity checks)."""
    name_len = len(secret.name.encode("utf-8")[:255])
    return len(MAGIC) + SALT_SIZE + NONCE_SIZE + TAG_SIZE + 2 + name_len + len(secret.data)


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt(secret: Secret, password: str) -> bytes:
    name = secret.name.encode("utf-8")[:255]
    plaintext = bytes([secret.kind, len(name)]) + name + secret.data

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, MAGIC)
    return MAGIC + salt + nonce + ciphertext


def decrypt(payload: bytes, password: str) -> Secret:
    if not payload.startswith(MAGIC):
        raise NotBongkobPayload()

    body = payload[len(MAGIC):]
    salt = body[:SALT_SIZE]
    nonce = body[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = body[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(password, salt)
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, MAGIC)
    except InvalidTag as exc:
        raise DecryptionError() from exc

    kind, name_len = plaintext[0], plaintext[1]
    name = plaintext[2:2 + name_len].decode("utf-8")
    return Secret(kind, plaintext[2 + name_len:], name)