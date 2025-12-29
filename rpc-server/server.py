from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import traceback
import sys

load_dotenv()

MONGO_URL = os.getenv("MONGODB_ATLAS_URL")
DB_NAME = os.getenv("DB_NAME", "worknet")
RPC_HOST = os.getenv("RPC_HOST", "127.0.0.1")
RPC_PORT = int(os.getenv("RPC_PORT", 8000))

def log_error(msg: str):
    print(f"[ERROR] {msg}")
    traceback.print_exc()

print("[INFO] Connexion à MongoDB...")
db = None
try:
    if not MONGO_URL:
        raise ValueError("MONGODB_ATLAS_URL non défini dans .env")
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    db = client[DB_NAME]
    print("[SUCCESS] MongoDB connecté:", DB_NAME)
except Exception as e:
    log_error(f"Impossible de connecter MongoDB: {e}")
    print("[WARNING] Mode TEST (services factices).")

try:
    from services.users_service import UsersService
    from services.gigs_service import GigsService
    from services.ordres_service import OrdersService
    from services.categories_service import CategoriesService
    from services.reviews_service import ReviewsService
    from services.messages_service import MessagesService
    from services.payments_service import PaymentsService
    from services.notifications_service import NotificationsService
    services_available = True
except Exception as e:
    print("[WARNING] Import services failed:", e)
    services_available = False

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2",)

print("[INFO] Création serveur RPC...")
try:
    server = SimpleXMLRPCServer((RPC_HOST, RPC_PORT), requestHandler=RequestHandler, allow_none=True)
    server.register_introspection_functions()
    print(f"[SUCCESS] Serveur RPC démarré sur {RPC_HOST}:{RPC_PORT}")
except Exception as e:
    log_error(f"Erreur création serveur: {e}")
    sys.exit(1)

def register_service(namespace: str, service_obj):
    for attr in dir(service_obj):
        if attr.startswith("_"):
            continue
        method = getattr(service_obj, attr)
        if callable(method):
            server.register_function(method, f"{namespace}.{attr}")

if services_available and db is not None:
    users = UsersService(db)
    gigs = GigsService(db)
    orders = OrdersService(db)
    categories = CategoriesService(db)
    reviews = ReviewsService(db)
    messages = MessagesService(db)
    payments = PaymentsService(db)
    notifications = NotificationsService(db)
else:
    class TestService:
        def __init__(self, name):
            self._name = name
        def ping(self):
            return f"{self._name} ok"
    users = TestService("users")
    gigs = TestService("gigs")
    orders = TestService("orders")
    categories = TestService("categories")
    reviews = TestService("reviews")
    messages = TestService("messages")
    payments = TestService("payments")
    notifications = TestService("notifications")

register_service("users", users)
register_service("gigs", gigs)
register_service("orders", orders)
register_service("categories", categories)
register_service("reviews", reviews)
register_service("messages", messages)
register_service("payments", payments)
register_service("notifications", notifications)

print("[START] Serveur prêt. Ctrl+C pour arrêter.")
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n[STOP] Arrêt par l'utilisateur.")
except Exception as e:
    log_error(f"Erreur serveur: {e}")
