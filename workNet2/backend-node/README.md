# WorkNet Backend Node.js API

API Gateway RESTful pour la plateforme WorkNet, construite avec Express.js et MongoDB. Cette API sert de point d'entrée principal et communique avec le serveur RPC Python pour la logique métier complexe.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Configuration](#configuration)
- [Structure du Projet](#structure-du-projet)
- [API Endpoints](#api-endpoints)
- [Authentification](#authentification)
- [RPC Client](#rpc-client)
- [Développement](#développement)
- [Tests](#tests)
- [Déploiement](#déploiement)

## 🎯 Vue d'ensemble

Le backend Node.js agit comme une API Gateway qui :
- Expose des endpoints RESTful
- Gère l'authentification JWT
- Valide les données d'entrée
- Communique avec le serveur RPC Python pour la logique métier
- Gère les erreurs de manière centralisée
- Fournit la pagination, la recherche et le filtrage

## 🚀 Installation

```bash
# Installer les dépendances
npm install

# Copier le fichier d'environnement
cp ../.env.example .env
# Éditer .env avec vos configurations
```

## ⚙️ Configuration

### Variables d'environnement

Créer un fichier `.env` à la racine du projet :

```env
# Server
NODE_ENV=development
PORT=3000

# MongoDB
MONGODB_URI=mongodb+srv://worknet_db:20011110@cluster0.kgbzmzf.mongodb.net/WorkNetBD?retryWrites=true&w=majority

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRES_IN=7d

# CORS
CORS_ORIGIN=http://localhost:3000,http://localhost:3001

# RPC Server
RPC_HOST=localhost
RPC_PORT=8000
RPC_PATH=/RPC2
RPC_TIMEOUT=10000
RPC_RETRIES=3

# Redis (optionnel)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX=100
```

## 📁 Structure du Projet

```
backend-node/
├── server.js                 # Point d'entrée du serveur Express
├── package.json
├── jest.config.js           # Configuration Jest pour tests
│
├── middlewares/             # Middlewares Express
│   ├── authMiddleware.js    # Authentification JWT
│   └── errorHandler.js      # Gestion globale des erreurs
│
├── routes/                  # Routes API
│   ├── userRoutes.js        # Routes utilisateurs
│   ├── gigRoutes.js         # Routes gigs
│   ├── orderRoutes.js       # Routes commandes
│   ├── categoryRoutes.js    # Routes catégories
│   ├── reviewRoutes.js     # Routes avis
│   ├── messageRoutes.js     # Routes messages
│   ├── paymentRoutes.js     # Routes paiements
│   ├── favoriteRoutes.js    # Routes favoris
│   ├── notificationRoutes.js # Routes notifications
│   └── complaintRoutes.js  # Routes réclamations
│
├── rpc-client/             # Client XML-RPC
│   ├── rpcClient.js        # Client RPC principal avec retry/timeout
│   ├── index.js
│   └── README.md
│
├── models/                 # Modèles Mongoose (pour référence)
│   ├── userModel.js
│   ├── gigModel.js
│   └── ...
│
├── utils/                  # Utilitaires
│   ├── rpcClient.js        # Wrapper legacy pour compatibilité
│   └── pagination.js       # Helpers de pagination
│
└── tests/                  # Tests
    ├── users.test.js       # Tests routes users
    ├── gigs.test.js        # Tests routes gigs
    ├── orders.test.js      # Tests routes orders
    ├── setup.js            # Configuration des tests
    └── README.md
```

## 🔌 API Endpoints

### Health Check

```
GET /health
```

Réponse :
```json
{
  "status": "ok",
  "message": "WorkNet Backend API is running",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "uptime": 123.456
}
```

### Users

#### Register
```
POST /api/users/register
Body: { username, email, password, role? }
```

#### Login
```
POST /api/users/login
Body: { email, password }
```

#### Get Profile
```
GET /api/users/profile/me
Headers: { Authorization: Bearer <token> }
```

#### Update Profile
```
PUT /api/users/profile/me
Headers: { Authorization: Bearer <token> }
Body: { username?, email?, phone?, country?, ... }
```

#### Get User by ID
```
GET /api/users/:id
Headers: { Authorization: Bearer <token> }
```

#### Get All Users
```
GET /api/users?page=1&limit=10&role=freelancer
Headers: { Authorization: Bearer <token> }
```

### Gigs

#### Get All Gigs
```
GET /api/gigs?search=logo&category=Design&minPrice=10&maxPrice=100&page=1&limit=12
```

#### Get Gig by ID
```
GET /api/gigs/:id
```

#### Create Gig
```
POST /api/gigs
Headers: { Authorization: Bearer <token> }
Body: { title, description, category, price, deliveryTime, ... }
```

#### Update Gig
```
PUT /api/gigs/:id
Headers: { Authorization: Bearer <token> }
Body: { title?, price?, ... }
```

#### Delete Gig
```
DELETE /api/gigs/:id
Headers: { Authorization: Bearer <token> }
```

#### Get Gigs by User
```
GET /api/gigs/user/:userId
```

### Orders

#### Get All Orders
```
GET /api/orders?status=pending&type=buyer&page=1&limit=10
Headers: { Authorization: Bearer <token> }
```

#### Get Order by ID
```
GET /api/orders/:id
Headers: { Authorization: Bearer <token> }
```

#### Create Order
```
POST /api/orders
Headers: { Authorization: Bearer <token> }
Body: { gigId, requirements?, deliveryDate? }
```

#### Update Order Status
```
PUT /api/orders/:id/status
Headers: { Authorization: Bearer <token> }
Body: { status }
```

#### Update Order
```
PUT /api/orders/:id
Headers: { Authorization: Bearer <token> }
Body: { requirements?, deliverables?, ... }
```

### Categories

```
GET /api/categories
GET /api/categories/:id
POST /api/categories (admin)
PUT /api/categories/:id (admin)
DELETE /api/categories/:id (admin)
```

### Reviews

```
GET /api/reviews/gig/:gigId
POST /api/reviews
PUT /api/reviews/:id
DELETE /api/reviews/:id
```

### Messages

```
GET /api/messages/conversations
GET /api/messages/conversation/:id
POST /api/messages
PUT /api/messages/:id/read
GET /api/messages/unread-count
```

### Payments

```
GET /api/payments
GET /api/payments/:id
POST /api/payments
PUT /api/payments/:id/process
PUT /api/payments/:id/refund
```

### Notifications

```
GET /api/notifications
PUT /api/notifications/:id/read
PUT /api/notifications/read-all
DELETE /api/notifications/:id
GET /api/notifications/unread-count
```

## 🔐 Authentification

### JWT Authentication

Toutes les routes protégées nécessitent un token JWT dans le header :

```
Authorization: Bearer <token>
```

### Middleware d'Authentification

```javascript
const { authMiddleware, authorize, isSeller, isOwnerOrAdmin } = require('./middlewares/authMiddleware');

// Route protégée
router.get('/protected', authMiddleware, (req, res) => {
  res.json({ user: req.user });
});

// Route avec rôle spécifique
router.delete('/admin-only', authMiddleware, authorize('admin'), (req, res) => {
  // Seuls les admins peuvent accéder
});

// Route seller uniquement
router.post('/create-gig', authMiddleware, isSeller, (req, res) => {
  // Seuls les sellers peuvent créer des gigs
});

// Route owner ou admin
router.put('/update/:id', authMiddleware, isOwnerOrAdmin, (req, res) => {
  // Owner ou admin peuvent modifier
});
```

### Obtenir un Token

```bash
# Login
curl -X POST http://localhost:3000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Réponse contient le token
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": { ... }
  }
}
```

## 🔗 RPC Client

Le backend communique avec le serveur RPC Python via XML-RPC.

### Configuration

Le client RPC est configuré dans `rpc-client/rpcClient.js` et accessible via :

```javascript
const { getRPCClient } = require('./rpc-client/rpcClient');
const rpcClient = getRPCClient();
```

### Utilisation dans les Routes

```javascript
router.post('/gigs', authMiddleware, async (req, res, next) => {
  try {
    const rpcClient = req.app.locals.rpcClient;
    const result = await rpcClient.gigsService_create(
      req.user.id,
      req.body
    );
    
    if (result.success) {
      res.status(201).json({ success: true, data: result });
    } else {
      res.status(400).json({ success: false, message: result.error });
    }
  } catch (error) {
    next(error);
  }
});
```

### Méthodes RPC Disponibles

Voir `rpc-client/README.md` pour la liste complète des méthodes RPC disponibles.

## 🛠 Développement

### Scripts Disponibles

```bash
# Développement avec nodemon
npm run dev

# Production
npm start

# Tests
npm test
npm run test:watch
npm test -- --coverage

# Linting
npm run lint
npm run lint:fix
```

### Mode Développement

```bash
npm run dev
```

Le serveur démarre sur `http://localhost:3000` avec hot-reload via nodemon.

### Structure d'une Route

```javascript
const express = require('express');
const router = express.Router();
const { body, validationResult } = require('express-validator');
const { authMiddleware } = require('../middlewares/authMiddleware');
const { callRPC } = require('../utils/rpcClient');

// Validation rules
const createValidation = [
  body('title').trim().isLength({ min: 5, max: 200 }),
  body('price').isFloat({ min: 0 })
];

// Helper pour validation errors
const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      success: false,
      message: 'Validation failed',
      errors: errors.array()
    });
  }
  next();
};

// Route
router.post('/',
  authMiddleware,
  createValidation,
  handleValidationErrors,
  async (req, res, next) => {
    try {
      // Appel RPC
      const result = await callRPC(req, 'gigsService.create', [
        req.user.id,
        req.body
      ]);
      
      res.status(201).json({
        success: true,
        data: result
      });
    } catch (error) {
      next(error);
    }
  }
);

module.exports = router;
```

## 🧪 Tests

### Exécuter les Tests

```bash
# Tous les tests
npm test

# Mode watch
npm run test:watch

# Avec couverture
npm test -- --coverage
```

### Structure des Tests

Les tests utilisent Jest et Supertest. Voir `tests/README.md` pour plus de détails.

### Exemple de Test

```javascript
describe('POST /api/gigs', () => {
  it('should create a gig successfully', async () => {
    const response = await request(app)
      .post('/api/gigs')
      .set('Authorization', `Bearer ${token}`)
      .send({
        title: 'Test Gig',
        description: 'Test description',
        category: 'Design',
        price: 50,
        deliveryTime: 3
      });

    expect(response.status).toBe(201);
    expect(response.body.success).toBe(true);
  });
});
```

## 🚢 Déploiement

### Production

```bash
# Build (si TypeScript)
npm run build

# Start
NODE_ENV=production npm start
```

### Docker

```bash
docker build -t worknet-backend .
docker run -p 3000:3000 worknet-backend
```

### Variables d'Environnement de Production

Assurez-vous de configurer :
- `NODE_ENV=production`
- `JWT_SECRET` fort et sécurisé
- `MONGODB_URI` de production
- `CORS_ORIGIN` avec les domaines autorisés

## 🔒 Sécurité

- **Helmet** : Headers de sécurité HTTP
- **CORS** : Configuration stricte des origines
- **Rate Limiting** : 100 requêtes par 15 minutes par IP
- **JWT** : Tokens sécurisés avec expiration
- **Input Validation** : Validation stricte avec express-validator
- **Password Hashing** : Bcrypt avec salt rounds

## 📊 Monitoring

### Health Check

```
GET /health
```

Vérifie :
- État du serveur
- Connexion MongoDB
- Disponibilité RPC Server

### Logging

Les logs sont gérés par Morgan :
- Format `dev` en développement
- Format `combined` en production
- Logs dans `console` et fichiers (si configuré)

## 🐛 Dépannage

### Problèmes Courants

1. **Erreur de connexion MongoDB**
   - Vérifier `MONGODB_URI` dans `.env`
   - Vérifier que MongoDB est démarré

2. **Erreur RPC Server**
   - Vérifier que le serveur RPC est démarré
   - Vérifier `RPC_HOST` et `RPC_PORT`

3. **Erreur JWT**
   - Vérifier `JWT_SECRET` dans `.env`
   - Vérifier que le token n'est pas expiré

## 📚 Ressources

- [Express.js Documentation](https://expressjs.com/)
- [Mongoose Documentation](https://mongoosejs.com/)
- [JWT Documentation](https://jwt.io/)
- [Express Validator](https://express-validator.github.io/docs/)

## 📄 Licence

ISC
