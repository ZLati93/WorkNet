"""
Security Utilities
JWT token generation/validation, password hashing, and permission management
"""

import os
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRES_IN = int(os.getenv('JWT_EXPIRES_IN_DAYS', '7'))  # days
JWT_REFRESH_EXPIRES_IN = int(os.getenv('JWT_REFRESH_EXPIRES_IN_DAYS', '30'))  # days

class SecurityError(Exception):
    """Custom security exception"""
    pass

# ==================== Password Hashing ====================

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
        
    Raises:
        SecurityError: If password hashing fails
    """
    try:
        if not password:
            raise SecurityError("Password cannot be empty")
        
        if len(password) < 6:
            raise SecurityError("Password must be at least 6 characters")
        
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise SecurityError(f"Failed to hash password: {str(e)}")

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against hash
    
    Args:
        password: Plain text password
        hashed: Hashed password string
        
    Returns:
        True if password matches, False otherwise
        
    Raises:
        SecurityError: If verification fails
    """
    try:
        if not password or not hashed:
            return False
        
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def validate_password_strength(password: str) -> Dict[str, any]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'valid': True,
        'errors': [],
        'strength': 'weak'
    }
    
    if len(password) < 6:
        result['valid'] = False
        result['errors'].append('Password must be at least 6 characters')
    
    if len(password) < 8:
        result['strength'] = 'weak'
    elif len(password) < 12:
        result['strength'] = 'medium'
    else:
        result['strength'] = 'strong'
    
    # Check for uppercase
    if not any(c.isupper() for c in password):
        result['strength'] = 'weak' if result['strength'] == 'weak' else 'medium'
    
    # Check for lowercase
    if not any(c.islower() for c in password):
        result['strength'] = 'weak' if result['strength'] == 'weak' else 'medium'
    
    # Check for numbers
    if not any(c.isdigit() for c in password):
        result['strength'] = 'weak' if result['strength'] == 'weak' else 'medium'
    
    # Check for special characters
    special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
    if not any(c in special_chars for c in password):
        result['strength'] = 'weak' if result['strength'] == 'weak' else 'medium'
    
    return result

# ==================== JWT Token Management ====================

