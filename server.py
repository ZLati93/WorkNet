# serveur.py
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any

from dotenv import load_dotenv
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from pymongo import MongoClient
from bson.objectid import ObjectId
from jose import jwt

# ------------------------ LOAD ENV ------------------------
load_dotenv()

MONGO_URI = os.getenv("MONGODB_ATLAS_URL")
DB_NAME = os.getenv("DB_NAME", "WorkNetBD")
RPC_HOST = os.getenv("RPC_HOST", "0.0.0.0")
RPC_PORT = int(os.getenv("RPC_PORT", 8000))

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGER_LA_CLE")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ------------------------ ERROR LOGGER ---------------------
def log_error(msg: str):
    print(f"[ERROR] {msg}")
    traceback.print_exc()


# ------------------------ DATABASE CONNECTION ------------------------
db = None
try:
    if not MONGO_URI:
        raise ValueError("MONGO_URI non défini dans le fichier .env")

    print("[INFO] Connexion à MongoDB ...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[DB_NAME]
    print(f"[SUCCESS] MongoDB connecté: {DB_NAME}")

except Exception as e:
    log_error(f"Connexion MongoDB impossible : {e}")
    db = None
    print("[WARNING] Mode TEST activé (services factices)")


# ------------------------ IMPORT SERVICES ------------------------
services_available = False

try:
    from services.users_service import UsersServiceRPC as RealUsersService
    from services.gigs_service import GigsService as RealGigsService
    from services.ordres_service import OrdersService as RealOrdersService
    from services.categories_service import CategoriesService as RealCategoriesService
    from services.reviews_service import ReviewsService as RealReviewsService
    from services.messages_service import MessagesService as RealMessagesService
    from services.payments_service import PaymentsService as RealPaymentsService
    from services.notifications_service import NotificationsService as RealNotificationsService
    from services.favorites_service import FavoritesService as RealFavoritesService
    from services.complaints_service import ComplaintsService as RealComplaintsService

    services_available = True
except Exception as e:
    print("[WARNING] Impossible d'importer les services réels.")
    log_error(e)


# ------------------------ JWT FUNCTIONS ------------------------
def create_access_token(data: Dict[str, Any], expires_delta=None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except Exception:
        raise ValueError("Invalid token")


# ------------------------ FALLBACK SERVICE ------------------------
class TestService:
    def __init__(self, name):
        self.name = name

    def ping(self):
        return f"{self.name} service OK (test mode)"


# ------------------------ INITIALISE SERVICES ------------------------
if services_available and db is not None:
    try:
        users = RealUsersService(db)
        gigs = RealGigsService(db)
        orders = RealOrdersService(db)
        categories = RealCategoriesService(db)
        reviews = RealReviewsService(db)
        messages = RealMessagesService(db)
        payments = RealPaymentsService(db)
        notifications = RealNotificationsService(db)
        favorites = RealFavoritesService(db)
        complaints = RealComplaintsService(db)

        print("[INFO] Services réels chargés.")
    except Exception as e:
        log_error("Erreur d'initialisation des services réels — Passage en mode test")
        users = TestService("users")
        gigs = TestService("gigs")
        orders = TestService("orders")
        categories = TestService("categories")
        reviews = TestService("reviews")
        messages = TestService("messages")
        payments = TestService("payments")
        notifications = TestService("notifications")
        favorites = TestService("favorites")
        complaints = TestService("complaints")

else:
    users = TestService("users")
    gigs = TestService("gigs")
    orders = TestService("orders")
    categories = TestService("categories")
    reviews = TestService("reviews")
    messages = TestService("messages")
    payments = TestService("payments")
    notifications = TestService("notifications")
    favorites = TestService("favorites")
    complaints = TestService("complaints")


# ------------------------ XML-RPC SERVER ------------------------
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2",)


try:
    server = SimpleXMLRPCServer(
        (RPC_HOST, RPC_PORT),
        requestHandler=RequestHandler,
        allow_none=True,
        logRequests=True,
    )
    server.register_introspection_functions()
    print(f"[SUCCESS] Serveur RPC lancé sur {RPC_HOST}:{RPC_PORT}")
except Exception as e:
    log_error("Impossible de démarrer le serveur RPC")
    sys.exit(1)


# ------------------------ REGISTER SERVICE METHODS ------------------------
def register_service(namespace: str, service_obj):
    for attr in dir(service_obj):
        if not attr.startswith("_"):
            fn = getattr(service_obj, attr)
            if callable(fn):
                server.register_function(fn, f"{namespace}.{attr}")
                print(f"[RPC] Méthode enregistrée : {namespace}.{attr}")


register_service("users", users)
register_service("gigs", gigs)
register_service("orders", orders)
register_service("categories", categories)
register_service("reviews", reviews)
register_service("messages", messages)
register_service("payments", payments)
register_service("notifications", notifications)
register_service("favorites", favorites)
register_service("complaints", complaints)


# ------------------------ START SERVER ------------------------
print("[START] Serveur RPC prêt. Ctrl+C pour arrêter.")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n[STOP] Serveur arrêté par l'utilisateur.")
except Exception as e:
    log_error(f"Erreur serveur: {e}")


