# Utilities - RPC Server

Utilitaires pour le serveur RPC WorkNet.

## Modules

### validators.py
Fonctions de validation pour les données d'entrée.

### security.py
Fonctions de sécurité : JWT, hachage de mots de passe, gestion des permissions.

### database.py
Utilitaires MongoDB : transactions, aggregations, helpers.

## Utilisation

### Security Utilities

```python
from utils.security import (
    hash_password,
    verify_password,
    generate_token,
    verify_token,
    check_permission
)

# Hash password
hashed = hash_password("my_password")

# Verify password
is_valid = verify_password("my_password", hashed)

# Generate JWT token
token = generate_token({'id': 'user123', 'role': 'freelancer'})

# Verify token
payload = verify_token(token)

# Check permissions
has_access = check_permission('admin', ['admin', 'moderator'])
```

### Database Utilities

```python
from utils.database import (
    execute_transaction,
    aggregate_user_stats,
    safe_find_one,
    to_object_id
)

# Execute transaction
def my_operation(db, session, user_id):
    db.users.update_one({'_id': user_id}, {'$set': {'active': True}}, session=session)
    return True

result = execute_transaction(db, my_operation, user_id)

# Aggregate stats
stats = aggregate_user_stats(db, user_id)

# Safe operations
user = safe_find_one(db.users, {'email': 'user@example.com'})
```

## Documentation complète

Voir les docstrings dans chaque fichier pour plus de détails.

