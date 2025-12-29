"""
Validation utilities for RPC services
"""

import re
from bson import ObjectId
from datetime import datetime

def validate_object_id(id_str):
    """Validate MongoDB ObjectId"""
    try:
        return ObjectId(id_str)
    except:
        raise ValueError(f"Invalid ObjectId: {id_str}")

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email}")
    return email

def validate_username(username):
    """Validate username"""
    if not username or len(username) < 3 or len(username) > 50:
        raise ValueError("Username must be between 3 and 50 characters")
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValueError("Username can only contain letters, numbers, and underscores")
    return username

def validate_role(role):
    """Validate user role"""
    valid_roles = ['client', 'freelancer', 'admin']
    if role not in valid_roles:
        raise ValueError(f"Invalid role. Must be one of: {valid_roles}")
    return role

def validate_price(price):
    """Validate price"""
    try:
        price = float(price)
        if price < 0:
            raise ValueError("Price must be non-negative")
        return price
    except (ValueError, TypeError):
        raise ValueError(f"Invalid price: {price}")

def validate_rating(rating):
    """Validate rating (1-5)"""
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        return rating
    except (ValueError, TypeError):
        raise ValueError(f"Invalid rating: {rating}")

def validate_status(status, valid_statuses):
    """Validate status"""
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
    return status

def validate_date(date_str):
    """Validate date string"""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        raise ValueError(f"Invalid date format: {date_str}")

