# RPC Server Tests

Tests unitaires pour les services RPC Python utilisant pytest.

## Structure

- `conftest.py` - Fixtures communes pour MongoDB mocking
- `test_users.py` - Tests pour users_service
- `test_gigs.py` - Tests pour gigs_service
- `test_orders.py` - Tests pour orders_service
- `test_payments.py` - Tests pour payments_service
- `test_security.py` - Tests pour utils/security

## Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Ou installer pytest spécifiquement
pip install pytest pytest-cov pytest-asyncio
```

## Exécution des tests

```bash
# Exécuter tous les tests
pytest

# Exécuter avec couverture de code
pytest --cov=src --cov-report=html

# Exécuter un fichier de test spécifique
pytest tests/test_users.py

# Exécuter une classe de test spécifique
pytest tests/test_users.py::TestUsersService

# Exécuter un test spécifique
pytest tests/test_users.py::TestUsersService::test_create_user_success

# Mode verbose
pytest -v

# Afficher les sorties print
pytest -s
```

## Fixtures

Les fixtures suivantes sont disponibles dans `conftest.py` :

- `mock_db` - Mock de la base de données MongoDB
- `mock_collection` - Mock d'une collection MongoDB
- `sample_user` - Données utilisateur d'exemple
- `sample_gig` - Données gig d'exemple
- `sample_order` - Données order d'exemple
- `sample_payment` - Données payment d'exemple
- `mock_session` - Mock de session MongoDB pour transactions
- `mock_transaction_context` - Mock de contexte de transaction

## Scénarios testés

### Users Service (`test_users.py`)
- ✅ Création d'utilisateur (succès, doublons, validation)
- ✅ Mise à jour d'utilisateur
- ✅ Suppression d'utilisateur (avec vérification des commandes actives)
- ✅ Inscription (register)
- ✅ Connexion (login)
- ✅ Récupération de profil
- ✅ Mise à jour de profil
- ✅ Changement de mot de passe
- ✅ Statistiques utilisateur
- ✅ Récupération par ID
- ✅ Liste des utilisateurs avec pagination

### Gigs Service (`test_gigs.py`)
- ✅ Création de gig (succès, validation, autorisation)
- ✅ Mise à jour de gig
- ✅ Suppression de gig (avec vérification des commandes actives)
- ✅ Récupération par ID
- ✅ Récupération par utilisateur
- ✅ Recherche de gigs (avec filtres)
- ✅ Mise à jour de note

### Orders Service (`test_orders.py`)
- ✅ Création de commande (succès, validation, vérifications)
- ✅ Mise à jour de statut
- ✅ Annulation de commande
- ✅ Analytics de commandes
- ✅ Récupération par ID
- ✅ Liste des commandes avec filtres

### Payments Service (`test_payments.py`)
- ✅ Création de paiement (avec calcul de frais)
- ✅ Traitement de paiement
- ✅ Remboursement
- ✅ Calcul des frais de plateforme
- ✅ Récupération de statut
- ✅ Liste des paiements

### Security Utilities (`test_security.py`)
- ✅ Hachage de mot de passe (bcrypt)
- ✅ Vérification de mot de passe
- ✅ Validation de la force du mot de passe
- ✅ Génération de token JWT
- ✅ Vérification de token JWT
- ✅ Refresh token
- ✅ Gestion des permissions
- ✅ Utilitaires de sécurité (sanitize, mask_email, etc.)

## Mocking MongoDB

Tous les tests utilisent des mocks pour MongoDB afin d'éviter :
- La nécessité d'une connexion MongoDB réelle
- Les dépendances externes
- Les effets de bord entre tests

Les mocks sont configurés dans `conftest.py` et utilisent `unittest.mock`.

## Notes

- Les tests sont isolés et indépendants
- Chaque test mocke ses propres dépendances
- Les fixtures sont réutilisables entre les fichiers de test
- La couverture de code peut être générée avec `--cov`

## Exemple d'utilisation

```python
def test_example(mock_db, sample_user):
    """Exemple de test utilisant les fixtures"""
    service = UsersService(mock_db)
    mock_db.users.find_one.return_value = sample_user
    
    result = service.get_by_id(str(sample_user['_id']))
    
    assert result['success'] is True
```

