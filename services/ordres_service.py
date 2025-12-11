from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from pymongo.errors import PyMongoError


class OrdersService:

    def __init__(self, db):
        self.orders = db["orders"]
        self.payments = db["payments"]
        self.users = db["users"]
        self.gigs = db["gigs"]

    # ---------------------------------------------------------
    # UTILITAIRES
    # ---------------------------------------------------------
    def _validate_oid(self, value, field):
        """Convert value into ObjectId with validation"""
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            raise ValueError(f"Invalid ObjectId for '{field}'")

    def _sanitize(self, order: dict):
        if not order:
            return None

        # Convert top-level ObjectIds
        for key in ["_id", "client_id", "freelancer_id", "gig_id"]:
            if key in order:
                order[key] = str(order[key])

        # Convert timeline / requirements / delivery_files inner IDs
        for field in ["timeline", "requirements", "delivery_files"]:
            if field in order and isinstance(order[field], list):
                for item in order[field]:
                    if "_id" in item:
                        item["_id"] = str(item["_id"])
                    if "user_id" in item and isinstance(item["user_id"], ObjectId):
                        item["user_id"] = str(item["user_id"])

        return order

    def _add_timeline(self, order_id: ObjectId, action: str, user_id: str = None, extra: dict = None):
        """Safely append timeline events without breaking logic."""
        try:
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
        except Exception:
            pass  # timeline must NEVER crash order workflow

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------
    def create_order(self, data: dict) -> dict:
        try:
            required = ["gig_id", "client_id", "freelancer_id", "price", "quantity"]
            for r in required:
                if r not in data or not data[r]:
                    return {"success": False, "error": f"Missing field '{r}'"}

            gig_id = self._validate_oid(data["gig_id"], "gig_id")
            client_id = self._validate_oid(data["client_id"], "client_id")
            freelancer_id = self._validate_oid(data["freelancer_id"], "freelancer_id")

            now = datetime.utcnow()

            order = {
                "gig_id": gig_id,
                "client_id": client_id,
                "freelancer_id": freelancer_id,
                "price": float(data["price"]),
                "quantity": int(data["quantity"]),
                "requirements": [],
                "delivery_files": [],
                "timeline": [],
                "status": "pending",
                "created_at": now,
                "updated_at": now,
                "expected_delivery": None,
                "started_at": None,
                "delivered_at": None,
                "completed_at": None,
                "cancelled_at": None
            }

            res = self.orders.insert_one(order)

            self._add_timeline(res.inserted_id, "order_created", data["client_id"])

            return {"success": True, "order_id": str(res.inserted_id)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    def update_order(self, order_id: str, fields: dict) -> dict:
        try:
            oid = self._validate_oid(order_id, "order_id")

            fields["updated_at"] = datetime.utcnow()

            res = self.orders.update_one({"_id": oid}, {"$set": fields})

            if res.matched_count == 0:
                return {"success": False, "error": "Order not found"}

            self._add_timeline(oid, "order_updated", None, {"fields": list(fields.keys())})

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # GET ORDER
    # ---------------------------------------------------------
    def get_order(self, order_id: str) -> dict:
        try:
            oid = self._validate_oid(order_id, "order_id")
            order = self.orders.find_one({"_id": oid})

            if not order:
                return {"success": False, "error": "Order not found"}

            return {"success": True, "order": self._sanitize(order)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # WORKFLOW
    # ---------------------------------------------------------

    def confirm_order(self, order_id: str, client_id: str) -> dict:
        """Client accepts the order and sends it to the freelancer."""
        try:
            oid = self._validate_oid(order_id, "order_id")
            order = self.orders.find_one({"_id": oid})

            if not order:
                return {"success": False, "error": "Order not found"}

            if order["status"] != "pending":
                return {"success": False, "error": "Order must be pending"}

            if str(order["client_id"]) != client_id:
                return {"success": False, "error": "Not authorized"}

            self.orders.update_one(
                {"_id": oid},
                {"$set": {"status": "accepted", "updated_at": datetime.utcnow()}}
            )

            self._add_timeline(oid, "order_confirmed", client_id)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def start_order(self, order_id: str, freelancer_id: str, expected_delivery: str) -> dict:
        """Freelancer starts the project."""
        try:
            oid = self._validate_oid(order_id, "order_id")
            order = self.orders.find_one({"_id": oid})

            if not order or order["status"] != "accepted":
                return {"success": False, "error": "Order must be accepted first"}

            if str(order["freelancer_id"]) != freelancer_id:
                return {"success": False, "error": "Not authorized"}

            try:
                exp = datetime.fromisoformat(expected_delivery)
            except:
                return {"success": False, "error": "Invalid expected_delivery format"}

            self.orders.update_one(
                {"_id": oid},
                {"$set": {
                    "status": "in_progress",
                    "expected_delivery": exp,
                    "started_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )

            self._add_timeline(oid, "order_started", freelancer_id)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def deliver_order(self, order_id: str, freelancer_id: str, files: list, message: str = None) -> dict:
        """Freelancer delivers the work."""
        try:
            oid = self._validate_oid(order_id, "order_id")
            order = self.orders.find_one({"_id": oid})

            if not order or order["status"] != "in_progress":
                return {"success": False, "error": "Order must be in progress"}

            if str(order["freelancer_id"]) != freelancer_id:
                return {"success": False, "error": "Not authorized"}

            if not files:
                return {"success": False, "error": "Files required"}

            delivered_files = [{
                "_id": ObjectId(),
                "file_url": f["file_url"],
                "file_name": f.get("file_name"),
                "uploaded_at": datetime.utcnow()
            } for f in files]

            self.orders.update_one(
                {"_id": oid},
                {
                    "$push": {"delivery_files": {"$each": delivered_files}},
                    "$set": {"status": "delivered", "delivered_at": datetime.utcnow()}
                }
            )

            self._add_timeline(oid, "order_delivered", freelancer_id, {"message": message})

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def request_revision(self, order_id: str, client_id: str, reason: str) -> dict:
        """Client requests revisions."""
        try:
            if not reason:
                return {"success": False, "error": "Reason required"}

            oid = self._validate_oid(order_id, "order_id")
            order = self.orders.find_one({"_id": oid})

            if not order or order["status"] != "delivered":
                return {"success": False, "error": "Order must be delivered"}

            if str(order["client_id"]) != client_id:
                return {"success": False, "error": "Not authorized"}

            self.orders.update_one(
                {"_id": oid},
                {"$set": {"status": "revision_requested", "updated_at": datetime.utcnow()}}
            )

            self._add_timeline(oid, "revision_requested", client_id, {"reason": reason})

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def accept_delivery(self, order_id: str, client_id: str) -> dict:
        """Client accepts delivery (before completion)."""
        try:
            oid = self._validate_oid(order_id, "order_id")
            order = self.orders.find_one({"_id": oid})

            if not order or order["status"] not in ["delivered", "revision_delivered"]:
                return {"success": False, "error": "Order is not delivered"}

            if str(order["client_id"]) != client_id:
                return {"success": False, "error": "Not authorized"}

            self._add_timeline(oid, "delivery_accepted", client_id)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def complete_order(self, order_id: str, client_id: str) -> dict:
        """Client completes the order and releases payment."""
        try:
            oid = self._validate_oid(order_id, "order_id")
            order = self.orders.find_one({"_id": oid})

            if not order or order["status"] != "delivered":
                return {"success": False, "error": "Order must be delivered first"}

            if str(order["client_id"]) != client_id:
                return {"success": False, "error": "Not authorized"}

            now = datetime.utcnow()
            amount = order["price"] * order["quantity"]

            # Update order status
            self.orders.update_one(
                {"_id": oid},
                {"$set": {"status": "completed", "completed_at": now, "updated_at": now}}
            )

            # Add payment
            self.payments.insert_one({
                "_id": ObjectId(),
                "order_id": oid,
                "client_id": order["client_id"],
                "freelancer_id": order["freelancer_id"],
                "amount": amount,
                "payment_method": "wallet",
                "status": "released",
                "created_at": now,
                "updated_at": now
            })

            # Update gig statistics
            self.gigs.update_one(
                {"_id": order["gig_id"]},
                {"$inc": {"total_orders": 1, "total_earning": amount}}
            )

            self._add_timeline(oid, "order_completed", client_id)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def dispute_order(self, order_id: str, user_id: str, message: str) -> dict:
        """User disputes the order."""
        try:
            if not message:
                return {"success": False, "error": "Message required"}

            oid = self._validate_oid(order_id, "order_id")

            self.orders.update_one(
                {"_id": oid},
                {"$set": {"status": "disputed", "updated_at": datetime.utcnow()}}
            )

            self._add_timeline(oid, "order_disputed", user_id, {"message": message})

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # SEARCHING
    # ---------------------------------------------------------
    def list_orders_by_client(self, client_id: str) -> dict:
        try:
            cid = self._validate_oid(client_id, "client_id")
            docs = self.orders.find({"client_id": cid})
            return {"success": True, "orders": [self._sanitize(o) for o in docs]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_orders_by_freelancer(self, freelancer_id: str) -> dict:
        try:
            fid = self._validate_oid(freelancer_id, "freelancer_id")
            docs = self.orders.find({"freelancer_id": fid})
            return {"success": True, "orders": [self._sanitize(o) for o in docs]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_orders_by_status(self, status: str) -> dict:
        try:
            docs = self.orders.find({"status": status})
            return {"success": True, "orders": [self._sanitize(o) for o in docs]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_active_orders(self, user_id: str) -> dict:
        try:
            uid = self._validate_oid(user_id, "user_id")
            docs = self.orders.find({
                "$or": [{"client_id": uid}, {"freelancer_id": uid}],
                "status": {"$in": ["pending", "accepted", "in_progress", "delivered"]}
            })
            return {"success": True, "orders": [self._sanitize(o) for o in docs]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # CANCEL ORDER
    # ---------------------------------------------------------
    def cancel_order(self, order_id: str, user_id: str, reason: str = None) -> dict:
        """Cancel order with full logic for client and freelancer."""
        try:
            oid = self._validate_oid(order_id, "order_id")
            order = self.orders.find_one({"_id": oid})

            if not order:
                return {"success": False, "error": "Order not found"}

            if order["status"] in ["completed", "cancelled"]:
                return {"success": False, "error": "Order cannot be cancelled"}

            # Client cancellations allowed only before freelancer starts
            if order["status"] in ["pending", "accepted"] and str(order["client_id"]) != user_id:
                return {"success": False, "error": "Only client can cancel"}

            # Freelancer cancellations allowed only if in progress
            if order["status"] == "in_progress" and str(order["freelancer_id"]) != user_id:
                return {"success": False, "error": "Only freelancer can cancel"}

            self.orders.update_one(
                {"_id": oid},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": datetime.utcnow(),
                        "cancel_reason": reason
                    }
                }
            )

            self._add_timeline(oid, "order_cancelled", user_id, {"reason": reason})

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}
