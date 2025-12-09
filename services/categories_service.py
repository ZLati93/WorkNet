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
    # 1. CREATE
    # ---------------------------------------------------------
    def create_category(
        self,
        name: str,
        description: str = "",
        parent_id: str = None,
        is_active: bool = True,
        sort_order: int = 0
    ) -> str:
        try:
            if not name or len(name.strip()) < 2:
                raise ValueError("Category name is required and must be >= 2 characters")

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
                    raise ValueError("Invalid parent category ID")

            res = self.collection.insert_one(category)
            return str(res.inserted_id)

        except (PyMongoError, ValueError) as e:
            print(f"[ERROR] create_category: {e}")
            raise e

    # ---------------------------------------------------------
    # 2. GET ONE
    # ---------------------------------------------------------
    def get_category(self, category_id: str) -> Optional[dict]:
        try:
            category_id = ObjectId(category_id)
        except InvalidId:
            raise ValueError("Invalid category ID")

        doc = self.collection.find_one({"_id": category_id})
        return self._sanitize(doc)

    # ---------------------------------------------------------
    # 3. UPDATE
    # ---------------------------------------------------------
    def update_category(self, category_id: str, update_data: dict) -> bool:
        try:
            cid = ObjectId(category_id)
        except InvalidId:
            raise ValueError("Invalid category ID")

        update_data["updated_at"] = datetime.utcnow()

        if "parent_category_id" in update_data and update_data["parent_category_id"]:
            try:
                update_data["parent_category_id"] = ObjectId(update_data["parent_category_id"])
            except InvalidId:
                raise ValueError("Invalid parent category ID")

        res = self.collection.update_one({"_id": cid}, {"$set": update_data})
        return res.modified_count > 0

    # ---------------------------------------------------------
    # 4. DELETE
    # ---------------------------------------------------------
    def delete_category(self, category_id: str) -> bool:
        try:
            cid = ObjectId(category_id)
        except InvalidId:
            raise ValueError("Invalid category ID")

        res = self.collection.delete_one({"_id": cid})
        return res.deleted_count > 0

    # ---------------------------------------------------------
    # 5. LIST ALL
    # ---------------------------------------------------------
    def list_categories(self, limit: int = 200, skip: int = 0) -> List[dict]:
        try:
            docs = (
                self.collection.find()
                .sort("sort_order", 1)
                .skip(skip)
                .limit(limit)
            )
            return [self._sanitize(d) for d in docs]
        except PyMongoError as e:
            print(f"[ERROR] list_categories: {e}")
            return []

    # ---------------------------------------------------------
    # 6. LIST ONLY ACTIVE
    # ---------------------------------------------------------
    def list_active_categories(self) -> List[dict]:
        try:
            docs = self.collection.find({"is_active": True}).sort("sort_order", 1)
            return [self._sanitize(d) for d in docs]
        except PyMongoError as e:
            print(f"[ERROR] list_active_categories: {e}")
            return []

    # ---------------------------------------------------------
    # 7. LIST ONLY PARENTS
    # ---------------------------------------------------------
    def list_parent_categories(self) -> List[dict]:
        try:
            docs = self.collection.find({"parent_category_id": {"$exists": False}})
            return [self._sanitize(d) for d in docs]
        except PyMongoError as e:
            print(f"[ERROR] list_parent_categories: {e}")
            return []

    # ---------------------------------------------------------
    # 8. LIST CHILDREN OF A PARENT CATEGORY
    # ---------------------------------------------------------
    def list_children_categories(self, parent_category_id: str) -> List[dict]:
        try:
            pid = ObjectId(parent_category_id)
        except InvalidId:
            raise ValueError("Invalid parent category ID")

        docs = self.collection.find({"parent_category_id": pid}).sort("sort_order", 1)
        return [self._sanitize(d) for d in docs]
