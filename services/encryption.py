# services/encryption.py
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from base64 import b64encode, b64decode
import os
from config.settings import settings

logger = logging.getLogger(__name__)

class EncryptionService:
    def __init__(self):
        self.key = self._generate_key()
    
    def _generate_key(self) -> bytes:
        """Generate encryption key"""
        # Use settings encryption key or generate from owner info
        if settings.ENCRYPTION_KEY:
            # Convert string key to bytes
            if len(settings.ENCRYPTION_KEY) == 44:  # Fernet key length
                return settings.ENCRYPTION_KEY.encode()
        
        # Generate from owner info (hidden in source)
        secret = f"{settings.OWNER_ID}{settings.OWNER_PHONE}{settings.OWNER_EMAIL}"
        salt = settings.SALT.encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = b64encode(kdf.derive(secret.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        try:
            fernet = Fernet(self.key)
            encrypted = fernet.encrypt(data.encode())
            return b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return ""
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        try:
            fernet = Fernet(self.key)
            encrypted = b64decode(encrypted_data.encode())
            decrypted = fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return ""
    
    def encrypt_file(self, file_path: str, output_path: str = None) -> bool:
        """Encrypt file"""
        try:
            if not output_path:
                output_path = file_path + ".enc"
            
            with open(file_path, 'rb') as f:
                data = f.read()
            
            fernet = Fernet(self.key)
            encrypted = fernet.encrypt(data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            return True
            
        except Exception as e:
            logger.error(f"Error encrypting file: {e}")
            return False
    
    def decrypt_file(self, file_path: str, output_path: str = None) -> bool:
        """Decrypt file"""
        try:
            if not output_path:
                output_path = file_path.replace(".enc", "")
            
            with open(file_path, 'rb') as f:
                encrypted = f.read()
            
            fernet = Fernet(self.key)
            decrypted = fernet.decrypt(encrypted)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted)
            
            return True
            
        except Exception as e:
            logger.error(f"Error decrypting file: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        import hashlib
        
        # Use hidden pepper from owner info
        pepper = f"{settings.OWNER_ID}{settings.OWNER_PHONE}"
        
        # Combine password with pepper and salt
        combined = password + pepper + settings.SALT
        
        # Create hash
        hash_obj = hashlib.sha256()
        hash_obj.update(combined.encode())
        
        return hash_obj.hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            new_hash = self.hash_password(password)
            return new_hash == hashed_password
        except:
            return False
    
    def generate_token(self, length: int = 32) -> str:
        """Generate secure token"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))