"""
Orders Service
RPC service for order-related operations with complete business logic
"""

import logging
from bson import ObjectId
from utils.validators import validate_object_id, validate_status

logger = logging.getLogger(__name__)

class OrdersService:
    """Orders RPC Service with complete business logic"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.orders if db else None
    
    def create(self, order_id, gig_id, buyer_id):
        """Create order with validation"""
        try:
            order_id = validate_object_id(order_id)
            gig_id = validate_object_id(gig_id)
            buyer_id = validate_object_id(buyer_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Validate gig exists
                    gig = self.db.gigs.find_one({'_id': gig_id}, session=session)
                    if not gig:
                        return {'success': False, 'error': 'Gig not found'}
                    
                    if not gig.get('isActive'):
                        return {'success': False, 'error': 'Gig is not active'}
                    
                    # Validate buyer exists
                    buyer = self.db.users.find_one({'_id': buyer_id}, session=session)
                    if not buyer:
                        return {'success': False, 'error': 'Buyer not found'}
                    
                    # Check if buyer is trying to buy their own gig
                    if gig.get('userId') == buyer_id:
                        return {'success': False, 'error': 'Cannot order your own gig'}
                    
                    # Get seller
                    seller_id = gig.get('userId')
                    seller = self.db.users.find_one({'_id': seller_id}, session=session)
                    if not seller:
                        return {'success': False, 'error': 'Seller not found'}
                    
                    logger.info(f"Order created: {order_id}, gig: {gig_id}, buyer: {buyer_id}")
                    
                    return {
                        'success': True,
                        'message': 'Order creation logged',
                        'order_id': str(order_id),
                        'seller_id': str(seller_id)
                    }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_status(self, order_id, status):
        """Update order status with workflow validation"""
        try:
            order_id = validate_object_id(order_id)
            valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled', 'disputed']
            status = validate_status(status, valid_statuses)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Get current order
                    order = self.collection.find_one({'_id': order_id}, session=session)
                    if not order:
                        return {'success': False, 'error': 'Order not found'}
                    
                    current_status = order.get('status')
                    
                    # Validate status transition
                    valid_transitions = {
                        'pending': ['in_progress', 'cancelled'],
                        'in_progress': ['completed', 'disputed', 'cancelled'],
                        'completed': [],
                        'cancelled': [],
                        'disputed': ['completed', 'cancelled']
                    }
                    
                    if status not in valid_transitions.get(current_status, []):
                        return {
                            'success': False,
                            'error': f'Invalid status transition from {current_status} to {status}'
                        }
                    
                    # Update order status
                    update_data = {
                        'status': status,
                        'updatedAt': self._get_current_time()
                    }
                    
                    # Add status-specific fields
                    if status == 'completed':
                        update_data['completedAt'] = self._get_current_time()
                    elif status == 'cancelled':
                        update_data['cancelledAt'] = self._get_current_time()
                    
                    result = self.collection.update_one(
                        {'_id': order_id},
                        {'$set': update_data},
                        session=session
                    )
                    
                    # If order completed, update seller earnings
                    if status == 'completed' and current_status != 'completed':
                        self._update_seller_earnings(order.get('sellerId'), order.get('price'), session)
                    
                    logger.info(f"Order status updated: {order_id}, {current_status} -> {status}")
                    return {
                        'success': True,
                        'message': 'Order status updated successfully',
                        'order_id': str(order_id),
                        'previous_status': current_status,
                        'new_status': status
                    }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_analytics(self, user_id, period):
        """Get order analytics for user"""
        try:
            user_id = validate_object_id(user_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Build date filter based on period
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            
            date_filters = {
                'week': now - timedelta(days=7),
                'month': now - timedelta(days=30),
                'year': now - timedelta(days=365),
                'all': None
            }
            
            date_filter = date_filters.get(period, date_filters['month'])
            
            # Build query
            query = {
                '$or': [
                    {'buyerId': user_id},
                    {'sellerId': user_id}
                ]
            }
            
            if date_filter:
                query['createdAt'] = {'$gte': date_filter}
            
            # Calculate analytics
            pipeline = [
                {'$match': query},
                {'$group': {
                    '_id': '$status',
                    'count': {'$sum': 1},
                    'totalRevenue': {'$sum': '$price'}
                }},
                {'$group': {
                    '_id': None,
                    'totalOrders': {'$sum': '$count'},
                    'completedOrders': {
                        '$sum': {
                            '$cond': [{'$eq': ['$_id', 'completed']}, '$count', 0]
                        }
                    },
                    'totalRevenue': {'$sum': '$totalRevenue'},
                    'statusBreakdown': {
                        '$push': {
                            'status': '$_id',
                            'count': '$count'
                        }
                    }
                }}
            ]
            
            analytics = list(self.collection.aggregate(pipeline))
            
            if analytics:
                result = analytics[0]
                result['success'] = True
                result['period'] = period
                return result
            else:
                return {
                    'success': True,
                    'totalOrders': 0,
                    'completedOrders': 0,
                    'totalRevenue': 0,
                    'statusBreakdown': [],
                    'period': period
                }
                
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error getting order analytics: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel(self, order_id, reason):
        """Cancel order with validation"""
        try:
            order_id = validate_object_id(order_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    order = self.collection.find_one({'_id': order_id}, session=session)
                    if not order:
                        return {'success': False, 'error': 'Order not found'}
                    
                    current_status = order.get('status')
                    if current_status in ['completed', 'cancelled']:
                        return {
                            'success': False,
                            'error': f'Cannot cancel order with status: {current_status}'
                        }
                    
                    # Update order
                    result = self.collection.update_one(
                        {'_id': order_id},
                        {
                            '$set': {
                                'status': 'cancelled',
                                'cancellationReason': reason,
                                'cancelledAt': self._get_current_time(),
                                'updatedAt': self._get_current_time()
                            }
                        },
                        session=session
                    )
                    
                    logger.info(f"Order cancelled: {order_id}, reason: {reason}")
                    return {
                        'success': True,
                        'message': 'Order cancelled successfully',
                        'order_id': str(order_id)
                    }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_seller_earnings(self, seller_id, amount, session):
        """Update seller total earnings"""
        try:
            self.db.users.update_one(
                {'_id': seller_id},
                {'$inc': {'totalEarnings': amount}},
                session=session
            )
        except Exception as e:
            logger.error(f"Error updating seller earnings: {e}")
    
    def _get_current_time(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow()
