from bson.objectid import ObjectId
from datetime import datetime
from pymongo.errors import PyMongoError
from typing import List, Optional

class GigsService:
    def __init__(self, db):
        self.collection = db["gigs"]

    def _sanitize(self, doc: dict) -> Optional[dict]:
        if not doc:
            return None
        for k in ["_id", "freelancer_id", "category_id"]:
            if k in doc:
                doc[k] = str(doc[k])
        return doc

    def create_gig(self, gig_data: dict) -> str:
        gig_data["freelancer_id"] = ObjectId(gig_data["freelancer_id"])
        gig_data["category_id"] = ObjectId(gig_data["category_id"])
        now = datetime.utcnow()

        defaults = {
            "status": "draft",
            "created_at": now,
            "updated_at": now,
            "total_orders": 0,
            "total_earning": 0.0,
            "gig_rating": 0.0,
            "gig_reviews": 0
        }
        gig_data.update(defaults)
        res = self.collection.insert_one(gig_data)
        return str(res.inserted_id)

    def get_gig(self, gig_id: str):
        doc = self.collection.find_one({"_id": ObjectId(gig_id)})
        return self._sanitize(doc)

    def update_gig(self, gig_id: str, update_data: dict) -> bool:
        update_data["updated_at"] = datetime.utcnow()
        if "freelancer_id" in update_data:
            update_data["freelancer_id"] = ObjectId(update_data["freelancer_id"])
        if "category_id" in update_data:
            update_data["category_id"] = ObjectId(update_data["category_id"])
        res = self.collection.update_one({"_id": ObjectId(gig_id)}, {"$set": update_data})
        return res.modified_count > 0

    def delete_gig(self, gig_id: str) -> bool:
        res = self.collection.delete_one({"_id": ObjectId(gig_id)})
        return res.deleted_count > 0

    def publish_gig(self, gig_id: str) -> bool:
        res = self.collection.update_one({"_id": ObjectId(gig_id)}, {
            "$set": {
                "status": "active",
                "published_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        })
        return res.modified_count > 0
