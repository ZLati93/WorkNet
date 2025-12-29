"""
Direct RPC Server Tests
Tests for Python RPC server using XML-RPC client
"""

import pytest
import xmlrpc.client
import time
import os
from datetime import datetime
from bson import ObjectId


# RPC Server Configuration
RPC_HOST = os.getenv('RPC_HOST', 'localhost')
RPC_PORT = int(os.getenv('RPC_PORT', '8000'))
RPC_URL = f'http://{RPC_HOST}:{RPC_PORT}/RPC2'


@pytest.fixture(scope='module')
def rpc_client():
    """Create XML-RPC client"""
    client = xmlrpc.client.ServerProxy(RPC_URL, allow_none=True)
    
    # Wait for server to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            result = client.ping()
            if result and result.get('status') == 'ok':
                break
        except Exception:
            if i < max_retries - 1:
                time.sleep(1)
            else:
                raise Exception("RPC server not available")
    
    return client


@pytest.fixture
def sample_user_id():
    """Generate sample user ID"""
    return str(ObjectId())


@pytest.fixture
def sample_gig_id():
    """Generate sample gig ID"""
    return str(ObjectId())


@pytest.fixture
def sample_order_id():
    """Generate sample order ID"""
    return str(ObjectId())


class TestRPCServerHealth:
    """Test RPC server health and connectivity"""

    def test_ping(self, rpc_client):
        """Test ping endpoint"""
        result = rpc_client.ping()
        
        assert result is not None
        assert result.get('status') == 'ok'
        assert 'mongodb' in result


class TestUsersServiceRPC:
    """Test Users Service RPC methods"""

    def test_users_service_register(self, rpc_client, sample_user_id):
        """Test user registration via RPC"""
        username = f'testuser_{int(time.time())}'
        email = f'test_{int(time.time())}@example.com'
        password = 'password123'
        role = 'client'
        
        result = rpc_client.usersService.register(username, email, password, role)
        
        assert result is not None
        assert result.get('success') is True
        assert 'user_id' in result
        assert 'token' in result

    def test_users_service_login(self, rpc_client):
        """Test user login via RPC"""
        # First register a user
        username = f'testuser_{int(time.time())}'
        email = f'test_{int(time.time())}@example.com'
        password = 'password123'
        
        register_result = rpc_client.usersService.register(username, email, password, 'client')
        assert register_result.get('success') is True
        
        # Then login
        login_result = rpc_client.usersService.login(email, password)
        
        assert login_result is not None
        assert login_result.get('success') is True
        assert 'token' in login_result
        assert 'user_id' in login_result

    def test_users_service_get_by_id(self, rpc_client):
        """Test getting user by ID via RPC"""
        # Register a user first
        username = f'testuser_{int(time.time())}'
        email = f'test_{int(time.time())}@example.com'
        password = 'password123'
        
        register_result = rpc_client.usersService.register(username, email, password, 'client')
        user_id = register_result.get('user_id')
        
        # Get user by ID
        result = rpc_client.usersService.get_by_id(user_id)
        
        assert result is not None
        assert result.get('success') is True
        assert result.get('user') is not None
        assert result['user'].get('username') == username

    def test_users_service_get_all(self, rpc_client):
        """Test getting all users via RPC"""
        result = rpc_client.usersService.get_all(1, 10, {})
        
        assert result is not None
        assert result.get('success') is True
        assert 'users' in result
        assert isinstance(result['users'], list)

    def test_users_service_update_profile(self, rpc_client):
        """Test updating user profile via RPC"""
        # Register a user first
        username = f'testuser_{int(time.time())}'
        email = f'test_{int(time.time())}@example.com'
        password = 'password123'
        
        register_result = rpc_client.usersService.register(username, email, password, 'client')
        user_id = register_result.get('user_id')
        
        # Update profile
        updates = {'username': 'updateduser'}
        result = rpc_client.usersService.update_profile(user_id, updates)
        
        assert result is not None
        assert result.get('success') is True

    def test_users_service_get_stats(self, rpc_client):
        """Test getting user stats via RPC"""
        # Register a user first
        username = f'testuser_{int(time.time())}'
        email = f'test_{int(time.time())}@example.com'
        password = 'password123'
        
        register_result = rpc_client.usersService.register(username, email, password, 'client')
        user_id = register_result.get('user_id')
        
        # Get stats
        result = rpc_client.usersService.get_stats(user_id)
        
        assert result is not None
        assert result.get('success') is True
        assert 'stats' in result


