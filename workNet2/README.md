# WorkNet - Plateforme de Mise en Relation Professionnelle

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js Version](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen)](https://nodejs.org/)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

WorkNet est une plateforme complète de mise en relation entre clients et freelancers, permettant la gestion de projets, la communication en temps réel, et le suivi des livraisons. La plateforme offre deux interfaces distinctes : une pour les clients cherchant des services et une pour les freelancers proposant leurs compétences.

## 📋 Table des Matières

- [Description du Projet](#description-du-projet)
- [Technologies Utilisées](#technologies-utilisées)
- [Architecture](#architecture)
- [Installation](#installation)
- [Guide de Développement](#guide-de-développement)
- [Documentation API](#documentation-api)
- [Tests](#tests)
- [Déploiement](#déploiement)
- [Contribution](#contribution)
- [Licence](#licence)

## 🎯 Description du Projet

WorkNet est une marketplace moderne qui connecte des clients avec des freelancers talentueux. La plateforme permet :

- **Pour les Clients** :
  - Recherche et découverte de services (gigs)
  - Création et gestion de commandes
  - Communication en temps réel avec les freelancers
  - Suivi des livraisons
  - Système de notation et d'avis

- **Pour les Freelancers** :
  - Création et gestion de gigs
  - Dashboard avec statistiques et analytics
  - Gestion des commandes
  - Messagerie avec les clients
  - Suivi des revenus et paiements

## 🛠 Technologies Utilisées

### Frontend
- **React 18** - Bibliothèque JavaScript pour l'interface utilisateur
- **TypeScript** - Typage statique pour JavaScript
- **Vite** - Outil de build moderne et rapide
- **Tailwind CSS** - Framework CSS utilitaire
- **React Router v6** - Routage côté client
- **React Query** - Gestion des données serveur et cache
- **React Hook Form** - Gestion des formulaires
- **Axios** - Client HTTP pour les requêtes API
- **Socket.io-client** - Communication en temps réel
- **Recharts** - Graphiques et visualisations

### Backend
- **Node.js 18+** - Runtime JavaScript côté serveur
- **Express.js** - Framework web pour Node.js
- **Mongoose** - ODM pour MongoDB
- **JWT** - Authentification par tokens
- **Bcrypt** - Hachage de mots de passe
- **XML-RPC** - Communication avec serveur RPC Python
- **Express Validator** - Validation des données
- **Helmet** - Sécurité HTTP
- **Morgan** - Logging des requêtes
- **Express Rate Limit** - Limitation du taux de requêtes

### Base de Données
- **MongoDB 7.0** - Base de données NoSQL principale
- **Redis 7** - Cache et gestion de sessions

### RPC Server
- **Python 3.11+** - Langage pour serveur RPC
- **XML-RPC** - Protocole RPC pour communication inter-services
- **PyMongo** - Client MongoDB pour Python
- **Bcrypt** - Hachage de mots de passe
- **PyJWT** - Gestion des tokens JWT

### DevOps & Outils
- **Docker** - Conteneurisation
- **Docker Compose** - Orchestration de conteneurs
- **Git** - Contrôle de version
- **ESLint** - Linter JavaScript/TypeScript
- **Prettier** - Formateur de code

### Tests
- **Jest** - Framework de tests JavaScript
- **Supertest** - Tests d'API HTTP
- **Vitest** - Framework de tests moderne
- **React Testing Library** - Tests de composants React
- **Pytest** - Framework de tests Python
- **Playwright** - Tests end-to-end avec navigateur

## 🏗 Architecture

### Architecture Globale

```
┌─────────────────┐         ┌─────────────────┐
│  Frontend       │         │  Frontend       │
│  Client         │         │  Freelancer     │
│  (React)        │         │  (React)        │
│  Port: 3000     │         │  Port: 3001     │
└────────┬────────┘         └────────┬────────┘
         │                            │
         │  HTTP/REST                 │  HTTP/REST
         │  WebSocket                 │  WebSocket
         │                            │
         └────────────┬───────────────┘
                      │
         ┌────────────▼────────────┐
         │   Backend Node.js       │
         │   API Gateway           │
         │   (Express.js)          │
         │   Port: 3000            │
         └────────────┬────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
    │ MongoDB │  │ Redis  │  │  RPC   │
    │ Port:   │  │ Port:  │  │ Server │
    │ 27017   │  │ 6379   │  │ Port:  │
    └─────────┘  └────────┘  │ 8000   │
                             └───┬────┘
                                 │ XML-RPC
                                 │
                         ┌───────▼───────┐
                         │  Python RPC   │
                         │  Server       │
                         │  (XML-RPC)    │
                         └───────┬───────┘
                                 │
                         ┌───────▼───────┐
                         │   MongoDB     │
                         │   (via PyMongo)│
                         └───────────────┘
```

### Flux de Données

1. **Frontend → Backend Node.js** : Requêtes HTTP/REST pour les opérations CRUD
2. **Backend Node.js → RPC Server** : Appels XML-RPC pour la logique métier complexe
3. **Backend Node.js ↔ MongoDB** : Opérations de base de données via Mongoose
4. **RPC Server ↔ MongoDB** : Opérations de base de données via PyMongo
5. **Backend Node.js ↔ Redis** : Cache et gestion de sessions
6. **Frontend ↔ Backend** : WebSocket pour communication temps réel

### Structure des Dossiers

```
WorkNet/
├── README.md                 # Documentation principale (ce fichier)
├── .gitignore                # Fichiers à ignorer par Git
├── .env.example              # Exemple de variables d'environnement
├── docker-compose.yml        # Configuration Docker Compose principale
├── DOCKER.md                 # Documentation Docker
│
├── docs/                     # Documentation du projet
│   ├── rapport.docx          # Rapport technique détaillé
│   ├── report.pdf            # Version PDF du rapport
│   └── presentation.pptx     # Présentation du projet
│
├── frontend-client/          # Application React pour les clients
│   ├── src/
│   │   ├── components/       # Composants réutilisables (Navbar, Footer, GigCard)
│   │   ├── pages/            # Pages (Home, Login, Register, Orders)
│   │   ├── services/         # Services API (authService, gigsService, ordersService)
│   │   ├── App.js            # Composant principal
│   │   └── index.js          # Point d'entrée
│   ├── tests/                # Tests (auth.test.js, gigs.test.js)
│   ├── package.json
│   └── vite.config.ts
│
├── frontend-freelancer/      # Application React pour les freelancers
│   ├── src/
│   │   ├── components/       # Composants (Navbar, Footer, GigForm, OrderCard, AnalyticsCard)
│   │   ├── pages/            # Pages (Dashboard, MyGigs, Messages, Login, Register)
│   │   ├── services/         # Services API (gigsService, messagesService, paymentsService)
│   │   ├── App.js
│   │   └── index.js
│   ├── tests/                # Tests (dashboard.test.js)
│   ├── package.json
│   └── vite.config.ts
│
├── backend-node/             # API REST principale (Node.js/Express)
│   ├── server.js            # Point d'entrée du serveur
│   ├── middlewares/         # Middlewares Express
│   │   ├── authMiddleware.js    # Authentification JWT
│   │   └── errorHandler.js      # Gestion globale des erreurs
│   ├── routes/              # Routes API
│   │   ├── userRoutes.js
│   │   ├── gigRoutes.js
│   │   ├── orderRoutes.js
│   │   ├── categoryRoutes.js
│   │   ├── reviewRoutes.js
│   │   ├── messageRoutes.js
│   │   ├── paymentRoutes.js
│   │   ├── favoriteRoutes.js
│   │   ├── notificationRoutes.js
│   │   └── complaintRoutes.js
│   ├── rpc-client/          # Client XML-RPC
│   │   ├── rpcClient.js     # Client RPC principal
│   │   └── README.md
│   ├── models/              # Modèles Mongoose
│   ├── utils/               # Utilitaires (pagination, rpcClient wrapper)
│   ├── tests/               # Tests (users.test.js, gigs.test.js, orders.test.js)
│   ├── package.json
│   └── jest.config.js
│
├── rpc-server/              # Serveur RPC Python (XML-RPC)
│   ├── src/
│   │   ├── server.py        # Serveur XML-RPC principal
│   │   ├── services/        # Services RPC
│   │   │   ├── users_service.py
│   │   │   ├── gigs_service.py
│   │   │   ├── orders_service.py
│   │   │   ├── categories_service.py
│   │   │   ├── reviews_service.py
│   │   │   ├── messages_service.py
│   │   │   ├── payments_service.py
│   │   │   └── notifications_service.py
│   │   └── utils/           # Utilitaires
│   │       ├── security.py      # JWT, password hashing, permissions
│   │       ├── database.py      # Helpers MongoDB, transactions, aggregations
│   │       └── validators.py     # Validation des données
│   ├── tests/               # Tests Python (test_users.py, test_gigs.py, etc.)
│   ├── requirements.txt
│   ├── pytest.ini
│   └── README.md
│
├── database/                # Scripts et migrations MongoDB
│   ├── dbConfig.js          # Configuration MongoDB
│   ├── models/              # Modèles Mongoose
│   ├── setupDatabase.js     # Script d'initialisation
│   ├── insertSampleData.js  # Données d'exemple
│   ├── resetDatabase.js     # Script de réinitialisation
│   ├── package.json
│   └── README.md
│
└── integration-qa/         # Tests d'intégration et QA
    ├── tests/
    │   ├── rpc_tests.py     # Tests directs RPC
    │   ├── api_tests.js     # Tests Node ↔ RPC integration
    │   └── e2e_tests.js     # Tests end-to-end complets
    ├── docker-compose.yml   # Docker Compose pour tests
    ├── Dockerfile.*         # Dockerfiles pour test runners
    ├── requirements.txt
    ├── package.json
    └── README.md
```

## 🚀 Installation

### Prérequis

- **Node.js** v18.0.0 ou supérieur
- **Python** 3.11 ou supérieur
- **Docker** et **Docker Compose** (recommandé)
- **MongoDB** 7.0+ (ou utiliser Docker)
- **Redis** 7+ (optionnel, ou utiliser Docker)
- **Git**

### Installation Rapide avec Docker

```bash
# 1. Cloner le dépôt
git clone <repository-url>
cd workNet1

# 2. Copier et configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos configurations

# 3. Démarrer tous les services
docker-compose up -d

# 4. Vérifier que tous les services sont démarrés
docker-compose ps

# 5. Accéder aux applications
# Frontend Client: http://localhost:3000
# Frontend Freelancer: http://localhost:3001
# Backend API: http://localhost:3000/api
# RPC Server: http://localhost:8000
```

### Installation Manuelle

#### 1. Cloner le dépôt

```bash
git clone <repository-url>
cd workNet1
```

#### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Éditer `.env` avec vos configurations (voir `.env.example` pour les variables disponibles).

#### 3. Installer les dépendances

**Backend Node.js :**
```bash
cd backend-node
npm install
cd ..
```

**Frontend Client :**
```bash
cd frontend-client
npm install
cd ..
```

**Frontend Freelancer :**
```bash
cd frontend-freelancer
npm install
cd ..
```

**RPC Server Python :**
```bash
cd rpc-server
pip install -r requirements.txt
cd ..
```

**Database Scripts :**
```bash
cd database
npm install
cd ..
```

**Integration QA :**
```bash
cd integration-qa
npm install
pip install -r requirements.txt
cd ..
```

#### 4. Configurer MongoDB

```bash
cd database
npm run setup    # Créer les collections et validateurs
npm run seed     # Insérer les données d'exemple
cd ..
```

#### 5. Démarrer les services

**Option A : Avec Docker Compose (Recommandé)**
```bash
docker-compose up
```

**Option B : Manuellement**

Terminal 1 - MongoDB (si non Docker) :
```bash
mongod --dbpath /path/to/data
```

Terminal 2 - Redis (si non Docker) :
```bash
redis-server
```

Terminal 3 - RPC Server :
```bash
cd rpc-server
python src/server.py
```

Terminal 4 - Backend Node.js :
```bash
cd backend-node
npm run dev
```

Terminal 5 - Frontend Client :
```bash
cd frontend-client
npm run dev
```

Terminal 6 - Frontend Freelancer :
```bash
cd frontend-freelancer
npm run dev
```

#### 6. Accéder aux applications

- **Frontend Client** : http://localhost:3000
- **Frontend Freelancer** : http://localhost:3001
- **Backend API** : http://localhost:3000/api
- **RPC Server** : http://localhost:8000
- **Health Check** : http://localhost:3000/health

## 💻 Guide de Développement

### Structure du Code

#### Backend Node.js

Les routes sont organisées par ressource dans `backend-node/routes/`. Chaque route :
- Valide les données d'entrée avec `express-validator`
- Utilise l'authentification JWT via `authMiddleware`
- Appelle le serveur RPC pour la logique métier
- Gère les erreurs via le middleware global

**Exemple de route :**
```javascript
router.post('/gigs', 
  authMiddleware, 
  createGigValidation, 
  handleValidationErrors,
  async (req, res, next) => {
    try {
      const rpcClient = req.app.locals.rpcClient;
      const result = await rpcClient.gigsService_create(
        req.user.id,
        req.body
      );
      res.status(201).json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }
);
```

#### RPC Server Python

Les services RPC sont dans `rpc-server/src/services/`. Chaque service :
- Valide les données avec `validators.py`
- Utilise MongoDB via PyMongo
- Gère les transactions MongoDB
- Retourne des résultats standardisés

**Exemple de service :**
```python
def create(self, user_id, gig_data):
    try:
        user_id = validate_object_id(user_id)
        # Validation et logique métier
        result = self.collection.insert_one(gig_data)
        return {'success': True, 'gig_id': str(result.inserted_id)}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

#### Frontend React

Les composants sont organisés par fonctionnalité :
- `components/` - Composants réutilisables
- `pages/` - Pages de l'application
- `services/` - Appels API
- `hooks/` - Hooks React personnalisés

**Exemple de service :**
```javascript
export const gigsService = {
  async getGigs(params = {}) {
    const response = await api.get('/gigs', { params });
    return response;
  }
};
```

### Standards de Code

- **JavaScript/TypeScript** : ESLint + Prettier
- **Python** : PEP 8 (utiliser `black` ou `autopep8`)
- **Commits** : Format conventionnel (feat:, fix:, docs:, etc.)
- **Tests** : Minimum 80% de couverture

### Workflow de Développement

1. **Créer une branche**
   ```bash
   git checkout -b feature/nom-de-la-fonctionnalite
   ```

2. **Développer et tester**
   ```bash
   # Backend
   cd backend-node
   npm run dev
   npm test

   # Frontend
   cd frontend-client
   npm run dev
   npm test
   ```

3. **Commit**
   ```bash
   git add .
   git commit -m "feat: ajouter nouvelle fonctionnalité"
   ```

4. **Push et Pull Request**
   ```bash
   git push origin feature/nom-de-la-fonctionnalite
   ```

## 📚 Documentation API

### Base URL

```
http://localhost:3000/api
```

### Authentification

La plupart des endpoints nécessitent un token JWT dans le header :

```
Authorization: Bearer <token>
```

### Endpoints Principaux

#### Users

- `POST /api/users/register` - Inscription
- `POST /api/users/login` - Connexion
- `GET /api/users/profile/me` - Profil utilisateur (authentifié)
- `PUT /api/users/profile/me` - Mettre à jour le profil
- `GET /api/users/:id` - Obtenir un utilisateur par ID
- `GET /api/users` - Liste des utilisateurs (avec pagination)

#### Gigs

- `GET /api/gigs` - Liste des gigs (recherche, filtres, pagination)
- `GET /api/gigs/:id` - Détails d'un gig
- `POST /api/gigs` - Créer un gig (authentifié, seller)
- `PUT /api/gigs/:id` - Mettre à jour un gig (authentifié, owner)
- `DELETE /api/gigs/:id` - Supprimer un gig (authentifié, owner)
- `GET /api/gigs/user/:userId` - Gigs d'un utilisateur

#### Orders

- `GET /api/orders` - Liste des commandes (authentifié)
- `GET /api/orders/:id` - Détails d'une commande
- `POST /api/orders` - Créer une commande (authentifié)
- `PUT /api/orders/:id/status` - Mettre à jour le statut
- `PUT /api/orders/:id` - Mettre à jour une commande

#### Categories

- `GET /api/categories` - Liste des catégories
- `GET /api/categories/:id` - Détails d'une catégorie
- `POST /api/categories` - Créer une catégorie (admin)
- `PUT /api/categories/:id` - Mettre à jour (admin)
- `DELETE /api/categories/:id` - Supprimer (admin)

#### Reviews

- `GET /api/reviews/gig/:gigId` - Avis d'un gig
- `POST /api/reviews` - Créer un avis (authentifié)
- `PUT /api/reviews/:id` - Mettre à jour un avis (owner)
- `DELETE /api/reviews/:id` - Supprimer un avis (owner)

#### Messages

- `GET /api/messages/conversations` - Liste des conversations
- `GET /api/messages/conversation/:id` - Messages d'une conversation
- `POST /api/messages` - Envoyer un message
- `PUT /api/messages/:id/read` - Marquer comme lu

#### Payments

- `GET /api/payments` - Liste des paiements (authentifié)
- `GET /api/payments/:id` - Détails d'un paiement
- `POST /api/payments` - Créer un paiement
- `PUT /api/payments/:id/process` - Traiter un paiement
- `PUT /api/payments/:id/refund` - Rembourser

#### Notifications

- `GET /api/notifications` - Liste des notifications (authentifié)
- `PUT /api/notifications/:id/read` - Marquer comme lu
- `PUT /api/notifications/read-all` - Tout marquer comme lu
- `DELETE /api/notifications/:id` - Supprimer une notification

### Exemples de Requêtes

#### Inscription

```bash
curl -X POST http://localhost:3000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "role": "client"
  }'
```

#### Connexion

```bash
curl -X POST http://localhost:3000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

#### Créer un Gig (authentifié)

```bash
curl -X POST http://localhost:3000/api/gigs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "title": "Logo Design",
    "description": "Professional logo design service",
    "category": "Graphic Design",
    "price": 50,
    "deliveryTime": 3
  }'
```

#### Rechercher des Gigs

```bash
curl "http://localhost:3000/api/gigs?search=logo&category=Graphic%20Design&page=1&limit=10"
```

### Codes de Statut HTTP

- `200 OK` - Succès
- `201 Created` - Ressource créée
- `400 Bad Request` - Requête invalide
- `401 Unauthorized` - Non authentifié
- `403 Forbidden` - Non autorisé
- `404 Not Found` - Ressource non trouvée
- `500 Internal Server Error` - Erreur serveur

## 🧪 Tests

### Tests Unitaires

**Backend Node.js :**
```bash
cd backend-node
npm test
npm run test:watch
npm test -- --coverage
```

**RPC Server Python :**
```bash
cd rpc-server
pytest
pytest --cov=src --cov-report=html
```

**Frontend Client :**
```bash
cd frontend-client
npm test
npm run test:coverage
```

**Frontend Freelancer :**
```bash
cd frontend-freelancer
npm test
npm run test:coverage
```

### Tests d'Intégration

```bash
cd integration-qa

# Tests RPC directs
npm run test:rpc

# Tests API ↔ RPC
npm run test:api

# Tests E2E
npm run test:e2e

# Tous les tests
npm run test:all
```

### Tests avec Docker

```bash
cd integration-qa
docker-compose build
docker-compose up --abort-on-container-exit
```

## 🚢 Déploiement

### Préparation

1. **Variables d'environnement de production**
   ```bash
   cp .env.example .env.production
   # Configurer les variables pour la production
   ```

2. **Build des applications**
   ```bash
   # Frontend Client
   cd frontend-client
   npm run build

   # Frontend Freelancer
   cd frontend-freelancer
   npm run build

   # Backend Node.js (si TypeScript)
   cd backend-node
   npm run build
   ```

### Déploiement avec Docker

```bash
# Build des images
docker-compose -f docker-compose.prod.yml build

# Démarrer en production
docker-compose -f docker-compose.prod.yml up -d

# Vérifier les logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Déploiement Manuel

1. **Backend Node.js**
   ```bash
   cd backend-node
   NODE_ENV=production npm start
   ```

2. **RPC Server**
   ```bash
   cd rpc-server
   python src/server.py
   ```

3. **Frontend** (servir les fichiers build avec nginx/apache)

## 🤝 Contribution

Nous accueillons les contributions ! Veuillez suivre ces étapes :

### Processus de Contribution

1. **Fork le projet**

2. **Créer une branche**
   ```bash
   git checkout -b feature/AmazingFeature
   ```

3. **Faire vos modifications**
   - Suivre les standards de code
   - Ajouter des tests pour les nouvelles fonctionnalités
   - Mettre à jour la documentation

4. **Tester vos modifications**
   ```bash
   npm test
   npm run lint
   ```

5. **Commit vos changements**
   ```bash
   git commit -m "feat: Add AmazingFeature"
   ```
   
   Formats de commit :
   - `feat:` - Nouvelle fonctionnalité
   - `fix:` - Correction de bug
   - `docs:` - Documentation
   - `style:` - Formatage
   - `refactor:` - Refactoring
   - `test:` - Tests
   - `chore:` - Tâches de maintenance

6. **Push vers la branche**
   ```bash
   git push origin feature/AmazingFeature
   ```

7. **Ouvrir une Pull Request**

### Guidelines de Code

- **JavaScript/TypeScript** : Utiliser ESLint et Prettier
- **Python** : Suivre PEP 8
- **Tests** : Maintenir une couverture > 80%
- **Documentation** : Mettre à jour les README et commentaires
- **Commits** : Messages clairs et descriptifs

### Code Review

Toutes les Pull Requests seront revues pour :
- Qualité du code
- Tests et couverture
- Documentation
- Performance
- Sécurité

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Contact et Support

- **Issues GitHub** : [Ouvrir une issue](https://github.com/your-repo/issues)
- **Email** : support@worknet.example.com
- **Documentation** : Voir les README dans chaque dossier

## 🙏 Remerciements

- Tous les contributeurs du projet
- La communauté open source
- Les technologies utilisées et leurs mainteneurs

---

**WorkNet** - Connecter talents et opportunités 🚀
