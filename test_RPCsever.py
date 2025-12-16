import xmlrpc.client
from pprint import pprint

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
RPC_URL = "http://localhost:8000"
rpc = xmlrpc.client.ServerProxy(RPC_URL)

# Remplacer par des ObjectId valides de ta DB
TEST_USER_ID = "64e1f2ab1234567890abcdef"
TEST_FREELANCER_ID = "64e1f2ab1234567890abcdef"
TEST_CATEGORY_ID = "64e1f2ab1234567890abcdea"
TEST_ORDER_ID = "64e1f2ab1234567890abcdeb"

print("[INFO] Début des tests fonctionnels RPC...")
print("---------------------------------------------------------\n")

# ---------------------------------------------------------
# 1️⃣ USERS
# ---------------------------------------------------------
print("=== TEST USERS ===")
try:
    res = rpc.users.get_user_by_id(TEST_USER_ID)
    pprint(res)
except Exception as e:
    print("Erreur Users:", e)

# ---------------------------------------------------------
# 2️⃣ GIGS
# ---------------------------------------------------------
print("\n=== TEST GIGS ===")
gig_data = {
    "category_id": TEST_CATEGORY_ID,
    "title": "Gig Test RPC",
    "description": "Description test RPC",
    "price": 50
}
# ⚠ create_gig prend 2 arguments : freelancer_id et data
res = rpc.gigs.create_gig(TEST_FREELANCER_ID, gig_data)
pprint(res)
GIG_ID = res.get("gig_id")

# Get Gig
res = rpc.gigs.get_gig_by_id(GIG_ID)
pprint(res)

# Update Gig
update_data = {"price": 75, "title": "Gig Modifié RPC"}
res = rpc.gigs.update_gig(GIG_ID, TEST_FREELANCER_ID, update_data)
pprint(res)

# ---------------------------------------------------------
# 3️⃣ ORDERS
# ---------------------------------------------------------
print("\n=== TEST ORDERS ===")
order_data = {
    "client_id": TEST_USER_ID,
    "freelancer_id": TEST_FREELANCER_ID,
    "gig_id": GIG_ID,
    "status": "pending",
    "price": 75
}
res = rpc.orders.create_order(order_data)
pprint(res)
ORDER_ID = res.get("order_id") or TEST_ORDER_ID

res = rpc.orders.get_order(ORDER_ID)
pprint(res)

# ---------------------------------------------------------
# 4️⃣ CATEGORIES
# ---------------------------------------------------------
print("\n=== TEST CATEGORIES ===")
cat_data = {"name": "Catégorie Test RPC", "description": "Desc test"}
res = rpc.categories.create_category(cat_data)
pprint(res)
CAT_ID = res.get("category_id")

res = rpc.categories.get_category_by_id(CAT_ID)
pprint(res)

update_cat = {"description": "Desc modifiée RPC"}
res = rpc.categories.update_category(CAT_ID, update_cat)
pprint(res)

# ---------------------------------------------------------
# 5️⃣ MESSAGES
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 6️⃣ FAVORITES
# ---------------------------------------------------------
print("\n=== TEST FAVORITES ===")
res = rpc.favorites.add_favorite(TEST_USER_ID, GIG_ID)
pprint(res)

res = rpc.favorites.list_favorites(TEST_USER_ID)
pprint(res)

res = rpc.favorites.remove_favorite(TEST_USER_ID, GIG_ID)
pprint(res)

# ---------------------------------------------------------
# 7️⃣ NOTIFICATIONS
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 8️⃣ REVIEWS
# ---------------------------------------------------------
print("\n=== TEST REVIEWS ===")
review_data = {
    "reviewer_id": TEST_USER_ID,
    "reviewed_id": TEST_FREELANCER_ID,
    "gig_id": GIG_ID,
    "rating": 5,
    "comment": "Review test RPC"
}
res = rpc.reviews.create_review(review_data)
pprint(res)
REVIEW_ID = res.get("review_id")

res = rpc.reviews.get_review(REVIEW_ID)
pprint(res)

# ---------------------------------------------------------
# 9️⃣ PAYMENTS
# ---------------------------------------------------------
print("\n=== TEST PAYMENTS ===")
payment_data = {
    "user_id": TEST_USER_ID,
    "order_id": ORDER_ID,
    "amount": 75,
    "currency": "USD",
    "status": "pending"
}
res = rpc.payments.create_payment_intent(payment_data)
pprint(res)

# ---------------------------------------------------------
# 10️⃣ COMPLAINTS
# ---------------------------------------------------------
print("\n=== TEST COMPLAINTS ===")
complaint_data = {
    "user_id": TEST_USER_ID,
    "order_id": ORDER_ID,
    "reason": "Test complaint RPC"
}
res = rpc.complaints.create_complaint(complaint_data)
pprint(res)
COMPLAINT_ID = res.get("complaint_id")

res = rpc.complaints.get_complaint(COMPLAINT_ID)
pprint(res)

print("\n[INFO] Tous les tests RPC sont terminés.")
