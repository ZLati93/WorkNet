"""
Categories Service
RPC service for category-related operations with complete business logic
"""

import logging
import re
from bson import ObjectId
from utils.validators import validate_object_id

logger = logging.getLogger(__name__)

class CategoriesService:
    """Categories RPC Service with complete business logic"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.categories if db else None
    
    def create(self, category_id, name, slug):
        """Create category with validation"""
        try:
            category_id = validate_object_id(category_id)
            
            # Validate name
            if not name or len(name) < 2 or len(name) > 100:
                return {'success': False, 'error': 'Category name must be between 2 and 100 characters'}
            
            # Validate slug format
            if not re.match(r'^[a-z0-9-]+$', slug):
                return {'success': False, 'error': 'Slug must be lowercase with hyphens only'}
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Check if slug already exists
            existing = self.collection.find_one({'slug': slug})
            if existing and str(existing['_id']) != str(category_id):
                return {'success': False, 'error': 'Category with this slug already exists'}
            
            logger.info(f"Category created: {category_id}, name: {name}, slug: {slug}")
            
            return {
                'success': True,
                'message': 'Category creation logged',
                'category_id': str(category_id)
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating category: {e}")
            return {'success': False, 'error': str(e)}
    
    def update(self, category_id, updates):
        """Update category with validation"""
        try:
            category_id = validate_object_id(category_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Validate updates
            allowed_fields = ['name', 'description', 'icon', 'image', 'isActive']
            filtered_updates = {}
            
            for key, value in updates.items():
                if key in allowed_fields:
                    if key == 'name' and value:
                        if len(value) < 2 or len(value) > 100:
                            return {'success': False, 'error': 'Category name must be between 2 and 100 characters'}
                    filtered_updates[key] = value
            
            if not filtered_updates:
                return {'success': False, 'error': 'No valid fields to update'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Check if category exists
                    category = self.collection.find_one({'_id': category_id}, session=session)
                    if not category:
                        return {'success': False, 'error': 'Category not found'}
                    
                    # Update category
                    filtered_updates['updatedAt'] = self._get_current_time()
                    result = self.collection.update_one(
                        {'_id': category_id},
                        {'$set': filtered_updates},
                        session=session
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"Category updated: {category_id}")
                        return {
                            'success': True,
                            'message': 'Category updated successfully',
                            'category_id': str(category_id)
                        }
                    else:
                        return {'success': False, 'error': 'No changes made'}
                        
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error updating category: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete(self, category_id):
        """Delete category with cascade checks"""
        try:
            category_id = validate_object_id(category_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            # Start transaction
            with self.db.client.start_session() as session:
                with session.start_transaction():
                    # Check if category exists
                    category = self.collection.find_one({'_id': category_id}, session=session)
                    if not category:
                        return {'success': False, 'error': 'Category not found'}
                    
                    # Check for gigs using this category
                    gigs_count = self.db.gigs.count_documents({
                        'category': category.get('name'),
                        'isActive': True
                    }, session=session)
                    
                    if gigs_count > 0:
                        return {
                            'success': False,
                            'error': f'Cannot delete category with {gigs_count} active gigs'
                        }
                    
                    # Soft delete
                    result = self.collection.update_one(
                        {'_id': category_id},
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
                    
                    logger.info(f"Category deleted: {category_id}")
                    return {
                        'success': True,
                        'message': 'Category deleted successfully',
                        'category_id': str(category_id)
                    }
                    
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error deleting category: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_stats(self, category_id):
        """Get category statistics"""
        try:
            category_id = validate_object_id(category_id)
            
            if not self.collection:
                return {'success': False, 'error': 'Database not available'}
            
            category = self.collection.find_one({'_id': category_id})
            if not category:
                return {'success': False, 'error': 'Category not found'}
            
            category_name = category.get('name')
            
            # Calculate statistics
            stats = {
                'totalGigs': 0,
                'activeGigs': 0,
                'totalOrders': 0,
                'completedOrders': 0,
                'averageRating': 0,
                'totalRevenue': 0
            }
            
            # Count gigs
            stats['totalGigs'] = self.db.gigs.count_documents({'category': category_name})
            stats['activeGigs'] = self.db.gigs.count_documents({
                'category': category_name,
                'isActive': True
            })
            
            # Get gig IDs for this category
            gig_ids = [g['_id'] for g in self.db.gigs.find({'category': category_name})]
            
            if gig_ids:
                # Count orders
                stats['totalOrders'] = self.db.orders.count_documents({'gigId': {'$in': gig_ids}})
                stats['completedOrders'] = self.db.orders.count_documents({
                    'gigId': {'$in': gig_ids},
                    'status': 'completed'
                })
                
                # Calculate total revenue
                pipeline = [
                    {'$match': {'gigId': {'$in': gig_ids}, 'status': 'completed'}},
                    {'$group': {'_id': None, 'totalRevenue': {'$sum': '$price'}}}
                ]
                revenue_result = list(self.db.orders.aggregate(pipeline))
                if revenue_result:
                    stats['totalRevenue'] = revenue_result[0].get('totalRevenue', 0)
                
                # Calculate average rating
                pipeline = [
                    {'$match': {'gigId': {'$in': gig_ids}}},
                    {'$group': {'_id': None, 'avgRating': {'$avg': '$rating'}}}
                ]
                rating_result = list(self.db.gigs.aggregate(pipeline))
                if rating_result:
                    stats['averageRating'] = round(rating_result[0].get('avgRating', 0), 2)
            
            return {
                'success': True,
                'stats': stats,
                'category_name': category_name
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error getting category stats: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_current_time(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow()
