"""
Password Hashing Utilities

Provides secure password hashing and verification using bcrypt.
This replaces Supabase Auth's password management with our own implementation.
"""

import bcrypt
from typing import Tuple


class PasswordHasher:
    """
    Password hasher using bcrypt.
    
    bcrypt automatically handles:
    - Salt generation and embedding
    - Configurable work factor (rounds)
    - Timing-safe comparison
    """
    
    def __init__(self, rounds: int = 12):
        """
        Initialize password hasher.
        
        Args:
            rounds: bcrypt work factor (log2 iterations). 
                    Default 12 = 2^12 = 4096 iterations.
                    Higher = more secure but slower.
        """
        self.rounds = rounds
    
    def hash(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string (includes salt)
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Uses timing-safe comparison to prevent timing attacks.
        
        Args:
            password: Plain text password to verify
            hashed_password: Previously hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except (ValueError, TypeError):
            # Invalid hash format
            return False
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if a password hash needs to be rehashed.
        
        This is useful when upgrading the work factor.
        
        Args:
            hashed_password: Existing password hash
            
        Returns:
            True if hash should be updated (e.g., work factor changed)
        """
        try:
            hashed_bytes = hashed_password.encode('utf-8')
            # Extract the work factor from the hash
            # bcrypt hash format: $2b$rounds$salt+hash
            parts = hashed_password.split('$')
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds != self.rounds
            return True
        except (ValueError, IndexError):
            return True


# Global instance with default settings
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password using the global hasher."""
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password using the global hasher."""
    return password_hasher.verify(password, hashed_password)
