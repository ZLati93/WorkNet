import xmlrpc.client
from pprint import pprint

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
RPC_URL = "http://localhost:8000"
rpc = xmlrpc.client.ServerProxy(RPC_URL, allow_none=True)

TEST_USER_ID = "64e1f2ab1234567890abcdef"
TEST_FREELANCER_ID = "64e1f2ab1234567890abcdef"
TEST_CATEGORY_ID = "64e1f2ab1234567890abcdea"
TEST_ORDER_ID = "64e1f2ab1234567890abcdeb"

print("[INFO] Début des tests fonctionnels RPC...")
print("---------------------------------------------------------\n")

# ---------------- USERS ----------------
print("=== TEST USERS ===")
try:
    res = rpc.users.get_user_by_id(TEST_USER_ID)
    pprint(res)
except Exception as e:
    print("Erreur Users:", e)

# ---------------- GIGS ----------------
print("\n=== TEST GIGS ===")
gig_data = {
    "category_id": TEST_CATEGORY_ID,
    "title": "Gig Test RPC",
    "description": "Description test RPC",
    "price": 50
}
res = rpc.gigs.create_gig(TEST_FREELANCER_ID, gig_data)
pprint(res)
GIG_ID = res.get("gig_id")

res = rpc.gigs.get_gig_by_id(GIG_ID)
pprint(res)

update_data = {"price": 75, "title": "Gig Modifié RPC"}
res = rpc.gigs.update_gig(GIG_ID, TEST_FREELANCER_ID, update_data)
pprint(res)

# ---------------- ORDERS ----------------
print("\n=== TEST ORDERS ===")
order_data = {
    "client_id": TEST_USER_ID,
    "freelancer_id": TEST_FREELANCER_ID,
    "gig_id": GIG_ID,
    "status": "pending",
    "price": 75,
    "quantity": 1  # ⚠ Ajouté pour valider la création
}
res = rpc.orders.create_order(order_data)
pprint(res)
ORDER_ID = res.get("order_id") or TEST_ORDER_ID

res = rpc.orders.get_order(ORDER_ID)
pprint(res)

# ---------------- CATEGORIES ----------------
print("\n=== TEST CATEGORIES ===")
cat_data = {
    "name": "Catégorie Test RPC",
    "description": "Desc test",
    "icon_url": "https://example.com/icon.png",  # ⚠ Obligatoire pour le schéma
    "sort_order": 1,
    "is_active": True
}
res = rpc.categories.create_category(cat_data)
pprint(res)
CAT_ID = res.get("category_id")

if CAT_ID:
    res = rpc.categories.get_category_by_id(CAT_ID)
    pprint(res)

    update_cat = {"description": "Desc modifiée RPC"}
    res = rpc.categories.update_category(CAT_ID, update_cat)
    pprint(res)

# ---------------- MESSAGES ----------------
print("\n=== TEST MESSAGES ===")
msg = rpc.messages.send_message(
    order_id=ORDER_ID,
    sender_id=TEST_USER_ID,
    receiver_id=TEST_FREELANCER_ID,
    content="Message test RPC"
)
pprint(msg)
MSG_ID = msg.get("message_id")

res = rpc.messages.list_conversations(TEST_USER_ID)
pprint(res)

res = rpc.messages.mark_as_read(MSG_ID)
pprint(res)

# ---------------- FAVORITES ----------------
print("\n=== TEST FAVORITES ===")
res = rpc.favorites.add_favorite(TEST_USER_ID, GIG_ID)
pprint(res)

res = rpc.favorites.list_favorites(TEST_USER_ID)
pprint(res)

res = rpc.favorites.remove_favorite(TEST_USER_ID, GIG_ID)
pprint(res)

# ---------------- NOTIFICATIONS ----------------
print("\n=== TEST NOTIFICATIONS ===")
notif = rpc.notifications.send_notification(
    TEST_USER_ID,
    "info",
    "Titre test notification",
    "Ceci est un test de notification RPC"
)
pprint(notif)
NOTIF_ID = notif.get("notification_id")

res = rpc.notifications.list_user_notifications(TEST_USER_ID)
pprint(res)

res = rpc.notifications.mark_notification_read(NOTIF_ID)
pprint(res)

print("\n[INFO] Tous les tests RPC sont terminés.")
