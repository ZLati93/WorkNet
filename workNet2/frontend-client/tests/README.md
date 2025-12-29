# Frontend Client Tests

Tests unitaires pour le frontend client utilisant React Testing Library et Vitest.

## Structure

- `setup.js` - Configuration globale des tests
- `auth.test.js` - Tests pour Login et Register
- `gigs.test.js` - Tests pour affichage et recherche de gigs

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

### auth.test.js
- ✅ Rendu du formulaire de login
- ✅ Validation des champs (email, password)
- ✅ Soumission du formulaire
- ✅ Gestion des erreurs
- ✅ État de chargement
- ✅ Rendu du formulaire d'inscription
- ✅ Validation (username, email, password, confirm password)
- ✅ Soumission du formulaire d'inscription
- ✅ Navigation entre login et register

### gigs.test.js
- ✅ Affichage de la page d'accueil
- ✅ Affichage des gigs
- ✅ État de chargement
- ✅ Gestion des erreurs
- ✅ État vide (no gigs)
- ✅ Recherche de gigs
- ✅ Filtrage par catégorie
- ✅ Tri des gigs
- ✅ Pagination
- ✅ Composant GigCard
- ✅ Affichage des détails (prix, note, ventes)
- ✅ Gestion des images manquantes

## Mocks

Les tests mockent :
- `authService` - Service d'authentification
- `gigsService` - Service de gigs
- `react-router-dom` - Navigation
- `window.location` - Redirection et reload

## Notes

- Les tests utilisent React Testing Library pour tester le comportement utilisateur
- Vitest est utilisé comme framework de test
- jsdom simule l'environnement DOM du navigateur
- Les tests sont isolés et indépendants

