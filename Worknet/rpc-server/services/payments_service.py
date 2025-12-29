"""
Payments Service for WorkNet RPC Server
Handles payment-related operations
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from services import BaseService
from typing import Dict, Any, Optional, List
from xmlrpc.client import Fault
from bson import ObjectId
from datetime import datetime


class PaymentsService(BaseService):
    """Service for payment management operations"""
    
    def __init__(self, db=None):
        """Initialize PaymentsService"""
        super().__init__(db)
        self.collection = self.get_collection('payments')
    
    def create_payment(self, order_id: str, amount: float, payment_method: str) -> Dict[str, Any]:
        """Create a new payment"""
        try:
            # Verify order exists
            orders_collection = self.get_collection('orders')
            order = orders_collection.find_one({'_id': ObjectId(order_id)})
            if not order:
                raise Fault(404, "Order not found")
            
            payment_data = {
                'orderId': ObjectId(order_id),
                'clientId': order.get('clientId'),
                'freelancerId': order.get('freelancerId'),
                'amount': amount,
                'paymentMethod': payment_method,
                'status': 'pending',
                'createdAt': None,
                'updatedAt': None
            }
            result = self.collection.insert_one(payment_data)
            payment_data['id'] = str(result.inserted_id)
            payment_data['_id'] = result.inserted_id
            return self._format_payment(payment_data)
        except Fault:
            raise
        except Exception as e:
            self.handle_error(e, "Failed to create payment")
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Get a payment by ID"""
        try:
            payment = self.collection.find_one({'_id': ObjectId(payment_id)})
            if not payment:
                raise Fault(404, "Payment not found")
            return self._format_payment(payment)
        except Fault:
            raise
        except Exception as e:
            self.handle_error(e, "Failed to get payment")
    
    def list_payments(self, order_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List payments with optional filters"""
        try:
            query = {}
            if order_id:
                query['orderId'] = ObjectId(order_id)
            if status:
                query['status'] = status
            
            payments = self.collection.find(query)
            return [self._format_payment(payment) for payment in payments]
        except Exception as e:
            self.handle_error(e, "Failed to list payments")
    
    def update_payment_status(self, payment_id: str, status: str, transaction_id: Optional[str] = None) -> Dict[str, Any]:
        """Update payment status"""
        try:
            valid_statuses = ['pending', 'processing', 'completed', 'failed', 'refunded']
            if status not in valid_statuses:
                raise Fault(400, f"Invalid status. Must be one of: {valid_statuses}")
            
            update_data = {'status': status, 'updatedAt': None}
            if transaction_id:
                update_data['transactionId'] = transaction_id
            
            result = self.collection.update_one(
                {'_id': ObjectId(payment_id)},
                {'$set': update_data}
            )
            if result.matched_count == 0:
                raise Fault(404, "Payment not found")
            
            # If payment completed, update order status
            if status == 'completed':
                payment = self.collection.find_one({'_id': ObjectId(payment_id)})
                orders_collection = self.get_collection('orders')
                orders_collection.update_one(
                    {'_id': payment.get('orderId')},
                    {'$set': {'status': 'paid', 'updatedAt': None}}
                )
            
            return self.get_payment(payment_id)
        except Fault:
            raise
        except Exception as e:
            self.handle_error(e, "Failed to update payment status")
    
    def _format_payment(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Format payment document for response"""
        return {
            'id': str(payment.get('_id')),
            'orderId': str(payment.get('orderId')),
            'clientId': str(payment.get('clientId')),
            'freelancerId': str(payment.get('freelancerId')),
            'amount': payment.get('amount'),
            'paymentMethod': payment.get('paymentMethod'),
            'status': payment.get('status'),
            'transactionId': payment.get('transactionId'),
        }

