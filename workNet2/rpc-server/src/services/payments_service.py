"""
Payments Service
RPC service for payment-related operations with complete business logic and fee calculations
"""

import logging
from bson import ObjectId
from utils.validators import validate_object_id, validate_price, validate_status

logger = logging.getLogger(__name__)

# Platform fee percentage
PLATFORM_FEE_PERCENTAGE = 0.20  # 20% platform fee

class PaymentsService:
    """Payments RPC Service with complete business logic"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.payments if db else None
    
    def create(self, payment_id, order_id, amount, payment_method):
        """Create payment with fee calculation"""
        try:
            payment_id = validate_object_id(payment_id)
            order_id = validate_object_id(order_id)
            amount = validate_price(amount)
            
            valid_methods = ['stripe', 'paypal', 'bank_transfer', 'other']
            if payment_method not in valid_methods:
                return {'success': False, 'error': f'Invalid payment method. Must be one of: {valid_methods}'}
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Validate order exists
                    order = self.db.orders.find_one({'_id': order_id}, session=session)
                    if not order:
                        return {'success': False, 'error': 'Order not found'}
                    
                    # Calculate fees
                    platform_fee = amount * PLATFORM_FEE_PERCENTAGE
                    seller_amount = amount - platform_fee
                    
                    logger.info(f"Payment created: {payment_id}, order: {order_id}, amount: {amount}, method: {payment_method}")
                    logger.info(f"Platform fee: {platform_fee}, Seller amount: {seller_amount}")
                    
                    return {
                        'success': True,
                        'message': 'Payment creation logged',
                        'payment_id': str(payment_id),
                        'amount': amount,
                        'platform_fee': round(platform_fee, 2),
                        'seller_amount': round(seller_amount, 2),
                        'payment_method': payment_method
                    }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return {'success': False, 'error': str(e)}
    
    def process(self, payment_id, status):
        """Process payment with status update"""
        try:
            payment_id = validate_object_id(payment_id)
            valid_statuses = ['pending', 'completed', 'failed', 'refunded']
            status = validate_status(status, valid_statuses)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Get payment
                    payment = self.collection.find_one({'_id': payment_id}, session=session)
                    if not payment:
                        return {'success': False, 'error': 'Payment not found'}
                    
                    current_status = payment.get('status')
                    
                    # Validate status transition
                    if current_status == 'completed' and status != 'refunded':
                        return {'success': False, 'error': 'Cannot change status from completed'}
                    
                    # Update payment status
                    update_data = {
                        'status': status,
                        'updatedAt': self._get_current_time()
                    }
                    
                    if status == 'completed':
                        update_data['completedAt'] = self._get_current_time()
                    elif status == 'refunded':
                        update_data['refundedAt'] = self._get_current_time()
                    
                    result = self.collection.update_one(
                        {'_id': payment_id},
                        {'$set': update_data},
                        session=session
                    )
                    
                    # If payment completed, update order status
                    if status == 'completed' and current_status != 'completed':
                        order_id = payment.get('orderId')
                        self.db.orders.update_one(
                            {'_id': order_id},
                            {
                                '$set': {
                                    'status': 'in_progress',
                                    'paymentIntent': str(payment_id),
                                    'updatedAt': self._get_current_time()
                                }
                            },
                            session=session
                        )
                        
                        # Calculate and update seller earnings
                        amount = payment.get('amount', 0)
                        platform_fee = amount * PLATFORM_FEE_PERCENTAGE
                        seller_amount = amount - platform_fee
                        
                        seller_id = self.db.orders.find_one({'_id': order_id}, session=session).get('sellerId')
                        self.db.users.update_one(
                            {'_id': seller_id},
                            {'$inc': {'totalEarnings': seller_amount}},
                            session=session
                        )
                    
                    logger.info(f"Payment processed: {payment_id}, {current_status} -> {status}")
                    return {
                        'success': True,
                        'message': 'Payment processed successfully',
                        'payment_id': str(payment_id),
                        'status': status
                    }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            return {'success': False, 'error': str(e)}
    
    def refund(self, payment_id, amount):
        """Refund payment with validation"""
        try:
            payment_id = validate_object_id(payment_id)
            amount = validate_price(amount)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Get payment
                    payment = self.collection.find_one({'_id': payment_id}, session=session)
                    if not payment:
                        return {'success': False, 'error': 'Payment not found'}
                    
                    if payment.get('status') != 'completed':
                        return {'success': False, 'error': 'Can only refund completed payments'}
                    
                    original_amount = payment.get('amount', 0)
                    if amount > original_amount:
                        return {'success': False, 'error': 'Refund amount cannot exceed original payment'}
                    
                    # Update payment status
                    result = self.collection.update_one(
                        {'_id': payment_id},
                        {
                            '$set': {
                                'status': 'refunded',
                                'refundAmount': amount,
                                'refundedAt': self._get_current_time(),
                                'updatedAt': self._get_current_time()
                            }
                        },
                        session=session
                    )
                    
                    # Update seller earnings (deduct refund)
                    order_id = payment.get('orderId')
                    order = self.db.orders.find_one({'_id': order_id}, session=session)
                    if order:
                        seller_id = order.get('sellerId')
                        platform_fee = amount * PLATFORM_FEE_PERCENTAGE
                        seller_refund = amount - platform_fee
                        
                        self.db.users.update_one(
                            {'_id': seller_id},
                            {'$inc': {'totalEarnings': -seller_refund}},
                            session=session
                        )
                    
                    logger.info(f"Payment refunded: {payment_id}, amount: {amount}")
                    return {
                        'success': True,
                        'message': 'Payment refunded successfully',
                        'payment_id': str(payment_id),
                        'refund_amount': amount
                    }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error refunding payment: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_status(self, payment_id):
        """Get payment status"""
        try:
            payment_id = validate_object_id(payment_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            payment = self.collection.find_one({'_id': payment_id})
            if not payment:
                return {'success': False, 'error': 'Payment not found'}
            
            return {
                'success': True,
                'status': payment.get('status'),
                'amount': payment.get('amount'),
                'payment_method': payment.get('paymentMethod'),
                'created_at': payment.get('createdAt').isoformat() if payment.get('createdAt') else None
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_fees(self, amount):
        """Calculate platform fees"""
        try:
            amount = validate_price(amount)
            platform_fee = amount * PLATFORM_FEE_PERCENTAGE
            seller_amount = amount - platform_fee
            
            return {
                'success': True,
                'total_amount': round(amount, 2),
                'platform_fee': round(platform_fee, 2),
                'platform_fee_percentage': PLATFORM_FEE_PERCENTAGE * 100,
                'seller_amount': round(seller_amount, 2)
            }
        except ValueError as e:
            return {'success': False, 'error': str(e)}
    
    def _get_current_time(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow()
