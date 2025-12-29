# WorkNet Frontend Client

Application React pour les clients de WorkNet. Interface permettant aux clients de rechercher des services, créer des commandes et communiquer avec les freelancers.

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

L'application frontend client permet :
- Recherche et découverte de gigs
- Inscription et connexion
- Création et gestion de commandes
- Visualisation des commandes passées
- Navigation intuitive et responsive

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
frontend-client/
├── src/
│   ├── App.js              # Composant principal avec routes
│   ├── index.js            # Point d'entrée avec React Query
│   ├── index.css           # Styles Tailwind
│   │
│   ├── components/         # Composants réutilisables
│   │   ├── Navbar.jsx      # Navigation avec auth
│   │   ├── Footer.jsx      # Footer
│   │   └── GigCard.jsx    # Carte pour afficher un gig
│   │
│   ├── pages/              # Pages de l'application
│   │   ├── Home.jsx        # Page d'accueil avec recherche
│   │   ├── Login.jsx       # Formulaire de connexion
│   │   ├── Register.jsx    # Formulaire d'inscription
│   │   └── Orders.jsx      # Gestion des commandes
│   │
│   └── services/           # Services API
│       ├── api.js          # Configuration Axios
│       ├── authService.js   # Authentification
│       ├── gigsService.js  # Gestion des gigs
│       └── ordersService.js # Gestion des commandes
│
├── tests/                  # Tests
│   ├── auth.test.js        # Tests login/register
│   ├── gigs.test.js        # Tests gig display/search
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

### Home (`/`)
- Barre de recherche de gigs
- Filtres par catégorie
- Tri (Newest, Price, Rating, Popular)
- Grille de gigs avec pagination
- États : loading, error, empty

### Login (`/login`)
- Formulaire de connexion
- Validation avec react-hook-form
- Gestion des erreurs
- Redirection après connexion

### Register (`/register`)
- Formulaire d'inscription
- Validation complète
- Vérification de correspondance des mots de passe
- Redirection après inscription

### Orders (`/orders`)
- Liste des commandes de l'utilisateur
- Filtres : type (all/buyer), statut
- Affichage des détails
- Actions : View Details, Cancel

## 🔌 Services

### authService
- `register(userData)` - Inscription
- `login(email, password)` - Connexion
- `logout()` - Déconnexion
- `getCurrentUser()` - Utilisateur actuel
- `isAuthenticated()` - Vérification auth
- `updateProfile(updates)` - Mise à jour profil

### gigsService
- `getGigs(params)` - Liste avec pagination/filtres
- `getGigById(id)` - Détails d'un gig
- `searchGigs(query, filters)` - Recherche
- `getGigsByCategory(category)` - Par catégorie

### ordersService
- `getOrders(params)` - Liste des commandes
- `getOrderById(id)` - Détails d'une commande
- `createOrder(orderData)` - Créer commande
- `updateOrderStatus(id, status)` - Mettre à jour statut
- `cancelOrder(id, reason)` - Annuler commande

## 🛠 Développement

### Scripts

```bash
# Développement
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

L'application démarre sur `http://localhost:3000`.

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

- `auth.test.js` - Tests d'authentification (login/register)
- `gigs.test.js` - Tests d'affichage et recherche de gigs

Voir `tests/README.md` pour plus de détails.

## 🎨 Styling

L'application utilise **Tailwind CSS** pour le styling. Les classes utilitaires sont utilisées directement dans les composants.

### Configuration Tailwind

Voir `tailwind.config.js` pour la configuration personnalisée.

## 📱 Responsive Design

L'application est entièrement responsive :
- Mobile-first approach
- Breakpoints Tailwind
- Navigation mobile avec menu hamburger

## 🔐 Authentification

L'authentification est gérée via :
- JWT tokens stockés dans localStorage
- Intercepteurs Axios pour ajouter le token
- Redirection automatique si non authentifié
- Refresh du token si nécessaire

## 📚 Technologies

- **React 18** - UI Library
- **React Router v6** - Routing
- **React Query** - Data fetching et cache
- **React Hook Form** - Form management
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Vitest** - Testing framework
- **React Testing Library** - Component testing

## 📄 Licence

ISC