def generate_token(payload: Dict, expires_in_days: Optional[int] = None) -> str:
    """
    Generate JWT token
    
    Args:
        payload: Token payload (should include 'id' and 'role')
        expires_in_days: Token expiration in days (default: JWT_EXPIRES_IN)
        
    Returns:
        JWT token string
        
    Raises:
        SecurityError: If token generation fails
    """
    try:
        if not payload.get('id'):
            raise SecurityError("Payload must include 'id'")
        
        expires_in = expires_in_days or JWT_EXPIRES_IN
        expiration = datetime.utcnow() + timedelta(days=expires_in)
        
        token_payload = {
            **payload,
            'exp': expiration,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise SecurityError(f"Failed to generate token: {str(e)}")

def generate_refresh_token(payload: Dict) -> str:
    """
    Generate refresh token
    
    Args:
        payload: Token payload
        
    Returns:
        Refresh token string
    """
    try:
        expiration = datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRES_IN)
        
        token_payload = {
            **payload,
            'exp': expiration,
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    except Exception as e:
        logger.error(f"Error generating refresh token: {e}")
        raise SecurityError(f"Failed to generate refresh token: {str(e)}")

def verify_token(token: str, token_type: str = 'access') -> Dict:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')
        
    Returns:
        Decoded token payload
        
    Raises:
        SecurityError: If token is invalid or expired
    """
    try:
        if not token:
            raise SecurityError("Token is required")
        
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Verify token type
        if decoded.get('type') != token_type:
            raise SecurityError(f"Invalid token type. Expected: {token_type}")
        
        return decoded
    except jwt.ExpiredSignatureError:
        raise SecurityError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise SecurityError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise SecurityError(f"Failed to verify token: {str(e)}")

def refresh_access_token(refresh_token: str) -> str:
    """
    Generate new access token from refresh token
    
    Args:
        refresh_token: Refresh token string
        
    Returns:
        New access token string
    """
    try:
        # Verify refresh token
        payload = verify_token(refresh_token, token_type='refresh')
        
        # Generate new access token
        new_payload = {
            'id': payload.get('id'),
            'role': payload.get('role')
        }
        
        return generate_token(new_payload)
    except SecurityError:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise SecurityError(f"Failed to refresh token: {str(e)}")

# ==================== Permission Management ====================

def check_permission(user_role: str, required_roles: List[str]) -> bool:
    """
    Check if user has required role
    
    Args:
        user_role: User's role
        required_roles: List of allowed roles
        
    Returns:
        True if user has permission, False otherwise
    """
    if not user_role:
        return False
    
    return user_role.lower() in [r.lower() for r in required_roles]

def require_role(*allowed_roles: str):
    """
    Decorator to require specific roles
    
    Usage:
        @require_role('admin', 'moderator')
        def admin_function():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user from args or kwargs
            user = kwargs.get('user') or (args[0] if args else None)
            
            if not user:
                raise SecurityError("User not found in request")
            
            user_role = user.get('role') if isinstance(user, dict) else getattr(user, 'role', None)
            
            if not check_permission(user_role, list(allowed_roles)):
                raise SecurityError(f"Access denied. Required roles: {allowed_roles}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_owner_or_role(*allowed_roles: str):
    """
    Decorator to require ownership or specific roles
    
    Usage:
        @require_owner_or_role('admin')
        def update_resource(resource_id, user):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get('user') or (args[0] if args else None)
            resource_user_id = kwargs.get('resource_user_id') or (args[1] if len(args) > 1 else None)
            
            if not user:
                raise SecurityError("User not found in request")
            
            user_id = user.get('id') if isinstance(user, dict) else getattr(user, '_id', None)
            user_role = user.get('role') if isinstance(user, dict) else getattr(user, 'role', None)
            
            # Check if user is owner
            is_owner = str(user_id) == str(resource_user_id)
            
            # Check if user has required role
            has_role = check_permission(user_role, list(allowed_roles))
            
            if not (is_owner or has_role):
                raise SecurityError("Access denied. Must be owner or have required role")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def is_admin(user_role: str) -> bool:
    """Check if user is admin"""
    return user_role and user_role.lower() == 'admin'

def is_seller(user_role: str, is_seller_flag: bool = False) -> bool:
    """Check if user is a seller/freelancer"""
    return (user_role and user_role.lower() == 'freelancer') or is_seller_flag

def is_client(user_role: str) -> bool:
    """Check if user is a client"""
    return user_role and user_role.lower() == 'client'

# ==================== Token Payload Helpers ====================

def create_token_payload(user_id: str, role: str, **extra) -> Dict:
    """
    Create standardized token payload
    
    Args:
        user_id: User ID
        role: User role
        **extra: Additional payload fields
        
    Returns:
        Token payload dictionary
    """
    payload = {
        'id': str(user_id),
        'role': role
    }
    payload.update(extra)
    return payload

def extract_user_from_token(token: str) -> Dict:
    """
    Extract user information from token
    
    Args:
        token: JWT token string
        
    Returns:
        User information dictionary
    """
    try:
        payload = verify_token(token)
        return {
            'id': payload.get('id'),
            'role': payload.get('role'),
            'exp': payload.get('exp'),
            'iat': payload.get('iat')
        }
    except SecurityError:
        raise
    except Exception as e:
        logger.error(f"Error extracting user from token: {e}")
        raise SecurityError(f"Failed to extract user from token: {str(e)}")

# ==================== Security Utilities ====================

def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize user input
    
    Args:
        input_str: Input string
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not input_str:
        return ''
    
    # Remove null bytes
    sanitized = input_str.replace('\x00', '')
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def generate_random_string(length: int = 32) -> str:
    """
    Generate random string for tokens/secrets
    
    Args:
        length: String length
        
    Returns:
        Random string
    """
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def mask_email(email: str) -> str:
    """
    Mask email address for privacy
    
    Args:
        email: Email address
        
    Returns:
        Masked email (e.g., j***@example.com)
    """
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 1:
        masked_local = '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 1)
    
    return f"{masked_local}@{domain}"

