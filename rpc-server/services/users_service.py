from datetime import datetime
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError
from typing import Optional, List
from utils.security import hash_password, verify_password

class UsersService:
    def __init__(self, db):
        self.collection = db["users"]

    def _sanitize(self, user: dict) -> Optional[dict]:
        if not user:
            return None
        user.pop("password_hash", None)
        user["_id"] = str(user["_id"])
        return user

    def create_user(self, user_data: dict) -> str:
        required = ["email", "username", "password", "role", "full_name"]
        for r in required:
            if r not in user_data or not user_data[r]:
                raise ValueError(f"Missing required field: {r}")

        user_data["email"] = user_data["email"].lower().strip()
        user_data["username"] = user_data["username"].lower().strip()
        if self.collection.find_one({"email": user_data["email"]}):
            raise ValueError("Email already exists")
        if self.collection.find_one({"username": user_data["username"]}):
            raise ValueError("Username already exists")

        user_data["password_hash"] = hash_password(user_data.pop("password"))
        now = datetime.utcnow()
        user_data.update({
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "is_verified": False
        })
        res = self.collection.insert_one(user_data)
        return str(res.inserted_id)

    def get_user(self, user_id: str) -> Optional[dict]:
        try:
            user = self.collection.find_one({"_id": ObjectId(user_id)})
            return self._sanitize(user)
        except:
            return None

    def get_user_by_email(self, email: str) -> Optional[dict]:
        try:
            user = self.collection.find_one({"email": email.lower().strip()})
            return self._sanitize(user)
        except:
            return None

    def update_user(self, user_id: str, update_data: dict) -> bool:
        update_data["updated_at"] = datetime.utcnow()
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        try:
            res = self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
            return res.modified_count > 0
        except:
            return False

    def delete_user(self, user_id: str) -> bool:
        try:
            res = self.collection.delete_one({"_id": ObjectId(user_id)})
            return res.deleted_count > 0
        except:
            return False

    def authenticate_user(self, email: str, password: str):
        user = self.collection.find_one({"email": email.lower().strip()})
        if user and verify_password(password, user.get("password_hash", "")):
            return self._sanitize(user)
        return None