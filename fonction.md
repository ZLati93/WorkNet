<think>
The user is asking for "tout les fonction qui je doit crier dans des services de serveur rpc" which translates to "all the functions that I must create in server RPC services" based on the WorkNet project schemas and pages.

</think># 🚀 Fonctions RPC à Créer pour WorkNet

Basé sur les schémas MongoDB et les pages du projet WorkNet, voici **toutes les fonctions RPC** que vous devez créer dans vos services serveur. Chaque fonction est organisée par service et inclut les paramètres d'entrée et de sortie.

## 📋 Structure des Services RPC

### *Format des Méthodes RPC*
```
worknet.{service}.{methodName}
```

### *Types de Données*
- `string` : Chaîne de caractères
- `int` : Nombre entier
- `double` : Nombre décimal
- `boolean` : Booléen
- `dateTime` : Date/heure ISO 8601
- `base64` : Données binaires encodées
- `struct` : Objet complexe
- `array` : Tableau

---

## 🔐 1. Service d'Authentification (worknet.auth)

```javascript
// Inscription utilisateur
worknet.auth.registerUser(params: struct) -> struct
// Paramètres: {email: string, username: string, password: string, role: string, full_name: string}
// Retour: {success: boolean, user_id: string, message: string}

// Connexion
worknet.auth.loginUser(params: struct) -> struct
// Paramètres: {email: string, password: string}
// Retour: {success: boolean, token: string, user: struct, message: string}

// Déconnexion
worknet.auth.logoutUser(params: struct) -> struct
// Paramètres: {token: string}
// Retour: {success: boolean, message: string}

// Rafraîchir token
worknet.auth.refreshToken(params: struct) -> struct
// Paramètres: {refresh_token: string}
// Retour: {success: boolean, token: string, refresh_token: string}

// Vérification email
worknet.auth.verifyEmail(params: struct) -> struct
// Paramètres: {token: string}
// Retour: {success: boolean, message: string}

// Demande réinitialisation mot de passe
worknet.auth.resetPasswordRequest(params: struct) -> struct
// Paramètres: {email: string}
// Retour: {success: boolean, message: string}

// Confirmation réinitialisation
worknet.auth.confirmResetPassword(params: struct) -> struct
// Paramètres: {token: string, new_password: string}
// Retour: {success: boolean, message: string}

// Changement mot de passe
worknet.auth.changePassword(params: struct) -> struct
// Paramètres: {user_id: string, old_password: string, new_password: string}
// Retour: {success: boolean, message: string}

// Validation token
worknet.auth.validateToken(params: struct) -> struct
// Paramètres: {token: string}
// Retour: {success: boolean, user: struct}
```

---

## 👤 2. Service de Gestion des Utilisateurs (worknet.user)

```javascript
// Récupérer profil
worknet.user.getUserProfile(params: struct) -> struct
// Paramètres: {user_id: string}
// Retour: {success: boolean, user: struct}

// Mettre à jour profil
worknet.user.updateUserProfile(params: struct) -> struct
// Paramètres: {user_id: string, profile_data: struct}
// Retour: {success: boolean, user: struct, message: string}

// Changer avatar
worknet.user.updateUserAvatar(params: struct) -> struct
// Paramètres: {user_id: string, avatar_file: base64, filename: string}
// Retour: {success: boolean, avatar_url: string, message: string}

// Mettre à jour compétences
worknet.user.updateUserSkills(params: struct) -> struct
// Paramètres: {user_id: string, skills: array}
// Retour: {success: boolean, message: string}

// Mettre à jour paramètres
worknet.user.updateUserSettings(params: struct) -> struct
// Paramètres: {user_id: string, settings: struct}
// Retour: {success: boolean, message: string}

// Désactiver compte
worknet.user.deactivateUser(params: struct) -> struct
// Paramètres: {user_id: string}
// Retour: {success: boolean, message: string}

// Réactiver compte
worknet.user.reactivateUser(params: struct) -> struct
// Paramètres: {user_id: string}
// Retour: {success: boolean, message: string}

// Supprimer compte
worknet.user.deleteUser(params: struct) -> struct
// Paramètres: {user_id: string}
// Retour: {success: boolean, message: string}

// Statistiques utilisateur
worknet.user.getUserStats(params: struct) -> struct
// Paramètres: {user_id: string}
// Retour: {success: boolean, stats: struct}

// Vérifier utilisateur
worknet.user.verifyUser(params: struct) -> struct
// Paramètres: {user_id: string}
// Retour: {success: boolean, message: string}

// Rechercher utilisateurs
worknet.user.searchUsers(params: struct) -> struct
// Paramètres: {query: string, role: string, page: int, limit: int}
// Retour: {success: boolean, users: array, total: int, page: int, pages: int}
```

