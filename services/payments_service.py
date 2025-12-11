from bson.objectid import ObjectId
from datetime import datetime
from pymongo.errors import PyMongoError
from typing import Optional, List, Dict


class PaymentsService:
    def __init__(self, db, platform_fee_rate: float = 0.1):
        self.collection = db["payments"]
        self.platform_fee_rate = platform_fee_rate

    # ---------------------------------------------------------
    # 🔧 Utility : Safe ObjectId
    # ---------------------------------------------------------
    def _safe_oid(self, oid: str):
        """Convert string → ObjectId with error handling."""
        try:
            return ObjectId(oid)
        except Exception:
            raise ValueError(f"Invalid ObjectId: {oid}")

    # ---------------------------------------------------------
    # 🔧 Utility : Sanitize MongoDB document
    # ---------------------------------------------------------
    def _sanitize(self, payment: dict) -> dict:
        if not payment:
            return None

        sanitized = payment.copy()
        sanitized["_id"] = str(payment["_id"])
        sanitized["order_id"] = str(payment["order_id"])
        sanitized["client_id"] = str(payment["client_id"])
        return sanitized

    # ---------------------------------------------------------
    # 💳 Create Payment
    # ---------------------------------------------------------
    def create_payment(self, payment_data: dict) -> str:
        required = ["order_id", "client_id", "amount", "payment_method"]

        for r in required:
            if r not in payment_data or not payment_data[r]:
                raise ValueError(f"Missing or empty required field: {r}")

        try:
            amount = float(payment_data["amount"])
            if amount <= 0:
                raise ValueError("Amount must be a positive number")

            payment = {
                "order_id": self._safe_oid(payment_data["order_id"]),
                "client_id": self._safe_oid(payment_data["client_id"]),
                "amount": amount,
                "payment_method": payment_data["payment_method"],
                "status": "pending",
                "transaction_id": str(ObjectId()),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            res = self.collection.insert_one(payment)
            return str(res.inserted_id)

        except PyMongoError as e:
            raise RuntimeError(f"Database error during create_payment: {str(e)}")

    # ---------------------------------------------------------
    # 🔍 Verify Payment
    # ---------------------------------------------------------
    def verify_payment(self, transaction_id: str) -> Optional[dict]:
        if not transaction_id:
            raise ValueError("transaction_id is required")

        try:
            payment = self.collection.find_one({"transaction_id": transaction_id})
            return self._sanitize(payment) if payment else None

        except PyMongoError as e:
            raise RuntimeError(f"Database error during verify_payment: {str(e)}")

    # ---------------------------------------------------------
    # ✔ Complete Payment
    # ---------------------------------------------------------
    def complete_payment(self, payment_id: str) -> bool:
        try:
            oid = self._safe_oid(payment_id)
            res = self.collection.update_one(
                {"_id": oid},
                {"$set": {"status": "completed", "updated_at": datetime.utcnow()}}
            )
            return res.modified_count > 0

        except PyMongoError as e:
            raise RuntimeError(f"Database error during complete_payment: {str(e)}")

    # ---------------------------------------------------------
    # ↩ Refund Payment
    # ---------------------------------------------------------
    def refund_payment(self, payment_id: str) -> bool:
        try:
            oid = self._safe_oid(payment_id)
            res = self.collection.update_one(
                {"_id": oid},
                {"$set": {"status": "refunded", "updated_at": datetime.utcnow()}}
            )
            return res.modified_count > 0

        except PyMongoError as e:
            raise RuntimeError(f"Database error during refund_payment: {str(e)}")

    # ---------------------------------------------------------
    # 🔄 Update Payment Status
    # ---------------------------------------------------------
    def update_payment_status(self, payment_id: str, status: str) -> bool:
        if not status:
            raise ValueError("Status cannot be empty")

        try:
            oid = self._safe_oid(payment_id)
            res = self.collection.update_one(
                {"_id": oid},
                {"$set": {"status": status, "updated_at": datetime.utcnow()}}
            )
            return res.modified_count > 0

        except PyMongoError as e:
            raise RuntimeError(f"Database error during update_payment_status: {str(e)}")

    # ---------------------------------------------------------
    # 🔍 Search / Listing
    # ---------------------------------------------------------
    def list_payments_by_client(self, client_id: str) -> List[dict]:
        try:
            cursor = self.collection.find({"client_id": self._safe_oid(client_id)})
            return [self._sanitize(p) for p in cursor]

        except PyMongoError as e:
            raise RuntimeError(f"Database error during list_payments_by_client: {str(e)}")

    def list_payments_by_order(self, order_id: str) -> List[dict]:
        try:
            cursor = self.collection.find({"order_id": self._safe_oid(order_id)})
            return [self._sanitize(p) for p in cursor]

        except PyMongoError as e:
            raise RuntimeError(f"Database error during list_payments_by_order: {str(e)}")

    def list_payments_by_status(self, status: str) -> List[dict]:
        if not status:
            raise ValueError("Status is required")

        try:
            cursor = self.collection.find({"status": status})
            return [self._sanitize(p) for p in cursor]

        except PyMongoError as e:
            raise RuntimeError(f"Database error during list_payments_by_status: {str(e)}")

    # ---------------------------------------------------------
    # 📊 Stats
    # ---------------------------------------------------------
    def calculate_platform_fee(self, amount: float) -> float:
        if amount < 0:
            raise ValueError("Amount must be >= 0")
        return round(amount * self.platform_fee_rate, 2)

    def calculate_freelancer_earnings(self, amount: float) -> float:
        if amount < 0:
            raise ValueError("Amount must be >= 0")
        return round(amount * (1 - self.platform_fee_rate), 2)
