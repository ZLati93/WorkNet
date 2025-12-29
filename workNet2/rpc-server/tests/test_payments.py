"""
Tests for Payments Service
"""

import pytest
from unittest.mock import Mock, MagicMock
from bson import ObjectId
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.payments_service import PaymentsService


class TestPaymentsService:
    """Test suite for PaymentsService"""

    def test_create_payment_success(self, mock_db, sample_payment, sample_order):
        """Test successful payment creation"""
        service = PaymentsService(mock_db)
        
        mock_db.orders.find_one.return_value = sample_order
        mock_db.payments.insert_one.return_value = Mock(inserted_id=sample_payment['_id'])
        
        result = service.create(
            str(sample_payment['_id']),
            str(sample_order['_id']),
            sample_payment['amount'],
            sample_payment['payment_method']
        )
        
        assert result['success'] is True
        assert 'payment_id' in result
        assert 'platform_fee' in result
        assert 'seller_amount' in result

    def test_create_payment_order_not_found(self, mock_db, sample_payment):
        """Test payment creation with non-existent order"""
        service = PaymentsService(mock_db)
        
        mock_db.orders.find_one.return_value = None
        
        result = service.create(
            str(sample_payment['_id']),
            str(ObjectId()),
            50.0,
            'stripe'
        )
        
        assert result['success'] is False
        assert 'order' in result['error'].lower()

    def test_create_payment_invalid_method(self, mock_db, sample_payment, sample_order):
        """Test payment creation with invalid payment method"""
        service = PaymentsService(mock_db)
        
        mock_db.orders.find_one.return_value = sample_order
        
        result = service.create(
            str(sample_payment['_id']),
            str(sample_order['_id']),
            50.0,
            'invalid_method'
        )
        
        assert result['success'] is False
        assert 'invalid' in result['error'].lower() or 'method' in result['error'].lower()

    def test_create_payment_no_database(self, sample_payment, sample_order):
        """Test payment creation when database is not available"""
        service = PaymentsService(None)
        
        result = service.create(
            str(sample_payment['_id']),
            str(sample_order['_id']),
            50.0,
            'stripe'
        )
        
        assert result['success'] is False
        assert 'database' in result['error'].lower()

    def test_process_payment_success(self, mock_db, sample_payment, sample_order, sample_user):
        """Test successful payment processing"""
        service = PaymentsService(mock_db)
        
        sample_payment['status'] = 'pending'
        mock_db.payments.find_one.return_value = sample_payment
        
        sample_order['seller_id'] = ObjectId('507f1f77bcf86cd799439012')
        mock_db.orders.find_one.return_value = sample_order
        
        mock_db.payments.update_one.return_value = Mock(modified_count=1)
        mock_db.orders.update_one.return_value = Mock(modified_count=1)
        mock_db.users.update_one.return_value = Mock(modified_count=1)
        
        result = service.process(str(sample_payment['_id']), 'completed')
        
        assert result['success'] is True
        assert result['status'] == 'completed'

    def test_process_payment_invalid_status_transition(self, mock_db, sample_payment):
        """Test payment processing with invalid status transition"""
        service = PaymentsService(mock_db)
        
        sample_payment['status'] = 'completed'
        mock_db.payments.find_one.return_value = sample_payment
        
        result = service.process(str(sample_payment['_id']), 'pending')
        
        assert result['success'] is False
        assert 'change' in result['error'].lower() or 'transition' in result['error'].lower()

    def test_process_payment_not_found(self, mock_db):
        """Test processing non-existent payment"""
        service = PaymentsService(mock_db)
        
        mock_db.payments.find_one.return_value = None
        
        result = service.process(str(ObjectId()), 'completed')
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_refund_payment_success(self, mock_db, sample_payment, sample_order, sample_user):
        """Test successful payment refund"""
        service = PaymentsService(mock_db)
        
        sample_payment['status'] = 'completed'
        sample_payment['amount'] = 100.0
        mock_db.payments.find_one.return_value = sample_payment
        
        sample_order['seller_id'] = ObjectId('507f1f77bcf86cd799439012')
        mock_db.orders.find_one.return_value = sample_order
        
        mock_db.payments.update_one.return_value = Mock(modified_count=1)
        mock_db.users.update_one.return_value = Mock(modified_count=1)
        
        result = service.refund(str(sample_payment['_id']), 50.0)
        
        assert result['success'] is True
        assert result['refund_amount'] == 50.0

    def test_refund_payment_not_completed(self, mock_db, sample_payment):
        """Test refunding payment that is not completed"""
        service = PaymentsService(mock_db)
        
        sample_payment['status'] = 'pending'
        mock_db.payments.find_one.return_value = sample_payment
        
        result = service.refund(str(sample_payment['_id']), 50.0)
        
        assert result['success'] is False
        assert 'completed' in result['error'].lower()

    def test_refund_payment_amount_exceeds_original(self, mock_db, sample_payment):
        """Test refunding more than original payment amount"""
        service = PaymentsService(mock_db)
        
        sample_payment['status'] = 'completed'
        sample_payment['amount'] = 50.0
        mock_db.payments.find_one.return_value = sample_payment
        
        result = service.refund(str(sample_payment['_id']), 100.0)
        
        assert result['success'] is False
        assert 'exceed' in result['error'].lower() or 'amount' in result['error'].lower()

    def test_refund_payment_not_found(self, mock_db):
        """Test refunding non-existent payment"""
        service = PaymentsService(mock_db)
        
        mock_db.payments.find_one.return_value = None
        
        result = service.refund(str(ObjectId()), 50.0)
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_status_success(self, mock_db, sample_payment):
        """Test getting payment status"""
        service = PaymentsService(mock_db)
        
        mock_db.payments.find_one.return_value = sample_payment
        
        result = service.get_status(str(sample_payment['_id']))
        
        assert result['success'] is True
        assert result['status'] == sample_payment['status']
        assert result['amount'] == sample_payment['amount']

    def test_get_status_not_found(self, mock_db):
        """Test getting status for non-existent payment"""
        service = PaymentsService(mock_db)
        
        mock_db.payments.find_one.return_value = None
        
        result = service.get_status(str(ObjectId()))
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_calculate_fees_success(self, mock_db):
        """Test calculating platform fees"""
        service = PaymentsService(mock_db)
        
        result = service.calculate_fees(100.0)
        
        assert result['success'] is True
        assert result['total_amount'] == 100.0
        assert result['platform_fee'] > 0
        assert result['seller_amount'] < 100.0
        assert result['platform_fee'] + result['seller_amount'] == 100.0

    def test_calculate_fees_zero_amount(self, mock_db):
        """Test calculating fees for zero amount"""
        service = PaymentsService(mock_db)
        
        result = service.calculate_fees(0.0)
        
        assert result['success'] is True
        assert result['platform_fee'] == 0.0
        assert result['seller_amount'] == 0.0

    def test_calculate_fees_invalid_amount(self, mock_db):
        """Test calculating fees with invalid amount"""
        service = PaymentsService(mock_db)
        
        result = service.calculate_fees(-10.0)
        
        assert result['success'] is False
        assert 'invalid' in result['error'].lower() or 'amount' in result['error'].lower()

    def test_get_all_payments_success(self, mock_db, sample_payment):
        """Test getting all payments with filters"""
        service = PaymentsService(mock_db)
        
        payments_list = [sample_payment]
        mock_db.payments.find.return_value.skip.return_value.limit.return_value = payments_list
        mock_db.payments.count_documents.return_value = 1
        
        filters = {'status': 'completed'}
        result = service.get_all(filters, 1, 10)
        
        assert result['success'] is True
        assert len(result['payments']) == 1

    def test_get_all_payments_with_pagination(self, mock_db, sample_payment):
        """Test getting payments with pagination"""
        service = PaymentsService(mock_db)
        
        payments_list = [sample_payment]
        mock_db.payments.find.return_value.skip.return_value.limit.return_value = payments_list
        mock_db.payments.count_documents.return_value = 1
        
        result = service.get_all({}, 2, 5)
        
        assert result['success'] is True
        assert result['page'] == 2
        assert result['limit'] == 5

    def test_get_by_id_success(self, mock_db, sample_payment):
        """Test getting payment by ID"""
        service = PaymentsService(mock_db)
        
        mock_db.payments.find_one.return_value = sample_payment
        
        result = service.get_by_id(str(sample_payment['_id']))
        
        assert result['success'] is True
        assert result['payment']['amount'] == sample_payment['amount']

    def test_get_by_id_not_found(self, mock_db):
        """Test getting non-existent payment"""
        service = PaymentsService(mock_db)
        
        mock_db.payments.find_one.return_value = None
        
        result = service.get_by_id(str(ObjectId()))
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

