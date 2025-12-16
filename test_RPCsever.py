import xmlrpc.client
from pprint import pprint

# ---------------------------------------------------------
# CONFIGURATION RPC
# ---------------------------------------------------------
RPC_URL = "http://localhost:8000"
rpc = xmlrpc.client.ServerProxy(RPC_URL, allow_none=True)

# IDs de test (à adapter selon ta DB)
TEST_USER_ID = "64e1f2ab1234567890abcdef"
TEST_FREELANCER_ID = "64e1f2ab1234567890abcdef"
TEST_CATEGORY_ID = "64e1f2ab1234567890abcdea"
TEST_ORDER_ID = "64e1f2ab1234567890abcdeb"

print("[INFO] Début des tests fonctionnels RPC...")
print("---------------------------------------------------------\n")

def safe_call(func, *args, **kwargs):
    """Appelle une méthode RPC en gérant les exceptions."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        return {"error": str(e), "success": False}

# ---------------------------------------------------------
# 1️⃣ USERS
# ---------------------------------------------------------
print("=== TEST USERS ===")
res = safe_call(rpc.users.get_user_by_id, TEST_USER_ID)
pprint(res)

# ---------------------------------------------------------
# 2️⃣ CATEGORIES
# ---------------------------------------------------------
print("\n=== TEST CATEGORIES ===")
cat_data = {
    "name": "Catégorie Test RPC",
    "description": "Desc test",
    "icon_url": "https://example.com/icon.png",
    "sort_order": 1,
    "is_active": True
}
res = safe_call(rpc.categories.create_category, cat_data)
pprint(res)
CAT_ID = res.get("category_id")

if CAT_ID:
    res = safe_call(rpc.categories.get_category_by_id, CAT_ID)
    pprint(res)
    update_cat = {"description": "Desc modifiée RPC"}
    res = safe_call(rpc.categories.update_category, CAT_ID, update_cat)
    pprint(res)

# ---------------------------------------------------------
# 3️⃣ GIGS
# ---------------------------------------------------------
print("\n=== TEST GIGS ===")
gig_data = {
    "category_id": TEST_CATEGORY_ID,
    "title": "Gig Test RPC",
    "description": "Description test RPC",
    "price": 50
}
res = safe_call(rpc.gigs.create_gig, TEST_FREELANCER_ID, gig_data)
pprint(res)
GIG_ID = res.get("gig_id")

if GIG_ID:
    res = safe_call(rpc.gigs.get_gig_by_id, GIG_ID)
    pprint(res)
    update_data = {"price": 75, "title": "Gig Modifié RPC"}
    res = safe_call(rpc.gigs.update_gig, GIG_ID, TEST_FREELANCER_ID, update_data)
    pprint(res)

# ---------------------------------------------------------
# 4️⃣ ORDERS
# ---------------------------------------------------------
print("\n=== TEST ORDERS ===")
order_data = {
    "client_id": TEST_USER_ID,
    "freelancer_id": TEST_FREELANCER_ID,
    "gig_id": GIG_ID,
    "status": "pending",
    "price": 75,
    "quantity": 1
}
res = safe_call(rpc.orders.create_order, TEST_USER_ID, order_data)
pprint(res)
ORDER_ID = res.get("order_id") or TEST_ORDER_ID

res = safe_call(rpc.orders.get_order, ORDER_ID, TEST_USER_ID)
pprint(res)

# ---------------------------------------------------------
# 5️⃣ REVIEWS
# ---------------------------------------------------------
print("\n=== TEST REVIEWS ===")
review_data = {
    "reviewer_id": TEST_USER_ID,
    "reviewed_id": TEST_FREELANCER_ID,
    "gig_id": GIG_ID,
    "rating": 5,
    "comment": "Review test RPC"
}
res = safe_call(rpc.reviews.create_review, review_data)
pprint(res)
REVIEW_ID = res.get("review_id")

if REVIEW_ID:
    res = safe_call(rpc.reviews.get_review, REVIEW_ID)
    pprint(res)

# ---------------------------------------------------------
# 6️⃣ MESSAGES
# ---------------------------------------------------------
print("\n=== TEST MESSAGES ===")
msg_data = {"content": "Message test RPC"}
msg = safe_call(rpc.messages.send_message, ORDER_ID, TEST_USER_ID, {"content": "Message test RPC"})
pprint(msg)
MSG_ID = msg.get("message_id")

if MSG_ID:
    res = safe_call(rpc.messages.list_conversations, TEST_USER_ID)
    pprint(res)
    res = safe_call(rpc.messages.mark_as_read, ORDER_ID, TEST_USER_ID)
    pprint(res)

# ---------------------------------------------------------
# 7️⃣ PAYMENTS
# ---------------------------------------------------------
print("\n=== TEST PAYMENTS ===")
payment = safe_call(rpc.payments.create_payment_intent, ORDER_ID, TEST_USER_ID, "card")
pprint(payment)

# ---------------------------------------------------------
# 8️⃣ FAVORITES
# ---------------------------------------------------------
print("\n=== TEST FAVORITES ===")
res = safe_call(rpc.favorites.add_favorite, TEST_USER_ID, GIG_ID)
pprint(res)
res = safe_call(rpc.favorites.list_favorites, TEST_USER_ID)
pprint(res)
res = safe_call(rpc.favorites.remove_favorite, TEST_USER_ID, GIG_ID)
pprint(res)

# ---------------------------------------------------------
# 9️⃣ NOTIFICATIONS
# ---------------------------------------------------------
print("\n=== TEST NOTIFICATIONS ===")
notif = safe_call(rpc.notifications.send_notification, TEST_USER_ID, "info", "Titre test", "Message test")
pprint(notif)
NOTIF_ID = notif.get("notification_id")

if NOTIF_ID:
    res = safe_call(rpc.notifications.list_user_notifications, TEST_USER_ID, {})
    pprint(res)
    res = safe_call(rpc.notifications.mark_notification_read, NOTIF_ID)
    pprint(res)

print("\n[INFO] Tous les tests RPC sont terminés.")
