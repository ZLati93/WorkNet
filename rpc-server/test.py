import xmlrpc.client

def test_server():
    print("Test du serveur XML-RPC...")
    
    try:
        # Connect to server
        server = xmlrpc.client.ServerProxy("http://localhost:8000")
        print("Connexion au serveur réussie")
        
        # Test introspection
        print("\nTest des méthodes disponibles...")
        methods = server.system.listMethods()
        print(f"Méthodes disponibles: {len(methods)}")
        
        # Vérifier nos méthodes
        user_methods = [m for m in methods if m.startswith('users.')]
        print(f"Méthodes users: {user_methods}")
        
        if 'users.create_user' not in methods:
            print("ERREUR: users.create_user n'est pas disponible")
            return
        
        print("\nTest de création d'utilisateur...")
        # Create a user
        user_id = server.users.create_user({
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
            "role": "freelancer",
            "full_name": "Test User"
        })
        print(f"Utilisateur créé avec ID: {user_id}")

        print("\nTest de récupération d'utilisateur...")
        # Get user
        user = server.users.get_user(user_id)
        print(f"Données utilisateur: {user}")

        print("\n[SUCCESS] Tous les tests réussis!")

    except xmlrpc.client.Fault as e:
        print(f"ERREUR XML-RPC: {e}")
    except ConnectionError as e:
        print(f"ERREUR de connexion: {e}")
        print("Assurez-vous que le serveur est démarré sur le port 8000")
    except Exception as e:
        print(f"ERREUR inattendue: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_server()