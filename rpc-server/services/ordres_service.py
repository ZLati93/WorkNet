from bson.objectid import ObjectId
from datetime import datetime
from pymongo.errors import PyMongoError


class OrdersService:
    def __init__(self, db):
        self.orders = db["orders"]
        self.payments = db["payments"]
        self.users = db["users"]
        self.gigs = db["gigs"]

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------
    def _sanitize(self, order: dict):
        if not order:
            return None
        for k in ["_id", "client_id", "freelancer_id", "gig_id"]:
            if k in order:
                order[k] = str(order[k])
        if "timeline" in order:
            for t in order["timeline"]:
                if "_id" in t:
                    t["_id"] = str(t["_id"])
        if "requirements" in order:
            for r in order["requirements"]:
                if "_id" in r:
                    r["_id"] = str(r["_id"])
        if "delivery_files" in order:
            for f in order["delivery_files"]:
                if "_id" in f:
                    f["_id"] = str(f["_id"])
        return order

    def _add_timeline(self, order_id: ObjectId, action: str, user_id: str, extra: dict = None):
        entry = {
            "_id": ObjectId(),
            "action": action,
            "user_id": ObjectId(user_id) if user_id else None,
            "timestamp": datetime.utcnow()
        }
        if extra:
            entry.update(extra)

        self.orders.update_one(
            {"_id": order_id},
            {"$push": {"timeline": entry}}
        )

    # ---------------------------------------------------------
    # Create order
    # ---------------------------------------------------------
    def create_order(self, order_data: dict) -> str:
        required = ["gig_id", "client_id", "freelancer_id", "price", "quantity"]
        for r in required:
            if r not in order_data:
                raise ValueError(f"Missing field: {r}")

        order_data["gig_id"] = ObjectId(order_data["gig_id"])
        order_data["client_id"] = ObjectId(order_data["client_id"])
        order_data["freelancer_id"] = ObjectId(order_data["freelancer_id"])

        now = datetime.utcnow()

        order = {
            "gig_id": order_data["gig_id"],
            "client_id": order_data["client_id"],
            "freelancer_id": order_data["freelancer_id"],
            "price": float(order_data["price"]),
            "quantity": int(order_data["quantity"]),
            "requirements": [],
            "delivery_files": [],
            "status": "pending",
            "timeline": [],
            "created_at": now,
            "updated_at": now,
            "expected_delivery": None,
            "started_at": None,
            "delivered_at": None,
            "completed_at": None,
            "cancelled_at": None
        }

        result = self.orders.insert_one(order)

        self._add_timeline(result.inserted_id, "order_created", str(order_data["client_id"]))

        return str(result.inserted_id)

    # ---------------------------------------------------------
    # Basic getters
    # ---------------------------------------------------------
    def get_order(self, order_id: str):
        doc = self.orders.find_one({"_id": ObjectId(order_id)})
        return self._sanitize(doc)

    def list_orders_by_client(self, client_id: str, limit=50, skip=0):
        docs = self.orders.find(
            {"client_id": ObjectId(client_id)}
        ).skip(skip).limit(limit)
        return [self._sanitize(o) for o in docs]

    def list_orders_by_freelancer(self, freelancer_id: str, limit=50, skip=0):
        docs = self.orders.find(
            {"freelancer_id": ObjectId(freelancer_id)}
        ).skip(skip).limit(limit)
        return [self._sanitize(o) for o in docs]

    # ---------------------------------------------------------
    # Accept / Reject / Start / Deliver / Complete / Cancel
    # ---------------------------------------------------------
    def accept_order(self, order_id: str, freelancer_id: str):
        oid = ObjectId(order_id)
        order = self.orders.find_one({"_id": oid})

        if not order:
            raise ValueError("Order not found")
        if str(order["freelancer_id"]) != freelancer_id:
            raise PermissionError("Not your order")

        if order["status"] != "pending":
            raise ValueError("Order must be pending")

        self.orders.update_one(
            {"_id": oid},
            {"$set": {"status": "accepted", "updated_at": datetime.utcnow()}}
        )
        self._add_timeline(oid, "order_accepted", freelancer_id)

        return True

    def reject_order(self, order_id: str, freelancer_id: str, reason: str = None):
        oid = ObjectId(order_id)
        order = self.orders.find_one({"_id": oid})

        if not order:
            raise ValueError("Order not found")
        if str(order["freelancer_id"]) != freelancer_id:
            raise PermissionError("Not your order")

        if order["status"] != "pending":
            raise ValueError("Order must be pending")

        self.orders.update_one(
            {"_id": oid},
            {
                "$set": {
                    "status": "rejected",
                    "cancelled_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "reject_reason": reason
                }
            }
        )
        self._add_timeline(oid, "order_rejected", freelancer_id, {"reason": reason})

        return True

    def start_order(self, order_id: str, freelancer_id: str, expected_delivery: str):
        oid = ObjectId(order_id)
        order = self.orders.find_one({"_id": oid})

        if not order:
            raise ValueError("Order not found")
        if order["status"] != "accepted":
            raise ValueError("Order must be accepted before starting")

        if str(order["freelancer_id"]) != freelancer_id:
            raise PermissionError("Not your order")

        exp = datetime.fromisoformat(expected_delivery)

        self.orders.update_one(
            {"_id": oid},
            {"$set": {
                "status": "in_progress",
                "started_at": datetime.utcnow(),
                "expected_delivery": exp,
                "updated_at": datetime.utcnow()
            }}
        )

        self._add_timeline(oid, "order_started", freelancer_id, {"expected_delivery": expected_delivery})

        return True

    def deliver_order(self, order_id: str, freelancer_id: str, delivery_files: list):
        oid = ObjectId(order_id)
        order = self.orders.find_one({"_id": oid})

        if not order:
            raise ValueError("Order not found")
        if order["status"] != "in_progress":
            raise ValueError("Order must be in progress to deliver")

        if str(order["freelancer_id"]) != freelancer_id:
            raise PermissionError("Not your order")

        formatted = []
        for f in delivery_files:
            formatted.append({
                "_id": ObjectId(),
                "file_url": f["file_url"],
                "file_name": f.get("file_name"),
                "uploaded_at": datetime.utcnow()
            })

        self.orders.update_one(
            {"_id": oid},
            {
                "$set": {
                    "status": "delivered",
                    "delivered_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$push": {"delivery_files": {"$each": formatted}}
            }
        )

        self._add_timeline(oid, "order_delivered", freelancer_id)

        return True

    def complete_order(self, order_id: str, client_id: str):
        oid = ObjectId(order_id)
        order = self.orders.find_one({"_id": oid})

        if not order:
            raise ValueError("Order not found")
        if order["status"] != "delivered":
            raise ValueError("Order must be delivered to complete")

        if str(order["client_id"]) != client_id:
            raise PermissionError("You are not the client")

        now = datetime.utcnow()

        # Mark order completed
        self.orders.update_one(
            {"_id": oid},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": now,
                    "updated_at": now
                }
            }
        )

        # Register payment release
        payment = {
            "order_id": oid,
            "client_id": order["client_id"],
            "freelancer_id": order["freelancer_id"],
            "amount": order["price"] * order["quantity"],
            "payment_method": "wallet",
            "status": "released",
            "created_at": now,
            "updated_at": now
        }
        self.payments.insert_one(payment)

        # Increment freelancer gig stats
        self.gigs.update_one(
            {"_id": order["gig_id"]},
            {"$inc": {"total_orders": 1, "total_earning": payment["amount"]}}
        )

        self._add_timeline(oid, "order_completed", client_id)

        return True

    def cancel_order(self, order_id: str, user_id: str, reason: str = None):
        oid = ObjectId(order_id)
        order = self.orders.find_one({"_id": oid})

        if not order:
            raise ValueError("Order not found")
        if order["status"] in ["completed", "cancelled"]:
            raise ValueError("Order already completed/cancelled")

        # Only client can cancel pending/accepted
        if order["status"] in ["pending", "accepted"] and str(order["client_id"]) != user_id:
            raise PermissionError("Only client can cancel at this stage")

        # Only freelancer can cancel in_progress
        if order["status"] == "in_progress" and str(order["freelancer_id"]) != user_id:
            raise PermissionError("Only freelancer can cancel during work")

        self.orders.update_one(
            {"_id": oid},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "cancel_reason": reason
                }
            }
        )

        self._add_timeline(oid, "order_cancelled", user_id, {"reason": reason})

        return True

    # ---------------------------------------------------------
    # Requiremnts
    # ---------------------------------------------------------
    def add_requirement(self, order_id: str, client_id: str, requirement_text: str):
        oid = ObjectId(order_id)
        order = self.orders.find_one({"_id": oid})
        if not order:
            raise ValueError("Order not found")

        if str(order["client_id"]) != client_id:
            raise PermissionError("Only client can add requirements")

        req = {
            "_id": ObjectId(),
            "text": requirement_text,
            "added_at": datetime.utcnow()
        }

        self.orders.update_one(
            {"_id": oid},
            {"$push": {"requirements": req}, "$set": {"updated_at": datetime.utcnow()}}
        )

        self._add_timeline(oid, "requirement_added", client_id)

        return True

    # ---------------------------------------------------------
    # Misc updates
    # ---------------------------------------------------------
    def update_expected_delivery(self, order_id: str, freelancer_id: str, new_date: str):
        oid = ObjectId(order_id)
        order = self.orders.find_one({"_id": oid})
        if not order:
            raise ValueError("Order not found")

        if str(order["freelancer_id"]) != freelancer_id:
            raise PermissionError("Not your order")

        exp = datetime.fromisoformat(new_date)

        self.orders.update_one(
            {"_id": oid},
            {"$set": {
                "expected_delivery": exp,
                "updated_at": datetime.utcnow()
            }}
        )

        self._add_timeline(oid, "expected_delivery_updated", freelancer_id, {"new_date": new_date})

        return True
