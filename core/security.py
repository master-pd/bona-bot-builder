# core/security.py
import logging
import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from base64 import b64encode, b64decode
from config.settings import settings

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.encryption_key = settings.ENCRYPTION_KEY.encode()
        self.sessions = {}
    
    def create_session(self, user_id: int, user_type: str = "user") -> str:
        """Create new session token"""
        session_token = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "user_type": user_type,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(seconds=settings.SESSION_TIMEOUT),
            "ip_address": None,
            "user_agent": None
        }
        
        self.sessions[session_token] = session_data
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token"""
        if session_token not in self.sessions:
            return None
        
        session_data = self.sessions[session_token]
        
        # Check expiration
        if datetime.now() > session_data["expires_at"]:
            del self.sessions[session_token]
            return None
        
        # Refresh expiration
        session_data["expires_at"] = datetime.now() + timedelta(seconds=settings.SESSION_TIMEOUT)
        return session_data
    
    def destroy_session(self, session_token: str) -> bool:
        """Destroy session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        fernet = Fernet(self.encryption_key)
        encrypted = fernet.encrypt(data.encode())
        return b64encode(encrypted).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        try:
            fernet = Fernet(self.encryption_key)
            encrypted = b64decode(encrypted_data.encode())
            decrypted = fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return None
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        salt = secrets.token_bytes(16)
        key_hash = hashlib.pbkdf2_hmac(
            'sha256',
            api_key.encode(),
            salt,
            100000
        )
        return b64encode(salt + key_hash).decode()
    
    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        """Verify API key"""
        try:
            decoded = b64decode(stored_hash.encode())
            salt = decoded[:16]
            stored_key = decoded[16:]
            
            key_hash = hashlib.pbkdf2_hmac(
                'sha256',
                api_key.encode(),
                salt,
                100000
            )
            
            return secrets.compare_digest(key_hash, stored_key)
        except:
            return False
    
    def generate_secure_password(self, length: int = 12) -> str:
        """Generate secure password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def sanitize_input(self, input_str: str) -> str:
        """Sanitize user input"""
        # Remove dangerous characters
        dangerous = ['<', '>', '&', '"', "'", ';', '(', ')', '`', '$', '*']
        for char in dangerous:
            input_str = input_str.replace(char, '')
        
        # Limit length
        if len(input_str) > 1000:
            input_str = input_str[:1000]
        
        return input_str.strip()
    
    def check_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP is allowed"""
        if ip_address in settings.ALLOWED_IPS:
            return True
        
        # Allow localhost
        if ip_address in ["127.0.0.1", "::1", "localhost"]:
            return True
        
        # Allow private network (for development)
        if ip_address.startswith("192.168.") or ip_address.startswith("10."):
            return True
        
        return False
    
    def audit_log(self, action: str, user_id: int, details: str = ""):
        """Log security audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user_id": user_id,
            "details": details,
            "ip_address": None  # Would be set from request
        }
        
        # Log to security log file
        log_file = settings.LOG_DIR / "security.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")
        
        logger.info(f"Security audit: {action} by user {user_id}")