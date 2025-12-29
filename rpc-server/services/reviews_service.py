from bson.objectid import ObjectId
from datetime import datetime

class ReviewsService:
    def __init__(self, db):
        self.collection = db["reviews"]

    def create_review(self, review_data: dict) -> str:
        required = ["order_id", "reviewer_id", "reviewee_id", "overall_rating"]
        for r in required:
            if r not in review_data:
                raise ValueError(f"Missing required: {r}")

        review_data["order_id"] = ObjectId(review_data["order_id"])
        review_data["reviewer_id"] = ObjectId(review_data["reviewer_id"])
        review_data["reviewee_id"] = ObjectId(review_data["reviewee_id"])
        now = datetime.utcnow()
        review_data.update({"created_at": now, "updated_at": now})
        res = self.collection.insert_one(review_data)
        return str(res.inserted_id)
