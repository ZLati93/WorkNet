from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError


class FavoritesService:

    def __init__(self, db, notifications_service=None):
        self.collection = db["favorites"]
        self.notifications_service = notifications_service  # Pour notifications automatiques

    # ---------------------------------------------------------
    # ⭐ Ajouter un gig aux favoris
    # ---------------------------------------------------------
    async def add_favorite(self, user_id: str, gig_id: str) -> dict:
        try:
            user_oid = ObjectId(user_id)
            gig_oid = ObjectId(gig_id)
        except InvalidId:
            return {"success": False, "error": "ID utilisateur ou gig invalide"}

        try:
            exists = await self.collection.find_one({"user_id": user_oid, "gig_id": gig_oid})
            if exists:
                return {"success": True, "message": "Déjà dans les favoris", "favorite_id": str(exists["_id"])}

            result = await self.collection.insert_one({
                "user_id": user_oid,
                "gig_id": gig_oid,
                "created_at": datetime.utcnow()
            })

            # Notification automatique si service fourni
            if self.notifications_service:
                await self.notifications_service._create_notification(
                    user_id=user_id,
                    title="Gig ajouté aux favoris",
                    message=f"Vous avez ajouté un gig à vos favoris.",
                    related_entity_type="gig",
                    related_entity_id=gig_id
                )

            return {"success": True, "message": "Ajouté aux favoris", "favorite_id": str(result.inserted_id)}

        except PyMongoError as e:
            return {"success": False, "error": f"Erreur MongoDB : {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Erreur inattendue : {str(e)}"}

    # ---------------------------------------------------------
    # ❌ Supprimer un gig des favoris
    # ---------------------------------------------------------
    async def remove_favorite(self, user_id: str, gig_id: str) -> dict:
        try:
            user_oid = ObjectId(user_id)
            gig_oid = ObjectId(gig_id)
        except InvalidId:
            return {"success": False, "error": "ID utilisateur ou gig invalide"}

        try:
            result = await self.collection.delete_one({"user_id": user_oid, "gig_id": gig_oid})
            if result.deleted_count == 0:
                return {"success": False, "message": "Ce gig n'est pas dans les favoris"}

            # Notification automatique
            if self.notifications_service:
                await self.notifications_service._create_notification(
                    user_id=user_id,
                    title="Gig retiré des favoris",
                    message=f"Vous avez retiré un gig de vos favoris.",
                    related_entity_type="gig",
                    related_entity_id=gig_id
                )

            return {"success": True, "message": "Supprimé des favoris"}

        except PyMongoError as e:
            return {"success": False, "error": f"Erreur MongoDB : {str(e)}"}

    # ---------------------------------------------------------
    # 📄 Lister tous les favoris d’un user
    # ---------------------------------------------------------
    async def list_favorites(self, user_id: str) -> dict:
        try:
            user_oid = ObjectId(user_id)
        except InvalidId:
            return {"success": False, "error": "ID utilisateur invalide"}

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
            return {"success": False, "error": f"Erreur MongoDB : {str(e)}"}

    # ---------------------------------------------------------
    # ✔ Vérifier si un gig est en favori
    # ---------------------------------------------------------
    async def is_favorite(self, user_id: str, gig_id: str) -> dict:
        try:
            user_oid = ObjectId(user_id)
            gig_oid = ObjectId(gig_id)
        except InvalidId:
            return {"success": False, "error": "ID utilisateur ou gig invalide"}

        try:
            fav = await self.collection.find_one({"user_id": user_oid, "gig_id": gig_oid})
            return {"success": True, "is_favorite": fav is not None}

        except PyMongoError as e:
            return {"success": False, "error": f"Erreur MongoDB : {str(e)}"}

    # ---------------------------------------------------------
    # 🗑 Supprimer tous les favoris d’un user
    # ---------------------------------------------------------
    async def clear_favorites(self, user_id: str) -> dict:
        try:
            user_oid = ObjectId(user_id)
        except InvalidId:
            return {"success": False, "error": "ID utilisateur invalide"}

        try:
            result = await self.collection.delete_many({"user_id": user_oid})

            # Notification automatique
            if self.notifications_service:
                await self.notifications_service._create_notification(
                    user_id=user_id,
                    title="Tous les favoris supprimés",
                    message="Tous vos gigs favoris ont été retirés.",
                    related_entity_type="user",
                    related_entity_id=user_id
                )

            return {"success": True, "deleted_count": result.deleted_count}

        except PyMongoError as e:
            return {"success": False, "error": f"Erreur MongoDB : {str(e)}"}
