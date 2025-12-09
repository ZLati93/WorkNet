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
    # 💬 1. Envoyer un message texte
    # ---------------------------------------------------------
    def send_message(self, order_id: str, sender_id: str, receiver_id: str,
                     content: str, message_type: str = "text") -> Dict:

        try:
            if not content or content.strip() == "":
                raise ValueError("Le message ne peut pas être vide")

            order = self._validate_object_id(order_id, "order_id")
            sender = self._validate_object_id(sender_id, "sender_id")
            receiver = self._validate_object_id(receiver_id, "receiver_id")

            msg = {
                "order_id": order,
                "sender_id": sender,
                "receiver_id": receiver,
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
    # 📎 2. Envoyer un message fichier
    # ---------------------------------------------------------
    def send_file_message(self, order_id: str, sender_id: str, receiver_id: str,
                          attachment_url: str, attachment_name: Optional[str] = None) -> Dict:

        try:
            if not attachment_url:
                raise ValueError("URL du fichier manquante")

            order = self._validate_object_id(order_id, "order_id")
            sender = self._validate_object_id(sender_id, "sender_id")
            receiver = self._validate_object_id(receiver_id, "receiver_id")

            msg = {
                "order_id": order,
                "sender_id": sender,
                "receiver_id": receiver,
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
    # ✔ 3. Marquer comme lu
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

            return {"success": True, "updated": res.modified_count > 0}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 📄 4. Récupérer la conversation d’une commande
    # ---------------------------------------------------------
    def get_conversation(self, order_id: str, limit: int = 50, skip: int = 0) -> Dict:
        try:
            oid = self._validate_object_id(order_id, "order_id")

            cursor = (self.collection.find({"order_id": oid})
                      .skip(skip)
                      .limit(limit)
                      .sort("created_at", 1))

            messages = []
            for m in cursor:
                m["_id"] = str(m["_id"])
                m["order_id"] = str(m["order_id"])
                m["sender_id"] = str(m["sender_id"])
                m["receiver_id"] = str(m["receiver_id"])
                messages.append(m)

            return {"success": True, "messages": messages}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 👤 5. Lister les messages d'un utilisateur
    # ---------------------------------------------------------
    def list_messages_by_user(self, user_id: str, limit: int = 50, skip: int = 0) -> Dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")

            cursor = (self.collection.find({
                "$or": [{"sender_id": uid}, {"receiver_id": uid}]
            })
                      .skip(skip)
                      .limit(limit)
                      .sort("created_at", -1))

            messages = []
            for m in cursor:
                m["_id"] = str(m["_id"])
                m["order_id"] = str(m["order_id"])
                m["sender_id"] = str(m["sender_id"])
                m["receiver_id"] = str(m["receiver_id"])
                messages.append(m)

            return {"success": True, "messages": messages}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 🗑 6. Supprimer un message
    # ---------------------------------------------------------
    def delete_message(self, message_id: str) -> Dict:
        try:
            mid = self._validate_object_id(message_id, "message_id")

            res = self.collection.delete_one({"_id": mid})

            if res.deleted_count == 0:
                return {"success": False, "error": "Message introuvable"}

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 🔔 7. Compter les messages non lus
    # ---------------------------------------------------------
    def count_unread_messages(self, user_id: str) -> Dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")

            count = self.collection.count_documents({
                "receiver_id": uid,
                "is_read": False
            })

            return {"success": True, "unread_count": count}

        except Exception as e:
            return {"success": False, "error": str(e)}
