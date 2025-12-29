from bson.objectid import ObjectId
from datetime import datetime

class MessagesService:
    def __init__(self, db):
        self.collection = db["messages"]

    def send_message(self, order_id, sender_id, receiver_id, content, message_type="text", attachment_url=None, attachment_name=None):
        if not content and not attachment_url:
            raise ValueError("Message vide")
        msg = {
            "order_id": ObjectId(order_id),
            "sender_id": ObjectId(sender_id),
            "receiver_id": ObjectId(receiver_id),
            "content": content,
            "message_type": message_type,
            "attachment_url": attachment_url,
            "attachment_name": attachment_name,
            "is_read": False,
            "created_at": datetime.utcnow()
        }
        res = self.collection.insert_one(msg)
        return str(res.inserted_id)
