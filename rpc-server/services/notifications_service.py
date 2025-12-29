from bson.objectid import ObjectId
from datetime import datetime

class NotificationsService:
    def __init__(self, db):
        self.collection = db["notifications"]

    def create_notification(self, user_id, ntype, title, message, action_url=None, related_entity_type=None, related_entity_id=None):
        notif = {
            "user_id": ObjectId(user_id),
            "type": ntype,
            "title": title,
            "message": message,
            "action_url": action_url,
            "is_read": False,
            "related_entity_type": related_entity_type,
            "created_at": datetime.utcnow()
        }
        if related_entity_id:
            notif["related_entity_id"] = ObjectId(related_entity_id)
        res = self.collection.insert_one(notif)
        return str(res.inserted_id)

