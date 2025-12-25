"""Video processing utilities."""
import os
import uuid
import subprocess
from pathlib import Path
from typing import Tuple
import magic

class VideoProcessor:
    """Handle video validation, processing, and storage."""
    
    ALLOWED_MIME_TYPES = {'video/mp4', 'video/webm', 'video/quicktime'}
    MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB
    
    def __init__(self, media_path: str):
        """Initialize with media storage path."""
        self.media_path = Path(media_path)
        self.media_path.mkdir(parents=True, exist_ok=True)
    
    def validate_video(self, file_data: bytes) -> bool:
        """Validate video file type and size."""
        if len(file_data) > self.MAX_VIDEO_SIZE:
            return False
        
        mime = magic.from_buffer(file_data, mime=True)
        return mime in self.ALLOWED_MIME_TYPES
    
    def save_video(self, file_data: bytes, filename: str) -> Tuple[str, str]:
        """
        Save video and generate a thumbnail.
        
        Returns:
            Tuple of (video_path, thumbnail_path)
        """
        if not self.validate_video(file_data):
            raise ValueError("Invalid video file")
        
        # Generate unique filename
        ext = Path(filename).suffix or '.mp4'
        unique_name = f"{uuid.uuid4()}{ext}"
        
        # Create date-based directory
        from datetime import datetime
        date_dir = datetime.now().strftime('%Y/%m/%d')
        target_dir = self.media_path / date_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Save video file
        video_path = target_dir / unique_name
        with open(video_path, 'wb') as f:
            f.write(file_data)
        
        # Generate thumbnail
        thumb_name = f"thumb_{Path(unique_name).stem}.jpg"
        thumb_path = target_dir / thumb_name
        
        try:
            # Use ffmpeg to extract the first frame
            subprocess.run([
                'ffmpeg',
                '-i', str(video_path),
                '-vframes', '1',
                '-an',
                '-s', '200x200',
                '-ss', '1',
                str(thumb_path)
            ], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # Fallback: if ffmpeg fails or is not installed, you might want a default thumb
            # For now, we'll just raise the error to be explicit
            raise RuntimeError(f"ffmpeg thumbnail generation failed: {e}")

        # Return relative paths
        rel_video = f"{date_dir}/{unique_name}"
        rel_thumb = f"{date_dir}/{Path(thumb_name).name}"
        
        return rel_video, rel_thumb
