from bson.objectid import ObjectId, InvalidId
from datetime import datetime
from typing import List, Optional
from pymongo.errors import PyMongoError


class CategoriesService:
    def __init__(self, db):
        self.collection = db["categories"]

    # ---------------------------------------------------------
    # Internal: Convertir ObjectId → str
    # ---------------------------------------------------------
    def _sanitize(self, doc: dict) -> Optional[dict]:
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        if "parent_category_id" in doc and doc["parent_category_id"]:
            doc["parent_category_id"] = str(doc["parent_category_id"])
        return doc

    # ---------------------------------------------------------
    # 1. CREATE CATEGORY
    # ---------------------------------------------------------
    def create_category(
        self,
        name: str,
        description: str = "",
        parent_id: str = None,
        is_active: bool = True,
        sort_order: int = 0
    ) -> dict:
        try:
            if not name or len(name.strip()) < 2:
                return {"success": False, "message": "Category name must be at least 2 characters"}

            category = {
                "name": name,
                "description": description,
                "is_active": is_active,
                "sort_order": sort_order,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            if parent_id:
                try:
                    category["parent_category_id"] = ObjectId(parent_id)
                except InvalidId:
                    return {"success": False, "message": "Invalid parent category ID"}

            res = self.collection.insert_one(category)
            return {"success": True, "category_id": str(res.inserted_id)}

        except PyMongoError as e:
            return {"success": False, "message": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 2. GET ONE CATEGORY
    # ---------------------------------------------------------
    def get_category(self, category_id: str) -> dict:
        try:
            cid = ObjectId(category_id)
        except InvalidId:
            return {"success": False, "message": "Invalid category ID"}

        try:
            doc = self.collection.find_one({"_id": cid})
            if not doc:
                return {"success": False, "message": "Category not found"}
            return {"success": True, "category": self._sanitize(doc)}

        except PyMongoError as e:
            return {"success": False, "message": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 3. UPDATE CATEGORY
    # ---------------------------------------------------------
    def update_category(self, category_id: str, update_data: dict) -> dict:
        try:
            cid = ObjectId(category_id)
        except InvalidId:
            return {"success": False, "message": "Invalid category ID"}

        update_data["updated_at"] = datetime.utcnow()

        if "parent_category_id" in update_data and update_data["parent_category_id"]:
            try:
                update_data["parent_category_id"] = ObjectId(update_data["parent_category_id"])
            except InvalidId:
                return {"success": False, "message": "Invalid parent category ID"}

        try:
            res = self.collection.update_one({"_id": cid}, {"$set": update_data})
            return {"success": True, "updated": res.modified_count > 0}

        except PyMongoError as e:
            return {"success": False, "message": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 4. DELETE CATEGORY
    # ---------------------------------------------------------
    def delete_category(self, category_id: str) -> dict:
        try:
            cid = ObjectId(category_id)
        except InvalidId:
            return {"success": False, "message": "Invalid category ID"}

        try:
            res = self.collection.delete_one({"_id": cid})
            if res.deleted_count == 0:
                return {"success": False, "message": "Category not found"}
            return {"success": True}

        except PyMongoError as e:
            return {"success": False, "message": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 5. LIST ALL CATEGORIES
    # ---------------------------------------------------------
    def list_categories(self, limit: int = 200, skip: int = 0) -> dict:
        try:
            docs = self.collection.find().sort("sort_order", 1).skip(skip).limit(limit)
            return {"success": True, "categories": [self._sanitize(d) for d in docs]}
        except PyMongoError as e:
            return {"success": False, "message": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 6. LIST ACTIVE CATEGORIES
    # ---------------------------------------------------------
    def list_active_categories(self) -> dict:
        try:
            docs = self.collection.find({"is_active": True}).sort("sort_order", 1)
            return {"success": True, "categories": [self._sanitize(d) for d in docs]}
        except PyMongoError as e:
            return {"success": False, "message": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 7. LIST ONLY PARENT CATEGORIES
    # ---------------------------------------------------------
    def list_parent_categories(self) -> dict:
        try:
            docs = self.collection.find({"parent_category_id": {"$exists": False}})
            return {"success": True, "categories": [self._sanitize(d) for d in docs]}
        except PyMongoError as e:
            return {"success": False, "message": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 8. LIST CHILDREN OF A PARENT CATEGORY
    # ---------------------------------------------------------
    def list_children_categories(self, parent_category_id: str) -> dict:
        try:
            pid = ObjectId(parent_category_id)
        except InvalidId:
            return {"success": False, "message": "Invalid parent category ID"}

        try:
            docs = self.collection.find({"parent_category_id": pid}).sort("sort_order", 1)
            return {"success": True, "categories": [self._sanitize(d) for d in docs]}
        except PyMongoError as e:
            return {"success": False, "message": f"MongoDB error: {str(e)}"}
