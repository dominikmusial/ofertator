"""
Encryption service for API keys.
Uses Fernet encryption to safely store user API keys.
"""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    def __init__(self):
        # Generate key from SECRET_KEY for consistency
        self._key = self._generate_key_from_secret()
        self.fernet = Fernet(self._key)
    
    def _generate_key_from_secret(self) -> bytes:
        """Generate a Fernet key from the app's SECRET_KEY"""
        # Create a deterministic key from SECRET_KEY
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ai_config_salt',  # Static salt for consistency
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
        return key
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key"""
        try:
            encrypted = self.fernet.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            raise ValueError("Failed to encrypt API key")
    
    def decrypt_api_key(self, encrypted_api_key: str) -> str:
        """Decrypt an API key"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_api_key.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            raise ValueError("Failed to decrypt API key")

# Global instance
encryption_service = EncryptionService() 