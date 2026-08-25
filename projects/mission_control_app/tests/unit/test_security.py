"""Unit tests for security utilities."""

from datetime import UTC, datetime, timedelta

from checklists_api.config import ALGORITHM, SECRET_KEY
from checklists_api.security import bcrypt_context, create_access_token
from jose import jwt


class TestCreateAccessToken:
    def test_token_contains_expected_payload(self):
        """Verify the token contains the expected payload."""
        # timedelta is in minutes
        expires = timedelta(minutes=30)
        token = create_access_token("testuser", 1, "user", expires)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert payload["id"] == 1
        assert payload["role"] == "user"
        assert "exp" in payload

    def test_token_expiry_is_in_future(self):
        """Verify the token expiry is in the future."""
        expires = timedelta(minutes=30)
        token = create_access_token("testuser", 1, "user", expires)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], UTC)
        now = datetime.now(UTC)
        assert exp > now
        assert (exp - now) < timedelta(minutes=31)

    def test_different_users_produce_different_tokens(self):
        """Verify different users produce different tokens."""
        token1 = create_access_token("user1", 1, "user", timedelta(minutes=30))
        token2 = create_access_token("user2", 2, "user", timedelta(minutes=30))
        assert token1 != token2


class TestBcryptContext:
    def test_hash_and_verify_success(self):
        """Verify that a password can be hashed and verified."""
        password = "mysecretpassword"
        hashed = bcrypt_context.hash(password)
        assert hashed != password
        assert bcrypt_context.verify(password, hashed)

    def test_verify_wrong_password_fails(self):
        """Verify that a wrong password fails verification."""
        password = "mysecretpassword"
        hashed = bcrypt_context.hash(password)
        assert not bcrypt_context.verify("wrongpassword", hashed)

    def test_different_hashes_each_call(self):
        """Verify that different hashes are produced for the same password."""
        password = "samepassword"
        hash1 = bcrypt_context.hash(password)
        hash2 = bcrypt_context.hash(password)
        assert hash1 != hash2
        assert bcrypt_context.verify(password, hash1)
        assert bcrypt_context.verify(password, hash2)
