from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import Optional, List, Dict


class NotificationsService:

    def __init__(self, db):
        self.collection = db["notifications"]

    # ---------------------------------------------------------
    # 🛠 Utilitaire : Validation ObjectId
    # ---------------------------------------------------------
    def _validate_object_id(self, value: str, field: str) -> ObjectId:
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            raise ValueError(f"ID invalide pour le champ '{field}'")

    # ---------------------------------------------------------
    # 🧼 Sanitize
    # ---------------------------------------------------------
    def _sanitize(self, notif: dict) -> dict:
        if not notif:
            return {}

        sanitized = {
            "_id": str(notif.get("_id")),
            "user_id": str(notif.get("user_id")),
            "type": notif.get("type"),
            "title": notif.get("title"),
            "message": notif.get("message"),
            "action_url": notif.get("action_url"),
            "related_entity_type": notif.get("related_entity_type"),
            "related_entity_id": str(notif.get("related_entity_id")) if notif.get("related_entity_id") else None,
            "is_read": notif.get("is_read", False),
            "created_at": notif.get("created_at").isoformat() if notif.get("created_at") else None
        }

        return sanitized

    # ---------------------------------------------------------
    # 🔔 Créer une notification
    # ---------------------------------------------------------
    def create_notification(self, data: dict) -> dict:
        try:
            required = ["user_id", "type", "title", "message"]
            for r in required:
                if r not in data or not data[r]:
                    raise ValueError(f"Champ manquant ou vide : {r}")

            notif = {
                "user_id": self._validate_object_id(data["user_id"], "user_id"),
                "type": data["type"],
                "title": data["title"],
                "message": data["message"],
                "action_url": data.get("action_url"),
                "related_entity_type": data.get("related_entity_type"),
                "related_entity_id": (
                    self._validate_object_id(data["related_entity_id"], "related_entity_id")
                    if data.get("related_entity_id") else None
                ),
                "is_read": False,
                "created_at": datetime.utcnow()
            }

            res = self.collection.insert_one(notif)
            return {"success": True, "notification_id": str(res.inserted_id)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 🎯 Envoyer une notification (wrapper)
    # ---------------------------------------------------------
    def send_notification(
        self, user_id: str, ntype: str, title: str, message: str,
        action_url: Optional[str] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None
    ) -> dict:

        try:
            data = {
                "user_id": user_id,
                "type": ntype,
                "title": title,
                "message": message,
                "action_url": action_url,
                "related_entity_type": related_entity_type,
                "related_entity_id": related_entity_id
            }
            return self.create_notification(data)

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # ✔ Marquer une notification comme lue
    # ---------------------------------------------------------
    def mark_notification_read(self, notification_id: str) -> dict:
        try:
            oid = self._validate_object_id(notification_id, "notification_id")
            res = self.collection.update_one({"_id": oid}, {"$set": {"is_read": True}})

            if res.matched_count == 0:
                return {"success": False, "error": "Notification introuvable"}

            return {"success": True, "updated_count": res.modified_count}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # ✔ Marquer TOUTES les notifications comme lues
    # ---------------------------------------------------------
    def mark_all_notifications_read(self, user_id: str) -> dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")
            res = self.collection.update_many(
                {"user_id": uid, "is_read": False},
                {"$set": {"is_read": True}}
            )
            return {"success": True, "updated_count": res.modified_count}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 🗑 Supprimer une notification
    # ---------------------------------------------------------
    def delete_notification(self, notification_id: str) -> dict:
        try:
            oid = self._validate_object_id(notification_id, "notification_id")
            res = self.collection.delete_one({"_id": oid})

            if res.deleted_count == 0:
                return {"success": False, "error": "Notification introuvable"}

            return {"success": True, "deleted_count": res.deleted_count}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 📄 Lister toutes les notifications d’un user
    # ---------------------------------------------------------
    def list_user_notifications(self, user_id: str, limit: int = 50, skip: int = 0) -> dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")
            cursor = (self.collection.find({"user_id": uid})
                      .sort("created_at", -1)
                      .skip(skip)
                      .limit(limit))
            notifs = [self._sanitize(n) for n in cursor]
            return {"success": True, "notifications": notifs}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 🔕 Lister uniquement les notifications NON lues
    # ---------------------------------------------------------
    def list_unread_notifications(self, user_id: str) -> dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")
            cursor = self.collection.find({"user_id": uid, "is_read": False}).sort("created_at", -1)
            notifs = [self._sanitize(n) for n in cursor]
            return {"success": True, "notifications": notifs}

        except Exception as e:
            return {"success": False, "error": str(e)}
