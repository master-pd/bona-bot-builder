# config/security.py
import bcrypt
import hashlib
from cryptography.fernet import Fernet
from base64 import b64encode, b64decode
import os
from config.settings import settings

class Security:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt with pepper"""
        # Hidden pepper from owner info
        pepper = f"{settings.OWNER_ID}{settings.OWNER_PHONE}".encode()
        peppered_password = password.encode() + pepper
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(peppered_password, salt)
        return hashed.decode()
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hashed password"""
        try:
            pepper = f"{settings.OWNER_ID}{settings.OWNER_PHONE}".encode()
            peppered_password = password.encode() + pepper
            return bcrypt.checkpw(peppered_password, hashed_password.encode())
        except:
            return False
    
    @staticmethod
    def encrypt_token(token: str) -> str:
        """Encrypt bot token"""
        fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        encrypted = fernet.encrypt(token.encode())
        return b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """Decrypt bot token"""
        try:
            fernet = Fernet(settings.ENCRYPTION_KEY.encode())
            encrypted = b64decode(encrypted_token.encode())
            decrypted = fernet.decrypt(encrypted)
            return decrypted.decode()
        except:
            return ""
    
    @staticmethod
    def encrypt_data(data: str) -> str:
        """Encrypt sensitive data"""
        cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        encrypted = cipher.encrypt(data.encode())
        return b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            cipher = Fernet(settings.ENCRYPTION_KEY.encode())
            encrypted = b64decode(encrypted_data.encode())
            decrypted = cipher.decrypt(encrypted)
            return decrypted.decode()
        except:
            return ""
    
    @staticmethod
    def generate_secure_key() -> str:
        """Generate secure encryption key"""
        return Fernet.generate_key().decode()