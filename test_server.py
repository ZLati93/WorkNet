import xmlrpc.client
import pprint

# Connexion au serveur RPC
rpc = xmlrpc.client.ServerProxy("http://localhost:8000")
pp = pprint.PrettyPrinter(indent=2)

# -----------------------------
# 1️⃣ Users
# -----------------------------
print("=== Users ===")

# Inscription : envoyer un seul dictionnaire
new_user = rpc.users.register_user({
    "alice123",
    "alice@example.com",
    "password123",
    "Alice Test"
})
pp.pprint(new_user)

user_id = new_user.get("user_id")

# Authentification
auth = rpc.users.authenticate_user({
    "alice@example.com",
    "password123"
})
pp.pprint(auth)

# Mise à jour du profil
update = rpc.users.update_user_profile(user_id, {
    "bio": "Je suis freelance."
})
pp.pprint(update)

# Activation / désactivation
rpc.users.deactivate_account(user_id)
rpc.users.activate_account(user_id)

# Ajouter / supprimer compétence
rpc.users.add_skill(user_id, "Python")
rpc.users.remove_skill(user_id, "Python")

