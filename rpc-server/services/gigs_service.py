from datetime import datetime
from bson.objectid import ObjectId

class GigsService:
    def __init__(self, db):
        self.db = db
        self.collection = db["gigs"]

    def create_gig(self, gig_data):
        # Validate required fields
        required_fields = ["freelancer_id", "category_id", "title", "description", "base_price", "delivery_days"]
        for field in required_fields:
            if field not in gig_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Convert IDs to ObjectId
        gig_data["freelancer_id"] = ObjectId(gig_data["freelancer_id"])
        gig_data["category_id"] = ObjectId(gig_data["category_id"])
        
        # Add timestamps and defaults
        gig_data["created_at"] = datetime.utcnow()
        gig_data["updated_at"] = datetime.utcnow()
        gig_data["status"] = "draft"
        gig_data["total_orders"] = 0
        gig_data["total_earning"] = 0.0
        gig_data["gig_rating"] = 0.0
        gig_data["gig_reviews"] = 0
        
        result = self.collection.insert_one(gig_data)
        return str(result.inserted_id)

    def get_gig(self, gig_id):
        gig = self.collection.find_one({"_id": ObjectId(gig_id)})
        if gig:
            gig["_id"] = str(gig["_id"])
            gig["freelancer_id"] = str(gig["freelancer_id"])
            gig["category_id"] = str(gig["category_id"])
            return gig
        return None

    def update_gig(self, gig_id, update_data):
        update_data["updated_at"] = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(gig_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_gig(self, gig_id):
        result = self.collection.delete_one({"_id": ObjectId(gig_id)})
        return result.deleted_count > 0

    def publish_gig(self, gig_id):
        result = self.collection.update_one(
            {"_id": ObjectId(gig_id)},
            {"$set": {"status": "active", "published_at": datetime.utcnow(), "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def get_gigs_by_freelancer(self, freelancer_id, status=None):
        query = {"freelancer_id": ObjectId(freelancer_id)}
        if status:
            query["status"] = status
        
        gigs = list(self.collection.find(query))
        for g in gigs:
            g["_id"] = str(g["_id"])
            g["freelancer_id"] = str(g["freelancer_id"])
            g["category_id"] = str(g["category_id"])
        return gigs

    def get_gigs_by_category(self, category_id, limit=20, skip=0):
        gigs = list(self.collection.find(
            {"category_id": ObjectId(category_id), "status": "active"}
        ).skip(skip).limit(limit))
        for g in gigs:
            g["_id"] = str(g["_id"])
            g["freelancer_id"] = str(g["freelancer_id"])
            g["category_id"] = str(g["category_id"])
        return gigs

    def search_gigs(self, query_text, category_id=None, min_price=None, max_price=None, limit=20):
        search_query = {"status": "active"}
        
        if category_id:
            search_query["category_id"] = ObjectId(category_id)
        
        if min_price is not None or max_price is not None:
            price_query = {}
            if min_price is not None:
                price_query["$gte"] = min_price
            if max_price is not None:
                price_query["$lte"] = max_price
            search_query["base_price"] = price_query
        
        # Text search
        if query_text:
            search_query["$text"] = {"$search": query_text}
        
        gigs = list(self.collection.find(search_query).limit(limit))
        for g in gigs:
            g["_id"] = str(g["_id"])
            g["freelancer_id"] = str(g["freelancer_id"])
            g["category_id"] = str(g["category_id"])
        return gigs

    def get_featured_gigs(self, limit=10):
        gigs = list(self.collection.find(
            {"status": "active", "is_featured": True}
        ).limit(limit))
        for g in gigs:
            g["_id"] = str(g["_id"])
            g["freelancer_id"] = str(g["freelancer_id"])
            g["category_id"] = str(g["category_id"])
        return gigs