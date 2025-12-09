import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from pymongo import MongoClient
from bson.objectid import ObjectId
from jose import jwt
from typing import Dict, Any

# ---- Load env ----
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "clE_sEcrEte_TROP_FAible_a_changer")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ---- Database ----
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.get_database("WorkNetBD")
    client.admin.command('ping')
    print("Connected to MongoDB successfully! 🎉")
except Exception as e:
    print(f"FATAL: Database connection failed: {e}")
    raise

# ---- JWT Functions ----
def create_access_token(data: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise ValueError("Invalid token")
        return user_id
    except Exception as e:
        raise ValueError("Invalid token") from e

# ---- Services ----
# Minimal UsersService example
class UsersService:
    def __init__(self, db):
        self.collection = db["users"]

    def register_user(self, email, password, full_name):
        if self.collection.find_one({"email": email}):
            return {"error": "Email already exists"}
        user = {"email": email, "password_hash": password, "full_name": full_name}
        result = self.collection.insert_one(user)
        return str(result.inserted_id)

    def authenticate_user(self, email, password):
        user = self.collection.find_one({"email": email, "password_hash": password})
        if not user:
            return None
        return str(user["_id"])

    def get_user(self, user_id):
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user.pop("password_hash", None)
        return user

users_service = UsersService(db)

# ---- RPC Functions ----

def register(email, password, full_name):
    return users_service.register_user(email, password, full_name)

def login(email, password):
    user_id = users_service.authenticate_user(email, password)
    if not user_id:
        return {"error": "Invalid credentials"}
    token = create_access_token({"user_id": user_id})
    return {"access_token": token, "user_id": user_id}

def get_user_info(token):
    try:
        user_id = verify_token(token)
        user = users_service.get_user(user_id)
        if not user:
            return {"error": "User not found"}
        return user
    except Exception as e:
        return {"error": str(e)}

# ---- XML-RPC Server ----

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

server = SimpleXMLRPCServer(("0.0.0.0", 8000), requestHandler=RequestHandler, allow_none=True)
server.register_introspection_functions()

# Register functions
server.register_function(register, 'register')
server.register_function(login, 'login')
server.register_function(get_user_info, 'get_user_info')

print("XML-RPC Server running on port 8000...")
server.serve_forever()
