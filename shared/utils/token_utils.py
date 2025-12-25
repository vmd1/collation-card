"""Token generation and validation utilities."""
import secrets
import string
from typing import Optional


class TokenGenerator:
    """Generate secure tokens for invite links."""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_short_token(length: int = 16) -> str:
        """Generate a shorter token for URLs."""
        return TokenGenerator.generate_token(length)
