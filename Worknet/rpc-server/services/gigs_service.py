"""
Gigs Service for WorkNet RPC Server
Handles gig-related operations
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from services import BaseService
from typing import Dict, Any, Optional, List
from xmlrpc.client import Fault
from bson import ObjectId


class GigsService(BaseService):
    """Service for gig management operations"""
    
    def __init__(self, db=None):
        """Initialize GigsService"""
        super().__init__(db)
        self.collection = self.get_collection('gigs')
    
    def create_gig(self, title: str, description: str, price: float, category: str, freelancer_id: str) -> Dict[str, Any]:
        """Create a new gig"""
        try:
            gig_data = {
                'title': title,
                'description': description,
                'price': price,
                'category': category,
                'freelancerId': ObjectId(freelancer_id),
                'status': 'active',
                'createdAt': None,  # Will be set by MongoDB
                'updatedAt': None
            }
            result = self.collection.insert_one(gig_data)
            gig_data['id'] = str(result.inserted_id)
            gig_data['_id'] = result.inserted_id
            return self._format_gig(gig_data)
        except Exception as e:
            self.handle_error(e, "Failed to create gig")
    
    def get_gig(self, gig_id: str) -> Dict[str, Any]:
        """Get a gig by ID"""
        try:
            gig = self.collection.find_one({'_id': ObjectId(gig_id)})
            if not gig:
                raise Fault(404, "Gig not found")
            return self._format_gig(gig)
        except Fault:
            raise
        except Exception as e:
            self.handle_error(e, "Failed to get gig")
    
    def list_gigs(self, category: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List gigs with optional filters"""
        try:
            query = {}
            if category:
                query['category'] = category
            if status:
                query['status'] = status
            
            gigs = self.collection.find(query).limit(limit)
            return [self._format_gig(gig) for gig in gigs]
        except Exception as e:
            self.handle_error(e, "Failed to list gigs")
    
    def update_gig(self, gig_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a gig"""
        try:
            updates['updatedAt'] = None  # Will be set by MongoDB
            result = self.collection.update_one(
                {'_id': ObjectId(gig_id)},
                {'$set': updates}
            )
            if result.matched_count == 0:
                raise Fault(404, "Gig not found")
            return self.get_gig(gig_id)
        except Fault:
            raise
        except Exception as e:
            self.handle_error(e, "Failed to update gig")
    
    def delete_gig(self, gig_id: str) -> bool:
        """Delete a gig"""
        try:
            result = self.collection.delete_one({'_id': ObjectId(gig_id)})
            return result.deleted_count > 0
        except Exception as e:
            self.handle_error(e, "Failed to delete gig")
    
    def _format_gig(self, gig: Dict[str, Any]) -> Dict[str, Any]:
        """Format gig document for response"""
        return {
            'id': str(gig.get('_id')),
            'title': gig.get('title'),
            'description': gig.get('description'),
            'price': gig.get('price'),
            'category': gig.get('category'),
            'freelancerId': str(gig.get('freelancerId')),
            'status': gig.get('status'),
        }

