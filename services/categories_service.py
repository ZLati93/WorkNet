from datetime import datetime
from bson import ObjectId, InvalidId
from pymongo.errors import PyMongoError


class CategoriesService:
    def __init__(self, db, notifications_service=None):
        self.collection = db["categories"]
        self.notifications_service = notifications_service  # notifications automatiques

    # ---------------------------------------------------------
    # Internal: Convertir ObjectId → str
    # ---------------------------------------------------------
    def _sanitize(self, doc: dict) -> dict:
        if not doc:
            return {}
        doc["_id"] = str(doc["_id"])
        if "parent_category_id" in doc and doc["parent_category_id"]:
            doc["parent_category_id"] = str(doc["parent_category_id"])
        return doc

    # ---------------------------------------------------------
    # List all categories
    # ---------------------------------------------------------
    def list_categories(self, limit: int = 200, skip: int = 0) -> dict:
        try:
            docs = self.collection.find().sort("sort_order", 1).skip(skip).limit(limit)
            return {"success": True, "categories": [self._sanitize(d) for d in docs]}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # Get category by ID
    # ---------------------------------------------------------
    def get_category_by_id(self, category_id: str) -> dict:
        try:
            cid = ObjectId(category_id)
        except InvalidId:
            return {"success": False, "error": "Invalid category ID"}

        try:
            doc = self.collection.find_one({"_id": cid})
            if not doc:
                return {"success": False, "error": "Category not found"}
            return {"success": True, "category": self._sanitize(doc)}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # Get category by slug (assuming field 'slug')
    # ---------------------------------------------------------
    def get_category_by_slug(self, slug: str) -> dict:
        try:
            doc = self.collection.find_one({"slug": slug})
            if not doc:
                return {"success": False, "error": "Category not found"}
            return {"success": True, "category": self._sanitize(doc)}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # List subcategories of a parent
    # ---------------------------------------------------------
    def list_subcategories(self, parent_id: str) -> dict:
        try:
            pid = ObjectId(parent_id)
        except InvalidId:
            return {"success": False, "error": "Invalid parent category ID"}

        try:
            docs = self.collection.find({"parent_category_id": pid}).sort("sort_order", 1)
            return {"success": True, "categories": [self._sanitize(d) for d in docs]}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # Admin: Create category
    # ---------------------------------------------------------
    def create_category(self, data: dict) -> dict:
        try:
            category = {
                "name": data.get("name"),
                "description": data.get("description", ""),
                "is_active": data.get("is_active", True),
                "sort_order": data.get("sort_order", 0),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            if "parent_category_id" in data and data["parent_category_id"]:
                try:
                    category["parent_category_id"] = ObjectId(data["parent_category_id"])
                except InvalidId:
                    return {"success": False, "error": "Invalid parent category ID"}

            res = self.collection.insert_one(category)

            # Notification automatique
            if self.notifications_service:
                self.notifications_service.send_notification(
                    user_id="admin",  # ou ID admin concerné
                    ntype="category_created",
                    title="Nouvelle catégorie créée",
                    message=f"Catégorie '{category['name']}' créée avec succès",
                    related_entity_type="category",
                    related_entity_id=str(res.inserted_id)
                )

            return {"success": True, "category_id": str(res.inserted_id)}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # Admin: Update category
    # ---------------------------------------------------------
    def update_category(self, category_id: str, data: dict) -> dict:
        try:
            cid = ObjectId(category_id)
        except InvalidId:
            return {"success": False, "error": "Invalid category ID"}

        update_data = data.copy()
        update_data["updated_at"] = datetime.utcnow()
        if "parent_category_id" in update_data and update_data["parent_category_id"]:
            try:
                update_data["parent_category_id"] = ObjectId(update_data["parent_category_id"])
            except InvalidId:
                return {"success": False, "error": "Invalid parent category ID"}

        try:
            res = self.collection.update_one({"_id": cid}, {"$set": update_data})
            return {"success": True, "updated": res.modified_count > 0}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # Admin: Delete category
    # ---------------------------------------------------------
    def delete_category(self, category_id: str) -> dict:
        try:
            cid = ObjectId(category_id)
        except InvalidId:
            return {"success": False, "error": "Invalid category ID"}

        try:
            res = self.collection.delete_one({"_id": cid})
            if res.deleted_count == 0:
                return {"success": False, "error": "Category not found"}
            return {"success": True, "deleted_count": res.deleted_count}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # Admin: Update category order
    # ---------------------------------------------------------
    def update_category_order(self, ordered_ids: list) -> dict:
        try:
            for index, cat_id in enumerate(ordered_ids):
                try:
                    oid = ObjectId(cat_id)
                    self.collection.update_one({"_id": oid}, {"$set": {"sort_order": index}})
                except InvalidId:
                    continue
            return {"success": True, "message": "Order updated"}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}

    # ---------------------------------------------------------
    # Admin: Toggle category status
    # ---------------------------------------------------------
    def toggle_category_status(self, category_id: str) -> dict:
        try:
            cid = ObjectId(category_id)
        except InvalidId:
            return {"success": False, "error": "Invalid category ID"}

        try:
            doc = self.collection.find_one({"_id": cid})
            if not doc:
                return {"success": False, "error": "Category not found"}
            new_status = not doc.get("is_active", True)
            res = self.collection.update_one({"_id": cid}, {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}})
            return {"success": True, "new_status": new_status, "updated": res.modified_count > 0}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
