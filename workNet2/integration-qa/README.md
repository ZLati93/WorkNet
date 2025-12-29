# WorkNet Integration QA

Tests d'intégration et de qualité pour la plateforme WorkNet. Inclut des tests directs RPC, des tests d'intégration API ↔ RPC, et des tests end-to-end complets.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Types de Tests](#types-de-tests)
- [Exécution des Tests](#exécution-des-tests)
- [Docker Compose](#docker-compose)
- [Structure](#structure)

## 🎯 Vue d'ensemble

Ce dossier contient trois types de tests :
1. **Tests RPC directs** - Tests Python pour le serveur RPC
2. **Tests API ↔ RPC** - Tests Node.js pour l'intégration
3. **Tests E2E** - Tests end-to-end complets

## 🚀 Installation

```bash
# Installer les dépendances Node.js
npm install

# Installer les dépendances Python
pip install -r requirements.txt
```

## 📊 Types de Tests

### 1. Tests RPC (`tests/rpc_tests.py`)

Tests directs du serveur RPC Python utilisant XML-RPC client.

**Scénarios testés :**
- Health check (ping)
- Users Service (register, login, get_by_id, update_profile, get_stats)
- Gigs Service (create, get_by_id, search, get_by_user, update_rating)
- Orders Service (create, get_by_id, get_all, update_status, get_analytics)
- Payments Service (create, calculate_fees, get_status)
- Categories, Reviews, Messages, Notifications Services
- Gestion des erreurs
- Performance (concurrent requests, latency)

### 2. Tests API (`tests/api_tests.js`)

Tests d'intégration entre le backend Node.js et le serveur RPC Python.

**Scénarios testés :**
- User Registration and Login Flow
- Gigs API ↔ RPC Integration
- Orders API ↔ RPC Integration
- Payments API ↔ RPC Integration
- Error Handling and Edge Cases
- Performance Tests

### 3. Tests E2E (`tests/e2e_tests.js`)

Tests end-to-end complets de toute la plateforme.

**Scénarios testés :**
- Complete User Journey - Client
- Complete User Journey - Freelancer
- Complete Order Flow
- Frontend Integration Tests
- Cross-Service Communication
- Error Scenarios
- Performance and Load Tests

## 🧪 Exécution des Tests

### Local (sans Docker)

```bash
# Tests RPC (Python)
npm run test:rpc
# ou
pytest tests/rpc_tests.py -v

# Tests API (Node.js)
npm run test:api
# ou
jest tests/api_tests.js

# Tests E2E (Node.js)
npm run test:e2e
# ou
jest tests/e2e_tests.js

# Tous les tests
npm run test:all
```

### Avec Docker Compose

```bash
# Construire les images
docker-compose build

# Exécuter tous les tests
docker-compose up --abort-on-container-exit

# Exécuter un service spécifique
docker-compose up rpc-tests
docker-compose up api-tests
docker-compose up e2e-tests

# Nettoyer
docker-compose down -v
```

## 🐳 Docker Compose

Le fichier `docker-compose.yml` configure :

- **mongodb-test** - MongoDB pour tests (port 27018)
- **api-gateway-test** - API Gateway (port 3002)
- **rpc-server-test** - Serveur RPC (port 8001)
- **redis-test** - Redis (port 6380)
- **rpc-tests** - Runner pour tests RPC Python
- **api-tests** - Runner pour tests API Node.js
- **e2e-tests** - Runner pour tests E2E avec Playwright

### Configuration

Les services utilisent des ports différents pour éviter les conflits avec l'environnement de développement.

## 📁 Structure

```
integration-qa/
├── tests/
│   ├── rpc_tests.py        # Tests directs RPC
│   ├── api_tests.js        # Tests Node ↔ RPC integration
│   ├── e2e_tests.js        # Tests end-to-end complets
│   └── README.md
│
├── docker-compose.yml      # Docker Compose pour tests
├── Dockerfile.rpc-tests    # Dockerfile pour tests RPC
├── Dockerfile.api-tests    # Dockerfile pour tests API
├── Dockerfile.e2e-tests    # Dockerfile pour tests E2E
│
├── requirements.txt        # Dépendances Python
├── package.json            # Dépendances Node.js
├── jest.config.js          # Configuration Jest
└── README.md              # Ce fichier
```

## ⚙️ Configuration

### Variables d'environnement

```env
# API Configuration
API_URL=http://localhost:3000/api

# RPC Configuration
RPC_HOST=localhost
RPC_PORT=8000

# Frontend URLs
CLIENT_URL=http://localhost:3000
FREELANCER_URL=http://localhost:3001

# MongoDB (for tests)
MONGODB_URI=mongodb://localhost:27018/worknet_test
```

## 📊 Rapports

Les rapports de tests sont générés dans `reports/` :
- `rpc_tests.xml` - Rapports JUnit pour tests RPC
- Rapports HTML pour couverture de code

## 📚 Ressources

- [Pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [Playwright Documentation](https://playwright.dev/)

## 📄 Licence

ISC
