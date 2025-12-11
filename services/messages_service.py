from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import Optional, List, Dict


class MessagesService:

    def __init__(self, db):
        self.collection = db["messages"]

    # ---------------------------------------------------------
    # 🔧 Utils : Validation ObjectId
    # ---------------------------------------------------------
    def _validate_object_id(self, id_str: str, field_name: str) -> ObjectId:
        try:
            return ObjectId(id_str)
        except (InvalidId, TypeError):
            raise ValueError(f"ID invalide pour '{field_name}'")

    # ---------------------------------------------------------
    # 🧼 Utils : Sanitize message
    # ---------------------------------------------------------
    def _sanitize(self, msg: dict) -> dict:
        return {
            "_id": str(msg.get("_id")),
            "order_id": str(msg.get("order_id")),
            "sender_id": str(msg.get("sender_id")),
            "receiver_id": str(msg.get("receiver_id")),
            "content": msg.get("content"),
            "message_type": msg.get("message_type"),
            "attachment_url": msg.get("attachment_url"),
            "attachment_name": msg.get("attachment_name"),
            "is_read": msg.get("is_read", False),
            "created_at": msg.get("created_at").isoformat() if msg.get("created_at") else None,
            "read_at": msg.get("read_at").isoformat() if msg.get("read_at") else None
        }

    # ---------------------------------------------------------
    # 💬 Envoyer un message texte
    # ---------------------------------------------------------
    def send_message(self, order_id: str, sender_id: str, receiver_id: str,
                     content: str, message_type: str = "text") -> Dict:

        try:
            if not content or content.strip() == "":
                raise ValueError("Le message ne peut pas être vide")

            msg = {
                "order_id": self._validate_object_id(order_id, "order_id"),
                "sender_id": self._validate_object_id(sender_id, "sender_id"),
                "receiver_id": self._validate_object_id(receiver_id, "receiver_id"),
                "content": content,
                "message_type": message_type,
                "attachment_url": None,
                "attachment_name": None,
                "is_read": False,
                "created_at": datetime.utcnow()
            }

            res = self.collection.insert_one(msg)
            return {"success": True, "message_id": str(res.inserted_id)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 📎 Envoyer un message fichier
    # ---------------------------------------------------------
    def send_file_message(self, order_id: str, sender_id: str, receiver_id: str,
                          attachment_url: str, attachment_name: Optional[str] = None) -> Dict:

        try:
            if not attachment_url:
                raise ValueError("URL du fichier manquante")

            msg = {
                "order_id": self._validate_object_id(order_id, "order_id"),
                "sender_id": self._validate_object_id(sender_id, "sender_id"),
                "receiver_id": self._validate_object_id(receiver_id, "receiver_id"),
                "content": None,
                "message_type": "file",
                "attachment_url": attachment_url,
                "attachment_name": attachment_name,
                "is_read": False,
                "created_at": datetime.utcnow()
            }

            res = self.collection.insert_one(msg)
            return {"success": True, "message_id": str(res.inserted_id)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # ✔ Marquer comme lu
    # ---------------------------------------------------------
    def mark_message_read(self, message_id: str) -> Dict:
        try:
            mid = self._validate_object_id(message_id, "message_id")
            res = self.collection.update_one(
                {"_id": mid},
                {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
            )

            if res.matched_count == 0:
                return {"success": False, "error": "Message introuvable"}

            return {"success": True, "updated_count": res.modified_count}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 📄 Récupérer la conversation d’une commande
    # ---------------------------------------------------------
    def get_conversation(self, order_id: str, limit: int = 50, skip: int = 0) -> Dict:
        try:
            oid = self._validate_object_id(order_id, "order_id")
            cursor = (self.collection.find({"order_id": oid})
                      .sort("created_at", 1)
                      .skip(skip)
                      .limit(limit))
            messages = [self._sanitize(m) for m in cursor]
            return {"success": True, "messages": messages}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 👤 Lister les messages d'un utilisateur
    # ---------------------------------------------------------
    def list_messages_by_user(self, user_id: str, limit: int = 50, skip: int = 0) -> Dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")
            cursor = (self.collection.find({"$or": [{"sender_id": uid}, {"receiver_id": uid}]})
                      .sort("created_at", -1)
                      .skip(skip)
                      .limit(limit))
            messages = [self._sanitize(m) for m in cursor]
            return {"success": True, "messages": messages}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 🗑 Supprimer un message
    # ---------------------------------------------------------
    def delete_message(self, message_id: str) -> Dict:
        try:
            mid = self._validate_object_id(message_id, "message_id")
            res = self.collection.delete_one({"_id": mid})

            if res.deleted_count == 0:
                return {"success": False, "error": "Message introuvable"}

            return {"success": True, "deleted_count": res.deleted_count}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 🔔 Compter les messages non lus
    # ---------------------------------------------------------
    def count_unread_messages(self, user_id: str) -> Dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")
            count = self.collection.count_documents({"receiver_id": uid, "is_read": False})
            return {"success": True, "unread_count": count}

        except Exception as e:
            return {"success": False, "error": str(e)}
