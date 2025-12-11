from datetime import datetime, timedelta
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError
from typing import Optional, List, Dict

# IMPORTANT : python-jose (et non PyJWT)
from jose import jwt

from utils.security import (
    hash_password,
    verify_password,
    SECRET_KEY,
    ALGORITHM,
)

class UsersServiceRPC:
    def __init__(self, db):
        self.collection = db["users"]

    # ------------------------- INTERNAL -------------------------
    def _to_objectid(self, value: str, field: str):
        try:
            return ObjectId(value)
        except Exception:
            raise ValueError(f"Invalid ObjectId for field '{field}'")

    def _sanitize(self, user: dict) -> dict:
        if not user:
            return {}
        user = user.copy()
        user.pop("password_hash", None)
        user["_id"] = str(user["_id"])
        if "created_at" in user:
            user["created_at"] = user["created_at"].isoformat()
        if "updated_at" in user:
            user["updated_at"] = user["updated_at"].isoformat()
        return user

    # ------------------------- AUTH -------------------------
    def register_user(self, email: str, password: str, full_name: str) -> dict:
        try:
            email = email.lower().strip()

            if self.collection.find_one({"email": email}):
                return {"error": "Email already exists"}

            username = email.split("@")[0].lower()
            if self.collection.find_one({"username": username}):
                return {"error": "Username already exists"}

            now = datetime.utcnow()
            user_doc = {
                "email": email,
                "username": username,
                "password_hash": hash_password(password),
                "role": "client",
                "full_name": full_name,
                "avatar_url": None,
                "skills": [],
                "hourly_rate": None,
                "is_active": True,
                "is_verified": False,
                "stats": {
                    "rating": 0,
                    "completed_orders": 0,
                    "total_reviews": 0,
                },
                "created_at": now,
                "updated_at": now,
            }

            result = self.collection.insert_one(user_doc)
            return {"user_id": str(result.inserted_id)}

        except PyMongoError as e:
            return {"error": f"Database error: {str(e)}"}

    def authenticate_user(self, email: str, password: str) -> dict:
        try:
            email = email.lower().strip()
            user = self.collection.find_one({"email": email})

            if not user or not verify_password(password, user.get("password_hash", "")):
                return {"error": "Invalid credentials"}

            return self._sanitize(user)

        except PyMongoError as e:
            return {"error": f"Database error: {str(e)}"}

    # ------------------------- PROFILE -------------------------
    def get_user_by_id(self, user_id: str) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            user = self.collection.find_one({"_id": oid})
            return self._sanitize(user)
        except Exception as e:
            return {"error": str(e)}

    def update_user_profile(self, user_id: str, fields: dict) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            fields["updated_at"] = datetime.utcnow()

            res = self.collection.update_one(
                {"_id": oid}, {"$set": fields}
            )
            return {"success": res.modified_count > 0}
        except Exception as e:
            return {"error": str(e)}

    def change_password(self, user_id: str, old_password: str, new_password: str) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            user = self.collection.find_one({"_id": oid})

            if not user or not verify_password(old_password, user.get("password_hash", "")):
                return {"error": "Old password incorrect"}

            new_hash = hash_password(new_password)

            res = self.collection.update_one(
                {"_id": oid}, {"$set": {"password_hash": new_hash}}
            )

            return {"success": res.modified_count > 0}

        except Exception as e:
            return {"error": str(e)}

    # ------------------------- ACCOUNT STATUS -------------------------
    def deactivate_account(self, user_id: str) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one(
                {"_id": oid}, {"$set": {"is_active": False}}
            )
            return {"success": res.modified_count > 0}
        except Exception as e:
            return {"error": str(e)}

    def activate_account(self, user_id: str) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one(
                {"_id": oid}, {"$set": {"is_active": True}}
            )
            return {"success": res.modified_count > 0}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------- FREELANCER -------------------------
    def add_skill(self, user_id: str, skill: str) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one(
                {"_id": oid}, {"$addToSet": {"skills": skill}}
            )
            return {"success": res.modified_count > 0}
        except Exception as e:
            return {"error": str(e)}

    def remove_skill(self, user_id: str, skill: str) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one(
                {"_id": oid}, {"$pull": {"skills": skill}}
            )
            return {"success": res.modified_count > 0}
        except Exception as e:
            return {"error": str(e)}

    def update_skills(self, user_id: str, skills_list: List[str]) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one(
                {"_id": oid}, {"$set": {"skills": skills_list}}
            )
            return {"success": res.modified_count > 0}
        except Exception as e:
            return {"error": str(e)}

    def update_hourly_rate(self, user_id: str, rate: float) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one(
                {"_id": oid}, {"$set": {"hourly_rate": rate}}
            )
            return {"success": res.modified_count > 0}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------- LISTING -------------------------
    def list_freelancers(self) -> list:
        try:
            cursor = self.collection.find({"role": "freelancer"})
            return [self._sanitize(u) for u in cursor]
        except PyMongoError as e:
            return [{"error": str(e)}]

    def list_clients(self) -> list:
        try:
            cursor = self.collection.find({"role": "client"})
            return [self._sanitize(u) for u in cursor]
        except PyMongoError as e:
            return [{"error": str(e)}]