---

## 💼 3. Service de Gestion des Gigs (worknet.gig)

```javascript
// Créer un gig
worknet.gig.createGig(params: struct) -> struct
// Paramètres: {freelancer_id: string, category_id: string, title: string, description: string, base_price: double, delivery_days: int}
// Retour: {success: boolean, gig_id: string, message: string}

// Récupérer un gig
worknet.gig.getGigById(params: struct) -> struct
// Paramètres: {gig_id: string}
// Retour: {success: boolean, gig: struct}

// Mettre à jour un gig
worknet.gig.updateGig(params: struct) -> struct
// Paramètres: {gig_id: string, gig_data: struct}
// Retour: {success: boolean, gig: struct, message: string}

// Supprimer un gig
worknet.gig.deleteGig(params: struct) -> struct
// Paramètres: {gig_id: string}
// Retour: {success: boolean, message: string}

// Publier un gig
worknet.gig.publishGig(params: struct) -> struct
// Paramètres: {gig_id: string}
// Retour: {success: boolean, message: string}

// Mettre en pause
worknet.gig.pauseGig(params: struct) -> struct
// Paramètres: {gig_id: string}
// Retour: {success: boolean, message: string}

// Reprendre
worknet.gig.resumeGig(params: struct) -> struct
// Paramètres: {gig_id: string}
// Retour: {success: boolean, message: string}

// Marquer comme featured
worknet.gig.featureGig(params: struct) -> struct
// Paramètres: {gig_id: string}
// Retour: {success: boolean, message: string}

// Recherche textuelle
worknet.gig.searchGigs(params: struct) -> struct
// Paramètres: {query: string, filters: struct, page: int, limit: int}
// Retour: {success: boolean, gigs: array, total: int, page: int, pages: int}

// Gigs par catégorie
worknet.gig.getGigsByCategory(params: struct) -> struct
// Paramètres: {category_id: string, filters: struct, page: int, limit: int}
// Retour: {success: boolean, gigs: array, total: int}

// Gigs d'un freelancer
worknet.gig.getGigsByFreelancer(params: struct) -> struct
// Paramètres: {freelancer_id: string}
// Retour: {success: boolean, gigs: array}

// Gigs en vedette
worknet.gig.getFeaturedGigs(params: struct) -> struct
// Paramètres: {limit: int}
// Retour: {success: boolean, gigs: array}

// Gigs tendance
worknet.gig.getTrendingGigs(params: struct) -> struct
// Paramètres: {period: string}
// Retour: {success: boolean, gigs: array}

// Gigs similaires
worknet.gig.getRelatedGigs(params: struct) -> struct
// Paramètres: {gig_id: string}
// Retour: {success: boolean, gigs: array}

// Gigs par localisation
worknet.gig.getGigsByLocation(params: struct) -> struct
// Paramètres: {country: string, city: string}
// Retour: {success: boolean, gigs: array}

// Gigs par prix
worknet.gig.getGigsByPriceRange(params: struct) -> struct
// Paramètres: {min_price: double, max_price: double}
// Retour: {success: boolean, gigs: array}

// Gigs par note
worknet.gig.getGigsByRating(params: struct) -> struct
// Paramètres: {min_rating: double}
// Retour: {success: boolean, gigs: array}

// Upload image gig
worknet.gig.uploadGigImage(params: struct) -> struct
// Paramètres: {gig_id: string, image_file: base64, filename: string}
// Retour: {success: boolean, image_url: string, message: string}

// Supprimer image gig
worknet.gig.deleteGigImage(params: struct) -> struct
// Paramètres: {gig_id: string, image_url: string}
// Retour: {success: boolean, message: string}

// Réorganiser images
worknet.gig.reorderGigImages(params: struct) -> struct
// Paramètres: {gig_id: string, image_order: array}
// Retour: {success: boolean, message: string}

// Upload vidéo gig
worknet.gig.uploadGigVideo(params: struct) -> struct
// Paramètres: {gig_id: string, video_file: base64, filename: string}
// Retour: {success: boolean, video_url: string, message: string}

// Supprimer vidéo gig
worknet.gig.deleteGigVideo(params: struct) -> struct
// Paramètres: {gig_id: string}
// Retour: {success: boolean, message: string}
```

