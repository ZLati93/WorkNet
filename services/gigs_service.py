from bson.objectid import ObjectId, InvalidId
from datetime import datetime
from typing import List, Optional, Dict
from pymongo.errors import PyMongoError


class GigsService:
    def __init__(self, db):
        self.collection = db["gigs"]

    # ---------------------------------------------------------
    # Utility: sanitize MongoDB document → JSON-safe
    # ---------------------------------------------------------
    def _sanitize(self, doc: dict) -> Optional[dict]:
        if not doc:
            return None
        try:
            for k in ["_id", "freelancer_id", "category_id"]:
                if k in doc:
                    doc[k] = str(doc[k])
            # Convert datetime to ISO format
            for dt_field in ["created_at", "updated_at", "published_at"]:
                if dt_field in doc and doc[dt_field]:
                    doc[dt_field] = doc[dt_field].isoformat()
            return doc
        except Exception:
            return None

    # ---------------------------------------------------------
    # 🎨 CREATE GIG
    # ---------------------------------------------------------
    def create_gig(self, gig_data: dict) -> dict:
        try:
            gig_data["freelancer_id"] = ObjectId(gig_data["freelancer_id"])
            gig_data["category_id"] = ObjectId(gig_data["category_id"])
        except InvalidId:
            return {"error": "Invalid freelancer_id or category_id"}

        now = datetime.utcnow()
        defaults = {
            "status": "draft",
            "created_at": now,
            "updated_at": now,
            "total_orders": 0,
            "total_earning": 0.0,
            "gig_rating": 0.0,
            "gig_reviews": 0,
            "featured": False
        }
        gig_data.update(defaults)

        try:
            res = self.collection.insert_one(gig_data)
            return {"success": True, "gig_id": str(res.inserted_id)}
        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 🔍 GET ONE GIG
    # ---------------------------------------------------------
    def get_gig(self, gig_id: str) -> dict:
        try:
            oid = ObjectId(gig_id)
        except InvalidId:
            return {"success": False, "error": "Invalid gig_id"}

        try:
            doc = self.collection.find_one({"_id": oid})
            return {"success": True, "gig": self._sanitize(doc)} if doc else {"success": False, "error": "Gig not found"}
        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # ✏ UPDATE GIG
    # ---------------------------------------------------------
    def update_gig(self, gig_id: str, update_data: dict) -> dict:
        try:
            gig_oid = ObjectId(gig_id)
        except InvalidId:
            return {"success": False, "error": "Invalid gig_id"}

        try:
            update_data["updated_at"] = datetime.utcnow()
            if "freelancer_id" in update_data:
                update_data["freelancer_id"] = ObjectId(update_data["freelancer_id"])
            if "category_id" in update_data:
                update_data["category_id"] = ObjectId(update_data["category_id"])
        except InvalidId:
            return {"success": False, "error": "Invalid freelancer_id or category_id"}

        try:
            res = self.collection.update_one({"_id": gig_oid}, {"$set": update_data})
            return {"success": True, "updated": res.modified_count > 0}
        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 🗑 DELETE GIG
    # ---------------------------------------------------------
    def delete_gig(self, gig_id: str) -> dict:
        try:
            oid = ObjectId(gig_id)
        except InvalidId:
            return {"success": False, "error": "Invalid gig_id"}

        try:
            res = self.collection.delete_one({"_id": oid})
            return {"success": True, "deleted": res.deleted_count > 0}
        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 📢 Publish / Pause / Activate / Reject
    # ---------------------------------------------------------
    def publish_gig(self, gig_id: str) -> dict:
        return self.update_gig(gig_id, {"status": "active", "published_at": datetime.utcnow()})

    def pause_gig(self, gig_id: str) -> dict:
        return self.update_gig(gig_id, {"status": "paused"})

    def activate_gig(self, gig_id: str) -> dict:
        return self.update_gig(gig_id, {"status": "active"})

    def reject_gig(self, gig_id: str, reason: str) -> dict:
        return self.update_gig(gig_id, {"status": "rejected", "reject_reason": reason})

    # ---------------------------------------------------------
    # 🔎 SEARCH + FILTER GIGS
    # ---------------------------------------------------------
    def search_gigs(self, keyword: str = "", filters: dict = {}, limit: int = 50, skip: int = 0) -> dict:
        try:
            query = {"$text": {"$search": keyword}} if keyword else {}
            query.update(filters)
            cursor = self.collection.find(query).skip(skip).limit(limit).sort("updated_at", -1)
            return {"success": True, "gigs": [self._sanitize(doc) for doc in cursor]}
        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    def list_gigs_by_category(self, category_id: str, limit=50, skip=0) -> dict:
        try:
            cursor = self.collection.find({"category_id": ObjectId(category_id)}).skip(skip).limit(limit)
            return {"success": True, "gigs": [self._sanitize(doc) for doc in cursor]}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    def list_gigs_by_freelancer(self, user_id: str, limit=50, skip=0) -> dict:
        try:
            cursor = self.collection.find({"freelancer_id": ObjectId(user_id)}).skip(skip).limit(limit)
            return {"success": True, "gigs": [self._sanitize(doc) for doc in cursor]}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    def list_featured_gigs(self, limit=20) -> dict:
        try:
            cursor = self.collection.find({"featured": True, "status": "active"}).sort("updated_at", -1).limit(limit)
            return {"success": True, "gigs": [self._sanitize(doc) for doc in cursor]}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    def list_recent_gigs(self, limit=20) -> dict:
        try:
            cursor = self.collection.find({"status": "active"}).sort("created_at", -1).limit(limit)
            return {"success": True, "gigs": [self._sanitize(doc) for doc in cursor]}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 📈 UPDATE GIG STATS
    # ---------------------------------------------------------
    def update_gig_stats(self, gig_id: str, stats: Dict) -> dict:
        try:
            oid = ObjectId(gig_id)
            stats["updated_at"] = datetime.utcnow()
            res = self.collection.update_one({"_id": oid}, {"$set": stats})
            return {"success": True, "updated": res.modified_count > 0}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

