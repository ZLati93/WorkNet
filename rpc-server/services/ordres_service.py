from datetime import datetime
from bson.objectid import ObjectId
import uuid

class OrdresService:
    def __init__(self, db):
        self.db = db
        self.collection = db["orders"]

    def create_order(self, order_data):
        # Validate required fields
        required_fields = ["client_id", "freelancer_id", "gig_id", "title", "amount", "deadline"]
        for field in required_fields:
            if field not in order_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Convert IDs to ObjectId
        order_data["client_id"] = ObjectId(order_data["client_id"])
        order_data["freelancer_id"] = ObjectId(order_data["freelancer_id"])
        order_data["gig_id"] = ObjectId(order_data["gig_id"])
        
        # Generate order number
        order_data["order_number"] = f"ORD-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Add timestamps and defaults
        order_data["created_at"] = datetime.utcnow()
        order_data["updated_at"] = datetime.utcnow()
        order_data["status"] = "pending"
        order_data["revision_count"] = 0
        
        result = self.collection.insert_one(order_data)
        return str(result.inserted_id)

    def get_order(self, order_id):
        order = self.collection.find_one({"_id": ObjectId(order_id)})
        if order:
            order["_id"] = str(order["_id"])
            order["client_id"] = str(order["client_id"])
            order["freelancer_id"] = str(order["freelancer_id"])
            order["gig_id"] = str(order["gig_id"])
            return order
        return None

    def update_order(self, order_id, update_data):
        update_data["updated_at"] = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def get_orders_by_client(self, client_id, status=None):
        query = {"client_id": ObjectId(client_id)}
        if status:
            query["status"] = status
        
        orders = list(self.collection.find(query).sort("created_at", -1))
        for o in orders:
            o["_id"] = str(o["_id"])
            o["client_id"] = str(o["client_id"])
            o["freelancer_id"] = str(o["freelancer_id"])
            o["gig_id"] = str(o["gig_id"])
        return orders

    def get_orders_by_freelancer(self, freelancer_id, status=None):
        query = {"freelancer_id": ObjectId(freelancer_id)}
        if status:
            query["status"] = status
        
        orders = list(self.collection.find(query).sort("created_at", -1))
        for o in orders:
            o["_id"] = str(o["_id"])
            o["client_id"] = str(o["client_id"])
            o["freelancer_id"] = str(o["freelancer_id"])
            o["gig_id"] = str(o["gig_id"])
        return orders

    def confirm_order(self, order_id):
        result = self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "confirmed", "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def start_order(self, order_id):
        result = self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "in_progress", "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def deliver_order(self, order_id, delivery_files=None, delivery_message=None):
        update_data = {
            "status": "delivered",
            "delivered_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        if delivery_files:
            update_data["delivery_files"] = delivery_files
        if delivery_message:
            update_data["delivery_message"] = delivery_message
        
        result = self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def complete_order(self, order_id):
        result = self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "completed", "completed_at": datetime.utcnow(), "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def request_revision(self, order_id):
        # Increment revision count
        order = self.collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            return False
        
        new_revision_count = order.get("revision_count", 0) + 1
        max_revisions = order.get("max_revisions", 3)
        
        if new_revision_count > max_revisions:
            raise ValueError("Maximum revisions reached")
        
        result = self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "revision_requested", "revision_count": new_revision_count, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def cancel_order(self, order_id):
        result = self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0