# services/users_service.py
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError
from typing import Optional, List, Dict
import jwt

from utils.security import hash_password, verify_password, generate_token, SECRET_KEY, ALGORITHM

class UsersService:
    def __init__(self, db):
        self.collection = db["users"]

    # ---------------------------------------------------------
    # 🔧 INTERNAL UTILITIES
    # ---------------------------------------------------------
    def _to_objectid(self, value: str, field: str):
        """Convert to ObjectId with error handling."""
        try:
            return ObjectId(value)
        except Exception:
            raise ValueError(f"Invalid ObjectId for field '{field}'")

    def _sanitize(self, user: dict) -> Optional[dict]:
        """Remove sensitive fields and clean the object."""
        if not user:
            return None
        user.pop("password_hash", None)
        user["_id"] = str(user["_id"])
        return user

    # ---------------------------------------------------------
    # 🔐 AUTHENTICATION
    # ---------------------------------------------------------
    def register_user(self, user_data: dict) -> str:
        try:
            # Validate required fields (adjusted to match main.py UserCreate, assuming role defaults to 'client' or 'freelancer')
            required = ["email", "password", "full_name"]
            for r in required:
                if r not in user_data or not user_data[r]:
                    raise ValueError(f"Missing required field: {r}")

            # Assume username is derived from email or full_name if not provided; role defaults to 'client'
            email = user_data["email"].lower().strip()
            username = user_data.get("username", email.split('@')[0]).lower().strip()  # Derive if not provided
            role = user_data.get("role", "client")  # Default role

            # Uniqueness check for email / username
            if self.collection.find_one({"email": email}):
                raise ValueError("Email already exists")
            if self.collection.find_one({"username": username}):
                raise ValueError("Username already exists")

            # Create user
            now = datetime.utcnow()
            user_doc = {
                "email": email,
                "username": username,
                "password_hash": hash_password(user_data["password"]),
                "role": role,
                "full_name": user_data["full_name"],
                "avatar_url": None,
                "skills": [],
                "hourly_rate": None,
                "is_active": True,
                "is_verified": False,
                "stats": {
                    "rating": 0,
                    "completed_orders": 0,
                    "total_reviews": 0
                },
                "created_at": now,
                "updated_at": now
            }

            result = self.collection.insert_one(user_doc)
            return str(result.inserted_id)

        except ValueError:
            raise
        except PyMongoError as e:
            raise RuntimeError(f"Database error during registration: {str(e)}")

    # ---------------------------------------------------------
    # 🔓 LOGIN (renamed to match main.py's authenticate_user)
    # ---------------------------------------------------------
    def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        try:
            email = email.lower().strip()

            user = self.collection.find_one({"email": email})
            if not user:
                return None

            if not verify_password(password, user.get("password_hash", "")):
                return None

            return self._sanitize(user)

        except PyMongoError as e:
            raise RuntimeError(f"Database error during login: {str(e)}")

    def logout_user(self, user_id: str) -> bool:
        # No processing needed (stateless JWT)
        print(f"User {user_id} logged out.")
        return True

    # ---------------------------------------------------------
    # 🔁 REFRESH TOKEN
    # ---------------------------------------------------------
    def refresh_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            new_payload = {
                "user_id": payload["user_id"],
                "exp": datetime.utcnow() + timedelta(minutes=30)
            }

            return jwt.encode(new_payload, SECRET_KEY, algorithm=ALGORITHM)

        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    # ---------------------------------------------------------
    # 📧 EMAIL VERIFICATION
    # ---------------------------------------------------------
    def verify_email(self, token: str) -> bool:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = self._to_objectid(payload["user_id"], "user_id")

            res = self.collection.update_one(
                {"_id": user_id},
                {"$set": {"is_verified": True}}
            )
            return res.modified_count > 0

        except jwt.InvalidTokenError:
            raise ValueError("Invalid email verification token")
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    def resend_verification(self, email: str) -> bool:
        print(f"Verification email resent to {email}")
        return True

    # ---------------------------------------------------------
    # 🔑 PASSWORD RESET
    # ---------------------------------------------------------
    def forgot_password(self, email: str) -> bool:
        email = email.lower().strip()

        reset_token = jwt.encode(
            {"email": email, "exp": datetime.utcnow() + timedelta(minutes=15)},
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        print(f"Password reset link sent to {email} with token {reset_token}.")
        return True

    def reset_password(self, token: str, new_password: str) -> bool:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload["email"].lower().strip()

            res = self.collection.update_one(
                {"email": email},
                {"$set": {"password_hash": hash_password(new_password)}}
            )
            return res.modified_count > 0

        except jwt.InvalidTokenError:
            raise ValueError("Invalid password reset token")
        except PyMongoError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    # ---------------------------------------------------------
    # 👤 PROFILE MANAGEMENT
    # ---------------------------------------------------------
    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        try:
            oid = self._to_objectid(user_id, "user_id")
            user = self.collection.find_one({"_id": oid})
            return self._sanitize(user)
        except (ValueError, PyMongoError):
            return None

    def get_user_by_email(self, email: str) -> Optional[dict]:
        try:
            email = email.lower().strip()
            user = self.collection.find_one({"email": email})
            return self._sanitize(user)
        except PyMongoError:
            return None

    def update_user_profile(self, user_id: str, fields: dict) -> bool:
        try:
            oid = self._to_objectid(user_id, "user_id")
            fields["updated_at"] = datetime.utcnow()
            res = self.collection.update_one({"_id": oid}, {"$set": fields})
            return res.modified_count > 0
        except (ValueError, PyMongoError):
            return False

    def update_avatar(self, user_id: str, avatar_url: str) -> bool:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one({"_id": oid}, {"$set": {"avatar_url": avatar_url}})
            return res.modified_count > 0
        except (ValueError, PyMongoError):
            return False

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        try:
            oid = self._to_objectid(user_id, "user_id")
            user = self.collection.find_one({"_id": oid})

            if not user:
                return False
            if not verify_password(old_password, user.get("password_hash", "")):
                return False

            new_hash = hash_password(new_password)
            res = self.collection.update_one({"_id": oid}, {"$set": {"password_hash": new_hash}})
            return res.modified_count > 0

        except (ValueError, PyMongoError):
            return False

    def deactivate_account(self, user_id: str) -> bool:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one({"_id": oid}, {"$set": {"is_active": False}})
            return res.modified_count > 0
        except (ValueError, PyMongoError):
            return False

    def activate_account(self, user_id: str) -> bool:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one({"_id": oid}, {"$set": {"is_active": True}})
            return res.modified_count > 0
        except (ValueError, PyMongoError):
            return False

    # ---------------------------------------------------------
    # ⭐ FREELANCER SPECIFIC
    # ---------------------------------------------------------
    def add_skill(self, user_id: str, skill: str) -> bool:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one({"_id": oid}, {"$addToSet": {"skills": skill}})
            return res.modified_count > 0
        except (ValueError, PyMongoError):
            return False

    def remove_skill(self, user_id: str, skill: str) -> bool:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one({"_id": oid}, {"$pull": {"skills": skill}})
            return res.modified_count > 0
        except (ValueError, PyMongoError):
            return False

    def update_skills(self, user_id: str, skills_list: List[str]) -> bool:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one({"_id": oid}, {"$set": {"skills": skills_list}})
            return res.modified_count > 0
        except (ValueError, PyMongoError):
            return False

    def update_hourly_rate(self, user_id: str, rate: float) -> bool:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one({"_id": oid}, {"$set": {"hourly_rate": rate}})
            return res.modified_count > 0
        except (ValueError, PyMongoError):
            return False

    def update_freelancer_stats(self, user_id: str, stats: Dict) -> bool:
        try:
            oid = self._to_objectid(user_id, "user_id")
            res = self.collection.update_one({"_id": oid}, {"$set": {"stats": stats}})
            return res.modified_count > 0
        except (ValueError, PyMongoError):
            return False

    # ---------------------------------------------------------
    # 🔍 SEARCH & LISTING
    # ---------------------------------------------------------
    def search_users(self, query: str, filters: dict = {}, pagination: dict = {}) -> List[dict]:
        try:
            q = {"$text": {"$search": query}} if query else {}
            q.update(filters)

            cursor = self.collection.find(q)\
                .skip(pagination.get("skip", 0))\
                .limit(pagination.get("limit", 10))

            return [self._sanitize(u) for u in cursor]

        except PyMongoError as e:
            raise RuntimeError(f"Database error during search: {str(e)}")

    def list_freelancers(self, filters: dict = {}) -> List[dict]:
        try:
            query = {"role": "freelancer"}
            query.update(filters)

            cursor = self.collection.find(query)
            return [self._sanitize(u) for u in cursor]

        except PyMongoError as e:
            raise RuntimeError(f"Database error fetching freelancers: {str(e)}")

    def list_clients(self, filters: dict = {}) -> List[dict]:
        try:
            query = {"role": "client"}
            query.update(filters)

            cursor = self.collection.find(query)
            return [self._sanitize(u) for u in cursor]

        except PyMongoError as e:
            raise RuntimeError(f"Database error fetching clients: {str(e)}")
