from datetime import datetime, timedelta
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError
from typing import List, Dict, Optional

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

    # ========================= INTERNAL =========================
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
        for k in ("created_at", "updated_at"):
            if k in user and isinstance(user[k], datetime):
                user[k] = user[k].isoformat()
        return user

    # ===========================================================
    # AUTH – CORE IMPLEMENTATION
    # ===========================================================
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
                "portfolio": [],
                "company": None,
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

            res = self.collection.insert_one(user_doc)
            return {"user_id": str(res.inserted_id)}

        except PyMongoError as e:
            return {"error": str(e)}

    def login_user(self, email: str, password: str) -> dict:
        try:
            user = self.collection.find_one({"email": email.lower().strip()})
            if not user or not verify_password(password, user["password_hash"]):
                return {"error": "Invalid credentials"}

            payload = {
                "sub": str(user["_id"]),
                "role": user["role"],
                "exp": datetime.utcnow() + timedelta(days=7),
            }

            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return {"token": token, "user": self._sanitize(user)}

        except Exception as e:
            return {"error": str(e)}

    def logout_user(self, user_id: str) -> dict:
        return {"success": True}

    def refresh_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            payload["exp"] = datetime.utcnow() + timedelta(days=7)
            return {"token": jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)}
        except Exception:
            return {"error": "Invalid token"}

    def forgot_password(self, email: str) -> dict:
        if not self.collection.find_one({"email": email.lower()}):
            return {"error": "Email not found"}
        return {"success": True}

    def reset_password(self, token: str, new_password: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            oid = self._to_objectid(payload["sub"], "user_id")
            self.collection.update_one(
                {"_id": oid},
                {"$set": {"password_hash": hash_password(new_password)}},
            )
            return {"success": True}
        except Exception:
            return {"error": "Invalid or expired token"}

    # ===========================================================
    # USER MANAGEMENT
    # ===========================================================
    def get_user_profile(self, user_id: str) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            return self._sanitize(self.collection.find_one({"_id": oid}))
        except Exception as e:
            return {"error": str(e)}

    def update_user_profile(self, user_id: str, data: dict) -> dict:
        try:
            data["updated_at"] = datetime.utcnow()
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one({"_id": oid}, {"$set": data})
            return {"success": res.modified_count > 0}
        except Exception as e:
            return {"error": str(e)}

    def update_user_avatar(self, user_id: str, image_url: str) -> dict:
        return self.update_user_profile(user_id, {"avatar_url": image_url})

    def change_password(self, user_id: str, old: str, new: str) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            user = self.collection.find_one({"_id": oid})

            if not verify_password(old, user["password_hash"]):
                return {"error": "Old password incorrect"}

            self.collection.update_one(
                {"_id": oid},
                {"$set": {"password_hash": hash_password(new)}},
            )
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    def deactivate_account(self, user_id: str) -> dict:
        return self.update_user_status(user_id, False)

    def delete_account(self, user_id: str) -> dict:
        try:
            oid = self._to_objectid(user_id, "user_id")
            self.collection.delete_one({"_id": oid})
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    # ===========================================================
    # FREELANCER
    # ===========================================================
    def update_freelancer_skills(self, user_id: str, skills: list) -> dict:
        return self.update_user_profile(user_id, {"skills": skills})

    def update_freelancer_portfolio(self, user_id: str, portfolio: list) -> dict:
        return self.update_user_profile(user_id, {"portfolio": portfolio})

    def get_freelancer_public_profile(self, username: str) -> dict:
        user = self.collection.find_one(
            {"username": username, "role": "freelancer", "is_active": True}
        )
        return self._sanitize(user)

    def search_freelancers(self, filters: dict) -> list:
        query = {"role": "freelancer", "is_active": True}

        if filters.get("skills"):
            query["skills"] = {"$in": filters["skills"]}

        if filters.get("min_rate"):
            query["hourly_rate"] = {"$gte": filters["min_rate"]}

        return [self._sanitize(u) for u in self.collection.find(query)]

    # ===========================================================
    # CLIENT
    # ===========================================================
    def update_client_company(self, user_id: str, data: dict) -> dict:
        return self.update_user_profile(user_id, {"company": data})

    # ===========================================================
    # ADMIN
    # ===========================================================
    def list_users(self, filters: dict = None, pagination: dict = None) -> list:
        filters = filters or {}
        cursor = self.collection.find(filters)
        return [self._sanitize(u) for u in cursor]

    def get_user_by_id(self, user_id: str) -> dict:
        return self.get_user_profile(user_id)

    def update_user_status(self, user_id: str, status: bool) -> dict:
        return self.update_user_profile(user_id, {"is_active": status})

    def delete_user_admin(self, user_id: str) -> dict:
        return self.delete_account(user_id)
