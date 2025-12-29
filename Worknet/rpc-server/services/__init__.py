"""
Base service class for RPC services
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from pymongo.database import Database
from xmlrpc.client import Fault


class BaseService(ABC):
    """Base class for all RPC services"""
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize the service
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        if db is None:
            raise ValueError("Database connection is required")
    
    def get_collection(self, collection_name: str):
        """
        Get a MongoDB collection
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            MongoDB collection object
        """
        if self.db is None:
            raise Fault(500, "Database not connected")
        return self.db[collection_name]
    
    def handle_error(self, error: Exception, context: str = ""):
        """
        Handle errors consistently
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        
        if isinstance(error, Fault):
            raise error
        
        # Convert common exceptions to appropriate Faults
        if isinstance(error, (ValueError, TypeError)):
            raise Fault(400, f"Invalid input: {error_msg}")
        elif isinstance(error, KeyError):
            raise Fault(404, f"Resource not found: {error_msg}")
        else:
            raise Fault(500, f"Internal error: {error_msg}")

