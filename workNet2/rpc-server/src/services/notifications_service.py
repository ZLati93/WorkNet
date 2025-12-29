"""
Notifications Service
RPC service for notification-related operations with complete business logic
"""

import logging
from bson import ObjectId
from utils.validators import validate_object_id, validate_status

logger = logging.getLogger(__name__)

class NotificationsService:
    """Notifications RPC Service with complete business logic"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.notifications if db else None
    
    def create(self, notification_id, user_id, notification_type):
        """Create notification"""
        try:
            notification_id = validate_object_id(notification_id)
            user_id = validate_object_id(user_id)
            
            valid_types = ['order', 'message', 'review', 'payment', 'system']
            if notification_type not in valid_types:
                return {'success': False, 'error': f'Invalid notification type. Must be one of: {valid_types}'}
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Validate user exists
            user = self.db.users.find_one({'_id': user_id})
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            logger.info(f"Notification created: {notification_id}, user: {user_id}, type: {notification_type}")
            
            return {
                'success': True,
                'message': 'Notification created',
                'notification_id': str(notification_id)
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def mark_as_read(self, notification_id):
        """Mark notification as read"""
        try:
            notification_id = validate_object_id(notification_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Get notification
                    notification = self.collection.find_one({'_id': notification_id}, session=session)
                    if not notification:
                        return {'success': False, 'error': 'Notification not found'}
                    
                    # Update notification
                    result = self.collection.update_one(
                        {'_id': notification_id},
                        {'$set': {'isRead': True}},
                        session=session
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"Notification marked as read: {notification_id}")
                        return {
                            'success': True,
                            'message': 'Notification marked as read',
                            'notification_id': str(notification_id)
                        }
                    else:
                        return {'success': False, 'error': 'Notification already read or not found'}
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_unread_count(self, user_id):
        """Get unread notification count"""
        try:
            user_id = validate_object_id(user_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Count unread notifications
            unread_count = self.collection.count_documents({
                'userId': user_id,
                'isRead': False
            })
            
            # Get breakdown by type
            pipeline = [
                {'$match': {'userId': user_id, 'isRead': False}},
                {'$group': {
                    '_id': '$type',
                    'count': {'$sum': 1}
                }}
            ]
            
            type_breakdown = list(self.collection.aggregate(pipeline))
            
            return {
                'success': True,
                'count': unread_count,
                'by_type': {item['_id']: item['count'] for item in type_breakdown}
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_bulk(self, user_ids, notification_type, message):
        """Send bulk notifications"""
        try:
            if not isinstance(user_ids, list) or len(user_ids) == 0:
                return {'success': False, 'error': 'user_ids must be a non-empty list'}
            
            valid_types = ['order', 'message', 'review', 'payment', 'system']
            if notification_type not in valid_types:
                return {'success': False, 'error': f'Invalid notification type. Must be one of: {valid_types}'}
            
            if not message or len(message) < 1 or len(message) > 500:
                return {'success': False, 'error': 'Message must be between 1 and 500 characters'}
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Validate all user IDs
            validated_user_ids = []
            for user_id_str in user_ids:
                try:
                    validated_user_ids.append(validate_object_id(user_id_str))
                except ValueError:
                    logger.warning(f"Invalid user ID skipped: {user_id_str}")
                    continue
            
            if not validated_user_ids:
                return {'success': False, 'error': 'No valid user IDs provided'}
            
            # Create notifications in bulk
            notifications = []
            current_time = self._get_current_time()
            
            for user_id in validated_user_ids:
                notifications.append({
                    'userId': user_id,
                    'type': notification_type,
                    'message': message,
                    'isRead': False,
                    'createdAt': current_time
                })
            
            # Insert bulk
            if notifications:
                result = self.collection.insert_many(notifications)
                logger.info(f"Bulk notifications sent: {len(result.inserted_ids)} notifications to {len(validated_user_ids)} users")
                
                return {
                    'success': True,
                    'message': f'Bulk notifications sent successfully',
                    'notifications_sent': len(result.inserted_ids),
                    'users_targeted': len(validated_user_ids)
                }
            else:
                return {'success': False, 'error': 'No notifications created'}
                
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error sending bulk notifications: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_current_time(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow()
