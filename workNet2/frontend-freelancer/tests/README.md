# Frontend Freelancer Tests

Tests unitaires pour le frontend freelancer utilisant React Testing Library et Vitest.

## Structure

- `setup.js` - Configuration globale des tests
- `dashboard.test.js` - Tests pour le dashboard freelancer

## Installation

```bash
# Installer les dépendances
npm install

# Installer Vitest et jsdom si nécessaire
npm install --save-dev vitest @vitest/ui jsdom
```

## Exécution des tests

```bash
# Exécuter tous les tests
npm test

# Mode watch
npm test -- --watch

# Interface UI
npm run test:ui

# Avec couverture
npm run test:coverage
```

## Tests disponibles

### dashboard.test.js
- ✅ Redirection si non authentifié
- ✅ Affichage du titre du dashboard
- ✅ Affichage des cartes de statistiques
- ✅ Calcul correct des totaux (gigs, orders, earnings, rating)
- ✅ Affichage des graphiques
- ✅ Affichage des commandes récentes
- ✅ Badges de statut des commandes
- ✅ Prix des commandes
- ✅ État vide (no orders)
- ✅ État de chargement
- ✅ Calcul des gigs actifs
- ✅ Calcul des commandes complétées
- ✅ Gestion des erreurs

## Mocks

Les tests mockent :
- `authService` - Service d'authentification
- `ordersService` - Service de commandes
- `gigsService` - Service de gigs
- `paymentsService` - Service de paiements
- `react-router-dom` - Navigation
- `recharts` - Composants de graphiques

## Notes

- Les tests utilisent React Testing Library pour tester le comportement utilisateur
- Vitest est utilisé comme framework de test
- jsdom simule l'environnement DOM du navigateur
- Les tests sont isolés et indépendants

