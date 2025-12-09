from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError


class FavoritesService:

    def __init__(self, db):
        self.collection = db["favorites"]

    # ---------------------------------------------------------
    # ⭐ 1. Ajouter un gig aux favoris
    # ---------------------------------------------------------
    async def add_to_favorites(self, user_id: str, gig_id: str):
        try:
            user_oid = ObjectId(user_id)
            gig_oid = ObjectId(gig_id)
        except InvalidId:
            return {"error": "Invalid user_id or gig_id"}

        try:
            # Vérifier si déjà dans favoris
            exists = await self.collection.find_one({
                "user_id": user_oid,
                "gig_id": gig_oid
            })

            if exists:
                return {
                    "message": "Déjà dans les favoris",
                    "favorite_id": str(exists["_id"])
                }

            # Ajouter
            result = await self.collection.insert_one({
                "user_id": user_oid,
                "gig_id": gig_oid,
                "created_at": datetime.utcnow()
            })

            return {
                "message": "Ajouté aux favoris",
                "favorite_id": str(result.inserted_id)
            }

        except PyMongoError as e:
            return {"error": f"MongoDB error: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    # ---------------------------------------------------------
    # ❌ 2. Supprimer un gig des favoris
    # ---------------------------------------------------------
    async def remove_from_favorites(self, user_id: str, gig_id: str):
        try:
            user_oid = ObjectId(user_id)
            gig_oid = ObjectId(gig_id)
        except InvalidId:
            return {"error": "Invalid user_id or gig_id"}

        try:
            result = await self.collection.delete_one({
                "user_id": user_oid,
                "gig_id": gig_oid
            })

            if result.deleted_count == 0:
                return {"message": "Ce gig n'est pas dans les favoris"}

            return {"message": "Supprimé des favoris"}

        except PyMongoError as e:
            return {"error": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # 📄 3. Lister tous les favoris d’un user
    # ---------------------------------------------------------
    async def list_favorites(self, user_id: str):
        try:
            user_oid = ObjectId(user_id)
        except InvalidId:
            return {"error": "Invalid user_id"}

        try:
            cursor = self.collection.find({"user_id": user_oid})
            favorites = []

            async for fav in cursor:
                favorites.append({
                    "favorite_id": str(fav["_id"]),
                    "gig_id": str(fav["gig_id"]),
                    "created_at": fav["created_at"].isoformat()
                })

            return favorites

        except PyMongoError as e:
            return {"error": f"MongoDB error: {str(e)}"}

    # ---------------------------------------------------------
    # ✔ 4. Vérifier si un gig est en favori
    # ---------------------------------------------------------
    async def is_favorite(self, user_id: str, gig_id: str):
        try:
            user_oid = ObjectId(user_id)
            gig_oid = ObjectId(gig_id)
        except InvalidId:
            return {"error": "Invalid user_id or gig_id"}

        try:
            fav = await self.collection.find_one({
                "user_id": user_oid,
                "gig_id": gig_oid
            })

            return {"is_favorite": fav is not None}

        except PyMongoError as e:
            return {"error": f"MongoDB error: {str(e)}"}
