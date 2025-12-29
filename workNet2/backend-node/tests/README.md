# Backend Tests

Tests unitaires pour les routes de l'API WorkNet utilisant Jest et Supertest.

## Structure

- `users.test.js` - Tests pour les routes users (CRUD, auth)
- `gigs.test.js` - Tests pour les routes gigs
- `orders.test.js` - Tests pour les routes orders
- `setup.js` - Configuration globale des tests

## Exécution des tests

```bash
# Exécuter tous les tests
npm test

# Exécuter les tests en mode watch
npm run test:watch

# Exécuter les tests avec couverture de code
npm test -- --coverage
```

## Configuration

Les tests utilisent :
- **Jest** - Framework de test
- **Supertest** - Test des routes Express
- **Mocks** - RPC Client et modèles Mongoose sont mockés

## Mocks

- `utils/rpcClient` - Mock du client RPC
- `models/userModel` - Mock du modèle User
- `models/gigModel` - Mock du modèle Gig
- `models/orderModel` - Mock du modèle Order
- `middlewares/authMiddleware` - Mock du middleware d'authentification

## Scénarios testés

### Users Tests
- ✅ Registration (succès, validation, erreurs)
- ✅ Login (succès, credentials invalides)
- ✅ Get profile (authentifié)
- ✅ Update profile (validation, erreurs)
- ✅ Get user by ID
- ✅ Get all users (pagination, filtres)
- ✅ Authentification (routes protégées)

### Gigs Tests
- ✅ Get all gigs (pagination, recherche, filtres)
- ✅ Get gig by ID
- ✅ Create gig (validation, seller role)
- ✅ Update gig
- ✅ Delete gig
- ✅ Get gigs by user
- ✅ Authentification et autorisation

### Orders Tests
- ✅ Get all orders (filtres, pagination)
- ✅ Get order by ID
- ✅ Create order (validation, gig checks)
- ✅ Update order status
- ✅ Update order
- ✅ Authentification et autorisation

## Notes

- Les tests mockent toutes les dépendances externes
- Les tests ne nécessitent pas de connexion MongoDB réelle
- Les tests ne nécessitent pas de serveur RPC réel
- Chaque test est indépendant et isolé

