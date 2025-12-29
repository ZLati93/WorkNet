from bson.objectid import ObjectId
from datetime import datetime

class PaymentsService:
    def __init__(self, db):
        self.collection = db["payments"]

    def create_payment(self, payment_data: dict) -> str:
        required = ["order_id", "client_id", "amount", "payment_method"]
        for r in required:
            if r not in payment_data:
                raise ValueError(f"Missing: {r}")

        payment_data["order_id"] = ObjectId(payment_data["order_id"])
        payment_data["client_id"] = ObjectId(payment_data["client_id"])
        now = datetime.utcnow()
        payment_data.update({"created_at": now, "updated_at": now, "status": "pending"})
        res = self.collection.insert_one(payment_data)
        return str(res.inserted_id)
