# WorkNet Database

Scripts et utilitaires pour la gestion de la base de données MongoDB de WorkNet.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Scripts Disponibles](#scripts-disponibles)
- [Modèles](#modèles)
- [Utilisation](#utilisation)

## 🎯 Vue d'ensemble

Ce dossier contient :
- Configuration de connexion MongoDB
- Modèles Mongoose pour toutes les collections
- Scripts d'initialisation de la base de données
- Scripts d'insertion de données d'exemple
- Scripts de réinitialisation

## 🚀 Installation

```bash
npm install
```

## 📜 Scripts Disponibles

### Setup Database

Crée toutes les collections avec leurs validateurs JSON Schema et indexes :

```bash
npm run setup
# ou
node setupDatabase.js
```

### Insert Sample Data

Insère des données d'exemple dans la base de données :

```bash
npm run seed
# ou
node insertSampleData.js
```

### Initialize (Setup + Seed)

Exécute setup puis seed :

```bash
npm run init
```

### Reset Database

Supprime toutes les collections (⚠️ Attention : destructif) :

```bash
npm run reset
# ou
node resetDatabase.js
```

## 📊 Modèles

Tous les modèles Mongoose sont dans `models/` :

- `userModel.js` - Utilisateurs (clients et freelancers)
- `gigModel.js` - Services/Gigs proposés
- `orderModel.js` - Commandes
- `categoryModel.js` - Catégories de services
- `reviewModel.js` - Avis et notes
- `messageModel.js` - Messages entre utilisateurs
- `paymentModel.js` - Paiements
- `favoritesModel.js` - Favoris
- `notificationModel.js` - Notifications
- `complaintModel.js` - Réclamations

## 🔧 Configuration

### MongoDB Connection

La connexion est configurée dans `dbConfig.js` :

```javascript
const MONGODB_URI = process.env.MONGODB_URI || 
  'mongodb+srv://worknet_db:20011110@cluster0.kgbzmzf.mongodb.net/WorkNetBD?retryWrites=true&w=majority';
```

### Variables d'environnement

```env
MONGODB_URI=mongodb+srv://worknet_db:20011110@cluster0.kgbzmzf.mongodb.net/WorkNetBD?retryWrites=true&w=majority
```

## 💻 Utilisation

### Exemple : Utiliser les modèles

```javascript
const User = require('./models/userModel');

// Créer un utilisateur
const user = await User.create({
  username: 'testuser',
  email: 'test@example.com',
  password: 'hashedpassword',
  role: 'client'
});

// Trouver un utilisateur
const foundUser = await User.findOne({ email: 'test@example.com' });
```

### Exemple : Utiliser dbConfig

```javascript
const { connectDB, disconnectDB } = require('./dbConfig');

// Connecter
await connectDB();

// Utiliser la base de données
// ...

// Déconnecter
await disconnectDB();
```

## 📁 Structure

```
database/
├── dbConfig.js              # Configuration MongoDB
├── setupDatabase.js         # Script d'initialisation
├── insertSampleData.js      # Données d'exemple
├── resetDatabase.js         # Script de réinitialisation
├── models/                  # Modèles Mongoose
│   ├── userModel.js
│   ├── gigModel.js
│   ├── orderModel.js
│   └── ...
├── package.json
└── README.md
```

## ⚠️ Notes

- Les scripts utilisent l'URI MongoDB configurée dans `dbConfig.js`
- `resetDatabase.js` supprime **toutes** les données (utiliser avec précaution)
- Les validateurs JSON Schema sont créés lors du setup
- Les indexes sont créés automatiquement via les modèles Mongoose

## 📄 Licence

ISC
