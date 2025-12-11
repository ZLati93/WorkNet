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

        if "created_at" in r:
            r["created_at"] = r["created_at"].isoformat()
        if "updated_at" in r:
            r["updated_at"] = r["updated_at"].isoformat()

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

            # Vérifier si un avis existe déjà pour cette commande
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

            result = self.collection.insert_one(review)
            return {"review_id": str(result.inserted_id)}

        except ValueError as e:
            return {"error": str(e)}
        except PyMongoError as e:
            return {"error": f"Database error: {str(e)}"}

    # ---------------------------------------------------------
    # ✏️ UPDATE
    # ---------------------------------------------------------
    def update_review(self, review_id: str, data: dict) -> dict:
        try:
            oid = self._to_objectid(review_id, "review_id")
            data["updated_at"] = datetime.utcnow()

            res = self.collection.update_one({"_id": oid}, {"$set": data})
            return {"success": res.modified_count > 0}

        except ValueError as e:
            return {"error": str(e)}
        except PyMongoError as e:
            return {"error": f"Database error: {str(e)}"}

    # ---------------------------------------------------------
    # 🗑 DELETE
    # ---------------------------------------------------------
    def delete_review(self, review_id: str) -> dict:
        try:
            oid = self._to_objectid(review_id, "review_id")

            res = self.collection.delete_one({"_id": oid})
            return {"success": res.deleted_count > 0}

        except ValueError as e:
            return {"error": str(e)}
        except PyMongoError as e:
            return {"error": f"Database error: {str(e)}"}

    # ---------------------------------------------------------
    # 🔍 GET
    # ---------------------------------------------------------
    def get_review(self, review_id: str) -> dict:
        try:
            oid = self._to_objectid(review_id, "review_id")
            review = self.collection.find_one({"_id": oid})
            return self._sanitize(review)

        except ValueError as e:
            return {"error": str(e)}
        except PyMongoError as e:
            return {"error": f"Database error: {str(e)}"}

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

        except ValueError as e:
            return {"error": str(e)}
        except PyMongoError as e:
            return {"error": f"Database error: {str(e)}"}

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

        except ValueError as e:
            return {"error": str(e)}
        except PyMongoError as e:
            return {"error": f"Database error: {str(e)}"}

    # ---------------------------------------------------------
    # 📜 LISTING
    # ---------------------------------------------------------
    def list_reviews_for_user(self, reviewee_id: str) -> list:
        try:
            oid = self._to_objectid(reviewee_id, "reviewee_id")
            cursor = self.collection.find({"reviewee_id": oid})
            return [self._sanitize(r) for r in cursor]

        except ValueError as e:
            return [{"error": str(e)}]
        except PyMongoError as e:
            return [{"error": f"Database error: {str(e)}"}]

    def list_reviews_by_reviewer(self, reviewer_id: str) -> list:
        try:
            oid = self._to_objectid(reviewer_id, "reviewer_id")
            cursor = self.collection.find({"reviewer_id": oid})
            return [self._sanitize(r) for r in cursor]

        except ValueError as e:
            return [{"error": str(e)}]
        except PyMongoError as e:
            return [{"error": f"Database error: {str(e)}"}]

    # ---------------------------------------------------------
    # ✔ CHECK IF REVIEW EXISTS
    # ---------------------------------------------------------
    def verify_review(self, order_id: str) -> dict:
        try:
            oid = self._to_objectid(order_id, "order_id")
            exists = self.collection.find_one({"order_id": oid}) is not None
            return {"exists": exists}

        except ValueError as e:
            return {"error": str(e)}
        except PyMongoError as e:
            return {"error": f"Database error: {str(e)}"}

            oid = self._to_objectid(order_id, "order_id")
            return self.collection.find_one({"order_id": oid}) is not None

        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")
