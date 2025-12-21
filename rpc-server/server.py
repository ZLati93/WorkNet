from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import pymongo
import sys
import traceback
import ssl

# Fonction pour logger les erreurs
def log_error(message):
    print(f"[ERROR] {message}")
    traceback.print_exc()

# Tentative d'importation des services avec gestion d'erreur détaillée
print("[INFO] Importation des services...")
try:
    from services.users_service import UsersService
    from services.gigs_service import GigsService
    from services.ordres_service import OrdresService
    print("[SUCCESS] Services importés avec succès")
    services_imported = True
except ImportError as e:
    log_error(f"Erreur d'importation des services: {e}")
    print("[WARNING] Vérifiez que les fichiers services/*.py existent et n'ont pas d'erreurs de syntaxe")
    UsersService = None
    GigsService = None
    OrdresService = None
    services_imported = False
except Exception as e:
    log_error(f"Erreur inattendue lors de l'importation: {e}")
    services_imported = False

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# MongoDB connection avec fallback complet
print("[INFO] Initialisation de la connexion MongoDB...")
db = None
connection_mode = "none"

if services_imported:
    # Essayer d'abord MongoDB Atlas
    try:
        print("[INFO] Tentative de connexion à MongoDB Atlas...")
        # Remplacez <db_password> par votre mot de passe réel
        atlas_url = "mongodb+srv://worknet_user:<db_password>@cluster0.l7wlpyp.mongodb.net/worknet?retryWrites=true&w=majority"
        
        # Configuration SSL pour éviter les problèmes TLS
        client = pymongo.MongoClient(
            atlas_url,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
            socketTimeoutMS=15000,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE  # Désactiver la vérification stricte des certificats
        )
        
        # Test the connection
        client.admin.command('ping')
        print("[SUCCESS] Connexion MongoDB Atlas réussie!")
        
        db = client["worknet"]
        connection_mode = "atlas"
        
        # Vérifier les collections
        collections = db.list_collection_names()
        print(f"[INFO] Collections disponibles: {collections}")
        
    except Exception as atlas_error:
        print(f"[WARNING] Échec de connexion Atlas: {str(atlas_error)[:100]}...")
        print("[INFO] Tentative de connexion à MongoDB local...")
        
        # Fallback vers MongoDB local
        try:
            client = pymongo.MongoClient(
                "mongodb://localhost:27017/",
                serverSelectionTimeoutMS=5000
            )
            client.admin.command('ping')
            print("[SUCCESS] Connexion MongoDB local réussie!")
            db = client["worknet"]
            connection_mode = "local"
            
            # Créer les collections si elles n'existent pas
            required_collections = ['users', 'gigs', 'orders', 'reviews', 'messages', 'payments', 'favorites', 'notifications']
            existing_collections = db.list_collection_names()
            for coll in required_collections:
                if coll not in existing_collections:
                    db.create_collection(coll)
                    print(f"[INFO] Collection '{coll}' créée")
            
        except Exception as local_error:
            print(f"[WARNING] Échec de connexion local: {str(local_error)[:100]}...")
            print("[INFO] Activation du mode test sans base de données")
            connection_mode = "test"
            db = None

else:
    print("[WARNING] Services non importés - mode test activé")
    connection_mode = "test"

# Create server
print("[INFO] Création du serveur XML-RPC...")
try:
    server = SimpleXMLRPCServer(("localhost", 8000), requestHandler=RequestHandler, allow_none=True)
    server.register_introspection_functions()
    print("[SUCCESS] Serveur XML-RPC créé")
except Exception as e:
    log_error(f"Erreur lors de la création du serveur: {e}")
    sys.exit(1)

# Register services
services_registered = False

if connection_mode in ["atlas", "local"] and services_imported:
    # Mode normal avec base de données
    try:
        print("[INFO] Initialisation des instances de service...")
        users_service = UsersService(db)
        gigs_service = GigsService(db)
        ordres_service = OrdresService(db)
        print("[SUCCESS] Instances de service créées")
        
        print("[INFO] Enregistrement des services...")
        server.register_instance(users_service, "users")
        server.register_instance(gigs_service, "gigs")
        server.register_instance(ordres_service, "ordres")
        print("[SUCCESS] Tous les services enregistrés!")
        services_registered = True
        
    except Exception as e:
        log_error(f"Erreur lors de l'enregistrement des services: {e}")
        print("[WARNING] Basculement en mode test")
        connection_mode = "test"

if connection_mode == "test" or not services_registered:
    # Mode test
    print("[INFO] Activation du mode test...")
    
    class TestUsersService:
        def create_user(self, data):
            print(f"[TEST] create_user appelé avec: {data}")
            return "test_user_id_123"
        
        def get_user(self, user_id):
            print(f"[TEST] get_user appelé avec ID: {user_id}")
            return {
                "_id": user_id,
                "email": "test@example.com",
                "username": "testuser",
                "role": "freelancer",
                "full_name": "Test User",
                "created_at": "2024-01-01T00:00:00Z"
            }
        
        def authenticate_user(self, email, password):
            if email == "test@example.com" and password == "password123":
                return self.get_user("test_user_id_123")
            return None
    
    class TestGigsService:
        def create_gig(self, data):
            print(f"[TEST] create_gig appelé avec: {data}")
            return "test_gig_id_456"
        
        def get_gig(self, gig_id):
            print(f"[TEST] get_gig appelé avec ID: {gig_id}")
            return {
                "_id": gig_id,
                "title": "Test Gig",
                "description": "This is a test gig",
                "base_price": 100.0,
                "status": "active"
            }
    
    class TestOrdresService:
        def create_order(self, data):
            print(f"[TEST] create_order appelé avec: {data}")
            return "test_order_id_789"
        
        def get_order(self, order_id):
            print(f"[TEST] get_order appelé avec ID: {order_id}")
            return {
                "_id": order_id,
                "title": "Test Order",
                "amount": 100.0,
                "status": "pending"
            }
    
    server.register_instance(TestUsersService(), "users")
    server.register_instance(TestGigsService(), "gigs")
    server.register_instance(TestOrdresService(), "ordres")
    print("[SUCCESS] Services de test enregistrés!")
    services_registered = True

# Afficher le statut final
print("\n" + "="*60)
print("STATUT DU SERVEUR:")
print(f"Services importés: {services_imported}")
print(f"Mode de connexion: {connection_mode}")
print(f"Base de données connectée: {db is not None}")
print(f"Services enregistrés: {services_registered}")
print("="*60)

if services_registered:
    print("[READY] Freelance RPC Server prêt sur le port 8000")
    if connection_mode == "test":
        print("[INFO] ⚠️  MODE TEST ACTIF - Les données ne seront pas persistées")
    elif connection_mode == "local":
        print("[INFO] ✅ Base de données locale utilisée")
    else:
        print("[INFO] ✅ MongoDB Atlas connecté")
else:
    print("[ERROR] Serveur non fonctionnel")
    sys.exit(1)

print("[START] Serveur en cours d'exécution... (Ctrl+C pour arrêter)")
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n[STOP] Serveur arrêté par l'utilisateur")
except Exception as e:
    log_error(f"Erreur fatale du serveur: {e}")