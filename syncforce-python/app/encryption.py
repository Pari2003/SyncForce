import os
from cryptography.fernet import Fernet
import base64

# In a real app, load this from a secure secrets manager
SECRET_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
fernet = Fernet(SECRET_KEY.encode())

def encrypt_field(data: str) -> str:
    """Encrypts a string field using Fernet (symmetric encryption)."""
    if not data:
        return data
    return fernet.encrypt(data.encode()).decode()

def decrypt_field(encrypted_data: str) -> str:
    """Decrypts a string field."""
    if not encrypted_data:
        return encrypted_data
    return fernet.decrypt(encrypted_data.encode()).decode()
