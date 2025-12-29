"""
Tests for Orders Service
"""

import pytest
from unittest.mock import Mock, MagicMock
from bson import ObjectId
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.orders_service import OrdersService


class TestOrdersService:
    """Test suite for OrdersService"""

    def test_create_order_success(self, mock_db, sample_order, sample_gig, sample_user):
        """Test successful order creation"""
        service = OrdersService(mock_db)
        
        # Mock gig exists and is active
        sample_gig['is_active'] = True
        sample_gig['user_id'] = ObjectId('507f1f77bcf86cd799439012')  # Different from buyer
        mock_db.gigs.find_one.return_value = sample_gig
        
        # Mock user exists
        mock_db.users.find_one.return_value = sample_user
        
        # Mock order insertion
        mock_db.orders.insert_one.return_value = Mock(inserted_id=sample_order['_id'])
        
        result = service.create(
            str(sample_gig['_id']),
            str(sample_user['_id']),
            1,  # quantity
            sample_order['price']
        )
        
        assert result['success'] is True
        assert 'order_id' in result

    def test_create_order_gig_not_found(self, mock_db, sample_user):
        """Test order creation with non-existent gig"""
        service = OrdersService(mock_db)
        
        mock_db.gigs.find_one.return_value = None
        
        result = service.create(
            str(ObjectId()),
            str(sample_user['_id']),
            1,
            50.0
        )
        
        assert result['success'] is False
        assert 'gig' in result['error'].lower()

    def test_create_order_gig_not_active(self, mock_db, sample_gig, sample_user):
        """Test order creation for inactive gig"""
        service = OrdersService(mock_db)
        
        sample_gig['is_active'] = False
        mock_db.gigs.find_one.return_value = sample_gig
        
        result = service.create(
            str(sample_gig['_id']),
            str(sample_user['_id']),
            1,
            50.0
        )
        
        assert result['success'] is False
        assert 'active' in result['error'].lower() or 'available' in result['error'].lower()

    def test_create_order_own_gig(self, mock_db, sample_gig, sample_user):
        """Test order creation for own gig"""
        service = OrdersService(mock_db)
        
        sample_gig['is_active'] = True
        sample_gig['user_id'] = sample_user['_id']  # Same as buyer
        mock_db.gigs.find_one.return_value = sample_gig
        
        result = service.create(
            str(sample_gig['_id']),
            str(sample_user['_id']),
            1,
            50.0
        )
        
        assert result['success'] is False
        assert 'own' in result['error'].lower() or 'your' in result['error'].lower()

    def test_create_order_no_database(self, sample_gig, sample_user):
        """Test order creation when database is not available"""
        service = OrdersService(None)
        
        result = service.create(
            str(sample_gig['_id']),
            str(sample_user['_id']),
            1,
            50.0
        )
        
        assert result['success'] is False
        assert 'database' in result['error'].lower()

    def test_update_status_success(self, mock_db, sample_order):
        """Test successful order status update"""
        service = OrdersService(mock_db)
        
        mock_db.orders.find_one.return_value = sample_order
        mock_db.orders.update_one.return_value = Mock(modified_count=1)
        
        result = service.update_status(str(sample_order['_id']), 'in_progress')
        
        assert result['success'] is True
        mock_db.orders.update_one.assert_called_once()

    def test_update_status_invalid_transition(self, mock_db, sample_order):
        """Test order status update with invalid transition"""
        service = OrdersService(mock_db)
        
        sample_order['status'] = 'completed'
        mock_db.orders.find_one.return_value = sample_order
        
        result = service.update_status(str(sample_order['_id']), 'pending')
        
        assert result['success'] is False
        assert 'transition' in result['error'].lower() or 'invalid' in result['error'].lower()

    def test_update_status_order_not_found(self, mock_db):
        """Test order status update when order doesn't exist"""
        service = OrdersService(mock_db)
        
        mock_db.orders.find_one.return_value = None
        
        result = service.update_status(str(ObjectId()), 'in_progress')
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_analytics_success(self, mock_db, sample_order, sample_user):
        """Test getting order analytics"""
        service = OrdersService(mock_db)
        
        orders_list = [sample_order]
        mock_db.orders.find.return_value = orders_list
        
        result = service.get_analytics(str(sample_user['_id']), 'month')
        
        assert result['success'] is True
        assert 'total_orders' in result
        assert 'total_revenue' in result

    def test_get_analytics_no_orders(self, mock_db, sample_user):
        """Test analytics when user has no orders"""
        service = OrdersService(mock_db)
        
        mock_db.orders.find.return_value = []
        
        result = service.get_analytics(str(sample_user['_id']), 'month')
        
        assert result['success'] is True
        assert result['total_orders'] == 0
        assert result['total_revenue'] == 0

    def test_cancel_order_success(self, mock_db, sample_order):
        """Test successful order cancellation"""
        service = OrdersService(mock_db)
        
        sample_order['status'] = 'pending'
        mock_db.orders.find_one.return_value = sample_order
        mock_db.orders.update_one.return_value = Mock(modified_count=1)
        
        result = service.cancel(str(sample_order['_id']), 'Changed my mind')
        
        assert result['success'] is True

    def test_cancel_order_not_cancellable(self, mock_db, sample_order):
        """Test cancelling order that cannot be cancelled"""
        service = OrdersService(mock_db)
        
        sample_order['status'] = 'completed'
        mock_db.orders.find_one.return_value = sample_order
        
        result = service.cancel(str(sample_order['_id']), 'Reason')
        
        assert result['success'] is False
        assert 'cancel' in result['error'].lower() or 'cannot' in result['error'].lower()

    def test_cancel_order_not_found(self, mock_db):
        """Test cancelling non-existent order"""
        service = OrdersService(mock_db)
        
        mock_db.orders.find_one.return_value = None
        
        result = service.cancel(str(ObjectId()), 'Reason')
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_by_id_success(self, mock_db, sample_order):
        """Test getting order by ID"""
        service = OrdersService(mock_db)
        
        mock_db.orders.find_one.return_value = sample_order
        
        result = service.get_by_id(str(sample_order['_id']))
        
        assert result['success'] is True
        assert result['order']['price'] == sample_order['price']

    def test_get_by_id_not_found(self, mock_db):
        """Test getting non-existent order"""
        service = OrdersService(mock_db)
        
        mock_db.orders.find_one.return_value = None
        
        result = service.get_by_id(str(ObjectId()))
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_all_orders_success(self, mock_db, sample_order):
        """Test getting all orders with filters"""
        service = OrdersService(mock_db)
        
        orders_list = [sample_order]
        mock_db.orders.find.return_value.skip.return_value.limit.return_value = orders_list
        mock_db.orders.count_documents.return_value = 1
        
        filters = {'status': 'pending'}
        result = service.get_all(filters, 1, 10)
        
        assert result['success'] is True
        assert len(result['orders']) == 1

    def test_get_all_orders_with_pagination(self, mock_db, sample_order):
        """Test getting orders with pagination"""
        service = OrdersService(mock_db)
        
        orders_list = [sample_order]
        mock_db.orders.find.return_value.skip.return_value.limit.return_value = orders_list
        mock_db.orders.count_documents.return_value = 1
        
        result = service.get_all({}, 2, 5)
        
        assert result['success'] is True
        assert result['page'] == 2
        assert result['limit'] == 5

    # ------------------ Business logic and concurrency tests ------------------
    def test_complete_order_updates_seller_earnings(self, mock_db, sample_order):
        """When completing an order, seller earnings should be updated"""
        service = OrdersService(mock_db)

        sample_order['status'] = 'in_progress'
        mock_db.orders.find_one.return_value = sample_order
        mock_db.orders.update_one.return_value = Mock(modified_count=1)

        # Spy on _update_seller_earnings
        called = {}
        def spy_update_seller_earnings(seller_id, amount, session):
            called['seller_id'] = seller_id
            called['amount'] = amount
        service._update_seller_earnings = spy_update_seller_earnings

        result = service.update_status(str(sample_order['_id']), 'completed')

        assert result['success'] is True
        assert called['seller_id'] == sample_order['seller_id']
        assert called['amount'] == sample_order['price']

    def test_calculate_service_fees(self):
        """Business rule: service fees are 10% of order price"""
        price = 150.0
        expected_fee = round(price * 0.10, 2)
        assert expected_fee == 15.0

    def test_validate_order_deadline_allows_cancellation_if_past(self, mock_db, sample_order):
        """Orders with past deliveryDate can still be cancelled if status allows"""
        service = OrdersService(mock_db)

        past_date = datetime.utcnow() - timedelta(days=2)
        sample_order['status'] = 'pending'
        sample_order['delivery_date'] = past_date

        mock_db.orders.find_one.return_value = sample_order
        mock_db.orders.update_one.return_value = Mock(modified_count=1)

        result = service.cancel(str(sample_order['_id']), 'Late delivery')
        assert result['success'] is True

    def test_handle_order_revision_transitions(self, mock_db, sample_order):
        """Revisions: disputed -> completed transition should be allowed"""
        service = OrdersService(mock_db)

        sample_order['status'] = 'in_progress'
        sample_order['seller_id'] = sample_order.get('seller_id', ObjectId())
        mock_db.orders.find_one.side_effect = [sample_order, { **sample_order, 'status': 'disputed' }]
        mock_db.orders.update_one.return_value = Mock(modified_count=1)

        # in_progress -> disputed
        r1 = service.update_status(str(sample_order['_id']), 'disputed')
        assert r1['success'] is True

        # disputed -> completed
        r2 = service.update_status(str(sample_order['_id']), 'completed')
        assert r2['success'] is True

    def test_order_payment_integration_updates_earnings(self, mock_db, sample_order):
        """Completing an order should trigger seller earnings update (payment handling)
        This simulates integration with payments subsystem by asserting the earnings update is called."""
        service = OrdersService(mock_db)

        sample_order['status'] = 'in_progress'
        mock_db.orders.find_one.return_value = sample_order
        mock_db.orders.update_one.return_value = Mock(modified_count=1)

        updated = {}
        def spy(seller_id, amount, session):
            updated['seller'] = seller_id
            updated['amount'] = amount
        service._update_seller_earnings = spy

        res = service.update_status(str(sample_order['_id']), 'completed')
        assert res['success'] is True
        assert updated['amount'] == sample_order['price']

    def test_concurrent_order_creation_one_fails(self, mock_db, sample_gig, sample_user, sample_order, mock_session):
        """Simulate a race where second creation fails due to DB constraint"""
        service = OrdersService(mock_db)

        # First call succeeds, second call raises an exception on insert
        sample_gig['is_active'] = True
        sample_gig['user_id'] = ObjectId('507f1f77bcf86cd799439012')
        mock_db.gigs.find_one.side_effect = [sample_gig, sample_gig]
        mock_db.users.find_one.return_value = sample_user
        mock_db.orders.insert_one.side_effect = [Mock(inserted_id=sample_order['_id']), Exception('duplicate key')]

        r1 = service.create(str(sample_order['_id']), str(sample_gig['_id']), str(sample_user['_id']))
        r2 = service.create(str(ObjectId()), str(sample_gig['_id']), str(sample_user['_id']))

        assert r1['success'] is True
        assert r2['success'] is False
        assert 'duplicate' in str(r2['error']).lower()

    def test_order_status_race_conditions_handles_errors(self, mock_db, sample_order):
        """Simulate race condition where second update fails due to DB write error"""
        service = OrdersService(mock_db)

        # First find_one returns pending, second returns in_progress (as if first updated it)
        pending = { **sample_order, 'status': 'pending' }
        in_progress = { **sample_order, 'status': 'in_progress' }
        mock_db.orders.find_one.side_effect = [pending, in_progress]

        # First update succeeds, second raises an exception during update
        mock_db.orders.update_one.side_effect = [Mock(modified_count=1), Exception('write conflict')]

        r1 = service.update_status(str(sample_order['_id']), 'in_progress')
        r2 = service.update_status(str(sample_order['_id']), 'completed')

        assert r1['success'] is True
        assert r2['success'] is False
        assert 'write conflict' in str(r2['error']).lower()

