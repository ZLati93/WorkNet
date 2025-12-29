"""
Pytest Configuration and Fixtures
Common fixtures for testing RPC services
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from bson import ObjectId
from datetime import datetime


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    db = Mock()
    db.users = Mock()
    db.gigs = Mock()
    db.orders = Mock()
    db.payments = Mock()
    db.reviews = Mock()
    db.categories = Mock()
    db.messages = Mock()
    db.conversations = Mock()
    db.notifications = Mock()
    db.client = Mock()
    return db


@pytest.fixture
def mock_collection():
    """Mock MongoDB collection"""
    collection = Mock()
    collection.find_one = Mock()
    collection.find = Mock()
    collection.insert_one = Mock()
    collection.update_one = Mock()
    collection.delete_one = Mock()
    collection.count_documents = Mock()
    collection.aggregate = Mock()
    return collection


@pytest.fixture
def sample_user():
    """Sample user data"""
    return {
        '_id': ObjectId('507f1f77bcf86cd799439011'),
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'hashed_password',
        'role': 'client',
        'is_active': True,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'profile': {
            'bio': '',
            'skills': [],
            'languages': [],
            'country': '',
            'profile_picture': ''
        },
        'stats': {
            'total_gigs': 0,
            'total_orders': 0,
            'total_reviews': 0,
            'average_rating': 0.0,
            'earnings': 0.0,
            'spent': 0.0
        }
    }


@pytest.fixture
def sample_gig():
    """Sample gig data"""
    return {
        '_id': ObjectId('507f1f77bcf86cd799439020'),
        'user_id': ObjectId('507f1f77bcf86cd799439011'),
        'category_id': ObjectId('507f1f77bcf86cd799439030'),
        'title': 'Test Gig',
        'description': 'This is a test gig description',
        'price': 50.0,
        'delivery_time': 3,
        'revision_number': 2,
        'status': 'active',
        'is_active': True,
        'average_rating': 4.5,
        'review_count': 10,
        'views': 100,
        'sales': 5,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }


@pytest.fixture
def sample_order():
    """Sample order data"""
    return {
        '_id': ObjectId('507f1f77bcf86cd799439040'),
        'gig_id': ObjectId('507f1f77bcf86cd799439020'),
        'buyer_id': ObjectId('507f1f77bcf86cd799439011'),
        'seller_id': ObjectId('507f1f77bcf86cd799439012'),
        'price': 50.0,
        'status': 'pending',
        'requirements': 'Test requirements',
        'delivery_date': datetime.utcnow(),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }


@pytest.fixture
def sample_payment():
    """Sample payment data"""
    return {
        '_id': ObjectId('507f1f77bcf86cd799439050'),
        'order_id': ObjectId('507f1f77bcf86cd799439040'),
        'user_id': ObjectId('507f1f77bcf86cd799439011'),
        'amount': 50.0,
        'status': 'pending',
        'payment_method': 'stripe',
        'transaction_id': 'txn_123456',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }


@pytest.fixture
def mock_session():
    """Mock MongoDB session for transactions"""
    session = Mock()
    session.start_transaction = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    return session


@pytest.fixture
def mock_transaction_context(mock_db, mock_session):
    """Mock transaction context manager"""
    mock_db.client.start_session.return_value = mock_session
    return mock_db

