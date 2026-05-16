"""Tests for security module."""

import pytest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password(self):
        """Test that password hashing works."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        """Test verification of correct password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test verification of wrong password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_unique(self):
        """Test that same password produces different hashes (salt)."""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_valid_token(self):
        """Test decoding of valid token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "testuser"

    def test_decode_invalid_token(self):
        """Test decoding of invalid token."""
        decoded = decode_access_token("invalid.token.here")
        
        assert decoded is None

    def test_token_contains_expiration(self):
        """Test that token contains expiration."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert "exp" in decoded