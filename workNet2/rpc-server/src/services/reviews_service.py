"""
Reviews Service
RPC service for review-related operations with complete business logic
"""

import logging
from bson import ObjectId
from utils.validators import validate_object_id, validate_rating

logger = logging.getLogger(__name__)

class ReviewsService:
    """Reviews RPC Service with complete business logic"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.reviews if db else None
    
    def create(self, review_id, gig_id, rating):
        """Create review and update gig rating"""
        try:
            review_id = validate_object_id(review_id)
            gig_id = validate_object_id(gig_id)
            rating = validate_rating(rating)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Validate gig exists
                    gig = self.db.gigs.find_one({'_id': gig_id}, session=session)
                    if not gig:
                        return {'success': False, 'error': 'Gig not found'}
                    
                    # Validate review exists
                    review = self.collection.find_one({'_id': review_id}, session=session)
                    if not review:
                        return {'success': False, 'error': 'Review not found'}
                    
                    # Recalculate gig rating
                    pipeline = [
                        {'$match': {'gigId': gig_id}},
                        {'$group': {
                            '_id': None,
                            'avgRating': {'$avg': '$rating'},
                            'count': {'$sum': 1}
                        }}
                    ]
                    
                    review_stats = list(self.collection.aggregate(pipeline, session=session))
                    
                    if review_stats and review_stats[0].get('count', 0) > 0:
                        avg_rating = review_stats[0]['avgRating']
                        review_count = review_stats[0]['count']
                        
                        # Update gig rating
                        self.db.gigs.update_one(
                            {'_id': gig_id},
                            {
                                '$set': {
                                    'rating': round(avg_rating, 2),
                                    'reviewCount': review_count,
                                    'updatedAt': self._get_current_time()
                                }
                            },
                            session=session
                        )
                        
                        logger.info(f"Review created: {review_id}, gig: {gig_id}, rating: {rating}")
                        return {
                            'success': True,
                            'message': 'Review created and gig rating updated',
                            'review_id': str(review_id),
                            'gig_rating': round(avg_rating, 2),
                            'review_count': review_count
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'No reviews found for calculation'
                        }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating review: {e}")
            return {'success': False, 'error': str(e)}
    
    def update(self, review_id, updates):
        """Update review and recalculate rating"""
        try:
            review_id = validate_object_id(review_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Validate updates
            allowed_fields = ['rating', 'comment', 'isVerified']
            filtered_updates = {}
            
            for key, value in updates.items():
                if key in allowed_fields:
                    if key == 'rating' and value is not None:
                        value = validate_rating(value)
                    filtered_updates[key] = value
            
            if not filtered_updates:
                return {'success': False, 'error': 'No valid fields to update'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Get review
                    review = self.collection.find_one({'_id': review_id}, session=session)
                    if not review:
                        return {'success': False, 'error': 'Review not found'}
                    
                    gig_id = review.get('gigId')
                    
                    # Update review
                    filtered_updates['updatedAt'] = self._get_current_time()
                    result = self.collection.update_one(
                        {'_id': review_id},
                        {'$set': filtered_updates},
                        session=session
                    )
                    
                    # Recalculate gig rating if rating changed
                    if 'rating' in filtered_updates:
                        self._recalculate_gig_rating(gig_id, session)
                    
                    if result.modified_count > 0:
                        logger.info(f"Review updated: {review_id}")
                        return {
                            'success': True,
                            'message': 'Review updated successfully',
                            'review_id': str(review_id)
                        }
                    else:
                        return {'success': False, 'error': 'No changes made'}
                        
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error updating review: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete(self, review_id):
        """Delete review and recalculate rating"""
        try:
            review_id = validate_object_id(review_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Get review
                    review = self.collection.find_one({'_id': review_id}, session=session)
                    if not review:
                        return {'success': False, 'error': 'Review not found'}
                    
                    gig_id = review.get('gigId')
                    
                    # Delete review
                    result = self.collection.delete_one({'_id': review_id}, session=session)
                    
                    # Recalculate gig rating
                    self._recalculate_gig_rating(gig_id, session)
                    
                    logger.info(f"Review deleted: {review_id}")
                    return {
                        'success': True,
                        'message': 'Review deleted successfully',
                        'review_id': str(review_id)
                    }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error deleting review: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_rating(self, gig_id):
        """Calculate average rating for gig"""
        try:
            gig_id = validate_object_id(gig_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Calculate average rating
            pipeline = [
                {'$match': {'gigId': gig_id}},
                {'$group': {
                    '_id': None,
                    'avgRating': {'$avg': '$rating'},
                    'count': {'$sum': 1},
                    'minRating': {'$min': '$rating'},
                    'maxRating': {'$max': '$rating'}
                }}
            ]
            
            review_stats = list(self.collection.aggregate(pipeline))
            
            if review_stats and review_stats[0].get('count', 0) > 0:
                stats = review_stats[0]
                return {
                    'success': True,
                    'rating': round(stats['avgRating'], 2),
                    'count': stats['count'],
                    'minRating': stats['minRating'],
                    'maxRating': stats['maxRating']
                }
            else:
                return {
                    'success': True,
                    'rating': 0,
                    'count': 0,
                    'minRating': 0,
                    'maxRating': 0
                }
                
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error calculating rating: {e}")
            return {'success': False, 'error': str(e)}
    
    def _recalculate_gig_rating(self, gig_id, session):
        """Recalculate and update gig rating"""
        try:
            pipeline = [
                {'$match': {'gigId': gig_id}},
                {'$group': {
                    '_id': None,
                    'avgRating': {'$avg': '$rating'},
                    'count': {'$sum': 1}
                }}
            ]
            
            review_stats = list(self.collection.aggregate(pipeline, session=session))
            
            if review_stats and review_stats[0].get('count', 0) > 0:
                avg_rating = review_stats[0]['avgRating']
                review_count = review_stats[0]['count']
                
                self.db.gigs.update_one(
                    {'_id': gig_id},
                    {
                        '$set': {
                            'rating': round(avg_rating, 2),
                            'reviewCount': review_count,
                            'updatedAt': self._get_current_time()
                        }
                    },
                    session=session
                )
            else:
                # No reviews, set to 0
                self.db.gigs.update_one(
                    {'_id': gig_id},
                    {'$set': {'rating': 0, 'reviewCount': 0}},
                    session=session
                )
        except Exception as e:
            logger.error(f"Error recalculating gig rating: {e}")
    
    def _get_current_time(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow()
