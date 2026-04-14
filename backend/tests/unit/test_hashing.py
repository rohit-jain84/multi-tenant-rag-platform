"""Tests for API key generation, hashing, verification, and content hashing."""

from app.utils.hashing import generate_api_key, hash_api_key, hash_content, verify_api_key


class TestGenerateApiKey:
    def test_starts_with_prefix(self):
        key = generate_api_key()
        assert key.startswith("rag_")

    def test_sufficient_length(self):
        key = generate_api_key()
        # rag_ prefix + 32 bytes of base64 ≈ 47 chars total
        assert len(key) > 40

    def test_unique_each_call(self):
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100


class TestHashAndVerify:
    def test_verify_correct_key(self):
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert verify_api_key(key, hashed) is True

    def test_verify_wrong_key(self):
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert verify_api_key("rag_wrong_key_here", hashed) is False

    def test_different_keys_produce_different_hashes(self):
        h1 = hash_api_key("rag_key_one")
        h2 = hash_api_key("rag_key_two")
        assert h1 != h2


class TestHashContent:
    def test_deterministic(self):
        content = b"hello world"
        assert hash_content(content) == hash_content(content)

    def test_different_content_different_hash(self):
        assert hash_content(b"aaa") != hash_content(b"bbb")

    def test_returns_hex_string(self):
        h = hash_content(b"test")
        assert len(h) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in h)