---

## 📦 4. Service de Gestion des Commandes (worknet.order)

```javascript
// Créer une commande
worknet.order.createOrder(params: struct) -> struct
// Paramètres: {client_id: string, freelancer_id: string, gig_id: string, title: string, amount: double, deadline: dateTime}
// Retour: {success: boolean, order_id: string, order_number: string, message: string}

// Récupérer commande
worknet.order.getOrderById(params: struct) -> struct
// Paramètres: {order_id: string}
// Retour: {success: boolean, order: struct}

// Commandes client
worknet.order.getOrdersByClient(params: struct) -> struct
// Paramètres: {client_id: string, filters: struct, page: int, limit: int}
// Retour: {success: boolean, orders: array, total: int}

// Commandes freelancer
worknet.order.getOrdersByFreelancer(params: struct) -> struct
// Paramètres: {freelancer_id: string, filters: struct, page: int, limit: int}
// Retour: {success: boolean, orders: array, total: int}

// Changer statut
worknet.order.updateOrderStatus(params: struct) -> struct
// Paramètres: {order_id: string, status: string, reason: string}
// Retour: {success: boolean, order: struct, message: string}

// Annuler commande
worknet.order.cancelOrder(params: struct) -> struct
// Paramètres: {order_id: string, reason: string}
// Retour: {success: boolean, message: string}

// Demander révision
worknet.order.requestRevision(params: struct) -> struct
// Paramètres: {order_id: string, revision_data: struct}
// Retour: {success: boolean, message: string}

// Livrer commande
worknet.order.deliverOrder(params: struct) -> struct
// Paramètres: {order_id: string, delivery_data: struct}
// Retour: {success: boolean, message: string}

// Marquer comme terminée
worknet.order.completeOrder(params: struct) -> struct
// Paramètres: {order_id: string}
// Retour: {success: boolean, message: string}

// Ouvrir litige
worknet.order.disputeOrder(params: struct) -> struct
// Paramètres: {order_id: string, dispute_data: struct}
// Retour: {success: boolean, message: string}

// Upload fichier livraison
worknet.order.uploadDeliveryFile(params: struct) -> struct
// Paramètres: {order_id: string, file: base64, filename: string}
// Retour: {success: boolean, file_url: string, message: string}

// Télécharger fichier livraison
worknet.order.downloadDeliveryFile(params: struct) -> base64
// Paramètres: {order_id: string, file_id: string}
// Retour: fichier binaire

// Supprimer fichier livraison
worknet.order.deleteDeliveryFile(params: struct) -> struct
// Paramètres: {order_id: string, file_id: string}
// Retour: {success: boolean, message: string}

// Lister fichiers livraison
worknet.order.getDeliveryFiles(params: struct) -> struct
// Paramètres: {order_id: string}
// Retour: {success: boolean, files: array}
```

---

## 💬 5. Service de Messagerie (worknet.message)

