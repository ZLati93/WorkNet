from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError


class FavoritesService:

    def __init__(self, db):
        self.collection = db["favorites"]

    # ---------------------------------------------------------
    # ⭐ Ajouter un gig aux favoris
    # ---------------------------------------------------------
    async def add_to_favorites(self, user_id: str, gig_id: str) -> dict:
        try:
            user_oid = ObjectId(user_id)
            gig_oid = ObjectId(gig_id)
        except InvalidId:
            return {"success": False, "error": "Invalid user_id or gig_id"}

        try:
            exists = await self.collection.find_one({"user_id": user_oid, "gig_id": gig_oid})
            if exists:
                return {"success": True, "message": "Déjà dans les favoris", "favorite_id": str(exists["_id"])}

            result = await self.collection.insert_one({
                "user_id": user_oid,
                "gig_id": gig_oid,
                "created_at": datetime.utcnow()
            })
            return {"success": True, "message": "Ajouté aux favoris", "favorite_id": str(result.inserted_id)}

        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    # ---------------------------------------------------------
    # ❌ Supprimer un gig des favoris
    # ---------------------------------------------------------
    async def remove_from_favorites(self, user_id: str, gig_id: str) -> dict:
        try:
            user_oid = ObjectId(user_id)
            gig_oid = ObjectId(gig_id)
        except InvalidId:
            return {"success": False, "error": "Invalid user_id or gig_id"}

        try:
            result = await self.collection.delete_one({"user_id": user_oid, "gig_id": gig_oid})
            if result.deleted_count == 0:
                return {"success": False, "message": "Ce gig n'est pas dans les favoris"}

            return {"success": True, "message": "Supprimé des favoris"}

        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 📄 Lister tous les favoris d’un user
    # ---------------------------------------------------------
    async def list_favorites(self, user_id: str) -> dict:
        try:
            user_oid = ObjectId(user_id)
        except InvalidId:
            return {"success": False, "error": "Invalid user_id"}

        try:
            cursor = self.collection.find({"user_id": user_oid})
            favorites = []
            async for fav in cursor:
                favorites.append({
                    "favorite_id": str(fav["_id"]),
                    "gig_id": str(fav["gig_id"]),
                    "created_at": fav["created_at"].isoformat()
                })
            return {"success": True, "favorites": favorites}

        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # ✔ Vérifier si un gig est en favori
    # ---------------------------------------------------------
    async def is_favorite(self, user_id: str, gig_id: str) -> dict:
        try:
            user_oid = ObjectId(user_id)
            gig_oid = ObjectId(gig_id)
        except InvalidId:
            return {"success": False, "error": "Invalid user_id or gig_id"}

        try:
            fav = await self.collection.find_one({"user_id": user_oid, "gig_id": gig_oid})
            return {"success": True, "is_favorite": fav is not None}

        except PyMongoError as e:
            return {"success": False, "error": f"MongoDB error: {str(e)}"}
