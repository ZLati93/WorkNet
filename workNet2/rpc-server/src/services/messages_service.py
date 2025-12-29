"""
Messages Service
RPC service for message-related operations with complete business logic
"""

import logging
from bson import ObjectId
from utils.validators import validate_object_id

logger = logging.getLogger(__name__)

class MessagesService:
    """Messages RPC Service with complete business logic"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.messages if db else None
    
    def create(self, message_id, conversation_id, sender_id):
        """Create message notification"""
        try:
            message_id = validate_object_id(message_id)
            conversation_id = validate_object_id(conversation_id)
            sender_id = validate_object_id(sender_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Validate conversation exists
            conversation = self.db.conversations.find_one({'_id': conversation_id})
            if not conversation:
                return {'success': False, 'error': 'Conversation not found'}
            
            # Validate sender is part of conversation
            if (conversation.get('user1Id') != sender_id and 
                conversation.get('user2Id') != sender_id):
                return {'success': False, 'error': 'Sender not part of conversation'}
            
            logger.info(f"Message created: {message_id}, conversation: {conversation_id}, sender: {sender_id}")
            
            # Update conversation last message time
            self.db.conversations.update_one(
                {'_id': conversation_id},
                {
                    '$set': {
                        'lastMessageAt': self._get_current_time(),
                        'updatedAt': self._get_current_time()
                    }
                }
            )
            
            return {
                'success': True,
                'message': 'Message creation logged',
                'message_id': str(message_id)
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return {'success': False, 'error': str(e)}
    
    def mark_as_read(self, message_id):
        """Mark message as read"""
        try:
            message_id = validate_object_id(message_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Get message
                    message = self.collection.find_one({'_id': message_id}, session=session)
                    if not message:
                        return {'success': False, 'error': 'Message not found'}
                    
                    # Update message
                    result = self.collection.update_one(
                        {'_id': message_id},
                        {'$set': {'isRead': True}},
                        session=session
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"Message marked as read: {message_id}")
                        return {
                            'success': True,
                            'message': 'Message marked as read',
                            'message_id': str(message_id)
                        }
                    else:
                        return {'success': False, 'error': 'Message already read or not found'}
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_unread_count(self, user_id):
        """Get unread message count for user"""
        try:
            user_id = validate_object_id(user_id)
            
            if not self.db:
                return {'success': False, 'error': 'Database not available'}
            
            # Get all conversations where user is participant
            conversations = list(self.db.conversations.find({
                '$or': [
                    {'user1Id': user_id},
                    {'user2Id': user_id}
                ]
            }))
            
            conversation_ids = [c['_id'] for c in conversations]
            
            if not conversation_ids:
                return {
                    'success': True,
                    'count': 0
                }
            
            # Count unread messages (not sent by user)
            unread_count = self.collection.count_documents({
                'conversationId': {'$in': conversation_ids},
                'senderId': {'$ne': user_id},
                'isRead': False
            })
            
            return {
                'success': True,
                'count': unread_count
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_current_time(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow()
