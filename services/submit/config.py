"""Submission service configuration."""
import os
from pathlib import Path


class Config:
    """Configuration for submission service."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:////data/virtual_card.db')
    MEDIA_PATH = os.getenv('MEDIA_PATH', '/media')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    
    # Rate limiting (requires Redis in production)
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    
    @staticmethod
    def init_paths():
        Path(Config.MEDIA_PATH).mkdir(parents=True, exist_ok=True)
        db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        if db_path.startswith('/'):
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
