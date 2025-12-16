from bson.objectid import ObjectId
from datetime import datetime
from typing import List, Dict, Optional
from pymongo.errors import PyMongoError


class ReviewsService:
    def __init__(self, db):
        self.collection = db["reviews"]

    # ---------------------------------------------------------
    # 🔧 UTILITAIRES
    # ---------------------------------------------------------
    def _to_objectid(self, value: str, field: str):
        try:
            return ObjectId(value)
        except Exception:
            raise ValueError(f"Invalid ObjectId for field '{field}'")

    def _sanitize(self, r: dict):
        if not r:
            return None

        r = r.copy()
        r["_id"] = str(r["_id"])
        r["order_id"] = str(r["order_id"])
        r["reviewer_id"] = str(r["reviewer_id"])
        r["reviewee_id"] = str(r["reviewee_id"])

        for k in ("created_at", "updated_at"):
            if k in r and isinstance(r[k], datetime):
                r[k] = r[k].isoformat()

        return r

    # ---------------------------------------------------------
    # 📝 CREATE
    # ---------------------------------------------------------
    def create_review(self, data: dict) -> dict:
        try:
            required = ["order_id", "reviewer_id", "reviewee_id", "overall_rating"]
            for f in required:
                if f not in data or not data[f]:
                    return {"error": f"Missing required field: {f}"}

            oid_order = self._to_objectid(data["order_id"], "order_id")
            if self.collection.find_one({"order_id": oid_order}):
                return {"error": "Review already exists for this order"}

            review = {
                "order_id": oid_order,
                "reviewer_id": self._to_objectid(data["reviewer_id"], "reviewer_id"),
                "reviewee_id": self._to_objectid(data["reviewee_id"], "reviewee_id"),
                "overall_rating": data["overall_rating"],
                "comment": data.get("comment"),
                "response": None,
                "is_public": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            res = self.collection.insert_one(review)
            return {"review_id": str(res.inserted_id)}

        except (ValueError, PyMongoError) as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # ✏️ UPDATE
    # ---------------------------------------------------------
    def update_review(self, review_id: str, data: dict) -> dict:
        try:
            oid = self._to_objectid(review_id, "review_id")
            data["updated_at"] = datetime.utcnow()
            res = self.collection.update_one({"_id": oid}, {"$set": data})
            return {"success": res.modified_count > 0}
        except (ValueError, PyMongoError) as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # 🗑 DELETE
    # ---------------------------------------------------------
    def delete_review(self, review_id: str) -> dict:
        try:
            oid = self._to_objectid(review_id, "review_id")
            res = self.collection.delete_one({"_id": oid})
            return {"success": res.deleted_count > 0}
        except (ValueError, PyMongoError) as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # 🔍 GET
    # ---------------------------------------------------------
    def get_review(self, review_id: str) -> dict:
        try:
            oid = self._to_objectid(review_id, "review_id")
            review = self.collection.find_one({"_id": oid})
            return self._sanitize(review)
        except (ValueError, PyMongoError) as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # ⭐ RESPOND
    # ---------------------------------------------------------
    def respond_to_review(self, review_id: str, message: str) -> dict:
        try:
            if not message:
                return {"error": "Response message cannot be empty"}

            oid = self._to_objectid(review_id, "review_id")
            res = self.collection.update_one(
                {"_id": oid},
                {"$set": {"response": message, "updated_at": datetime.utcnow()}},
            )
            return {"success": res.modified_count > 0}
        except (ValueError, PyMongoError) as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # 👁 UPDATE VISIBILITY
    # ---------------------------------------------------------
    def update_review_visibility(self, review_id: str, is_public: bool) -> dict:
        try:
            oid = self._to_objectid(review_id, "review_id")
            res = self.collection.update_one(
                {"_id": oid},
                {"$set": {"is_public": is_public, "updated_at": datetime.utcnow()}},
            )
            return {"success": res.modified_count > 0}
        except (ValueError, PyMongoError) as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # 📜 LISTING
    # ---------------------------------------------------------
    def list_reviews_for_user(self, user_id: str) -> list:
        try:
            oid = self._to_objectid(user_id, "reviewee_id")
            cursor = self.collection.find({"reviewee_id": oid})
            return [self._sanitize(r) for r in cursor]
        except (ValueError, PyMongoError) as e:
            return [{"error": str(e)}]

    def list_reviews_by_reviewer(self, reviewer_id: str) -> list:
        try:
            oid = self._to_objectid(reviewer_id, "reviewer_id")
            cursor = self.collection.find({"reviewer_id": oid})
            return [self._sanitize(r) for r in cursor]
        except (ValueError, PyMongoError) as e:
            return [{"error": str(e)}]

    # ---------------------------------------------------------
    # 📊 STATS / CHECK
    # ---------------------------------------------------------
    def verify_review(self, order_id: str) -> dict:
        try:
            oid = self._to_objectid(order_id, "order_id")
            exists = self.collection.find_one({"order_id": oid}) is not None
            return {"exists": exists}
        except (ValueError, PyMongoError) as e:
            return {"error": str(e)}

    def list_reviews_for_gig(self, gig_id: str) -> list:
        try:
            oid = self._to_objectid(gig_id, "gig_id")
            cursor = self.collection.find({"gig_id": oid})
            return [self._sanitize(r) for r in cursor]
        except (ValueError, PyMongoError) as e:
            return [{"error": str(e)}]

    def get_review_stats(self, freelancer_id: str) -> dict:
        try:
            oid = self._to_objectid(freelancer_id, "freelancer_id")
            reviews = list(self.collection.find({"reviewee_id": oid, "is_public": True}))
            total = len(reviews)
            avg_rating = (
                sum(r["overall_rating"] for r in reviews) / total if total > 0 else 0
            )
            return {"total_reviews": total, "average_rating": avg_rating}
        except (ValueError, PyMongoError) as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # Admin
    # ---------------------------------------------------------
    def list_all_reviews(self, filters: dict = None, pagination: dict = None) -> list:
        filters = filters or {}
        cursor = self.collection.find(filters)
        return [self._sanitize(r) for r in cursor]

    def delete_review_admin(self, review_id: str) -> dict:
        return self.delete_review(review_id)

