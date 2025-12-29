# WorkNet RPC Server

Serveur XML-RPC Python pour la plateforme WorkNet. Ce serveur gère la logique métier complexe et communique avec MongoDB pour les opérations de base de données.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Configuration](#configuration)
- [Services RPC](#services-rpc)
- [Structure du Projet](#structure-du-projet)
- [Utilisation](#utilisation)
- [Tests](#tests)
- [Développement](#développement)

## 🎯 Vue d'ensemble

Le serveur RPC Python fournit :
- Logique métier centralisée
- Transactions MongoDB
- Validation des données
- Gestion d'erreurs robuste
- Logging détaillé
- Support multi-threading

## 🚀 Installation

### Prérequis

- Python 3.11 ou supérieur
- MongoDB (local ou distant)
- pip (gestionnaire de paquets Python)

### Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Ou avec virtualenv (recommandé)
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## ⚙️ Configuration

### Variables d'environnement

Créer un fichier `.env` à la racine :

```env
# RPC Server
RPC_HOST=0.0.0.0
RPC_PORT=8000

# MongoDB
MONGODB_URI=mongodb+srv://worknet_db:20011110@cluster0.kgbzmzf.mongodb.net/WorkNetBD?retryWrites=true&w=majority
DB_NAME=worknet

# JWT (pour security utils)
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRES_IN_DAYS=7
JWT_REFRESH_EXPIRES_IN_DAYS=30

# Environment
NODE_ENV=development
LOG_LEVEL=INFO
```

## 🔧 Services RPC

### Users Service

**Méthodes disponibles :**
- `usersService.register(username, email, password, role)` - Inscription
- `usersService.login(email, password)` - Connexion
- `usersService.get_by_id(user_id)` - Récupérer par ID
- `usersService.get_all(page, limit, filters)` - Liste avec pagination
- `usersService.update_profile(user_id, updates)` - Mettre à jour profil
- `usersService.change_password(user_id, old_password, new_password)` - Changer mot de passe
- `usersService.delete_user(user_id)` - Supprimer utilisateur
- `usersService.get_stats(user_id)` - Statistiques utilisateur

**Exemple d'appel :**
```python
import xmlrpc.client

client = xmlrpc.client.ServerProxy('http://localhost:8000/RPC2')
result = client.usersService.register('newuser', 'user@example.com', 'password123', 'client')
print(result)
```

### Gigs Service

**Méthodes disponibles :**
- `gigsService.create(user_id, gig_data)` - Créer un gig
- `gigsService.update(gig_id, updates)` - Mettre à jour
- `gigsService.delete(gig_id)` - Supprimer
- `gigsService.get_by_id(gig_id)` - Récupérer par ID
- `gigsService.get_by_user(user_id, page, limit)` - Gigs d'un utilisateur
- `gigsService.search(query, filters, page, limit)` - Rechercher
- `gigsService.update_rating(gig_id, new_rating)` - Mettre à jour note

### Orders Service

**Méthodes disponibles :**
- `ordersService.create(gig_id, buyer_id, quantity, total_price)` - Créer commande
- `ordersService.update_status(order_id, status)` - Mettre à jour statut
- `ordersService.get_by_id(order_id)` - Récupérer par ID
- `ordersService.get_all(filters, page, limit)` - Liste avec filtres
- `ordersService.get_analytics(user_id, period)` - Analytics
- `ordersService.cancel(order_id, reason)` - Annuler commande

### Payments Service

**Méthodes disponibles :**
- `paymentsService.create(payment_id, order_id, amount, payment_method)` - Créer paiement
- `paymentsService.process(payment_id, status)` - Traiter paiement
- `paymentsService.refund(payment_id, amount)` - Rembourser
- `paymentsService.get_status(payment_id)` - Statut du paiement
- `paymentsService.calculate_fees(amount)` - Calculer frais

### Categories Service

**Méthodes disponibles :**
- `categoriesService.create(name, slug, description)` - Créer catégorie
- `categoriesService.update(category_id, updates)` - Mettre à jour
- `categoriesService.delete(category_id)` - Supprimer
- `categoriesService.get_all(page, limit)` - Liste
- `categoriesService.get_by_id(category_id)` - Par ID
- `categoriesService.get_by_slug(slug)` - Par slug
- `categoriesService.get_stats(category_id)` - Statistiques

### Reviews Service

**Méthodes disponibles :**
- `reviewsService.create(review_id, gig_id, rating)` - Créer avis
- `reviewsService.update(review_id, updates)` - Mettre à jour
- `reviewsService.delete(review_id)` - Supprimer
- `reviewsService.calculate_rating(gig_id)` - Calculer note moyenne

### Messages Service

**Méthodes disponibles :**
- `messagesService.create(message_id, conversation_id, sender_id)` - Créer message
- `messagesService.mark_as_read(message_id)` - Marquer comme lu
- `messagesService.get_unread_count(user_id)` - Nombre non lus

### Notifications Service

**Méthodes disponibles :**
- `notificationsService.create(notification_id, user_id, type)` - Créer notification
- `notificationsService.mark_as_read(notification_id)` - Marquer comme lu
- `notificationsService.get_unread_count(user_id)` - Nombre non lus
- `notificationsService.send_bulk(user_ids, type, message, link)` - Envoi en masse

### Health Check

**Méthode :**
- `ping()` - Vérifier l'état du serveur

**Réponse :**
```python
{
    'status': 'ok',
    'message': 'RPC Server is running',
    'mongodb': 'connected'
}
```

## 📁 Structure du Projet

```
rpc-server/
├── src/
│   ├── server.py              # Serveur XML-RPC principal
│   │
│   ├── services/              # Services RPC
│   │   ├── users_service.py
│   │   ├── gigs_service.py
│   │   ├── orders_service.py
│   │   ├── categories_service.py
│   │   ├── reviews_service.py
│   │   ├── messages_service.py
│   │   ├── payments_service.py
│   │   └── notifications_service.py
│   │
│   └── utils/                 # Utilitaires
│       ├── security.py       # JWT, password hashing, permissions
│       ├── database.py        # Helpers MongoDB, transactions, aggregations
│       └── validators.py     # Validation des données
│
├── tests/                     # Tests
│   ├── conftest.py           # Fixtures pytest
│   ├── test_users.py
│   ├── test_gigs.py
│   ├── test_orders.py
│   ├── test_payments.py
│   └── test_security.py
│
├── requirements.txt           # Dépendances Python
├── pytest.ini               # Configuration pytest
├── Dockerfile.python        # Dockerfile pour Python
└── README.md                # Ce fichier
```

## 💻 Utilisation

### Démarrer le Serveur

```bash
# Depuis la racine du projet
python src/server.py

# Ou avec Python 3 explicitement
python3 src/server.py
```

Le serveur démarre sur `http://0.0.0.0:8000` par défaut.

### Appeler depuis Node.js

```javascript
const { getRPCClient } = require('./rpc-client/rpcClient');
const rpcClient = getRPCClient();

// Appel RPC
const result = await rpcClient.usersService_register(
  'username',
  'email@example.com',
  'password123',
  'client'
);
```

### Appeler depuis Python

```python
import xmlrpc.client

client = xmlrpc.client.ServerProxy('http://localhost:8000/RPC2')

# Ping
result = client.ping()
print(result)

# Register user
result = client.usersService.register(
    'testuser',
    'test@example.com',
    'password123',
    'client'
)
print(result)
```

### Appeler depuis cURL

```bash
# Ping
curl -X POST http://localhost:8000/RPC2 \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0"?><methodCall><methodName>ping</methodName><params></params></methodCall>'
```

## 🧪 Tests

### Exécuter les Tests

```bash
# Tous les tests
pytest

# Avec couverture
pytest --cov=src --cov-report=html

# Un fichier spécifique
pytest tests/test_users.py

# Mode verbose
pytest -v
```

### Structure des Tests

Les tests utilisent pytest avec des fixtures pour mocker MongoDB. Voir `tests/README.md` pour plus de détails.

## 🛠 Développement

### Ajouter un Nouveau Service

1. **Créer le fichier service**
   ```python
   # src/services/new_service.py
   from utils.validators import validate_object_id
   
   class NewService:
       def __init__(self, db):
           self.db = db
           self.collection = db.new_collection if db else None
       
       def create(self, data):
           # Logique métier
           pass
   ```

2. **Enregistrer dans server.py**
   ```python
   from src.services.new_service import NewService
   
   server.register_instance(NewService(db), allow_dotted_names=True)
   ```

3. **Ajouter les tests**
   ```python
   # tests/test_new_service.py
   def test_create_success(mock_db):
       service = NewService(mock_db)
       result = service.create({...})
       assert result['success'] is True
   ```

### Utiliser les Utilitaires

**Security :**
```python
from utils.security import hash_password, verify_password, generate_token

hashed = hash_password('password123')
is_valid = verify_password('password123', hashed)
token = generate_token({'id': 'user123', 'role': 'client'})
```

**Database :**
```python
from utils.database import execute_transaction, aggregate_user_stats

def my_operation(db, session, user_id):
    db.users.update_one({'_id': user_id}, {'$set': {'active': True}}, session=session)

execute_transaction(db, my_operation, user_id)
stats = aggregate_user_stats(db, user_id)
```

**Validators :**
```python
from utils.validators import validate_object_id, validate_email

user_id = validate_object_id('507f1f77bcf86cd799439011')
email = validate_email('user@example.com')
```

## 🐳 Docker

### Build et Run

```bash
# Build
docker build -f Dockerfile.python -t worknet-rpc-server .

# Run
docker run -p 8000:8000 \
  -e MONGODB_URI=mongodb://localhost:27017/worknet \
  -e RPC_PORT=8000 \
  worknet-rpc-server
```

### Avec Docker Compose

Le serveur RPC est inclus dans `docker-compose.yml` principal.

## 📊 Logging

Les logs sont écrits dans :
- **Console** (stdout) - Format configuré
- **Fichier** `rpc_server.log` - Logs persistants

Niveau de log configurable via `LOG_LEVEL` dans `.env`.

## 🔒 Sécurité

- **Password Hashing** : Bcrypt avec 12 rounds
- **JWT Tokens** : Génération et validation sécurisées
- **Input Validation** : Validation stricte de toutes les entrées
- **MongoDB Injection** : Protection via validation ObjectId
- **Error Handling** : Pas d'exposition d'informations sensibles

## 🐛 Dépannage

### Problèmes Courants

1. **Erreur de connexion MongoDB**
   - Vérifier `MONGODB_URI` dans `.env`
   - Vérifier que MongoDB est accessible

2. **Port déjà utilisé**
   - Changer `RPC_PORT` dans `.env`
   - Vérifier qu'aucun autre processus n'utilise le port

3. **Erreur d'import**
   - Vérifier que toutes les dépendances sont installées
   - Vérifier le PYTHONPATH

## 📚 Ressources

- [XML-RPC Documentation](https://docs.python.org/3/library/xmlrpc.server.html)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)

## 📄 Licence

ISC
