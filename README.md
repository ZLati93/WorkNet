###WorkNet

## 📘 Description du Projet

**WorkNet** est une plateforme de marché freelance distribuée inspirée de Fiverr, conçue pour permettre aux freelances de publier et gérer leurs services ("gigs"), et aux clients de rechercher, commander et payer pour des tâches. Le système utilise des appels RPC (Remote Procedure Call) pour assurer une communication distribuée entre les composants, répondant aux exigences académiques en systèmes distribués (RPC/RMI/CORBA).

### 🎯 Objectifs
- Créer une plateforme de marché freelance distribuée.
- Implémenter une architecture modulaire avec séparation des responsabilités.
- Démontrer l'utilisation de RPC pour la logique métier.
- Fournir une interface utilisateur intuitive pour clients et freelances.

### ✨ Fonctionnalités Principales
- **Pour les Clients** :
  - Inscription/Connexion.
  - Recherche et visualisation des gigs.
  - Passage de commandes et suivi des paiements.
- **Pour les Freelances** :
  - Inscription/Connexion.
  - Création et gestion des gigs.
  - Gestion des commandes (acceptation/refus).
- **Fonctionnalités Communes** :
  - Messagerie en temps réel (optionnel).
  - Simulation de paiements.
  - Tolérance aux pannes (gestion d'erreurs réseau).

## 🏗 Architecture Générale

Le système est composé de plusieurs composants distribués :
- **Frontend Client (React)** : Interface pour les clients (recherche de gigs, commandes).
- **Frontend Freelancer (React)** : Interface pour les freelances (gestion des gigs, commandes).
- **Backend Gateway (Node.js)** : Passerelle entre le frontend et le serveur RPC.
- **Serveur RPC (Python)** : Logique métier distribuée (utilisateurs, gigs, commandes).
- **Base de Données (MongoDB)** : Stockage centralisé des données.

### Flux de Communication
1. Frontend → HTTP/JSON → Node.js Gateway.
2. Node.js → RPC → Serveur Python.
3. Serveur Python → Requêtes → MongoDB.

### 📊 Diagramme d'Architecture
Voici une description textuelle du diagramme d'architecture (utilisez Draw.io pour une version visuelle) :
- **Frontend (React, Port 3000)** : Envoie HTTP/JSON à Node.js (e.g., GET/POST vers /api/*).
- **Node.js API Gateway (Port 5000)** : Reçoit HTTP, convertit en appels RPC (e.g., via xmlrpc.client vers Python sur Port 8000).
- **Serveur RPC Python (Port 8000)** : Gère les méthodes RPC, interroge la DB sur Port 27017 (MongoDB).
- **MongoDB (Port 27017)** : Stocke les données.

*Idée de Diagramme Visuel :* Boîtes pour chaque composant, flèches montrant le flux (e.g., React → Node.js → Python RPC → DB), avec étiquettes pour protocoles (HTTP, RPC) et ports.

## 🛠 Technologies Utilisées
- **Frontend** : React.js (avec Tailwind CSS pour le styling).
- **Backend Gateway** : Node.js (Express.js).
- **Serveur RPC** : Python (XML-RPC ou gRPC).
- **Base de Données** : MongoDB Atlas.
- **Outils** : GitHub (versioning), Docker Compose (déploiement simulé), Draw.io (diagrammes UML).

## 🚀 Installation et Configuration

### Prérequis
- Node.js (v14+)
- Python (v3.8+)
- MongoDB (local ou Atlas)
- Git

### Étapes d'Installation
1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/votre-repo/WorkNet.git
   cd WorkNet
   ```

2. **Installer les dépendances pour chaque module** :
   - Frontend Client :
     ```bash
     cd frontend-client
     npm install
     ```
   - Frontend Freelancer :
     ```bash
     cd ../frontend-freelancer
     npm install
     ```
   - Backend Node.js :
     ```bash
     cd ../backend-node
     npm install
     ```
   - Serveur RPC Python :
     ```bash
     cd ../rpc-server
     pip install -r requirements.txt
     ```

3. **Configurer la base de données** :
   - Créez une base MongoDB et mettez à jour `dbConfig.js` avec l'URI.

4. **Lancer les composants** :
   - Démarrer MongoDB.
   - Serveur RPC : `python server.py` (port 8000).
   - Backend Node.js : `npm start` (port 5000).
   - Frontend Client : `npm start` (port 3000).
   - Frontend Freelancer : `npm start` (port 3001, par exemple).

5. **Simulation distribuée** :
   Utilisez `docker-compose.yml` dans `integration-qa/` pour lancer les conteneurs.

## 📖 Utilisation
- Accédez au frontend client via `http://localhost:3000`.
- Accédez au frontend freelance via `http://localhost:3001`.
- Testez les appels RPC via les tests dans `integration-qa/tests/`.

## 📁 Structure du Projet
```
WorkNet/
│
├── frontend-client/           # Interface React pour les clients
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/          # Appels Axios vers Node.js
│   │   └── App.js
│   └── package.json
│
├── frontend-freelancer/       # Interface React pour les freelances
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/          # Appels Axios vers Node.js
│   │   └── App.js
│   └── package.json
│
├── backend-node/              # Passerelle Node.js
│   ├── routes/
│   │   ├── gigs.js
│   │   ├── users.js
│   │   └── orders.js
│   ├── rpc-client/            # Client RPC pour appeler Python
│   │   └── rpcClient.js
│   ├── server.js
│   └── package.json
│
├── rpc-server/                # Serveur RPC Python
│   ├── server.py              # Implémentation XML-RPC/gRPC
│   ├── services/
│   │   ├── users_service.py
│   │   ├── gigs_service.py
│   │   └── orders_service.py
│   └── requirements.txt
│
├── database/                  # Couche base de données
│   ├── models/
│   │   ├── userModel.js
│   │   ├── gigModel.js
│   │   └── orderModel.js
│   └── dbConfig.js
│
├── integration-qa/            # Tests et intégration
│   ├── tests/
│   │   ├── rpc_tests.py
│   │   └── integration_tests.js
│   └── docker-compose.yml     # Simulation distribuée
│
├── docs/
│   ├── report.docx
│   ├── report.pdf
│   └── presentation.pptx
│
└── README.md
```

## 👥 Équipe et Responsabilités
- **Étudiant 1** : Frontend Client (UI pour clients).
- **Étudiant 2** : Frontend Freelancer (UI pour freelances).
- **Étudiant 3** : Backend Gateway (Node.js).
- **Étudiant 4** : Serveur RPC (Python).
- **Étudiant 5** : Base de Données (MongoDB).
- **Étudiant 6** : Intégration & QA (tests, GitHub).

## 🧱 Schéma de Base de Données (MongoDB)
- **users** : {_id, username, email, password, role, profile, created_at}
- **gigs** : {_id, freelancer_id, title, description, price, category, tags, status, created_at}
- **orders** : {_id, client_id, gig_id, status, price, deadline, created_at}
- **messages** : {_id, order_id, sender_id, receiver_id, message, timestamp}

*Notes :* Utilisez Mongoose (pour Node.js) ou PyMongo (pour Python) pour interagir. Index sur _id, email, etc., pour les performances.

## 🧪 Tests
- Tests unitaires pour RPC : `rpc_tests.py`.
- Tests d'intégration : `integration_tests.js`.
- Exécutez avec `npm test` ou `pytest`.

## 📝 Documentation Supplémentaire
- Rapport complet : `docs/report.pdf`.
- Présentation : `docs/presentation.pptx`.
- Diagrammes UML : Cas d'usage, classes, séquences, déploiement.

## 🔄 Améliorations Futures
- Ajouter une authentification JWT.
- Implémenter des WebSockets pour le chat en temps réel.
- Déployer sur des serveurs cloud (e.g., AWS, Heroku).

## 🤝 Contribution
1. Forkez le projet.
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`).
3. Commitez vos changements (`git commit -m 'Add some AmazingFeature'`).
4. Pushez vers la branche (`git push origin feature/AmazingFeature`).
5. Ouvrez une Pull Request.

## 📄 Licence
Ce projet est sous licence MIT. Voir `LICENSE` pour plus de détails.

## 📞 Contact
- **Auteur** :latifa zgari
- **Email** :latifazgari1@gmail.com
- **GitHub** : https://github.com/ZLati93

---

Pour toute question ou modification, contactez l'équipe via GitHub Issues. Bon développement ! 🚀
