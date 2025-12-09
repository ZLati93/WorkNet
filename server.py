import os
from typing import Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- Imports FastAPI & Sécurité ---
from fastapi import FastAPI, HTTPException, Body, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field

# --- Imports Database ---
from pymongo import MongoClient

# ---- Import Services ----
from services.users_service import UsersService
from services.gigs_service import GigsService
from services.ordres_service import OrdersService 
from services.reviews_service import ReviewsService
from services.messages_service import MessagesService
from services.notifications_service import NotificationsService
from services.payments_service import PaymentsService
from services.complaints_service import ComplaintsService
from services.favorites_service import FavoritesService 

# -----------------------------------------
# 🔑 SCHÉMAS PYDANTIC
# -----------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenData(BaseModel):
    user_id: str | None = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str

class GigCreate(BaseModel):
    title: str
    description: str
    price: float
    seller_id: str

class OrderCreate(BaseModel):
    gig_id: str
    buyer_id: str

class ReviewCreate(BaseModel):
    order_id: str
    reviewer_id: str
    rating: int
    comment: str

class MessageCreate(BaseModel):
    order_id: str
    sender_id: str
    receiver_id: str
    content: str

class PaymentCreate(BaseModel):
    user_id: str
    amount: float
    method: str

class ComplaintCreate(BaseModel):
    complaint_user_id: str
    order_id: str
    content: str

class FavoriteCreate(BaseModel):
    user_id: str
    gig_id: str

# -----------------------------------------
# ⚙️ CONFIGURATION & SÉCURITÉ JWT
# -----------------------------------------

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "clE_sEcrEte_TROP_FAible_a_changer")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
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
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed")

@app.post("/auth/login", response_model=TokenResponse)
def login_user(credentials: UserLogin):
    user = users_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login credentials")
    
    access_token = create_access_token(data={"user_id": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer", "user_id": str(user["_id"])}

@app.post("/auth/logout/{user_id}")
def logout(user_id: str, current_user_id: str = Depends(get_current_user_id)):
    if user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot logout another user")
    users_service.logout_user(user_id)
    return {"status": "success"}

# -----------------------------------------
# 👤 USERS
# -----------------------------------------

@app.get("/users/me")
def get_current_user(current_user_id: str = Depends(get_current_user_id)):
    user = users_service.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.pop("password_hash", None)
    return user

@app.put("/users/{user_id}")
def update_user(user_id: str, data: Dict[str, Any] = Body(...), current_user_id: str = Depends(get_current_user_id)):
    if user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    try:
        ok = users_service.update_user_profile(user_id, data)
        if ok:
            return {"status": "updated"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Update failed")
    except Exception as e:
        print(f"Update error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad data")

# -----------------------------------------
# 🎨 GIGS
# -----------------------------------------

@app.post("/gigs")
def create_gig(gig: GigCreate, current_user_id: str = Depends(get_current_user_id)):
    if gig.seller_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    try:
        gig_id = gigs_service.create_gig(gig.model_dump())
        return {"status": "success", "gig_id": gig_id}
    except Exception as e:
        print(f"Gig creation error: {e}")
        raise HTTPException(status_code=400, detail="Creation failed")

@app.get("/gigs/{gig_id}")
def get_gig(gig_id: str):
    gig = gigs_service.get_gig(gig_id)
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")
    return gig

# -----------------------------------------
# 📦 ORDERS
# -----------------------------------------

@app.post("/orders")
def create_order(order: OrderCreate, current_user_id: str = Depends(get_current_user_id)):
    if order.buyer_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        order_id = orders_service.create_order(order.model_dump())
        return {"status": "success", "order_id": order_id}
    except Exception as e:
        print(f"Order creation error: {e}")
        raise HTTPException(status_code=400, detail="Order creation failed")

@app.get("/orders/{order_id}")
def get_order(order_id: str, current_user_id: str = Depends(get_current_user_id)):
    order = orders_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(order.get("buyer_id")) != current_user_id and str(order.get("seller_id")) != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return order

# -----------------------------------------
# ⭐ REVIEWS
# -----------------------------------------

@app.post("/reviews")
def create_review(review: ReviewCreate, current_user_id: str = Depends(get_current_user_id)):
    if review.reviewer_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized reviewer")
    try:
        review_id = reviews_service.create_review(review.model_dump())
        return {"status": "success", "review_id": review_id}
    except Exception as e:
        print(f"Review creation error: {e}")
        raise HTTPException(status_code=400, detail="Review creation failed")

# -----------------------------------------
# 💬 MESSAGES
# -----------------------------------------

@app.post("/messages/send")
def send_message(msg: MessageCreate, current_user_id: str = Depends(get_current_user_id)):
    if msg.sender_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized sender")
    try:
        msg_id = messages_service.send_message(msg.order_id, msg.sender_id, msg.receiver_id, msg.content)
        return {"status": "sent", "message_id": msg_id}
    except Exception as e:
        print(f"Message sending error: {e}")
        raise HTTPException(status_code=400, detail="Message sending failed")

# -----------------------------------------
# 🔔 NOTIFICATIONS
# -----------------------------------------

@app.get("/notifications/{user_id}")
def list_notifications(user_id: str, current_user_id: str = Depends(get_current_user_id)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return notifications_service.list_user_notifications(user_id)

# -----------------------------------------
# 💳 PAYMENTS
# -----------------------------------------

@app.post("/payments")
def create_payment(payment: PaymentCreate, current_user_id: str = Depends(get_current_user_id)):
    if payment.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized payment")
    try:
        pid = payments_service.create_payment(payment.model_dump())
        return {"status": "success", "payment_id": pid}
    except Exception as e:
        print(f"Payment creation error: {e}")
        raise HTTPException(status_code=400, detail="Payment creation failed")

# -----------------------------------------
# 📢 COMPLAINTS
# -----------------------------------------

@app.post("/complaints")
def create_complaint(complaint: ComplaintCreate, current_user_id: str = Depends(get_current_user_id)):
    if complaint.complaint_user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        cid = complaints_service.create_complaint(complaint.model_dump())
        return {"status": "success", "complaint_id": cid}
    except Exception as e:
        print(f"Complaint creation error: {e}")
        raise HTTPException(status_code=400, detail="Complaint creation failed")

@app.get("/complaints/{user_id}")
def list_user_complaints(user_id: str, current_user_id: str = Depends(get_current_user_id)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return complaints_service.list_complaints_by_user(user_id)

# -----------------------------------------
# ⭐ FAVORITES
# -----------------------------------------

@app.post("/favorites/add")
def add_favorite(fav: FavoriteCreate, current_user_id: str = Depends(get_current_user_id)):
    if fav.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return favorites_service.add_to_favorites(fav.user_id, fav.gig_id)

@app.post("/favorites/remove")
def remove_favorite(fav: FavoriteCreate, current_user_id: str = Depends(get_current_user_id)):
    if fav.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return favorites_service.remove_from_favorites(fav.user_id, fav.gig_id)

@app.get("/favorites/{user_id}")
def list_favorites(user_id: str, current_user_id: str = Depends(get_current_user_id)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return favorites_service.list_favorites(user_id)

# -----------------------------------------
# 🏁 ROOT
# -----------------------------------------

@app.get("/")
def home():
    return {"message": "WorkNet API is running 🚀. Please authenticate for full access."}
