import xmlrpc.client
import pprint

# Connexion au serveur RPC
rpc = xmlrpc.client.ServerProxy("http://localhost:8000")
pp = pprint.PrettyPrinter(indent=2)

# -----------------------------
# 1️⃣ Users
# -----------------------------
print("=== Users ===")

# Inscription
new_user = rpc.users.register_user(
    "alice123",             # username
    "alice@example.com",    # email
    "password123",          # password
    "Alice Test"            # full_name
)
pp.pprint(new_user)
user_id = new_user.get("user_id")

# Authentification
auth = rpc.users.authenticate_user("alice@example.com", "password123")
pp.pprint(auth)

# Mise à jour du profil
update = rpc.users.update_user_profile(user_id, {"bio": "Je suis freelance."})
pp.pprint(update)

# Activation / désactivation
rpc.users.deactivate_account(user_id)
rpc.users.activate_account(user_id)

# Ajouter / supprimer compétence
rpc.users.add_skill(user_id, "Python")
rpc.users.remove_skill(user_id, "Python")

# -----------------------------
# 2️⃣ Gigs
# -----------------------------
print("\n=== Gigs ===")

gig_data = {
    "title": "Développement Python",
    "description": "Création de scripts Python",
    "freelancer_id": user_id,
    "category_id": "64f123456789abcdef012345",  # exemple
    "price": 100
}
gig = rpc.gigs.create_gig(gig_data)
pp.pprint(gig)
gig_id = gig.get("gig_id")

# Mise à jour
rpc.gigs.update_gig(gig_id, {"price": 120})

# Publier / pause
rpc.gigs.publish_gig(gig_id)
rpc.gigs.pause_gig(gig_id)

# Recherche
gigs_found = rpc.gigs.search_gigs("Python")
pp.pprint(gigs_found)

# Listes
pp.pprint(rpc.gigs.list_gigs_by_category("64f123456789abcdef012345"))
pp.pprint(rpc.gigs.list_gigs_by_freelancer(user_id))
pp.pprint(rpc.gigs.list_featured_gigs())
pp.pprint(rpc.gigs.list_recent_gigs())

# -----------------------------
# 3️⃣ Orders
# -----------------------------
print("\n=== Orders ===")

order_data = {
    "gig_id": gig_id,
    "client_id": user_id,
    "freelancer_id": user_id,
    "details": "Commande test",
    "price": 120
}
order = rpc.orders.create_order(order_data)
pp.pprint(order)
order_id = order.get("order_id")

rpc.orders.start_order(order_id)
rpc.orders.deliver_order(order_id, "Livraison test")
rpc.orders.complete_order(order_id)
rpc.orders.cancel_order(order_id)

# -----------------------------
# 4️⃣ Categories
# -----------------------------
print("\n=== Categories ===")

cat_id = rpc.categories.create_category("Développement", "Catégorie test")
pp.pprint(cat_id)

rpc.categories.update_category(cat_id, {"description": "MAJ description"})
pp.pprint(rpc.categories.get_category(cat_id))
pp.pprint(rpc.categories.list_categories())
pp.pprint(rpc.categories.list_active_categories())
pp.pprint(rpc.categories.list_parent_categories())
pp.pprint(rpc.categories.list_children_categories(cat_id))

rpc.categories.delete_category(cat_id)

# -----------------------------
# 5️⃣ Messages
# -----------------------------
print("\n=== Messages ===")

msg = rpc.messages.send_message(order_id, user_id, user_id, "Bonjour, test message")
pp.pprint(msg)
rpc.messages.mark_message_read(msg.get("message_id"))
pp.pprint(rpc.messages.get_conversation(order_id))
pp.pprint(rpc.messages.list_messages_by_user(user_id))
pp.pprint(rpc.messages.count_unread_messages(user_id))

# -----------------------------
# 6️⃣ Notifications
# -----------------------------
print("\n=== Notifications ===")

notif = rpc.notifications.send_notification(user_id, "info", "Titre test", "Message test")
pp.pprint(notif)
notif_id = notif.get("notification_id")
rpc.notifications.mark_notification_read(notif_id)
pp.pprint(rpc.notifications.list_user_notifications(user_id))
rpc.notifications.mark_all_notifications_read(user_id)
rpc.notifications.delete_notification(notif_id)

# -----------------------------
# 7️⃣ Favorites
# -----------------------------
print("\n=== Favorites ===")

fav = rpc.favorites.add_to_favorites(user_id, gig_id)
pp.pprint(fav)
pp.pprint(rpc.favorites.is_favorite(user_id, gig_id))
pp.pprint(rpc.favorites.list_favorites(user_id))
rpc.favorites.remove_from_favorites(user_id, gig_id)

# -----------------------------
# 8️⃣ Complaints
# -----------------------------
print("\n=== Complaints ===")

complaint_id = rpc.complaints.create_complaint(user_id, user_id, "user", "Spam", "Test plainte")
pp.pprint(complaint_id)
pp.pprint(rpc.complaints.get_complaint(complaint_id))
pp.pprint(rpc.complaints.list_complaints_by_user(user_id))
pp.pprint(rpc.complaints.list_pending_complaints())
rpc.complaints.update_complaint_status(complaint_id, "resolved", "Résolu par admin")
rpc.complaints.delete_complaint(complaint_id)

# -----------------------------
# 9️⃣ Reviews & Payments
# -----------------------------
print("\n=== Reviews & Payments ===")

# Exemples (à adapter selon ton serveur)
# review = rpc.reviews.create_review(user_id, "target_id", 5, "Super travail")
# payment = rpc.payments.create_payment(order_id, user_id, 120)

print("✅ Tests RPC terminés.")

