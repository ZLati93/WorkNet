from bson.objectid import ObjectId, InvalidId
from datetime import datetime
from typing import List, Optional, Dict
from pymongo.errors import PyMongoError


class GigsService:
    def __init__(self, db):
        self.collection = db["gigs"]
        self.categories = db["categories"]
        self.favorites = db["favorites"]
        self.reviews = db["gig_reviews"]

    # ---------------------------------------------------------
    # 🔧 Utils : sanitize MongoDB doc → JSON-safe
    # ---------------------------------------------------------
    def _sanitize(self, doc: dict) -> Optional[dict]:
        if not doc:
            return None
        try:
            for k in ["_id", "freelancer_id", "category_id"]:
                if k in doc and doc[k]:
                    doc[k] = str(doc[k])
            for dt_field in ["created_at", "updated_at", "published_at"]:
                if dt_field in doc and doc[dt_field]:
                    doc[dt_field] = doc[dt_field].isoformat()
            return doc
        except Exception:
            return None

    def _validate_object_id(self, id_str: str, field_name: str) -> ObjectId:
        try:
            return ObjectId(id_str)
        except (InvalidId, TypeError):
            raise ValueError(f"ID invalide pour '{field_name}'")

    # ---------------------------------------------------------
    # 🎨 CREATE / UPDATE / DELETE GIG
    # ---------------------------------------------------------
    def create_gig(self, freelancer_id: str, data: dict) -> dict:
        try:
            data["freelancer_id"] = self._validate_object_id(freelancer_id, "freelancer_id")
            data["category_id"] = self._validate_object_id(data["category_id"], "category_id")
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
            data.update(defaults)
            res = self.collection.insert_one(data)
            return {"success": True, "gig_id": str(res.inserted_id)}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    def update_gig(self, gig_id: str, freelancer_id: str, data: dict) -> dict:
        try:
            gig_oid = self._validate_object_id(gig_id, "gig_id")
            freelancer_oid = self._validate_object_id(freelancer_id, "freelancer_id")
            data["updated_at"] = datetime.utcnow()
            if "category_id" in data:
                data["category_id"] = self._validate_object_id(data["category_id"], "category_id")
            res = self.collection.update_one({"_id": gig_oid, "freelancer_id": freelancer_oid}, {"$set": data})
            return {"success": True, "updated": res.modified_count > 0}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    def delete_gig(self, gig_id: str, freelancer_id: str) -> dict:
        try:
            gig_oid = self._validate_object_id(gig_id, "gig_id")
            freelancer_oid = self._validate_object_id(freelancer_id, "freelancer_id")
            res = self.collection.delete_one({"_id": gig_oid, "freelancer_id": freelancer_oid})
            return {"success": True, "deleted": res.deleted_count > 0}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 📄 LISTING GIGS / SEARCH / FILTERS / PAGINATION
    # ---------------------------------------------------------
    def list_gigs(self, filters: dict = {}, pagination: dict = {"limit": 50, "skip": 0}) -> dict:
        try:
            limit = pagination.get("limit", 50)
            skip = pagination.get("skip", 0)
            cursor = self.collection.find(filters).sort("updated_at", -1).skip(skip).limit(limit)
            return {"success": True, "gigs": [self._sanitize(doc) for doc in cursor]}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    def search_gigs(self, query: str = "", filters: dict = {}, pagination: dict = {"limit": 50, "skip": 0}) -> dict:
        try:
            mongo_query = {"$text": {"$search": query}} if query else {}
            mongo_query.update(filters)
            limit = pagination.get("limit", 50)
            skip = pagination.get("skip", 0)
            cursor = self.collection.find(mongo_query).sort("updated_at", -1).skip(skip).limit(limit)
            return {"success": True, "gigs": [self._sanitize(doc) for doc in cursor]}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    def list_my_gigs(self, freelancer_id: str, filters: dict = {}, pagination: dict = {"limit": 50, "skip": 0}) -> dict:
        try:
            freelancer_oid = self._validate_object_id(freelancer_id, "freelancer_id")
            filters["freelancer_id"] = freelancer_oid
            return self.list_gigs(filters, pagination)
        except ValueError as e:
            return {"success": False, "error": str(e)}

    def list_featured_gigs(self, limit=20) -> dict:
        try:
            cursor = self.collection.find({"featured": True, "status": "active"}).sort("updated_at", -1).limit(limit)
            return {"success": True, "gigs": [self._sanitize(doc) for doc in cursor]}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    def get_gig_by_id(self, gig_id: str) -> dict:
        try:
            oid = self._validate_object_id(gig_id, "gig_id")
            doc = self.collection.find_one({"_id": oid})
            return {"success": True, "gig": self._sanitize(doc)} if doc else {"success": False, "error": "Gig not found"}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # ⭐ Favorites (Client)
    # ---------------------------------------------------------
    def add_to_favorites(self, user_id: str, gig_id: str) -> dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")
            gid = self._validate_object_id(gig_id, "gig_id")
            if self.favorites.find_one({"user_id": uid, "gig_id": gid}):
                return {"success": False, "error": "Already in favorites"}
            self.favorites.insert_one({"user_id": uid, "gig_id": gid, "created_at": datetime.utcnow()})
            return {"success": True}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    def remove_from_favorites(self, user_id: str, gig_id: str) -> dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")
            gid = self._validate_object_id(gig_id, "gig_id")
            res = self.favorites.delete_one({"user_id": uid, "gig_id": gid})
            return {"success": True, "deleted": res.deleted_count > 0}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    def list_favorite_gigs(self, user_id: str, pagination: dict = {"limit": 50, "skip": 0}) -> dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")
            limit = pagination.get("limit", 50)
            skip = pagination.get("skip", 0)
            favs = list(self.favorites.find({"user_id": uid}).skip(skip).limit(limit))
            gig_ids = [f["gig_id"] for f in favs]
            cursor = self.collection.find({"_id": {"$in": gig_ids}})
            return {"success": True, "gigs": [self._sanitize(doc) for doc in cursor]}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 📊 Analytics & Reviews
    # ---------------------------------------------------------
    def get_gig_reviews(self, gig_id: str, pagination: dict = {"limit": 50, "skip": 0}) -> dict:
        try:
            gid = self._validate_object_id(gig_id, "gig_id")
            limit = pagination.get("limit", 50)
            skip = pagination.get("skip", 0)
            cursor = self.reviews.find({"gig_id": gid}).sort("created_at", -1).skip(skip).limit(limit)
            reviews = []
            for r in cursor:
                r["_id"] = str(r["_id"])
                r["user_id"] = str(r.get("user_id"))
                r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else None
                reviews.append(r)
            return {"success": True, "reviews": reviews}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    def get_gig_analytics(self, gig_id: str, freelancer_id: str) -> dict:
        try:
            gid = self._validate_object_id(gig_id, "gig_id")
            fid = self._validate_object_id(freelancer_id, "freelancer_id")
            gig = self.collection.find_one({"_id": gid, "freelancer_id": fid})
            if not gig:
                return {"success": False, "error": "Gig not found"}
            return {"success": True, "analytics": {
                "total_orders": gig.get("total_orders", 0),
                "total_earning": gig.get("total_earning", 0.0),
                "gig_rating": gig.get("gig_rating", 0.0),
                "gig_reviews": gig.get("gig_reviews", 0)
            }}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # ⚙️ Admin functions
    # ---------------------------------------------------------
    def list_gigs_admin(self, filters: dict = {}, pagination: dict = {"limit": 50, "skip": 0}) -> dict:
        return self.list_gigs(filters, pagination)

    def update_gig_status_admin(self, gig_id: str, status: str) -> dict:
        try:
            oid = self._validate_object_id(gig_id, "gig_id")
            res = self.collection.update_one({"_id": oid}, {"$set": {"status": status, "updated_at": datetime.utcnow()}})
            return {"success": True, "updated": res.modified_count > 0}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}

    def feature_gig(self, gig_id: str, featured: bool) -> dict:
        try:
            oid = self._validate_object_id(gig_id, "gig_id")
            res = self.collection.update_one({"_id": oid}, {"$set": {"featured": featured, "updated_at": datetime.utcnow()}})
            return {"success": True, "updated": res.modified_count > 0}
        except (InvalidId, PyMongoError) as e:
            return {"success": False, "error": str(e)}
