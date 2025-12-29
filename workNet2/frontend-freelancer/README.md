# WorkNet Frontend Freelancer

Application React pour les freelancers de WorkNet. Interface permettant aux freelancers de gérer leurs gigs, commandes, messages et analytics.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Configuration](#configuration)
- [Structure du Projet](#structure-du-projet)
- [Pages](#pages)
- [Services](#services)
- [Développement](#développement)
- [Tests](#tests)

## 🎯 Vue d'ensemble

L'application frontend freelancer permet :
- Dashboard avec statistiques et graphiques
- Gestion complète des gigs (CRUD)
- Gestion des commandes avec workflow
- Messagerie en temps réel
- Analytics et visualisations

## 🚀 Installation

```bash
# Installer les dépendances
npm install

# Copier le fichier d'environnement
cp ../.env.example .env
# Configurer VITE_API_URL dans .env
```

## ⚙️ Configuration

### Variables d'environnement

Créer un fichier `.env` :

```env
VITE_API_URL=http://localhost:3000/api
VITE_WS_URL=ws://localhost:5002
VITE_NODE_ENV=development
```

## 📁 Structure du Projet

```
frontend-freelancer/
├── src/
│   ├── App.js              # Composant principal avec routes
│   ├── index.js            # Point d'entrée avec React Query
│   ├── index.css           # Styles Tailwind
│   │
│   ├── components/         # Composants réutilisables
│   │   ├── Navbar.jsx      # Navigation avec compteur messages
│   │   ├── Footer.jsx      # Footer
│   │   ├── GigForm.jsx     # Formulaire création/édition gig
│   │   ├── OrderCard.jsx   # Carte pour afficher une commande
│   │   └── AnalyticsCard.jsx # Composant graphiques réutilisable
│   │
│   ├── pages/              # Pages de l'application
│   │   ├── Dashboard.jsx   # Dashboard avec stats et graphiques
│   │   ├── MyGigs.jsx      # Gestion des gigs
│   │   ├── Messages.jsx   # Messagerie
│   │   ├── Login.jsx       # Connexion
│   │   └── Register.jsx    # Inscription freelancer
│   │
│   └── services/           # Services API
│       ├── api.js          # Configuration Axios
│       ├── authService.js  # Authentification
│       ├── gigsService.js  # Gestion des gigs
│       ├── ordersService.js # Gestion des commandes
│       ├── messagesService.js # Messagerie
│       ├── paymentsService.js # Paiements
│       └── categoriesService.js # Catégories
│
├── tests/                  # Tests
│   ├── dashboard.test.js   # Tests dashboard
│   └── setup.js
│
├── public/
│   └── index.html
│
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

## 📄 Pages

### Dashboard (`/`)
- Statistiques : Total Gigs, Total Orders, Total Earnings, Rating
- Graphiques : Orders by Status (Bar Chart), Earnings Trend (Line Chart)
- Liste des commandes récentes
- Protection de route (redirection si non authentifié)

### My Gigs (`/gigs`)
- Liste des gigs du freelancer
- Création/édition via modal GigForm
- Actions : Edit, Activate/Deactivate, Delete
- Affichage : Image, titre, description, prix, note, ventes

### Messages (`/messages`)
- Liste des conversations à gauche
- Zone de messages à droite
- Envoi de messages en temps réel
- Compteur de messages non lus
- Auto-refresh toutes les 5 secondes

### Login (`/login`)
- Connexion avec vérification du rôle freelancer
- Redirection si rôle incorrect

### Register (`/register`)
- Inscription en tant que freelancer
- Validation complète

## 🔌 Services

### gigsService
- `getMyGigs(params)` - Gigs du freelancer
- `createGig(gigData)` - Créer un gig
- `updateGig(id, updates)` - Mettre à jour
- `deleteGig(id)` - Supprimer
- `toggleGigStatus(id, isActive)` - Activer/désactiver

### messagesService
- `getConversations(params)` - Liste des conversations
- `getConversationMessages(conversationId)` - Messages d'une conversation
- `sendMessage(conversationId, text)` - Envoyer un message
- `markAsRead(messageId)` - Marquer comme lu
- `getUnreadCount()` - Nombre de messages non lus

### paymentsService
- `getPayments(params)` - Liste des paiements
- `getEarningsSummary(period)` - Résumé des gains
- `getPaymentById(id)` - Détails d'un paiement

### ordersService
- `getOrders(params)` - Commandes (type: seller)
- `updateOrderStatus(id, status)` - Mettre à jour statut
- `getOrderById(id)` - Détails d'une commande

## 🛠 Développement

### Scripts

```bash
# Développement (port 3001)
npm run dev

# Build production
npm run build

# Preview build
npm run preview

# Tests
npm test
npm run test:coverage
```

### Démarrer en développement

```bash
npm run dev
```

L'application démarre sur `http://localhost:3001`.

## 🧪 Tests

```bash
# Tous les tests
npm test

# Mode watch
npm test -- --watch

# Avec couverture
npm run test:coverage
```

### Tests Disponibles

- `dashboard.test.js` - Tests du dashboard freelancer

Voir `tests/README.md` pour plus de détails.

## 📊 Analytics

Le dashboard utilise **Recharts** pour les visualisations :
- Bar Chart pour orders by status
- Line Chart pour earnings trend
- Pie Chart disponible via AnalyticsCard

## 🎨 Styling

L'application utilise **Tailwind CSS** avec un thème vert pour les freelancers (différent du client qui utilise bleu).

## 🔐 Authentification

- Vérification du rôle freelancer lors du login
- Redirection si rôle incorrect
- Protection de toutes les routes sauf login/register

## 📚 Technologies

- **React 18** - UI Library
- **React Router v6** - Routing
- **React Query** - Data fetching et cache
- **React Hook Form** - Form management
- **Recharts** - Graphiques et visualisations
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Vitest** - Testing framework
- **React Testing Library** - Component testing

## 📄 Licence

ISC

