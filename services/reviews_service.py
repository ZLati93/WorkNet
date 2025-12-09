from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional, List, Dict
from pymongo.errors import PyMongoError


class ReviewsService:
    def __init__(self, db):
        self.collection = db["reviews"]

    # ---------------------------------------------------------
    # 🔧 Utilitaires internes
    # ---------------------------------------------------------
    def _to_objectid(self, value: str, field: str):
        """Convertit en ObjectId avec gestion d'erreur."""
        try:
            return ObjectId(value)
        except Exception:
            raise ValueError(f"Invalid ObjectId for field '{field}'")

    def _sanitize(self, r: dict):
        """Transforme ObjectId → str et nettoie la structure."""
        if not r:
            return None

        r["_id"] = str(r["_id"])
        r["order_id"] = str(r["order_id"])
        r["reviewer_id"] = str(r["reviewer_id"])
        r["reviewee_id"] = str(r["reviewee_id"])
        return r

    # ---------------------------------------------------------
    # 📝 CREATE
    # ---------------------------------------------------------
    def create_review(self, review_data: dict) -> str:
        try:
            required = ["order_id", "reviewer_id", "reviewee_id", "overall_rating"]
            for r in required:
                if r not in review_data or not review_data[r]:
                    raise ValueError(f"Missing required field: {r}")

            review = {
                "order_id": self._to_objectid(review_data["order_id"], "order_id"),
                "reviewer_id": self._to_objectid(review_data["reviewer_id"], "reviewer_id"),
                "reviewee_id": self._to_objectid(review_data["reviewee_id"], "reviewee_id"),
                "overall_rating": review_data["overall_rating"],
                "comment": review_data.get("comment"),
                "response": None,
                "is_public": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = self.collection.insert_one(review)
            return str(result.inserted_id)

        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    # ---------------------------------------------------------
    # ✏️ UPDATE
    # ---------------------------------------------------------
    def update_review(self, review_id: str, data: dict) -> bool:
        try:
            oid = self._to_objectid(review_id, "review_id")
            data["updated_at"] = datetime.utcnow()

            res = self.collection.update_one({"_id": oid}, {"$set": data})
            return res.modified_count > 0

        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    # ---------------------------------------------------------
    # 🗑 DELETE
    # ---------------------------------------------------------
    def delete_review(self, review_id: str) -> bool:
        try:
            oid = self._to_objectid(review_id, "review_id")
            res = self.collection.delete_one({"_id": oid})
            return res.deleted_count > 0

        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    # ---------------------------------------------------------
    # 🔍 GET
    # ---------------------------------------------------------
    def get_review(self, review_id: str) -> Optional[dict]:
        try:
            oid = self._to_objectid(review_id, "review_id")
            review = self.collection.find_one({"_id": oid})
            return self._sanitize(review)

        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    # ---------------------------------------------------------
    # ⭐ RESPONSE TO A REVIEW
    # ---------------------------------------------------------
    def respond_to_review(self, review_id: str, message: str) -> bool:
        try:
            if not message:
                raise ValueError("Response message cannot be empty")

            oid = self._to_objectid(review_id, "review_id")
            res = self.collection.update_one(
                {"_id": oid},
                {"$set": {"response": message, "updated_at": datetime.utcnow()}}
            )
            return res.modified_count > 0

        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    # ---------------------------------------------------------
    # 👁 UPDATE VISIBILITY
    # ---------------------------------------------------------
    def update_review_visibility(self, review_id: str, is_public: bool) -> bool:
        try:
            oid = self._to_objectid(review_id, "review_id")
            res = self.collection.update_one(
                {"_id": oid},
                {"$set": {"is_public": is_public, "updated_at": datetime.utcnow()}}
            )
            return res.modified_count > 0

        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    # ---------------------------------------------------------
    # 📜 LISTING
    # ---------------------------------------------------------
    def list_reviews_for_user(self, reviewee_id: str) -> List[dict]:
        try:
            oid = self._to_objectid(reviewee_id, "reviewee_id")
            cursor = self.collection.find({"reviewee_id": oid})

            return [self._sanitize(r) for r in cursor]

        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    def list_reviews_by_reviewer(self, reviewer_id: str) -> List[dict]:
        try:
            oid = self._to_objectid(reviewer_id, "reviewer_id")
            cursor = self.collection.find({"reviewer_id": oid})

            return [self._sanitize(r) for r in cursor]

        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    # ---------------------------------------------------------
    # ✔ VERIFY (1 seule review par commande)
    # ---------------------------------------------------------
    def verify_review(self, order_id: str) -> bool:
        try:
            oid = self._to_objectid(order_id, "order_id")
            return self.collection.find_one({"order_id": oid}) is not None

        except ValueError as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")
