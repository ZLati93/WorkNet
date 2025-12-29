# Integration QA Tests

Tests d'intégration et de qualité pour la plateforme WorkNet.

## Structure

- `rpc_tests.py` - Tests directs du serveur RPC Python
- `api_tests.js` - Tests d'intégration Node.js API ↔ RPC Server
- `e2e_tests.js` - Tests end-to-end complets

## Types de tests

### 1. RPC Tests (`rpc_tests.py`)
Tests directs du serveur RPC Python utilisant XML-RPC client.

**Scénarios testés :**
- ✅ Health check (ping)
- ✅ Users Service (register, login, get_by_id, update_profile, get_stats)
- ✅ Gigs Service (create, get_by_id, search, get_by_user, update_rating)
- ✅ Orders Service (create, get_by_id, get_all, update_status, get_analytics)
- ✅ Payments Service (create, calculate_fees, get_status)
- ✅ Categories Service (get_all, get_by_id)
- ✅ Reviews Service (calculate_rating)
- ✅ Messages Service (get_unread_count)
- ✅ Notifications Service (get_unread_count, send_bulk)
- ✅ Gestion des erreurs
- ✅ Performance (concurrent requests, latency)

### 2. API Tests (`api_tests.js`)
Tests d'intégration entre le backend Node.js et le serveur RPC Python.

**Scénarios testés :**
- ✅ User Registration and Login Flow
- ✅ Gigs API ↔ RPC Integration (create, get, search, update)
- ✅ Orders API ↔ RPC Integration (create, get, update status)
- ✅ Payments API ↔ RPC Integration (calculate fees)
- ✅ Error Handling and Edge Cases
- ✅ Performance Tests (concurrent requests, response time)

### 3. E2E Tests (`e2e_tests.js`)
Tests end-to-end complets de toute la plateforme.

**Scénarios testés :**
- ✅ Complete User Journey - Client (register → search → order)
- ✅ Complete User Journey - Freelancer (register → create gig → manage orders)
- ✅ Complete Order Flow (create → update status → complete)
- ✅ Frontend Integration Tests (homepage, search, dashboard)
- ✅ Cross-Service Communication (data consistency)
- ✅ Error Scenarios (invalid auth, missing fields, non-existent resources)
- ✅ Performance and Load Tests (concurrent requests, pagination)

## Exécution des tests

### Local (sans Docker)

```bash
# Installer les dépendances
npm install
pip install -r requirements.txt

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

## Configuration

### Variables d'environnement

```bash
# API Configuration
API_URL=http://localhost:3000/api

# RPC Configuration
RPC_HOST=localhost
RPC_PORT=8000

# Frontend URLs
CLIENT_URL=http://localhost:3000
FREELANCER_URL=http://localhost:3001

# MongoDB (for tests)
MONGODB_URI=mongodb://localhost:27017/worknet_test
```

## Docker Compose pour Tests

Le fichier `docker-compose.yml` configure :

- **mongodb-test** - Base de données MongoDB pour tests (port 27018)
- **api-gateway-test** - API Gateway Node.js (port 3002)
- **rpc-server-test** - Serveur RPC Python (port 8001)
- **redis-test** - Cache Redis (port 6380)
- **rpc-tests** - Runner pour tests RPC Python
- **api-tests** - Runner pour tests API Node.js
- **e2e-tests** - Runner pour tests E2E avec Playwright

## Rapports

Les rapports de tests sont générés dans le dossier `reports/` :
- `rpc_tests.xml` - Rapports JUnit pour tests RPC
- `api_tests.xml` - Rapports pour tests API
- `e2e_tests.xml` - Rapports pour tests E2E

## Notes

- Les tests utilisent une base de données MongoDB séparée (`worknet_test`)
- Les ports sont différents pour éviter les conflits avec l'environnement de développement
- Les tests sont isolés et peuvent être exécutés en parallèle
- Les services sont démarrés avec health checks pour s'assurer qu'ils sont prêts

