"""
Database Utilities
MongoDB helper functions, complex aggregations, and transaction management
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from bson import ObjectId
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    DuplicateKeyError,
    WriteError,
    PyMongoError
)
from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom database exception"""
    pass

# ==================== Connection Management ====================

def get_database_connection(uri: str, db_name: str) -> Database:
    """
    Get database connection
    
    Args:
        uri: MongoDB connection URI
        db_name: Database name
        
    Returns:
        Database instance
        
    Raises:
        DatabaseError: If connection fails
    """
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        db = client[db_name]
        logger.info(f"Database connection established: {db_name}")
        return db
    except ConnectionFailure as e:
        logger.error(f"Database connection failed: {e}")
        raise DatabaseError(f"Failed to connect to database: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        raise DatabaseError(f"Database error: {str(e)}")

# ==================== Transaction Management ====================

def execute_transaction(db: Database, operations: Callable, *args, **kwargs) -> Any:
    """
    Execute operations within a transaction
    
    Args:
        db: Database instance
        operations: Function containing operations to execute
        *args: Positional arguments for operations function
        **kwargs: Keyword arguments for operations function
        
    Returns:
        Result from operations function
        
    Raises:
        DatabaseError: If transaction fails
    """
    session = db.client.start_session()
    try:
        with session.start_transaction():
            result = operations(db, session, *args, **kwargs)
            return result
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        session.abort_transaction()
        raise DatabaseError(f"Transaction failed: {str(e)}")
    finally:
        session.end_session()

def with_transaction(db: Database):
    """
    Decorator for transaction management
    
    Usage:
        @with_transaction(db)
        def my_operation(db, session, arg1, arg2):
            # Use session for all operations
            db.collection.insert_one({}, session=session)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            session = db.client.start_session()
            try:
                with session.start_transaction():
                    # Inject session as second argument
                    result = func(db, session, *args, **kwargs)
                    return result
            except Exception as e:
                logger.error(f"Transaction failed in {func.__name__}: {e}")
                session.abort_transaction()
                raise DatabaseError(f"Transaction failed: {str(e)}")
            finally:
                session.end_session()
        return wrapper
    return decorator

# ==================== ObjectId Utilities ====================

def to_object_id(id_value: Any) -> ObjectId:
    """
    Convert value to ObjectId
    
    Args:
        id_value: Value to convert (string, ObjectId, etc.)
        
    Returns:
        ObjectId instance
        
    Raises:
        DatabaseError: If conversion fails
    """
    try:
        if isinstance(id_value, ObjectId):
            return id_value
        if isinstance(id_value, str):
            return ObjectId(id_value)
        raise ValueError(f"Cannot convert {type(id_value)} to ObjectId")
    except Exception as e:
        raise DatabaseError(f"Invalid ObjectId: {str(e)}")

def to_object_id_list(id_list: List[Any]) -> List[ObjectId]:
    """
    Convert list of values to ObjectIds
    
    Args:
        id_list: List of values to convert
        
    Returns:
        List of ObjectId instances
    """
    return [to_object_id(id_val) for id_val in id_list]

def is_valid_object_id(id_value: Any) -> bool:
    """
    Check if value is a valid ObjectId
    
    Args:
        id_value: Value to check
        
    Returns:
        True if valid, False otherwise
    """
    try:
        to_object_id(id_value)
        return True
    except:
        return False

# ==================== Query Builders ====================

def build_date_range_query(field: str, start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None) -> Dict:
    """
    Build date range query
    
    Args:
        field: Field name
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        MongoDB query dictionary
    """
    query = {}
    if start_date or end_date:
        query[field] = {}
        if start_date:
            query[field]['$gte'] = start_date
        if end_date:
            query[field]['$lte'] = end_date
    return query

def build_text_search_query(fields: List[str], search_term: str) -> Dict:
    """
    Build text search query
    
    Args:
        fields: List of fields to search
        search_term: Search term
        
    Returns:
        MongoDB query dictionary
    """
    if not search_term:
        return {}
    
    return {
        '$or': [
            {field: {'$regex': search_term, '$options': 'i'}}
            for field in fields
        ]
    }

def build_pagination_query(page: int, limit: int) -> Dict:
    """
    Build pagination parameters
    
    Args:
        page: Page number (1-indexed)
        limit: Items per page
        
    Returns:
        Dictionary with skip and limit
    """
    page = max(1, page)
    limit = max(1, min(limit, 100))  # Max 100 items per page
    skip = (page - 1) * limit
    
    return {
        'skip': skip,
        'limit': limit,
        'page': page
    }

# ==================== Aggregation Pipelines ====================

def build_lookup_pipeline(from_collection: str, local_field: str, 
                         foreign_field: str, as_field: str) -> Dict:
    """
    Build $lookup aggregation stage
    
    Args:
        from_collection: Collection to lookup
        local_field: Local field name
        foreign_field: Foreign field name
        as_field: Output field name
        
    Returns:
        $lookup stage dictionary
    """
    return {
        '$lookup': {
            'from': from_collection,
            'localField': local_field,
            'foreignField': foreign_field,
            'as': as_field
        }
    }

def build_match_pipeline(query: Dict) -> Dict:
    """
    Build $match aggregation stage
    
    Args:
        query: MongoDB query
        
    Returns:
        $match stage dictionary
    """
    return {'$match': query}

def build_group_pipeline(group_by: str, aggregations: Dict) -> Dict:
    """
    Build $group aggregation stage
    
    Args:
        group_by: Field to group by (use None for single group)
        aggregations: Aggregation operations
        
    Returns:
        $group stage dictionary
    """
    group_stage = {'_id': group_by} if group_by else {'_id': None}
    group_stage.update(aggregations)
    return {'$group': group_stage}

def build_sort_pipeline(sort_fields: Dict) -> Dict:
    """
    Build $sort aggregation stage
    
    Args:
        sort_fields: Dictionary of field: direction (1 for asc, -1 for desc)
        
    Returns:
        $sort stage dictionary
    """
    return {'$sort': sort_fields}

def build_project_pipeline(fields: Dict) -> Dict:
    """
    Build $project aggregation stage
    
    Args:
        fields: Dictionary of field: 1 (include) or 0 (exclude)
        
    Returns:
        $project stage dictionary
    """
    return {'$project': fields}

def build_facet_pipeline(facets: Dict) -> Dict:
    """
    Build $facet aggregation stage
    
    Args:
        facets: Dictionary of facet_name: pipeline
        
    Returns:
        $facet stage dictionary
    """
    return {'$facet': facets}

# ==================== Complex Aggregations ====================

def aggregate_user_stats(db: Database, user_id: ObjectId, 
                         session: Optional[Any] = None) -> Dict:
    """
    Aggregate comprehensive user statistics
    
    Args:
        db: Database instance
        user_id: User ObjectId
        session: MongoDB session (optional)
        
    Returns:
        User statistics dictionary
    """
    user_id_str = str(user_id)
    
    # Get user
    user = db.users.find_one({'_id': user_id}, session=session)
    if not user:
        return {}
    
    stats = {
        'userId': user_id_str,
        'role': user.get('role'),
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
    
    if user.get('role') == 'freelancer':
        # Order statistics
        stats['totalOrders'] = db.orders.count_documents(
            {'sellerId': user_id}, session=session
        )
        stats['completedOrders'] = db.orders.count_documents(
            {'sellerId': user_id, 'status': 'completed'}, session=session
        )
        stats['activeOrders'] = db.orders.count_documents(
            {'sellerId': user_id, 'status': {'$in': ['pending', 'in_progress']}},
            session=session
        )
        
        # Gig statistics
        stats['totalGigs'] = db.gigs.count_documents(
            {'userId': user_id}, session=session
        )
        stats['activeGigs'] = db.gigs.count_documents(
            {'userId': user_id, 'isActive': True}, session=session
        )
        
        # Review statistics
        gig_ids = [g['_id'] for g in db.gigs.find({'userId': user_id}, session=session)]
        if gig_ids:
            pipeline = [
                {'$match': {'gigId': {'$in': gig_ids}}},
                {'$group': {
                    '_id': None,
                    'avgRating': {'$avg': '$rating'},
                    'count': {'$sum': 1}
                }}
            ]
            review_stats = list(db.reviews.aggregate(pipeline, session=session))
            if review_stats:
                stats['averageRating'] = round(review_stats[0].get('avgRating', 0), 2)
                stats['totalReviews'] = review_stats[0].get('count', 0)
    
    return stats

def aggregate_gig_stats(db: Database, gig_id: ObjectId,
                       session: Optional[Any] = None) -> Dict:
    """
    Aggregate comprehensive gig statistics
    
    Args:
        db: Database instance
        gig_id: Gig ObjectId
        session: MongoDB session (optional)
        
    Returns:
        Gig statistics dictionary
    """
    gig = db.gigs.find_one({'_id': gig_id}, session=session)
    if not gig:
        return {}
    
    stats = {
        'gigId': str(gig_id),
        'title': gig.get('title'),
        'price': gig.get('price', 0),
        'rating': gig.get('rating', 0),
        'sales': gig.get('sales', 0),
        'totalOrders': 0,
        'completedOrders': 0,
        'activeOrders': 0,
        'totalReviews': 0,
        'averageRating': 0,
        'totalRevenue': 0
    }
    
    # Order statistics
    stats['totalOrders'] = db.orders.count_documents(
        {'gigId': gig_id}, session=session
    )
    stats['completedOrders'] = db.orders.count_documents(
        {'gigId': gig_id, 'status': 'completed'}, session=session
    )
    stats['activeOrders'] = db.orders.count_documents(
        {'gigId': gig_id, 'status': {'$in': ['pending', 'in_progress']}},
        session=session
    )
    
    # Revenue calculation
    pipeline = [
        {'$match': {'gigId': gig_id, 'status': 'completed'}},
        {'$group': {
            '_id': None,
            'totalRevenue': {'$sum': '$price'}
        }}
    ]
    revenue_result = list(db.orders.aggregate(pipeline, session=session))
    if revenue_result:
        stats['totalRevenue'] = revenue_result[0].get('totalRevenue', 0)
    
    # Review statistics
    pipeline = [
        {'$match': {'gigId': gig_id}},
        {'$group': {
            '_id': None,
            'avgRating': {'$avg': '$rating'},
            'count': {'$sum': 1}
        }}
    ]
    review_result = list(db.reviews.aggregate(pipeline, session=session))
    if review_result:
        stats['averageRating'] = round(review_result[0].get('avgRating', 0), 2)
        stats['totalReviews'] = review_result[0].get('count', 0)
    
    return stats

def aggregate_category_stats(db: Database, category_name: str,
                            session: Optional[Any] = None) -> Dict:
    """
    Aggregate category statistics
    
    Args:
        db: Database instance
        category_name: Category name
        session: MongoDB session (optional)
        
    Returns:
        Category statistics dictionary
    """
    stats = {
        'category': category_name,
        'totalGigs': 0,
        'activeGigs': 0,
        'totalOrders': 0,
        'completedOrders': 0,
        'totalRevenue': 0,
        'averageRating': 0
    }
    
    # Get gig IDs for category
    gig_ids = [g['_id'] for g in db.gigs.find({'category': category_name}, session=session)]
    
    if gig_ids:
        stats['totalGigs'] = len(gig_ids)
        stats['activeGigs'] = db.gigs.count_documents(
            {'category': category_name, 'isActive': True}, session=session
        )
        
        # Order statistics
        stats['totalOrders'] = db.orders.count_documents(
            {'gigId': {'$in': gig_ids}}, session=session
        )
        stats['completedOrders'] = db.orders.count_documents(
            {'gigId': {'$in': gig_ids}, 'status': 'completed'}, session=session
        )
        
        # Revenue calculation
        pipeline = [
            {'$match': {'gigId': {'$in': gig_ids}, 'status': 'completed'}},
            {'$group': {
                '_id': None,
                'totalRevenue': {'$sum': '$price'}
            }}
        ]
        revenue_result = list(db.orders.aggregate(pipeline, session=session))
        if revenue_result:
            stats['totalRevenue'] = revenue_result[0].get('totalRevenue', 0)
        
        # Average rating
        pipeline = [
            {'$match': {'gigId': {'$in': gig_ids}}},
            {'$group': {
                '_id': None,
                'avgRating': {'$avg': '$rating'}
            }}
        ]
        rating_result = list(db.gigs.aggregate(pipeline, session=session))
        if rating_result:
            stats['averageRating'] = round(rating_result[0].get('avgRating', 0), 2)
    
    return stats

# ==================== Helper Functions ====================

def safe_find_one(collection: Collection, query: Dict, 
                 session: Optional[Any] = None) -> Optional[Dict]:
    """
    Safely find one document
    
    Args:
        collection: MongoDB collection
        query: Query dictionary
        session: MongoDB session (optional)
        
    Returns:
        Document or None
    """
    try:
        return collection.find_one(query, session=session)
    except Exception as e:
        logger.error(f"Error finding document: {e}")
        return None

def safe_insert_one(collection: Collection, document: Dict,
                   session: Optional[Any] = None) -> Optional[ObjectId]:
    """
    Safely insert one document
    
    Args:
        collection: MongoDB collection
        document: Document to insert
        session: MongoDB session (optional)
        
    Returns:
        Inserted document ID or None
    """
    try:
        result = collection.insert_one(document, session=session)
        return result.inserted_id
    except DuplicateKeyError as e:
        logger.error(f"Duplicate key error: {e}")
        raise DatabaseError("Duplicate key violation")
    except Exception as e:
        logger.error(f"Error inserting document: {e}")
        raise DatabaseError(f"Failed to insert document: {str(e)}")

def safe_update_one(collection: Collection, query: Dict, update: Dict,
                   session: Optional[Any] = None) -> bool:
    """
    Safely update one document
    
    Args:
        collection: MongoDB collection
        query: Query dictionary
        update: Update dictionary
        session: MongoDB session (optional)
        
    Returns:
        True if document was updated, False otherwise
    """
    try:
        result = collection.update_one(query, update, session=session)
        return result.modified_count > 0
    except WriteError as e:
        logger.error(f"Write error: {e}")
        raise DatabaseError(f"Failed to update document: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        raise DatabaseError(f"Failed to update document: {str(e)}")

def safe_delete_one(collection: Collection, query: Dict,
                   session: Optional[Any] = None) -> bool:
    """
    Safely delete one document
    
    Args:
        collection: MongoDB collection
        query: Query dictionary
        session: MongoDB session (optional)
        
    Returns:
        True if document was deleted, False otherwise
    """
    try:
        result = collection.delete_one(query, session=session)
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise DatabaseError(f"Failed to delete document: {str(e)}")

def get_current_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.utcnow()

def add_timestamps(document: Dict, include_updated: bool = True) -> Dict:
    """
    Add createdAt and updatedAt timestamps to document
    
    Args:
        document: Document dictionary
        include_updated: Whether to include updatedAt
        
    Returns:
        Document with timestamps
    """
    now = get_current_timestamp()
    document['createdAt'] = document.get('createdAt', now)
    if include_updated:
        document['updatedAt'] = now
    return document

