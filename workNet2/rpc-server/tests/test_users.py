"""
Tests for Users Service
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from bson import ObjectId
from datetime import datetime
import bcrypt

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.users_service import UsersService


class TestUsersService:
    """Test suite for UsersService"""

    def test_create_user_success(self, mock_db, sample_user):
        """Test successful user creation"""
        service = UsersService(mock_db)
        
        # Mock collection methods
        mock_db.users.find_one.return_value = None  # No existing user
        mock_db.users.insert_one.return_value = Mock(inserted_id=sample_user['_id'])
        
        result = service.create(
            str(sample_user['_id']),
            sample_user['username'],
            sample_user['email'],
            sample_user['role']
        )
        
        assert result['success'] is True
        mock_db.users.find_one.assert_called_once()

    def test_create_user_duplicate_email(self, mock_db, sample_user):
        """Test user creation with duplicate email"""
        service = UsersService(mock_db)
        
        # Mock existing user
        mock_db.users.find_one.return_value = sample_user
        
        result = service.create(
            str(sample_user['_id']),
            sample_user['username'],
            sample_user['email'],
            sample_user['role']
        )
        
        assert result['success'] is False
        assert 'already exists' in result['error'].lower()

    def test_create_user_invalid_email(self, mock_db):
        """Test user creation with invalid email"""
        service = UsersService(mock_db)
        
        result = service.create(
            str(ObjectId()),
            'testuser',
            'invalid-email',
            'client'
        )
        
        assert result['success'] is False
        assert 'validation' in result['error'].lower() or 'email' in result['error'].lower()

    def test_create_user_invalid_username(self, mock_db):
        """Test user creation with invalid username"""
        service = UsersService(mock_db)
        
        result = service.create(
            str(ObjectId()),
            'ab',  # Too short
            'test@example.com',
            'client'
        )
        
        assert result['success'] is False

    def test_create_user_no_database(self):
        """Test user creation when database is not available"""
        service = UsersService(None)
        
        result = service.create(
            str(ObjectId()),
            'testuser',
            'test@example.com',
            'client'
        )
        
        assert result['success'] is False
        assert 'database' in result['error'].lower()

    def test_update_user_success(self, mock_db, sample_user):
        """Test successful user update"""
        service = UsersService(mock_db)
        
        updates = {'username': 'updateduser'}
        mock_db.users.find_one.return_value = sample_user
        mock_db.users.update_one.return_value = Mock(modified_count=1)
        
        result = service.update(str(sample_user['_id']), updates)
        
        assert result['success'] is True
        mock_db.users.update_one.assert_called_once()

    def test_update_user_not_found(self, mock_db):
        """Test user update when user doesn't exist"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = None
        mock_db.users.update_one.return_value = Mock(modified_count=0)
        
        result = service.update(str(ObjectId()), {'username': 'updated'})
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_delete_user_success(self, mock_db, sample_user):
        """Test successful user deletion"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = sample_user
        mock_db.orders.find_one.return_value = None  # No active orders
        mock_db.users.delete_one.return_value = Mock(deleted_count=1)
        
        result = service.delete(str(sample_user['_id']))
        
        assert result['success'] is True
        mock_db.users.delete_one.assert_called_once()

    def test_delete_user_with_active_orders(self, mock_db, sample_user):
        """Test user deletion when user has active orders"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = sample_user
        mock_db.orders.find_one.return_value = {'_id': ObjectId()}  # Active order exists
        
        result = service.delete(str(sample_user['_id']))
        
        assert result['success'] is False
        assert 'active orders' in result['error'].lower()

    def test_delete_user_not_found(self, mock_db):
        """Test user deletion when user doesn't exist"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = None
        
        result = service.delete(str(ObjectId()))
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_stats_success(self, mock_db, sample_user):
        """Test getting user statistics"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = sample_user
        
        result = service.get_stats(str(sample_user['_id']))
        
        assert result['success'] is True
        assert 'stats' in result
        assert result['stats']['total_gigs'] == 0

    def test_get_stats_user_not_found(self, mock_db):
        """Test getting stats for non-existent user"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = None
        
        result = service.get_stats(str(ObjectId()))
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_register_user_success(self, mock_db):
        """Test user registration"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = None  # No existing user
        mock_db.users.insert_one.return_value = Mock(
            inserted_id=ObjectId('507f1f77bcf86cd799439011')
        )
        
        result = service.register(
            'newuser',
            'newuser@example.com',
            'password123',
            'client'
        )
        
        assert result['success'] is True
        assert 'token' in result
        assert 'user_id' in result

    def test_register_user_duplicate_email(self, mock_db, sample_user):
        """Test registration with duplicate email"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = sample_user
        
        result = service.register(
            'newuser',
            sample_user['email'],
            'password123',
            'client'
        )
        
        assert result['success'] is False
        assert 'already exists' in result['error'].lower()

    def test_login_success(self, mock_db, sample_user):
        """Test successful login"""
        service = UsersService(mock_db)
        
        # Hash password
        hashed_password = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
        sample_user['password'] = hashed_password.decode('utf-8')
        
        mock_db.users.find_one.return_value = sample_user
        
        result = service.login('test@example.com', 'password123')
        
        assert result['success'] is True
        assert 'token' in result
        assert result['user_id'] == str(sample_user['_id'])

    def test_login_invalid_credentials(self, mock_db, sample_user):
        """Test login with invalid credentials"""
        service = UsersService(mock_db)
        
        hashed_password = bcrypt.hashpw('correctpassword'.encode('utf-8'), bcrypt.gensalt())
        sample_user['password'] = hashed_password.decode('utf-8')
        
        mock_db.users.find_one.return_value = sample_user
        
        result = service.login('test@example.com', 'wrongpassword')
        
        assert result['success'] is False
        assert 'invalid' in result['error'].lower() or 'credentials' in result['error'].lower()

    def test_login_user_not_found(self, mock_db):
        """Test login when user doesn't exist"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = None
        
        result = service.login('nonexistent@example.com', 'password123')
        
        assert result['success'] is False
        assert 'invalid' in result['error'].lower() or 'credentials' in result['error'].lower()

    def test_get_by_id_success(self, mock_db, sample_user):
        """Test getting user by ID"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = sample_user
        
        result = service.get_by_id(str(sample_user['_id']))
        
        assert result['success'] is True
        assert result['user']['username'] == sample_user['username']

    def test_get_by_id_not_found(self, mock_db):
        """Test getting non-existent user"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = None
        
        result = service.get_by_id(str(ObjectId()))
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_all_users_success(self, mock_db, sample_user):
        """Test getting all users with pagination"""
        service = UsersService(mock_db)
        
        users_list = [sample_user]
        mock_db.users.find.return_value.skip.return_value.limit.return_value = users_list
        mock_db.users.count_documents.return_value = 1
        
        result = service.get_all(1, 10, {})
        
        assert result['success'] is True
        assert len(result['users']) == 1
        assert result['total'] == 1

    def test_get_all_users_with_filters(self, mock_db, sample_user):
        """Test getting users with filters"""
        service = UsersService(mock_db)
        
        users_list = [sample_user]
        mock_db.users.find.return_value.skip.return_value.limit.return_value = users_list
        mock_db.users.count_documents.return_value = 1
        
        filters = {'role': 'client'}
        result = service.get_all(1, 10, filters)
        
        assert result['success'] is True
        mock_db.users.find.assert_called()

    def test_update_profile_success(self, mock_db, sample_user):
        """Test updating user profile"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = sample_user
        mock_db.users.update_one.return_value = Mock(modified_count=1)
        
        updates = {'profile': {'bio': 'New bio'}}
        result = service.update_profile(str(sample_user['_id']), updates)
        
        assert result['success'] is True

    def test_update_profile_password_not_allowed(self, mock_db, sample_user):
        """Test that password cannot be updated via update_profile"""
        service = UsersService(mock_db)
        
        mock_db.users.find_one.return_value = sample_user
        
        updates = {'password': 'newpassword'}
        result = service.update_profile(str(sample_user['_id']), updates)
        
        assert result['success'] is False
        assert 'password' in result['error'].lower()

    def test_change_password_success(self, mock_db, sample_user):
        """Test successful password change"""
        service = UsersService(mock_db)
        
        old_password = 'oldpassword123'
        hashed_old = bcrypt.hashpw(old_password.encode('utf-8'), bcrypt.gensalt())
        sample_user['password'] = hashed_old.decode('utf-8')
        
        mock_db.users.find_one.return_value = sample_user
        mock_db.users.update_one.return_value = Mock(modified_count=1)
        
        result = service.change_password(
            str(sample_user['_id']),
            old_password,
            'newpassword123'
        )
        
        assert result['success'] is True

    def test_change_password_invalid_old_password(self, mock_db, sample_user):
        """Test password change with wrong old password"""
        service = UsersService(mock_db)
        
        hashed_password = bcrypt.hashpw('correctpassword'.encode('utf-8'), bcrypt.gensalt())
        sample_user['password'] = hashed_password.decode('utf-8')
        
        mock_db.users.find_one.return_value = sample_user
        
        result = service.change_password(
            str(sample_user['_id']),
            'wrongpassword',
            'newpassword123'
        )
        
        assert result['success'] is False
        assert 'invalid' in result['error'].lower() or 'password' in result['error'].lower()

    # ------------------ Additional tests for hashing, JWT, and validation ------------------
    def test_hash_and_verify_password_methods(self):
        """Test UsersService.hash_password and verify_password"""
        service = UsersService(None)
        plain = 'My$ecureP4ssw0rd'
        hashed = service.hash_password(plain)
        assert isinstance(hashed, str)
        assert service.verify_password(plain, hashed) is True
        assert service.verify_password('wrongpass', hashed) is False

    def test_generate_and_verify_jwt_token(self):
        """Test token generation and verification using security utils"""
        from src.utils import security
        payload = {'id': '507f1f77bcf86cd799439011', 'role': 'client'}
        token = security.generate_token(payload)
        assert isinstance(token, str)
        decoded = security.verify_token(token)
        assert decoded.get('id') == payload['id']
        assert decoded.get('role') == payload['role']
        assert decoded.get('type') == 'access'

    @pytest.mark.parametrize('email,valid', [
        ('test@example.com', True),
        ('invalid-email', False),
        ('user@localhost', False),
        ('user.name+tag+sorting@example.com', True)
    ])
    def test_validate_email_format(self, email, valid):
        """Test validate_email with multiple inputs"""
        from src.utils import validators
        if valid:
            assert validators.validate_email(email) == email
        else:
            with pytest.raises(ValueError):
                validators.validate_email(email)

    @pytest.mark.parametrize('password,expected_strength,valid', [
        ('short', 'weak', False),
        ('Password1', 'medium', True),
        ('Str0ng!Passw0rd', 'strong', True),
        ('nopunctuation1', 'medium', True),
    ])
    def test_validate_password_strength(self, password, expected_strength, valid):
        """Test password strength validation"""
        from src.utils import security
        result = security.validate_password_strength(password)
        assert result['strength'] == expected_strength
        assert result['valid'] == valid or (valid is True and result['valid'] is True)

    @pytest.mark.parametrize('role,valid', [
        ('client', True),
        ('freelancer', True),
        ('admin', True),
        ('superuser', False),
        ('', False),
    ])
    def test_validate_user_role(self, role, valid):
        """Test validate_role function with valid and invalid roles"""
        from src.utils import validators
        if valid:
            assert validators.validate_role(role) == role
        else:
            with pytest.raises(ValueError):
                validators.validate_role(role)