class TestGigsServiceRPC:
    """Test Gigs Service RPC methods"""

    def test_gigs_service_create(self, rpc_client, sample_user_id):
        """Test creating gig via RPC"""
        # Note: This requires a valid user_id and category_id
        # In real scenario, you'd create these first
        
        gig_data = {
            'title': 'Test Gig',
            'description': 'This is a test gig description for testing purposes',
            'category_id': str(ObjectId()),
            'price': 50.0,
            'delivery_time': 3,
            'revision_number': 2
        }
        
        # This might fail if user/category don't exist, which is expected
        result = rpc_client.gigsService.create(sample_user_id, gig_data)
        
        # Should return a result (either success or error)
        assert result is not None

    def test_gigs_service_get_by_id(self, rpc_client, sample_gig_id):
        """Test getting gig by ID via RPC"""
        result = rpc_client.gigsService.get_by_id(sample_gig_id)
        
        # Should return a result (either success or error)
        assert result is not None

    def test_gigs_service_search(self, rpc_client):
        """Test searching gigs via RPC"""
        result = rpc_client.gigsService.search('test', {}, 1, 10)
        
        assert result is not None
        assert result.get('success') is True
        assert 'gigs' in result
        assert isinstance(result['gigs'], list)

    def test_gigs_service_get_by_user(self, rpc_client, sample_user_id):
        """Test getting gigs by user via RPC"""
        result = rpc_client.gigsService.get_by_user(sample_user_id, 1, 10)
        
        assert result is not None
        assert result.get('success') is True
        assert 'gigs' in result


class TestOrdersServiceRPC:
    """Test Orders Service RPC methods"""

    def test_orders_service_create(self, rpc_client, sample_gig_id, sample_user_id):
        """Test creating order via RPC"""
        result = rpc_client.ordersService.create(
            sample_gig_id,
            sample_user_id,
            1,  # quantity
            50.0  # total_price
        )
        
        # Should return a result
        assert result is not None

    def test_orders_service_get_by_id(self, rpc_client, sample_order_id):
        """Test getting order by ID via RPC"""
        result = rpc_client.ordersService.get_by_id(sample_order_id)
        
        assert result is not None

    def test_orders_service_get_all(self, rpc_client):
        """Test getting all orders via RPC"""
        result = rpc_client.ordersService.get_all({}, 1, 10)
        
        assert result is not None
        assert result.get('success') is True
        assert 'orders' in result

    def test_orders_service_update_status(self, rpc_client, sample_order_id):
        """Test updating order status via RPC"""
        result = rpc_client.ordersService.update_status(sample_order_id, 'in_progress')
        
        # Should return a result
        assert result is not None

    def test_orders_service_get_analytics(self, rpc_client, sample_user_id):
        """Test getting order analytics via RPC"""
        result = rpc_client.ordersService.get_analytics(sample_user_id, 'month')
        
        assert result is not None
        assert result.get('success') is True


class TestPaymentsServiceRPC:
    """Test Payments Service RPC methods"""

    def test_payments_service_create(self, rpc_client, sample_order_id, sample_user_id):
        """Test creating payment via RPC"""
        result = rpc_client.paymentsService.create(
            str(ObjectId()),
            sample_order_id,
            50.0,
            'stripe'
        )
        
        assert result is not None

    def test_payments_service_calculate_fees(self, rpc_client):
        """Test calculating payment fees via RPC"""
        result = rpc_client.paymentsService.calculate_fees(100.0)
        
        assert result is not None
        assert result.get('success') is True
        assert 'platform_fee' in result
        assert 'seller_amount' in result
        assert result['platform_fee'] + result['seller_amount'] == 100.0

    def test_payments_service_get_status(self, rpc_client):
        """Test getting payment status via RPC"""
        payment_id = str(ObjectId())
        result = rpc_client.paymentsService.get_status(payment_id)
        
        # Should return a result (either success or error)
        assert result is not None


