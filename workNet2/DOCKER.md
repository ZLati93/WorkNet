# Docker Compose - WorkNet

Ce document décrit la configuration Docker Compose pour WorkNet.

## Services

### 1. MongoDB
- **Image**: `mongo:7.0`
- **Port**: `27017`
- **Health Check**: Vérifie que MongoDB répond aux commandes ping
- **Volumes**: 
  - `mongodb_data`: Données persistantes
  - `mongodb_config`: Configuration MongoDB
- **Variables d'environnement**:
  - `MONGO_ROOT_USERNAME`: Nom d'utilisateur root (défaut: admin)
  - `MONGO_ROOT_PASSWORD`: Mot de passe root (défaut: password)
  - `MONGO_DATABASE`: Nom de la base de données (défaut: worknet)

### 2. Node.js API Gateway
- **Build**: `./backend-node`
- **Port**: `3000`
- **Health Check**: Vérifie l'endpoint `/health`
- **Dépendances**: MongoDB (healthy), Redis (healthy)
- **Variables d'environnement**:
  - `PORT`: Port du serveur (défaut: 3000)
  - `MONGODB_URI`: URI de connexion MongoDB
  - `REDIS_HOST`: Hôte Redis (défaut: redis)
  - `REDIS_PORT`: Port Redis (défaut: 6379)
  - `JWT_SECRET`: Clé secrète JWT
  - `CORS_ORIGIN`: Origines CORS autorisées

### 3. Python RPC Server
- **Build**: `./rpc-server` (Dockerfile.python)
- **Port**: `8000`
- **Health Check**: Vérifie que le port 8000 est accessible
- **Dépendances**: MongoDB (healthy)
- **Variables d'environnement**:
  - `RPC_PORT`: Port du serveur RPC (défaut: 8000)
  - `MONGODB_URI`: URI de connexion MongoDB

### 4. Redis Cache
- **Image**: `redis:7-alpine`
- **Port**: `6379`
- **Health Check**: Vérifie que Redis répond aux commandes ping
- **Volumes**: `redis_data` pour la persistance

## Réseau

Tous les services sont connectés au réseau `worknet-network` avec le sous-réseau `172.20.0.0/16`.

## Volumes

- `mongodb_data`: Données MongoDB
- `mongodb_config`: Configuration MongoDB
- `redis_data`: Données Redis
- `api_gateway_logs`: Logs de l'API Gateway
- `rpc_server_logs`: Logs du serveur RPC

## Utilisation

### Démarrer tous les services
```bash
docker-compose up -d
```

### Démarrer un service spécifique
```bash
docker-compose up -d mongodb
docker-compose up -d api-gateway
docker-compose up -d rpc-server
```

### Voir les logs
```bash
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f api-gateway
```

### Arrêter les services
```bash
docker-compose down
```

### Arrêter et supprimer les volumes
```bash
docker-compose down -v
```

### Reconstruire les images
```bash
docker-compose build --no-cache
```

### Vérifier l'état des services
```bash
docker-compose ps
```

## Health Checks

Tous les services ont des health checks configurés :
- **MongoDB**: Vérifie toutes les 10s
- **API Gateway**: Vérifie toutes les 30s
- **RPC Server**: Vérifie toutes les 30s
- **Redis**: Vérifie toutes les 10s

Les services dépendants attendent que MongoDB et Redis soient "healthy" avant de démarrer.

## Variables d'environnement

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```env
# MongoDB
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your-secure-password
MONGO_DATABASE=worknet

# Redis
REDIS_PASSWORD=your-redis-password

# API Gateway
JWT_SECRET=your-jwt-secret-key
CORS_ORIGIN=http://localhost:3000,http://localhost:3001

# Environment
NODE_ENV=production
```

## Dépannage

### Vérifier les health checks
```bash
docker-compose ps
```

### Accéder aux logs d'un service
```bash
docker-compose logs api-gateway
```

### Accéder à un conteneur
```bash
docker-compose exec api-gateway sh
docker-compose exec mongodb mongosh
```

### Réinitialiser MongoDB
```bash
docker-compose down -v
docker volume rm worknet1_mongodb_data
docker-compose up -d mongodb
```

