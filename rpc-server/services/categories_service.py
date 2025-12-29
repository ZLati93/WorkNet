from bson.objectid import ObjectId
from datetime import datetime
from pymongo.errors import PyMongoError
from typing import List, Optional

class CategoriesService:
    def __init__(self, db):
        self.collection = db["categories"]

    def _sanitize(self, doc: dict) -> dict:
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return doc

    def create_category(self, name: str, description: str = "", parent_id: str = None, is_active: bool = True, sort_order: int = 0) -> str:
        cat = {
            "name": name,
            "description": description,
            "is_active": is_active,
            "sort_order": sort_order,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        if parent_id:
            cat["parent_category_id"] = ObjectId(parent_id)
        res = self.collection.insert_one(cat)
        return str(res.inserted_id)

    def list_categories(self, limit: int = 100, skip: int = 0) -> List[dict]:
        docs = list(self.collection.find().skip(skip).limit(limit))
        return [self._sanitize(d) for d in docs]

    def get_category(self, cat_id: str) -> Optional[dict]:
        doc = self.collection.find_one({"_id": ObjectId(cat_id)})
        return self._sanitize(doc)

    def update_category(self, cat_id: str, update_data: dict) -> bool:
        update_data["updated_at"] = datetime.utcnow()
        if "parent_category_id" in update_data and update_data["parent_category_id"]:
            update_data["parent_category_id"] = ObjectId(update_data["parent_category_id"])
        res = self.collection.update_one({"_id": ObjectId(cat_id)}, {"$set": update_data})
        return res.modified_count > 0

    def delete_category(self, cat_id: str) -> bool:
        res = self.collection.delete_one({"_id": ObjectId(cat_id)})
        return res.deleted_count > 0
