from bson.objectid import ObjectId
from datetime import datetime, timedelta
from pymongo.errors import PyMongoError
from typing import Optional, List, Dict


class PaymentsServiceRPC:
    def __init__(self, db, platform_fee_rate: float = 0.1):
        self.collection = db["payments"]
        self.withdrawals = db["withdrawals"]
        self.platform_fee_rate = platform_fee_rate

    # ---------------------------------------------------------
    # 🔧 Utility
    # ---------------------------------------------------------
    def _safe_oid(self, oid: str):
        try:
            return ObjectId(oid)
        except Exception:
            raise ValueError(f"Invalid ObjectId: {oid}")

    def _sanitize(self, payment: dict) -> dict:
        if not payment:
            return None
        sanitized = payment.copy()
        sanitized["_id"] = str(payment["_id"])
        sanitized["order_id"] = str(payment["order_id"])
        sanitized["client_id"] = str(payment["client_id"])
        return sanitized

    # ---------------------------------------------------------
    # 💳 CREATE / PROCESS PAYMENT
    # ---------------------------------------------------------
    def create_payment_intent(self, order_id: str, client_id: str, method: str) -> dict:
        try:
            payment_data = {
                "order_id": order_id,
                "client_id": client_id,
                "amount": 0,  # amount will be set during process_payment
                "payment_method": method
            }
            payment_id = self.create_payment(payment_data)
            return {"payment_id": payment_id}
        except Exception as e:
            return {"error": str(e)}

    def process_payment(self, order_id: str, client_id: str, data: dict) -> dict:
        try:
            payment_data = {
                "order_id": order_id,
                "client_id": client_id,
                "amount": data.get("amount"),
                "payment_method": data.get("payment_method")
            }
            payment_id = self.create_payment(payment_data)
            self.complete_payment(payment_id)
            return {"payment_id": payment_id, "status": "completed"}
        except Exception as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # 🔍 GET / LIST
    # ---------------------------------------------------------
    def list_payments(self, user_id: str) -> list:
        try:
            return self.list_payments_by_client(user_id)
        except Exception as e:
            return [{"error": str(e)}]

    def get_payment(self, payment_id: str, user_id: str) -> dict:
        try:
            payment = self.verify_payment(payment_id)
            if payment and payment["client_id"] == user_id:
                return payment
            return {"error": "Payment not found or access denied"}
        except Exception as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # ↩ REFUNDS
    # ---------------------------------------------------------
    def request_refund(self, order_id: str, client_id: str, reason: str) -> dict:
        try:
            payments = self.list_payments_by_order(order_id)
            payment = next((p for p in payments if p["client_id"] == client_id), None)
            if not payment:
                return {"error": "Payment not found"}
            self.refund_payment(payment["_id"])
            return {"success": True, "reason": reason}
        except Exception as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # 📈 FREELANCER EARNINGS
    # ---------------------------------------------------------
    def get_earnings(self, freelancer_id: str, filters: dict = None) -> dict:
        try:
            oid = self._safe_oid(freelancer_id)
            query = {"freelancer_id": oid, "status": "completed"}
            if filters:
                if "start_date" in filters:
                    query["created_at"] = {"$gte": filters["start_date"]}
                if "end_date" in filters:
                    query.setdefault("created_at", {})["$lte"] = filters["end_date"]

            payments = list(self.collection.find(query))
            total_earnings = sum(p["amount"] for p in payments)
            freelancer_earnings = sum(self.calculate_freelancer_earnings(p["amount"]) for p in payments)

            return {"total_earnings": total_earnings, "freelancer_earnings": freelancer_earnings}
        except Exception as e:
            return {"error": str(e)}

    def request_withdrawal(self, freelancer_id: str, data: dict) -> dict:
        try:
            withdrawal = {
                "freelancer_id": self._safe_oid(freelancer_id),
                "amount": data.get("amount"),
                "status": "pending",
                "requested_at": datetime.utcnow(),
                "method": data.get("method", "bank_transfer"),
            }
            res = self.withdrawals.insert_one(withdrawal)
            return {"withdrawal_id": str(res.inserted_id)}
        except Exception as e:
            return {"error": str(e)}

    def list_withdrawals(self, freelancer_id: str) -> list:
        try:
            oid = self._safe_oid(freelancer_id)
            cursor = self.withdrawals.find({"freelancer_id": oid})
            return [self._sanitize(w) for w in cursor]
        except Exception as e:
            return [{"error": str(e)}]

    def get_revenue_analytics(self, freelancer_id: str, period: str) -> dict:
        try:
            oid = self._safe_oid(freelancer_id)
            now = datetime.utcnow()
            start_date = now - timedelta(days=30) if period == "month" else now - timedelta(days=7)
            payments = list(self.collection.find({
                "freelancer_id": oid,
                "status": "completed",
                "created_at": {"$gte": start_date}
            }))
            total = sum(p["amount"] for p in payments)
            return {"period": period, "total_revenue": total, "count": len(payments)}
        except Exception as e:
            return {"error": str(e)}

    # ---------------------------------------------------------
    # Admin
    # ---------------------------------------------------------
    def list_all_payments(self, filters: dict = None, pagination: dict = None) -> list:
        try:
            cursor = self.collection.find(filters or {})
            return [self._sanitize(p) for p in cursor]
        except Exception as e:
            return [{"error": str(e)}]

    def process_withdrawal(self, withdrawal_id: str, status: str) -> dict:
        try:
            oid = self._safe_oid(withdrawal_id)
            res = self.withdrawals.update_one(
                {"_id": oid}, {"$set": {"status": status, "processed_at": datetime.utcnow()}}
            )
            return {"success": res.modified_count > 0}
        except Exception as e:
            return {"error": str(e)}

    def update_payment_status(self, payment_id: str, status: str) -> dict:
        try:
            success = self.complete_payment(payment_id) if status == "completed" else self.refund_payment(payment_id)
            return {"success": success}
        except Exception as e:
            return {"error": str(e)}

    def get_platform_earnings(self, period: str) -> dict:
        try:
            now = datetime.utcnow()
            start_date = now - timedelta(days=30) if period == "month" else now - timedelta(days=7)
            payments = list(self.collection.find({"status": "completed", "created_at": {"$gte": start_date}}))
            total = sum(p["amount"] for p in payments)
            platform_total = sum(self.calculate_platform_fee(p["amount"]) for p in payments)
            return {"period": period, "total_payments": total, "platform_earnings": platform_total}
        except Exception as e:
            return {"error": str(e)}
