from werkzeug.security import generate_password_hash, check_password_hash
import jwt,datetime

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(stored_password: str, provided_password: str) -> bool:
    return check_password_hash(stored_password, provided_password)

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

def create_jwt_token(payload: dict, expires_in: int = 3600):
    # Add expiration time
    payload_copy = payload.copy()
    payload_copy["exp"] = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    payload_copy["iat"] = datetime.datetime.utcnow()  # issued at
    payload_copy["iss"] = "chat-app"  # optional: issuer
    
    token = jwt.encode(payload_copy, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_jwt_token(token: str):
    try:
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_payload
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

