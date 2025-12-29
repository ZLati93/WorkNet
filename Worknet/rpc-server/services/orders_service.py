"""
Orders Service for WorkNet RPC Server
Handles order-related operations
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


class OrdersService(BaseService):
    """Service for order management operations"""
    
    def __init__(self, db=None):
        """Initialize OrdersService"""
        super().__init__(db)
        self.collection = self.get_collection('orders')
    
    def create_order(self, gig_id: str, client_id: str, requirements: str) -> Dict[str, Any]:
        """Create a new order"""
        try:
            # Get gig to get price
            gigs_collection = self.get_collection('gigs')
            gig = gigs_collection.find_one({'_id': ObjectId(gig_id)})
            if not gig:
                raise Fault(404, "Gig not found")
            
            order_data = {
                'gigId': ObjectId(gig_id),
                'clientId': ObjectId(client_id),
                'freelancerId': gig.get('freelancerId'),
                'requirements': requirements,
                'price': gig.get('price'),
                'status': 'pending',
                'createdAt': None,
                'updatedAt': None
            }
            result = self.collection.insert_one(order_data)
            order_data['id'] = str(result.inserted_id)
            order_data['_id'] = result.inserted_id
            return self._format_order(order_data)
        except Fault:
            raise
        except Exception as e:
            self.handle_error(e, "Failed to create order")
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get an order by ID"""
        try:
            order = self.collection.find_one({'_id': ObjectId(order_id)})
            if not order:
                raise Fault(404, "Order not found")
            return self._format_order(order)
        except Fault:
            raise
        except Exception as e:
            self.handle_error(e, "Failed to get order")
    
    def list_orders(self, client_id: Optional[str] = None, freelancer_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List orders with optional filters"""
        try:
            query = {}
            if client_id:
                query['clientId'] = ObjectId(client_id)
            if freelancer_id:
                query['freelancerId'] = ObjectId(freelancer_id)
            if status:
                query['status'] = status
            
            orders = self.collection.find(query)
            return [self._format_order(order) for order in orders]
        except Exception as e:
            self.handle_error(e, "Failed to list orders")
    
    def update_order_status(self, order_id: str, status: str) -> Dict[str, Any]:
        """Update order status"""
        try:
            valid_statuses = ['pending', 'accepted', 'in_progress', 'completed', 'cancelled']
            if status not in valid_statuses:
                raise Fault(400, f"Invalid status. Must be one of: {valid_statuses}")
            
            result = self.collection.update_one(
                {'_id': ObjectId(order_id)},
                {'$set': {'status': status, 'updatedAt': None}}
            )
            if result.matched_count == 0:
                raise Fault(404, "Order not found")
            return self.get_order(order_id)
        except Fault:
            raise
        except Exception as e:
            self.handle_error(e, "Failed to update order status")
    
    def _format_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Format order document for response"""
        return {
            'id': str(order.get('_id')),
            'gigId': str(order.get('gigId')),
            'clientId': str(order.get('clientId')),
            'freelancerId': str(order.get('freelancerId')),
            'requirements': order.get('requirements'),
            'price': order.get('price'),
            'status': order.get('status'),
        }

