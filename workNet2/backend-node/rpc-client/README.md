# RPC Client - WorkNet

Client XML-RPC pour communiquer avec le serveur RPC Python.

## Configuration

Le client RPC peut être configuré via les variables d'environnement :

```env
RPC_SERVER_URL=http://localhost:8000
RPC_HOST=localhost
RPC_PORT=8000
RPC_TIMEOUT=10000
RPC_RETRIES=3
```

## Utilisation

### Importation

```javascript
const { getRPCClient, createRPCClient, callRPC } = require('./rpc-client/rpcClient');
```

### Utilisation du singleton (recommandé)

```javascript
const rpcClient = getRPCClient();

// Appeler une méthode RPC
const result = await rpcClient.callMethod('methodName', [param1, param2]);
```

### Créer une nouvelle instance

```javascript
const rpcClient = createRPCClient({
  host: 'localhost',
  port: 8000,
  timeout: 10000,
  retries: 3
});
```

## Méthodes disponibles

### Méthode générique

```javascript
// Appel générique avec retry automatique
const result = await rpcClient.callMethod('service.method', [param1, param2], {
  timeout: 5000,
  retries: 2,
  skipRetry: false
});
```

### Services disponibles

#### User Service

```javascript
// Créer un utilisateur
await rpcClient.usersService_create(userId, username, email, role);

// Mettre à jour un utilisateur
await rpcClient.usersService_update(userId, updates);

// Supprimer un utilisateur
await rpcClient.usersService_delete(userId);

// Obtenir les statistiques
await rpcClient.usersService_getStats(userId);
```

#### Gig Service

```javascript
// Créer un gig
await rpcClient.gigsService_create(gigId, userId, title);

// Mettre à jour un gig
await rpcClient.gigsService_update(gigId, updates);

// Supprimer un gig
await rpcClient.gigsService_delete(gigId);

// Rechercher des gigs
await rpcClient.gigsService_search(query, filters);

// Mettre à jour la note
await rpcClient.gigsService_updateRating(gigId);
```

#### Order Service

```javascript
// Créer une commande
await rpcClient.ordersService_create(orderId, gigId, buyerId);

// Mettre à jour le statut
await rpcClient.ordersService_updateStatus(orderId, status);

// Obtenir les analytics
await rpcClient.ordersService_getAnalytics(userId, period);

// Annuler une commande
await rpcClient.ordersService_cancel(orderId, reason);
```

#### Category Service

```javascript
await rpcClient.categoriesService_create(categoryId, name, slug);
await rpcClient.categoriesService_update(categoryId, updates);
await rpcClient.categoriesService_delete(categoryId);
await rpcClient.categoriesService_getStats(categoryId);
```

#### Review Service

```javascript
await rpcClient.reviewsService_create(reviewId, gigId, rating);
await rpcClient.reviewsService_update(reviewId, updates);
await rpcClient.reviewsService_delete(reviewId);
await rpcClient.reviewsService_calculateRating(gigId);
```

#### Message Service

```javascript
await rpcClient.messagesService_create(messageId, conversationId, senderId);
await rpcClient.messagesService_markAsRead(messageId);
await rpcClient.messagesService_getUnreadCount(userId);
```

#### Payment Service

```javascript
await rpcClient.paymentsService_create(paymentId, orderId, amount, paymentMethod);
await rpcClient.paymentsService_process(paymentId, status);
await rpcClient.paymentsService_refund(paymentId, amount);
await rpcClient.paymentsService_getStatus(paymentId);
```

#### Notification Service

```javascript
await rpcClient.notificationsService_create(notificationId, userId, type);
await rpcClient.notificationsService_markAsRead(notificationId);
await rpcClient.notificationsService_getUnreadCount(userId);
await rpcClient.notificationsService_sendBulk(userIds, type, message);
```

## Gestion des erreurs

Le client RPC gère automatiquement les erreurs et les retries :

```javascript
try {
  const result = await rpcClient.callMethod('service.method', [params]);
} catch (error) {
  if (error.name === 'RPCError') {
    console.error('RPC Error:', error.message);
    console.error('Method:', error.method);
    console.error('Params:', error.params);
  }
}
```

## Timeouts et Retries

### Configuration globale

```javascript
const rpcClient = getRPCClient({
  timeout: 10000,    // 10 secondes
  retries: 3,        // 3 tentatives
  retryDelay: 1000   // 1 seconde entre les tentatives
});
```

### Configuration par appel

```javascript
// Appel avec timeout personnalisé
await rpcClient.callMethod('method', [params], {
  timeout: 5000,
  retries: 2
});

// Appel sans retry
await rpcClient.callMethod('method', [params], {
  skipRetry: true
});
```

## Statistiques

Obtenir les statistiques du client RPC :

```javascript
const stats = rpcClient.getStats();
console.log(stats);
// {
//   totalCalls: 100,
//   successfulCalls: 95,
//   failedCalls: 5,
//   retries: 10,
//   isConnected: true,
//   successRate: '95.00%'
// }
```

## Événements

Le client RPC émet des événements :

```javascript
rpcClient.on('connected', () => {
  console.log('RPC Client connected');
});

rpcClient.on('error', (error) => {
  console.error('RPC Client error:', error);
});

rpcClient.on('close', () => {
  console.log('RPC Client closed');
});
```

## Health Check

Vérifier la connexion au serveur RPC :

```javascript
const health = await rpcClient.ping();
console.log(health);
```

## Reconnexion

Reconnecter manuellement au serveur RPC :

```javascript
await rpcClient.reconnect();
```

## Utilisation dans les routes

```javascript
const { getRPCClient } = require('../rpc-client/rpcClient');

router.post('/users', async (req, res, next) => {
  try {
    const rpcClient = getRPCClient();
    
    // Appeler le service RPC
    await rpcClient.usersService_create(userId, username, email, role);
    
    res.json({ success: true });
  } catch (error) {
    next(error);
  }
});
```

## Exemple complet

```javascript
const { getRPCClient } = require('./rpc-client/rpcClient');

async function example() {
  const rpcClient = getRPCClient();
  
  try {
    // Health check
    const health = await rpcClient.ping();
    console.log('RPC Server health:', health);
    
    // Créer un utilisateur
    await rpcClient.usersService_create('user123', 'john_doe', 'john@example.com', 'client');
    
    // Créer un gig
    await rpcClient.gigsService_create('gig123', 'user123', 'Logo Design');
    
    // Obtenir les statistiques
    const stats = rpcClient.getStats();
    console.log('RPC Stats:', stats);
    
  } catch (error) {
    console.error('RPC Error:', error);
  }
}
```