```javascript
// Envoyer message
worknet.message.sendMessage(params: struct) -> struct
// Paramètres: {order_id: string, sender_id: string, receiver_id: string, content: string, message_type: string}
// Retour: {success: boolean, message_id: string, message: struct}

// Messages d'une commande
worknet.message.getMessagesByOrder(params: struct) -> struct
// Paramètres: {order_id: string, page: int, limit: int}
// Retour: {success: boolean, messages: array, total: int}

// Messages non lus
worknet.message.getUnreadMessages(params: struct) -> struct
// Paramètres: {user_id: string}
// Retour: {success: boolean, count: int, messages: array}

// Marquer comme lu
worknet.message.markMessageAsRead(params: struct) -> struct
// Paramètres: {message_id: string}
// Retour: {success: boolean, message: string}

// Conversations utilisateur
worknet.message.getMessageThreads(params: struct) -> struct
// Paramètres: {user_id: string}
// Retour: {success: boolean, threads: array}

// Supprimer message
worknet.message.deleteMessage(params: struct) -> struct
// Paramètres: {message_id: string}
// Retour: {success: boolean, message: string}

// Upload pièce jointe
worknet.message.uploadMessageAttachment(params: struct) -> struct
// Paramètres: {message_id: string, file: base64, filename: string}
// Retour: {success: boolean, attachment_url: string, message: string}

// Récupérer pièces jointes
worknet.message.getMessageAttachments(params: struct) -> struct
// Paramètres: {message_id: string}
// Retour: {success: boolean, attachments: array}
```

---

## ⭐ 6. Service d'Avis (worknet.review)

```javascript
// Créer un avis
worknet.review.createReview(params: struct) -> struct
// Paramètres: {order_id: string, reviewer_id: string, reviewee_id: string, overall_rating: double, title: string, comment: string}
// Retour: {success: boolean, review_id: string, message: string}

// Récupérer avis
worknet.review.getReviewById(params: struct) -> struct
// Paramètres: {review_id: string}
// Retour: {success: boolean, review: struct}

// Avis d'un utilisateur
worknet.review.getReviewsByUser(params: struct) -> struct
// Paramètres: {user_id: string, page: int, limit: int}
// Retour: {success: boolean, reviews: array, total: int}

// Mettre à jour avis
worknet.review.updateReview(params: struct) -> struct
// Paramètres: {review_id: string, review_data: struct}
// Retour: {success: boolean, review: struct, message: string}

// Supprimer avis
worknet.review.deleteReview(params: struct) -> struct
// Paramètres: {review_id: string}
// Retour: {success: boolean, message: string}

// Répondre à un avis
worknet.review.respondToReview(params: struct) -> struct
// Paramètres: {review_id: string, response: string}
// Retour: {success: boolean, message: string}

// Signaler avis
worknet.review.reportReview(params: struct) -> struct
// Paramètres: {review_id: string, reason: string}
// Retour: {success: boolean, message: string}

// Note moyenne
worknet.review.getAverageRating(params: struct) -> struct
// Paramètres: {user_id: string}
// Retour: {success: boolean, average_rating: double, total_reviews: int}
```

---

## 💳 7. Service de Paiement (worknet.payment)

```javascript
// Traiter paiement
worknet.payment.processPayment(params: struct) -> struct
// Paramètres: {order_id: string, payment_data: struct}
// Retour: {success: boolean, payment_id: string, transaction_id: string, message: string}

// Remboursement
worknet.payment.refundPayment(params: struct) -> struct
// Paramètres: {payment_id: string, amount: double, reason: string}
// Retour: {success: boolean, refund_id: string, message: string}

// Détails paiement
worknet.payment.getPaymentById(params: struct) -> struct
// Paramètres: {payment_id: string}
// Retour: {success: boolean, payment: struct}

// Paiements utilisateur
worknet.payment.getPaymentsByUser(params: struct) -> struct
// Paramètres: {user_id: string, filters: struct, page: int, limit: int}
// Retour: {success: boolean, payments: array, total: int}

// Paiements commande
worknet.payment.getPaymentsByOrder(params: struct) -> struct
// Paramètres: {order_id: string}
// Retour: {success: boolean, payments: array}

// Versement freelancer
worknet.payment.processPayout(params: struct) -> struct
// Paramètres: {freelancer_id: string, amount: double}
// Retour: {success: boolean, payout_id: string, message: string}

// Historique paiements
worknet.payment.getPaymentHistory(params: struct) -> struct
// Paramètres: {user_id: string, filters: struct, page: int, limit: int}
// Retour: {success: boolean, payments: array, total: int}

// Webhook paiement
worknet.payment.handlePaymentWebhook(params: struct) -> struct
// Paramètres: {webhook_data: struct}
// Retour: {success: boolean, message: string}
```

---

## ❤️ 8. Service des Favoris (worknet.favorite)

```javascript