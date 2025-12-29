"""
Users Service for WorkNet RPC Server
Handles user-related operations
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from services import BaseService
from utils.security import SecurityUtils
from typing import Dict, Any, Optional
from xmlrpc.client import Fault


class UsersService(BaseService):
    """Service for user management operations"""
    
    def __init__(self, db=None):
        """
        Initialize UsersService
        
        Args:
            db: MongoDB database instance
        """
        super().__init__(db)
        self.collection = self.get_collection('users')
    
    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user and return a token
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Dictionary with user info and token
        
        Raises:
            Fault: If authentication fails
        """
        try:
            # Find user by email
            user = self.collection.find_one({'email': email})
            
            if not user:
                raise Fault(401, "Invalid email or password")
            
            # Verify password
            if not SecurityUtils.verify_password(password, user.get('password', '')):
                raise Fault(401, "Invalid email or password")
            
            # Check if user is active
            if not user.get('isActive', True):
                raise Fault(403, "Account is inactive")
            
            if user.get('isSuspended', False):
                raise Fault(403, "Account is suspended")
            
            # Generate token
            token = SecurityUtils.generate_token(
                user_id=str(user['_id']),
                role=user.get('role', 'client'),
                additional_data={'email': email}
            )
            
            # Remove sensitive data
            user_dict = {
                'id': str(user['_id']),
                'email': user.get('email'),
                'username': user.get('username'),
                'firstName': user.get('firstName'),
                'lastName': user.get('lastName'),
                'role': user.get('role'),
                'isEmailVerified': user.get('isEmailVerified', False),
            }
            
            return {
                'user': user_dict,
                'token': token
            }
            
        except Fault:
            raise
        except Exception as e:
            self.handle_error(e, "Authentication failed")
    
    def get_user_by_id(self, user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            token: Authentication token (optional, for private info)
        
        Returns:
            User information
        """
        try:
            from bson import ObjectId
            
            user = self.collection.find_one({'_id': ObjectId(user_id)})
            
            if not user:
                raise Fault(404, "User not found")
            
            # Remove sensitive fields
            user_dict = {
                'id': str(user['_id']),
                'username': user.get('username'),
                'firstName': user.get('firstName'),
                'lastName': user.get('lastName'),
                'role': user.get('role'),
            }
            
            # Include additional fields if authenticated as same user or admin
            if token:
                try:
                    auth_info = SecurityUtils.require_auth(token)
                    if auth_info.get('user_id') == user_id or auth_info.get('role') == 'admin':
                        user_dict.update({
                            'email': user.get('email'),
                            'phone': user.get('phone'),
                            'country': user.get('country'),
                            'city': user.get('city'),
                        })
                except:
                    pass  # If token invalid, just return public info
            
            return user_dict
            
        except Fault:
            raise
        except Exception as e:
            self.handle_error(e, "Failed to get user")

