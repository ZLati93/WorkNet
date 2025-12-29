"""
Security utilities for authentication and authorization
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from xmlrpc.client import Fault


# Authentication errors
class AuthenticationError(Fault):
    """Raised when authentication fails"""
    pass


class AuthorizationError(Fault):
    """Raised when authorization fails"""
    pass


class SecurityUtils:
    """Security utility class for authentication and authorization"""
    
    # Get JWT secret from environment
    JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verify a password against a hash
        
        Args:
            password: Plain text password
            hashed: Hashed password
        
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def generate_token(user_id: str, role: str, additional_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a JWT token for a user
        
        Args:
            user_id: User ID
            role: User role ('client', 'freelancer', 'admin')
            additional_data: Additional data to include in token
        
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=SecurityUtils.JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        
        if additional_data:
            payload.update(additional_data)
        
        return jwt.encode(payload, SecurityUtils.JWT_SECRET, algorithm=SecurityUtils.JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token payload
        
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                SecurityUtils.JWT_SECRET,
                algorithms=[SecurityUtils.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError(401, "Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(401, f"Invalid token: {str(e)}")
    
    @staticmethod
    def require_auth(token: Optional[str]) -> Dict[str, Any]:
        """
        Require authentication and return user info from token
        
        Args:
            token: JWT token string
        
        Returns:
            User information from token
        
        Raises:
            AuthenticationError: If token is missing or invalid
        """
        if not token:
            raise AuthenticationError(401, "Authentication token required")
        
        return SecurityUtils.verify_token(token)
    
    @staticmethod
    def require_role(token: Optional[str], required_roles: list) -> Dict[str, Any]:
        """
        Require authentication and specific role(s)
        
        Args:
            token: JWT token string
            required_roles: List of allowed roles
        
        Returns:
            User information from token
        
        Raises:
            AuthenticationError: If token is invalid
            AuthorizationError: If user role is not authorized
        """
        user_info = SecurityUtils.require_auth(token)
        user_role = user_info.get('role')
        
        if user_role not in required_roles:
            raise AuthorizationError(
                403,
                f"Access denied. Required roles: {required_roles}, but user has role: {user_role}"
            )
        
        return user_info
    
    @staticmethod
    def require_admin(token: Optional[str]) -> Dict[str, Any]:
        """Require admin role"""
        return SecurityUtils.require_role(token, ['admin'])
    
    @staticmethod
    def require_freelancer(token: Optional[str]) -> Dict[str, Any]:
        """Require freelancer role"""
        return SecurityUtils.require_role(token, ['freelancer', 'admin'])
    
    @staticmethod
    def require_client(token: Optional[str]) -> Dict[str, Any]:
        """Require client role"""
        return SecurityUtils.require_role(token, ['client', 'admin'])

