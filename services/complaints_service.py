from bson.objectid import ObjectId, InvalidId
from datetime import datetime
from pymongo.errors import PyMongoError


class ComplaintsService:
    def __init__(self, db):
        self.collection = db["complaints"]

    # ------------------------------------------------------------
    # 🛠️ UTILITAIRE : Convertir ObjectId → string
    # ------------------------------------------------------------
    def _sanitize(self, doc: dict):
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        doc["target_id"] = str(doc["target_id"])
        return doc

    # ------------------------------------------------------------
    # 📌 1. Créer une plainte
    # ------------------------------------------------------------
    def create_complaint(self, user_id: str, target_id: str, target_type: str,
                         reason: str, description: str = "") -> dict:
        try:
            user_oid = ObjectId(user_id)
            target_oid = ObjectId(target_id)

            complaint = {
                "user_id": user_oid,
                "target_id": target_oid,
                "target_type": target_type,  # "user" | "gig" | "order"
                "reason": reason,
                "description": description,
                "status": "pending",
                "admin_note": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            res = self.collection.insert_one(complaint)
            return {"success": True, "complaint_id": str(res.inserted_id)}

        except InvalidId:
            return {"success": False, "error": "Invalid user_id or target_id"}

        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB insert error: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    # ------------------------------------------------------------
    # 📌 2. Récupérer une plainte par ID
    # ------------------------------------------------------------
    def get_complaint(self, complaint_id: str) -> dict:
        try:
            oid = ObjectId(complaint_id)
            doc = self.collection.find_one({"_id": oid})
            if not doc:
                return {"success": False, "error": "Complaint not found"}
            return {"success": True, "complaint": self._sanitize(doc)}

        except InvalidId:
            return {"success": False, "error": "Invalid complaint_id"}

        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    # ------------------------------------------------------------
    # 📌 3. Liste des plaintes par utilisateur
    # ------------------------------------------------------------
    def list_complaints_by_user(self, user_id: str) -> dict:
        try:
            oid = ObjectId(user_id)
            cursor = self.collection.find({"user_id": oid})
            complaints = [self._sanitize(d) for d in cursor]
            return {"success": True, "complaints": complaints}

        except InvalidId:
            return {"success": False, "error": "Invalid user_id"}

        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    # ------------------------------------------------------------
    # 📌 4. Liste des plaintes EN ATTENTE (admin)
    # ------------------------------------------------------------
    def list_pending_complaints(self) -> dict:
        try:
            cursor = self.collection.find({"status": "pending"})
            complaints = [self._sanitize(d) for d in cursor]
            return {"success": True, "complaints": complaints}

        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    # ------------------------------------------------------------
    # 📌 5. Mettre à jour le statut d’une plainte
    # ------------------------------------------------------------
    def update_complaint_status(self, complaint_id: str, status: str, admin_note: str = None) -> dict:
        try:
            if status not in ["pending", "in_review", "resolved", "rejected"]:
                return {"success": False, "error": "Invalid complaint status"}

            oid = ObjectId(complaint_id)
            update_data = {"status": status, "updated_at": datetime.utcnow()}
            if admin_note:
                update_data["admin_note"] = admin_note

            res = self.collection.update_one({"_id": oid}, {"$set": update_data})
            if res.matched_count == 0:
                return {"success": False, "error": "Complaint not found"}

            return {"success": True, "updated": res.modified_count > 0}

        except InvalidId:
            return {"success": False, "error": "Invalid complaint_id"}

        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    # ------------------------------------------------------------
    # 📌 6. Supprimer une plainte
    # ------------------------------------------------------------
    def delete_complaint(self, complaint_id: str) -> dict:
        try:
            oid = ObjectId(complaint_id)
            res = self.collection.delete_one({"_id": oid})
            if res.deleted_count == 0:
                return {"success": False, "error": "Complaint not found"}
            return {"success": True}

        except InvalidId:
            return {"success": False, "error": "Invalid complaint_id"}

        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}
