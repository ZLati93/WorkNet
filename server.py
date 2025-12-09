import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from pymongo import MongoClient
from bson.objectid import ObjectId
from typing import Dict, Any
import jwt
from services.users_service import UsersService
from utils.security import SECRET_KEY, ALGORITHM, hash_password, verify_password

# ---- Load env ----
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "worknet")

# ---- Database ----
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.get_database(DB_NAME)
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
<<<<<<< HEAD
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Token data is invalid",
                                headers={"WWW-Authenticate": "Bearer"})
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"})
    return user_id

# -----------------------------------------
# 🚀 INITIALISATION API
# -----------------------------------------

app = FastAPI(title="WorkNet Backend API", version="1.0")

ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:8000").split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------
# 🗄 DATABASE
# -----------------------------------------

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME=os.getenv("DB_NAME")
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database(DB_NAME)
    # Test the connection by pinging the database
    client.admin.command('ping')
    print("Connected to MongoDB Atlas successfully! 🎉")
except Exception as e:
    print(f"FATAL: Database connection failed: {e}")
    raise

# -----------------------------------------
# 🧩 SERVICES
# -----------------------------------------

users_service = UsersService(db)
gigs_service = GigsService(db)
orders_service = OrdersService(db)
reviews_service = ReviewsService(db)
messages_service = MessagesService(db)
notifications_service = NotificationsService(db)
payments_service = PaymentsService(db)
complaints_service = ComplaintsService(db)
favorites_service = FavoritesService(db)

# -----------------------------------------
# 🚦 ROUTES AUTHENTIFICATION
# -----------------------------------------

@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate):
    try:
        user_id = users_service.register_user(user_data.model_dump())
        return {"status": "success", "user_id": user_id}
=======
        if not user_id:
            raise ValueError("Invalid token")
        return user_id
>>>>>>> c4b94ab (Adaptation UsersService pour XML-RPC)
    except Exception as e:
        raise ValueError("Invalid token") from e

# ---- Users Service ----
users_service = UsersService(db)

# ---- Helper to sanitize for XML-RPC ----
def sanitize_for_rpc(user: dict) -> dict:
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

# ---- RPC Functions ----
def register(email, password, full_name):
    try:
        user_id = users_service.register_user({
            "email": email,
            "password": password,
            "full_name": full_name
        })
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        return {"error": str(e)}

def login(email, password):
    try:
        user = users_service.authenticate_user(email, password)
        if not user:
            return {"error": "Invalid credentials"}
        token = create_access_token({"user_id": user["_id"]})
        return {"access_token": token, "user_id": user["_id"]}
    except Exception as e:
        return {"error": str(e)}

def get_user_info(token):
    try:
        user_id = verify_token(token)
        user = users_service.get_user_by_id(user_id)
        if not user:
            return {"error": "User not found"}
        return sanitize_for_rpc(user)
    except Exception as e:
        return {"error": str(e)}

# ---- XML-RPC Server ----
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

server = SimpleXMLRPCServer(("0.0.0.0", 8000), requestHandler=RequestHandler, allow_none=True)
server.register_introspection_functions()

# Register RPC functions
server.register_function(register, 'register')
server.register_function(login, 'login')
server.register_function(get_user_info, 'get_user_info')

print("XML-RPC Server running on port 8000...")
server.serve_forever()