class TestCategoriesServiceRPC:
    """Test Categories Service RPC methods"""

    def test_categories_service_get_all(self, rpc_client):
        """Test getting all categories via RPC"""
        result = rpc_client.categoriesService.get_all(1, 10)
        
        assert result is not None
        assert result.get('success') is True
        assert 'categories' in result

    def test_categories_service_get_by_id(self, rpc_client):
        """Test getting category by ID via RPC"""
        category_id = str(ObjectId())
        result = rpc_client.categoriesService.get_by_id(category_id)
        
        assert result is not None


class TestReviewsServiceRPC:
    """Test Reviews Service RPC methods"""

    def test_reviews_service_calculate_rating(self, rpc_client, sample_gig_id):
        """Test calculating gig rating via RPC"""
        result = rpc_client.reviewsService.calculate_rating(sample_gig_id)
        
        assert result is not None
        assert result.get('success') is True
        assert 'rating' in result


class TestMessagesServiceRPC:
    """Test Messages Service RPC methods"""

    def test_messages_service_get_unread_count(self, rpc_client, sample_user_id):
        """Test getting unread message count via RPC"""
        result = rpc_client.messagesService.get_unread_count(sample_user_id)
        
        assert result is not None
        assert result.get('success') is True
        assert 'count' in result


class TestNotificationsServiceRPC:
    """Test Notifications Service RPC methods"""

    def test_notifications_service_get_unread_count(self, rpc_client, sample_user_id):
        """Test getting unread notification count via RPC"""
        result = rpc_client.notificationsService.get_unread_count(sample_user_id)
        
        assert result is not None
        assert result.get('success') is True
        assert 'count' in result

    def test_notifications_service_send_bulk(self, rpc_client):
        """Test sending bulk notifications via RPC"""
        user_ids = [str(ObjectId()), str(ObjectId())]
        result = rpc_client.notificationsService.send_bulk(
            user_ids,
            'system',
            'Test notification',
            '/test'
        )
        
        assert result is not None
        assert result.get('success') is True


class TestRPCErrorHandling:
    """Test RPC error handling"""

    def test_invalid_method_call(self, rpc_client):
        """Test calling non-existent method"""
        with pytest.raises(Exception):
            rpc_client.nonExistentMethod()

    def test_invalid_parameters(self, rpc_client):
        """Test calling method with invalid parameters"""
        # This should return an error response, not raise exception
        result = rpc_client.usersService.get_by_id('invalid-id')
        
        assert result is not None
        assert result.get('success') is False

    def test_rpc_timeout_handling(self, rpc_client):
        """Test RPC timeout handling"""
        # Create client with short timeout
        import xmlrpc.client
        short_timeout_client = xmlrpc.client.ServerProxy(
            RPC_URL,
            allow_none=True,
            timeout=1  # 1 second timeout
        )
        
        # Normal call should work
        result = short_timeout_client.ping()
        assert result is not None


class TestRPCPerformance:
    """Test RPC performance"""

    def test_concurrent_requests(self, rpc_client):
        """Test handling concurrent RPC requests"""
        import concurrent.futures
        
        def make_request():
            return rpc_client.ping()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        assert len(results) == 10
        assert all(r.get('status') == 'ok' for r in results)

    def test_request_latency(self, rpc_client):
        """Test RPC request latency"""
        import time
        
        start_time = time.time()
        result = rpc_client.ping()
        end_time = time.time()
        
        latency = end_time - start_time
        
        assert result is not None
        assert latency < 1.0  # Should respond within 1 second

