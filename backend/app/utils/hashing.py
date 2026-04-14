import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()


def generate_api_key() -> str:
    return f"rag_{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    return _ph.hash(key)


def verify_api_key(key: str, key_hash: str) -> bool:
    try:
        return _ph.verify(key_hash, key)
    except VerifyMismatchError:
        return False


def hash_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
