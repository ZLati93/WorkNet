import hashlib
from datetime import datetime, timedelta
from jose import jwt

# Clé secrète et algorithme pour JWT
SECRET_KEY = "super-secret-key"   # ⚠️ à mettre dans .env
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Hash un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Vérifie si le mot de passe correspond au hash"""
    return hash_password(password) == hashed

def generate_token(data: dict, expires_delta: timedelta = None) -> str:
    """Génère un JWT token avec expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
