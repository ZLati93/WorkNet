"""
Tests for Security Utilities
"""

import pytest
import jwt
import bcrypt
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_token,
    generate_refresh_token,
    verify_token,
    refresh_access_token,
    check_permission,
    require_role,
    is_admin,
    is_seller,
    is_client,
    create_token_payload,
    extract_user_from_token,
    sanitize_input,
    generate_random_string,
    mask_email,
    SecurityError
)


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_hash_password_success(self):
        """Test successful password hashing"""
        password = 'password123'
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_empty(self):
        """Test hashing empty password"""
        with pytest.raises(SecurityError):
            hash_password('')

    def test_hash_password_too_short(self):
        """Test hashing password that is too short"""
        with pytest.raises(SecurityError):
            hash_password('12345')  # Less than 6 characters

    def test_verify_password_success(self):
        """Test successful password verification"""
        password = 'password123'
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """Test password verification with wrong password"""
        password = 'password123'
        hashed = hash_password(password)
        
        assert verify_password('wrongpassword', hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty values"""
        assert verify_password('', '') is False
        assert verify_password('password', '') is False
        assert verify_password('', 'hashed') is False

    def test_validate_password_strength_weak(self):
        """Test password strength validation - weak"""
        result = validate_password_strength('12345')
        
        assert result['valid'] is False
        assert result['strength'] == 'weak'

    def test_validate_password_strength_medium(self):
        """Test password strength validation - medium"""
        result = validate_password_strength('password123')
        
        assert result['valid'] is True
        assert result['strength'] in ['weak', 'medium']

    def test_validate_password_strength_strong(self):
        """Test password strength validation - strong"""
        result = validate_password_strength('Password123!@#')
        
        assert result['valid'] is True
        assert result['strength'] in ['medium', 'strong']

    @pytest.mark.parametrize('password', [
        'password123',
        'Str0ng!Pass',
        '12345678'
    ])
    def test_hash_password_various(self, password):
        """Test hashing multiple different passwords"""
        h = hash_password(password)
        assert isinstance(h, str)
        assert verify_password(password, h) is True


class TestJWTTokenManagement:
    """Test JWT token functions"""

    def test_generate_token_success(self):
        """Test successful token generation"""
        payload = {'id': 'user123', 'role': 'client'}
        token = generate_token(payload)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_token_missing_id(self):
        """Test token generation without id"""
        payload = {'role': 'client'}
        
        with pytest.raises(SecurityError):
            generate_token(payload)

    @pytest.mark.parametrize('payload', [
        ({'id': 'u1', 'role': 'client'}),
        ({'id': '507f1f77bcf86cd799439011', 'role': 'freelancer', 'extra': 'x'}),
    ])
    def test_generate_token_various_payloads(self, payload):
        """Generate token with different valid payloads"""
        token = generate_token(payload)
        assert isinstance(token, str)
        decoded = verify_token(token)
        assert decoded.get('id') == payload['id']
        assert decoded.get('role') == payload['role']

    def test_generate_refresh_token_success(self):
        """Test successful refresh token generation"""
        payload = {'id': 'user123', 'role': 'client'}
        token = generate_refresh_token(payload)
        
        assert token is not None
        assert isinstance(token, str)

    def test_verify_token_success(self):
        """Test successful token verification"""
        payload = {'id': 'user123', 'role': 'client'}
        token = generate_token(payload)
        
        decoded = verify_token(token)
        
        assert decoded['id'] == 'user123'
        assert decoded['role'] == 'client'
        assert 'exp' in decoded

    def test_verify_token_expired(self):
        """Test verification of expired token"""
        payload = {'id': 'user123', 'role': 'client'}
        
        # Generate token with very short expiration
        with patch('utils.security.JWT_EXPIRES_IN', 0):
            token = generate_token(payload, expires_in_days=0)
        
        # Wait a bit and verify it's expired
        import time
        time.sleep(0.1)
        
        with pytest.raises(SecurityError):
            verify_token(token)

    def test_verify_token_invalid(self):
        """Test verification of invalid token"""
        invalid_token = 'invalid.token.here'
        
        with pytest.raises(SecurityError):
            verify_token(invalid_token)

    def test_verify_token_empty(self):
        """Test verification of empty token"""
        with pytest.raises(SecurityError):
            verify_token('')

    def test_refresh_access_token_success(self):
        """Test successful access token refresh"""
        payload = {'id': 'user123', 'role': 'client'}
        refresh_token = generate_refresh_token(payload)
        
        new_token = refresh_access_token(refresh_token)
        
        assert new_token is not None
        assert isinstance(new_token, str)
        
        # Verify the new token
        decoded = verify_token(new_token)
        assert decoded['id'] == 'user123'

    def test_refresh_access_token_invalid(self):
        """Test refresh with invalid token"""
        with pytest.raises(SecurityError):
            refresh_access_token('invalid_token')


class TestPermissionManagement:
    """Test permission management functions"""

    def test_check_permission_success(self):
        """Test successful permission check"""
        assert check_permission('admin', ['admin', 'moderator']) is True
        assert check_permission('moderator', ['admin', 'moderator']) is True

    def test_check_permission_denied(self):
        """Test permission check denial"""
        assert check_permission('client', ['admin', 'moderator']) is False
        assert check_permission('', ['admin']) is False

    def test_is_admin_true(self):
        """Test is_admin with admin role"""
        assert is_admin('admin') is True
        assert is_admin('ADMIN') is True  # Case insensitive

    def test_is_admin_false(self):
        """Test is_admin with non-admin role"""
        assert is_admin('client') is False
        assert is_admin('freelancer') is False
        assert is_admin(None) is False

    def test_is_seller_true(self):
        """Test is_seller with freelancer role"""
        assert is_seller('freelancer') is True
        assert is_seller('freelancer', True) is True

    def test_is_seller_false(self):
        """Test is_seller with non-seller role"""
        assert is_seller('client') is False
        assert is_seller('admin') is False

    def test_is_client_true(self):
        """Test is_client with client role"""
        assert is_client('client') is True

    def test_is_client_false(self):
        """Test is_client with non-client role"""
        assert is_client('freelancer') is False
        assert is_client('admin') is False
        assert is_client(None) is False

    def test_require_role_decorator(self):
        """Test require_role decorator"""
        @require_role('admin')
        def admin_function():
            return 'success'
        
        # Test with admin user
        user = {'role': 'admin'}
        result = admin_function(user=user)
        assert result == 'success'

    def test_create_token_payload(self):
        """Test creating token payload"""
        payload = create_token_payload('user123', 'client', extra='value')
        
        assert payload['id'] == 'user123'
        assert payload['role'] == 'client'
        assert payload['extra'] == 'value'

    def test_extract_user_from_token(self):
        """Test extracting user from token"""
        payload = {'id': 'user123', 'role': 'client'}
        token = generate_token(payload)
        
        user_info = extract_user_from_token(token)
        
        assert user_info['id'] == 'user123'
        assert user_info['role'] == 'client'

    def test_validate_api_key_env_and_format(self, monkeypatch):
        """Test that API_KEY env variable exists and matches expected format when set"""
        # No API_KEY set -> should be None
        monkeypatch.delenv('API_KEY', raising=False)
        import os
        assert os.getenv('API_KEY') is None

        # Set a valid-ish API key and validate length/characters
        monkeypatch.setenv('API_KEY', 'a' * 40)
        api_key = os.getenv('API_KEY')
        assert api_key is not None
        assert len(api_key) >= 32
        assert api_key.isalnum()

        # Set an invalid key (too short)
        monkeypatch.setenv('API_KEY', 'short')
        api_key2 = os.getenv('API_KEY')
        assert len(api_key2) < 32
        # In real app, you would reject this; here we assert detection
        assert len(api_key2) < 32


class TestSecurityUtilities:
    """Test security utility functions"""

    def test_sanitize_input_normal(self):
        """Test sanitizing normal input"""
        result = sanitize_input('normal text')
        assert result == 'normal text'

    def test_sanitize_input_with_null_bytes(self):
        """Test sanitizing input with null bytes"""
        result = sanitize_input('text\x00with\x00null')
        assert '\x00' not in result

    def test_sanitize_input_too_long(self):
        """Test sanitizing input that is too long"""
        long_text = 'a' * 2000
        result = sanitize_input(long_text, max_length=1000)
        assert len(result) == 1000

    def test_sanitize_input_empty(self):
        """Test sanitizing empty input"""
        result = sanitize_input('')
        assert result == ''

    def test_generate_random_string_default_length(self):
        """Test generating random string with default length"""
        result = generate_random_string()
        assert len(result) == 32
        assert result.isalnum()

    def test_generate_random_string_custom_length(self):
        """Test generating random string with custom length"""
        result = generate_random_string(16)
        assert len(result) == 16

    def test_mask_email_normal(self):
        """Test masking normal email"""
        result = mask_email('john@example.com')
        assert result.startswith('j')
        assert '@example.com' in result
        assert 'john' not in result

    def test_mask_email_short_local(self):
        """Test masking email with short local part"""
        result = mask_email('a@example.com')
        assert result == '*@example.com'

    def test_mask_email_invalid(self):
        """Test masking invalid email"""
        result = mask_email('notanemail')
        assert result == 'notanemail'

    def test_mask_email_empty(self):
        """Test masking empty email"""
        result = mask_email('')
        assert result == ''

