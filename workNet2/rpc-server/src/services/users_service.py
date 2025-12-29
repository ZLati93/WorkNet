"""
Users Service
RPC service for user-related operations with complete business logic
"""

import logging
import bcrypt
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, WriteError
from utils.validators import validate_object_id, validate_email, validate_username, validate_role

logger = logging.getLogger(__name__)

class UsersService:
    """Users RPC Service with complete business logic"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.users if db else None
    
    def create(self, user_id, username, email, role):
        """Create user notification/logging with validation"""
        try:
            # Validate inputs
            user_id = validate_object_id(user_id)
            username = validate_username(username)
            email = validate_email(email)
            role = validate_role(role)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Check if user already exists
            existing_user = self.collection.find_one({
                '$or': [
                    {'email': email},
                    {'username': username}
                ]
            })
            
            if existing_user:
                return {
                    'success': False,
                    'error': 'User with this email or username already exists'
                }
            
            # Log user creation
            logger.info(f"User created: {user_id}, {username}, {email}, {role}")
            
            # Update user metadata if user exists
            result = self.collection.update_one(
                {'_id': user_id},
                {
                    '$set': {
                        'username': username,
                        'email': email,
                        'role': role,
                        'updatedAt': self._get_current_time()
                    }
                },
                upsert=False
            )
            
            return {
                'success': True,
                'message': 'User creation logged',
                'user_id': str(user_id)
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {'success': False, 'error': str(e)}
    
    def update(self, user_id, updates):
        """Update user with validation and transaction"""
        try:
            user_id = validate_object_id(user_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Validate updates
            allowed_fields = ['username', 'email', 'phone', 'country', 'profilePicture', 'skills', 'isSeller']
            filtered_updates = {}
            
            for key, value in updates.items():
                if key in allowed_fields:
                    if key == 'username' and value:
                        value = validate_username(value)
                    elif key == 'email' and value:
                        value = validate_email(value)
                    filtered_updates[key] = value
            
            if not filtered_updates:
                return {'success': False, 'error': 'No valid fields to update'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Check if user exists
                    user = self.collection.find_one({'_id': user_id}, session=session)
                    if not user:
                        return {'success': False, 'error': 'User not found'}
                    
                    # Check for duplicate email/username if updating
                    if 'email' in filtered_updates or 'username' in filtered_updates:
                        query = {'_id': {'$ne': user_id}}
                        if 'email' in filtered_updates:
                            query['email'] = filtered_updates['email']
                        if 'username' in filtered_updates:
                            query['username'] = filtered_updates['username']
                        
                        duplicate = self.collection.find_one(query, session=session)
                        if duplicate:
                            return {'success': False, 'error': 'Email or username already exists'}
                    
                    # Update user
                    filtered_updates['updatedAt'] = self._get_current_time()
                    result = self.collection.update_one(
                        {'_id': user_id},
                        {'$set': filtered_updates},
                        session=session
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"User updated: {user_id}")
                        return {
                            'success': True,
                            'message': 'User updated successfully',
                            'user_id': str(user_id)
                        }
                    else:
                        return {'success': False, 'error': 'No changes made'}
                        
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete(self, user_id):
        """Delete user with cascade checks"""
        try:
            user_id = validate_object_id(user_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Check if user exists
                    user = self.collection.find_one({'_id': user_id}, session=session)
                    if not user:
                        return {'success': False, 'error': 'User not found'}
                    
                    # Check for active orders
                    active_orders = self.db.orders.count_documents({
                        '$or': [
                            {'buyerId': user_id, 'status': {'$in': ['pending', 'in_progress']}},
                            {'sellerId': user_id, 'status': {'$in': ['pending', 'in_progress']}}
                        ]
                    }, session=session)
                    
                    if active_orders > 0:
                        return {
                            'success': False,
                            'error': f'Cannot delete user with {active_orders} active orders'
                        }
                    
                    # Soft delete (mark as deleted instead of removing)
                    result = self.collection.update_one(
                        {'_id': user_id},
                        {
                            '$set': {
                                'deleted': True,
                                'deletedAt': self._get_current_time(),
                                'updatedAt': self._get_current_time()
                            }
                        },
                        session=session
                    )
                    
                    logger.info(f"User deleted: {user_id}")
                    return {
                        'success': True,
                        'message': 'User deleted successfully',
                        'user_id': str(user_id)
                    }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_stats(self, user_id):
        """Get comprehensive user statistics"""
        try:
            user_id = validate_object_id(user_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            user = self.collection.find_one({'_id': user_id})
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Calculate statistics
            stats = {
                'rating': user.get('rating', 0),
                'totalEarnings': user.get('totalEarnings', 0),
                'totalOrders': 0,
                'completedOrders': 0,
                'activeOrders': 0,
                'totalGigs': 0,
                'activeGigs': 0,
                'totalReviews': 0,
                'averageRating': 0
            }
            
            # Count orders
            if user.get('role') == 'freelancer':
                stats['totalOrders'] = self.db.orders.count_documents({'sellerId': user_id})
                stats['completedOrders'] = self.db.orders.count_documents({
                    'sellerId': user_id,
                    'status': 'completed'
                })
                stats['activeOrders'] = self.db.orders.count_documents({
                    'sellerId': user_id,
                    'status': {'$in': ['pending', 'in_progress']}
                })
                
                # Count gigs
                stats['totalGigs'] = self.db.gigs.count_documents({'userId': user_id})
                stats['activeGigs'] = self.db.gigs.count_documents({
                    'userId': user_id,
                    'isActive': True
                })
                
                # Calculate average rating from reviews
                pipeline = [
                    {'$match': {'gigId': {'$in': [g['_id'] for g in self.db.gigs.find({'userId': user_id})]}}},
                    {'$group': {'_id': None, 'avgRating': {'$avg': '$rating'}, 'count': {'$sum': 1}}}
                ]
                review_stats = list(self.db.reviews.aggregate(pipeline))
                if review_stats:
                    stats['averageRating'] = review_stats[0].get('avgRating', 0)
                    stats['totalReviews'] = review_stats[0].get('count', 0)
            
            return {
                'success': True,
                'stats': stats
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'success': False, 'error': str(e)}
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _get_current_time(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow()
