import hashlib
from datetime import datetime
from bson.objectid import ObjectId

class UsersService:
    def __init__(self, db):
        self.db = db
        self.collection = db["users"]

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, user_data):
        # Validate required fields
        required_fields = ["email", "username", "password", "role", "full_name"]
        for field in required_fields:
            if field not in user_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check if email or username already exists
        if self.collection.find_one({"email": user_data["email"]}):
            raise ValueError("Email already exists")
        if self.collection.find_one({"username": user_data["username"]}):
            raise ValueError("Username already exists")
        
        # Hash password
        user_data["password_hash"] = self.hash_password(user_data.pop("password"))
        
        # Add timestamps
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        user_data["is_active"] = True
        user_data["is_verified"] = False
        
        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)

    def get_user(self, user_id):
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
            return user
        return None

    def get_user_by_email(self, email):
        user = self.collection.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
            return user
        return None

    def update_user(self, user_id, update_data):
        update_data["updated_at"] = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_user(self, user_id):
        result = self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    def authenticate_user(self, email, password):
        user = self.collection.find_one({"email": email})
        if user and user["password_hash"] == self.hash_password(password):
            user["_id"] = str(user["_id"])
            return user
        return None

    def get_freelancers(self, limit=10, skip=0):
        freelancers = list(self.collection.find(
            {"role": "freelancer", "is_active": True}
        ).skip(skip).limit(limit))
        for f in freelancers:
            f["_id"] = str(f["_id"])
        return freelancers

    def search_freelancers(self, skills=None, country=None, rating_min=None):
        query = {"role": "freelancer", "is_active": True}
        if skills:
            query["skills"] = {"$in": skills}
        if country:
            query["country"] = country
        if rating_min:
            query["rating"] = {"$gte": rating_min}
        
        freelancers = list(self.collection.find(query))
        for f in freelancers:
            f["_id"] = str(f["_id"])
        return freelancers