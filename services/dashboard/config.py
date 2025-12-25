"""Dashboard service configuration."""
import os
from pathlib import Path


class Config:
    """Configuration for dashboard service."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:////data/virtual_card.db')
    MEDIA_PATH = os.getenv('MEDIA_PATH', '/media')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB for cover images
    
    # Ensure paths exist
    @staticmethod
    def init_paths():
        Path(Config.MEDIA_PATH).mkdir(parents=True, exist_ok=True)
        db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        if db_path.startswith('/'):
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
