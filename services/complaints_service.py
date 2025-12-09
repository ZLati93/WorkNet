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
    def create_complaint(self, user_id: str, target_id: str, target_type: str, reason: str, description: str = "") -> str:
        try:
            # Valider ObjectId
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
            return str(res.inserted_id)

        except InvalidId:
            raise ValueError("Invalid user_id or target_id format")

        except PyMongoError as e:
            raise Exception(f"MongoDB insert error: {str(e)}")

        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    # ------------------------------------------------------------
    # 📌 2. Récupérer une plainte par ID
    # ------------------------------------------------------------
    def get_complaint(self, complaint_id: str):
        try:
            oid = ObjectId(complaint_id)
            doc = self.collection.find_one({"_id": oid})
            return self._sanitize(doc)

        except InvalidId:
            return None

        except PyMongoError:
            return None

    # ------------------------------------------------------------
    # 📌 3. Liste des plaintes par utilisateur
    # ------------------------------------------------------------
    def list_complaints_by_user(self, user_id: str):
        try:
            oid = ObjectId(user_id)
            docs = self.collection.find({"user_id": oid})
            return [self._sanitize(d) for d in docs]

        except InvalidId:
            return []

        except PyMongoError:
            return []

    # ------------------------------------------------------------
    # 📌 4. Liste des plaintes EN ATTENTE (admin)
    # ------------------------------------------------------------
    def list_pending_complaints(self):
        try:
            docs = self.collection.find({"status": "pending"})
            return [self._sanitize(d) for d in docs]

        except PyMongoError:
            return []

    # ------------------------------------------------------------
    # 📌 5. Mettre à jour le statut d’une plainte
    # ------------------------------------------------------------
    def update_complaint_status(self, complaint_id: str, status: str, admin_note: str = None) -> bool:
        try:
            if status not in ["pending", "in_review", "resolved", "rejected"]:
                raise ValueError("Invalid complaint status")

            oid = ObjectId(complaint_id)

            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }

            if admin_note:
                update_data["admin_note"] = admin_note

            res = self.collection.update_one(
                {"_id": oid},
                {"$set": update_data}
            )
            return res.modified_count > 0

        except InvalidId:
            raise ValueError("Invalid complaint_id")

        except PyMongoError as e:
            raise Exception(f"MongoDB update error: {str(e)}")

    # ------------------------------------------------------------
    # 📌 6. Supprimer une plainte
    # ------------------------------------------------------------
    def delete_complaint(self, complaint_id: str) -> bool:
        try:
            oid = ObjectId(complaint_id)
            res = self.collection.delete_one({"_id": oid})
            return res.deleted_count > 0

        except InvalidId:
            return False

        except PyMongoError:
            return False
