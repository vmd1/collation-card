"""Image processing utilities."""
import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import magic


class ImageProcessor:
    """Handle image validation, processing, and storage."""
    
    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
    THUMB_SIZE = (200, 200)
    FULL_MAX_WIDTH = 1600
    
    def __init__(self, media_path: str):
        """Initialize with media storage path."""
        self.media_path = Path(media_path)
        self.media_path.mkdir(parents=True, exist_ok=True)
    
    def validate_image(self, file_data: bytes) -> bool:
        """Validate image file type and size."""
        if len(file_data) > self.MAX_IMAGE_SIZE:
            return False
        
        mime = magic.from_buffer(file_data, mime=True)
        return mime in self.ALLOWED_MIME_TYPES
    
    def save_image(self, file_data: bytes, filename: str) -> Tuple[str, str]:
        """
        Save image with thumbnail generation.
        
        Returns:
            Tuple of (full_image_path, thumbnail_path)
        """
        if not self.validate_image(file_data):
            raise ValueError("Invalid image file")
        
        # Generate unique filename
        ext = Path(filename).suffix or '.jpg'
        unique_name = f"{uuid.uuid4()}{ext}"
        
        # Create date-based directory
        from datetime import datetime
        date_dir = datetime.now().strftime('%Y/%m/%d')
        target_dir = self.media_path / date_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Save original/resized full image
        full_path = target_dir / unique_name
        img = Image.open(io.BytesIO(file_data))
        
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        
        # Resize if too large
        if img.width > self.FULL_MAX_WIDTH:
            ratio = self.FULL_MAX_WIDTH / img.width
            new_size = (self.FULL_MAX_WIDTH, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        img.save(full_path, quality=85, optimize=True)
        
        # Generate thumbnail
        thumb_name = f"thumb_{unique_name}"
        thumb_path = target_dir / thumb_name
        img.thumbnail(self.THUMB_SIZE, Image.Resampling.LANCZOS)
        img.save(thumb_path, quality=80, optimize=True)
        
        # Return relative paths
        rel_full = f"{date_dir}/{unique_name}"
        rel_thumb = f"{date_dir}/{thumb_name}"
        
        return rel_full, rel_thumb


import io
