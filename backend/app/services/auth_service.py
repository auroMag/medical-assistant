from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # bcrypt ha limite 72 bytes, tronchiamo per sicurezza
    password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    plain = plain[:72]
    return pwd_context.verify(plain, hashed)