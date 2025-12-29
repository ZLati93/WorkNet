"""
Gigs Service
RPC service for gig-related operations with complete business logic
"""

import logging
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, WriteError
from utils.validators import validate_object_id, validate_price

logger = logging.getLogger(__name__)

class GigsService:
    """Gigs RPC Service with complete business logic"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.gigs if db else None
    
    def create(self, gig_id, user_id, title):
        """Create gig with validation"""
        try:
            gig_id = validate_object_id(gig_id)
            user_id = validate_object_id(user_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Validate user exists and is a seller
            user = self.db.users.find_one({'_id': user_id})
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            if not user.get('isSeller') and user.get('role') != 'freelancer':
                return {'success': False, 'error': 'User must be a seller to create gigs'}
            
            # Log gig creation
            logger.info(f"Gig created: {gig_id}, user: {user_id}, title: {title}")
            
            return {
                'success': True,
                'message': 'Gig creation logged',
                'gig_id': str(gig_id)
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating gig: {e}")
            return {'success': False, 'error': str(e)}
    
    def update(self, gig_id, updates):
        """Update gig with validation and transaction"""
        try:
            gig_id = validate_object_id(gig_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Validate updates
            allowed_fields = ['title', 'description', 'category', 'price', 'deliveryTime', 
                            'revisionNumber', 'images', 'features', 'isActive']
            filtered_updates = {}
            
            for key, value in updates.items():
                if key in allowed_fields:
                    if key == 'price' and value is not None:
                        value = validate_price(value)
                    filtered_updates[key] = value
            
            if not filtered_updates:
                return {'success': False, 'error': 'No valid fields to update'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Check if gig exists
                    gig = self.collection.find_one({'_id': gig_id}, session=session)
                    if not gig:
                        return {'success': False, 'error': 'Gig not found'}
                    
                    # Update gig
                    filtered_updates['updatedAt'] = self._get_current_time()
                    result = self.collection.update_one(
                        {'_id': gig_id},
                        {'$set': filtered_updates},
                        session=session
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"Gig updated: {gig_id}")
                        return {
                            'success': True,
                            'message': 'Gig updated successfully',
                            'gig_id': str(gig_id)
                        }
                    else:
                        return {'success': False, 'error': 'No changes made'}
                        
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error updating gig: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete(self, gig_id):
        """Delete gig with cascade checks"""
        try:
            gig_id = validate_object_id(gig_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Check if gig exists
                    gig = self.collection.find_one({'_id': gig_id}, session=session)
                    if not gig:
                        return {'success': False, 'error': 'Gig not found'}
                    
                    # Check for active orders
                    active_orders = self.db.orders.count_documents({
                        'gigId': gig_id,
                        'status': {'$in': ['pending', 'in_progress']}
                    }, session=session)
                    
                    if active_orders > 0:
                        return {
                            'success': False,
                            'error': f'Cannot delete gig with {active_orders} active orders'
                        }
                    
                    # Soft delete
                    result = self.collection.update_one(
                        {'_id': gig_id},
                        {
                            '$set': {
                                'isActive': False,
                                'deleted': True,
                                'deletedAt': self._get_current_time(),
                                'updatedAt': self._get_current_time()
                            }
                        },
                        session=session
                    )
                    
                    logger.info(f"Gig deleted: {gig_id}")
                    return {
                        'success': True,
                        'message': 'Gig deleted successfully',
                        'gig_id': str(gig_id)
                    }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error deleting gig: {e}")
            return {'success': False, 'error': str(e)}
    
    def search(self, query, filters):
        """Search gigs with filters"""
        try:
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Build search query
            search_query = {'isActive': True, 'deleted': {'$ne': True}}
            
            # Text search
            if query:
                search_query['$or'] = [
                    {'title': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}}
                ]
            
            # Apply filters
            if filters:
                if 'category' in filters:
                    search_query['category'] = filters['category']
                if 'minPrice' in filters:
                    search_query['price'] = {'$gte': float(filters['minPrice'])}
                if 'maxPrice' in filters:
                    if 'price' in search_query:
                        search_query['price']['$lte'] = float(filters['maxPrice'])
                    else:
                        search_query['price'] = {'$lte': float(filters['maxPrice'])}
                if 'minRating' in filters:
                    search_query['rating'] = {'$gte': float(filters['minRating'])}
            
            # Execute search
            gigs = list(self.collection.find(search_query).limit(50))
            
            return {
                'success': True,
                'results': [self._serialize_gig(gig) for gig in gigs],
                'count': len(gigs)
            }
            
        except Exception as e:
            logger.error(f"Error searching gigs: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_rating(self, gig_id):
        """Update gig rating from reviews"""
        try:
            gig_id = validate_object_id(gig_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Calculate average rating from reviews
            pipeline = [
                {'$match': {'gigId': gig_id}},
                {'$group': {
                    '_id': None,
                    'avgRating': {'$avg': '$rating'},
                    'count': {'$sum': 1}
                }}
            ]
            
            review_stats = list(self.db.reviews.aggregate(pipeline))
            
            if review_stats and review_stats[0].get('count', 0) > 0:
                avg_rating = review_stats[0]['avgRating']
                review_count = review_stats[0]['count']
                
                # Update gig rating
                result = self.collection.update_one(
                    {'_id': gig_id},
                    {
                        '$set': {
                            'rating': round(avg_rating, 2),
                            'reviewCount': review_count,
                            'updatedAt': self._get_current_time()
                        }
                    }
                )
                
                logger.info(f"Gig rating updated: {gig_id}, rating: {avg_rating}")
                return {
                    'success': True,
                    'rating': round(avg_rating, 2),
                    'reviewCount': review_count
                }
            else:
                # No reviews, set rating to 0
                self.collection.update_one(
                    {'_id': gig_id},
                    {'$set': {'rating': 0, 'reviewCount': 0}}
                )
                return {
                    'success': True,
                    'rating': 0,
                    'reviewCount': 0
                }
                
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error updating gig rating: {e}")
            return {'success': False, 'error': str(e)}
    
    def _serialize_gig(self, gig):
        """Serialize gig document"""
        return {
            'id': str(gig['_id']),
            'title': gig.get('title'),
            'price': gig.get('price'),
            'rating': gig.get('rating', 0),
            'category': gig.get('category')
        }
    
    def _get_current_time(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow()
