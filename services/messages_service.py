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
        if not msg:
            return {}
        return {
            "_id": str(msg.get("_id")),
            "order_id": str(msg.get("order_id")) if msg.get("order_id") else None,
            "sender_id": str(msg.get("sender_id")) if msg.get("sender_id") else None,
            "receiver_id": str(msg.get("receiver_id")) if msg.get("receiver_id") else None,
            "content": msg.get("content"),
            "message_type": msg.get("message_type"),
            "attachment_url": msg.get("attachment_url"),
            "attachment_name": msg.get("attachment_name"),
            "is_read": msg.get("is_read", False),
            "created_at": msg.get("created_at").isoformat() if msg.get("created_at") else None,
            "read_at": msg.get("read_at").isoformat() if msg.get("read_at") else None
        }

    # ---------------------------------------------------------
    # 📄 Liste des messages avec filtres et pagination uniforme
    # ---------------------------------------------------------
    def list_messages_filtered(
        self,
        filters: Optional[Dict] = None,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        message_type: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
        skip: int = 0
    ) -> Dict:
        try:
            query = filters.copy() if filters else {}

            if user_id:
                uid = self._validate_object_id(user_id, "user_id")
                query["$or"] = [{"sender_id": uid}, {"receiver_id": uid}]

            if order_id:
                query["order_id"] = self._validate_object_id(order_id, "order_id")

            if message_type:
                query["message_type"] = message_type

            if is_read is not None:
                query["is_read"] = is_read

            cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            messages = [self._sanitize(m) for m in cursor]

            return {"success": True, "messages": messages, "count": len(messages)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 💬 Envoyer un message texte ou fichier
    # ---------------------------------------------------------
    def send_message(
        self, order_id: str, sender_id: str, receiver_id: str,
        content: Optional[str] = None,
        message_type: str = "text",
        attachment_url: Optional[str] = None,
        attachment_name: Optional[str] = None
    ) -> Dict:
        try:
            if message_type == "text" and (not content or content.strip() == ""):
                raise ValueError("Le message texte ne peut pas être vide")

            if message_type == "file" and not attachment_url:
                raise ValueError("URL du fichier manquante pour message fichier")

            msg = {
                "order_id": self._validate_object_id(order_id, "order_id"),
                "sender_id": self._validate_object_id(sender_id, "sender_id"),
                "receiver_id": self._validate_object_id(receiver_id, "receiver_id"),
                "content": content if message_type == "text" else None,
                "message_type": message_type,
                "attachment_url": attachment_url if message_type == "file" else None,
                "attachment_name": attachment_name if message_type == "file" else None,
                "is_read": False,
                "created_at": datetime.utcnow(),
                "read_at": None
            }

            res = self.collection.insert_one(msg)
            return {"success": True, "message_id": str(res.inserted_id)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # ✔ Marquer un ou plusieurs messages comme lus
    # ---------------------------------------------------------
    def mark_as_read(self, message_ids: Optional[List[str]] = None, order_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
        try:
            query = {}
            if message_ids:
                oids = [self._validate_object_id(mid, "message_id") for mid in message_ids]
                query["_id"] = {"$in": oids}

            if order_id and user_id:
                query.update({
                    "order_id": self._validate_object_id(order_id, "order_id"),
                    "receiver_id": self._validate_object_id(user_id, "user_id"),
                    "is_read": False
                })

            res = self.collection.update_many(query, {"$set": {"is_read": True, "read_at": datetime.utcnow()}})
            return {"success": True, "updated_count": res.modified_count}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 📄 Lister les conversations distinctes d'un utilisateur
    # ---------------------------------------------------------
    def list_conversations(self, user_id: str, limit: int = 50, skip: int = 0) -> Dict:
        try:
            uid = self._validate_object_id(user_id, "user_id")
            pipeline = [
                {"$match": {"$or": [{"sender_id": uid}, {"receiver_id": uid}]}},
                {"$sort": {"created_at": -1}},
                {"$group": {"_id": "$order_id", "latest": {"$first": "$$ROOT"}}},
                {"$skip": skip},
                {"$limit": limit}
            ]
            docs = self.collection.aggregate(pipeline)
            conversations = [self._sanitize(d["latest"]) for d in docs]
            return {"success": True, "conversations": conversations, "count": len(conversations)}
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

    # ---------------------------------------------------------
    # ⬇ Gestion des fichiers
    # ---------------------------------------------------------
    def upload_attachment(self, file_data: Dict) -> Dict:
        try:
            return self.send_message(
                order_id=file_data["order_id"],
                sender_id=file_data["sender_id"],
                receiver_id=file_data["receiver_id"],
                message_type="file",
                attachment_url=file_data["attachment_url"],
                attachment_name=file_data.get("attachment_name")
            )
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_attachment(self, file_id: str, user_id: str) -> Dict:
        try:
            mid = self._validate_object_id(file_id, "file_id")
            uid = self._validate_object_id(user_id, "user_id")
            res = self.collection.delete_one({"_id": mid, "sender_id": uid})
            if res.deleted_count == 0:
                return {"success": False, "error": "Fichier introuvable ou permission refusée"}
            return {"success": True, "deleted_count": res.deleted_count}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # 🔹 Messages système
    # ---------------------------------------------------------
    def send_system_message(self, order_id: str, user_id: str, content: str, message_type: str = "system") -> Dict:
        try:
            system_id = "000000000000000000000000"  # ID fictif pour système
            return self.send_message(order_id, system_id, user_id, content, message_type)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # Admin : liste et suppression
    # ---------------------------------------------------------
    def list_messages(self, filters: Optional[Dict] = None, limit: int = 50, skip: int = 0) -> Dict:
        try:
            query = filters.copy() if filters else {}
            cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            messages = [self._sanitize(m) for m in cursor]
            return {"success": True, "messages": messages, "count": len(messages)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_message_admin(self, message_id: str) -> Dict:
        try:
            mid = self._validate_object_id(message_id, "message_id")
            res = self.collection.delete_one({"_id": mid})
            if res.deleted_count == 0:
                return {"success": False, "error": "Message introuvable"}
            return {"success": True, "deleted_count": res.deleted_count}
        except Exception as e:
            return {"success": False, "error": str(e)}
