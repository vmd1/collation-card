"""Submission service layer."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import uuid
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from shared.models import Message, InviteLink
from shared.utils import ContentSanitizer, ImageProcessor, VideoProcessor


class SubmissionService:
    """Handle message submissions."""
    
    def __init__(self, db_session: Session, media_path: str):
        self.db = db_session
        self.sanitizer = ContentSanitizer()
        self.image_processor = ImageProcessor(media_path)
        self.video_processor = VideoProcessor(media_path)
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """Validate invite token."""
        link = self.db.query(InviteLink).filter(InviteLink.token == token).first()
        
        if not link:
            return False, "Invalid token"
        
        if not link.is_active:
            return False, "Token has been deactivated"
        
        if link.expires_at and link.expires_at < datetime.utcnow():
            return False, "Token has expired"
        
        if link.max_uses and link.uses_count >= link.max_uses:
            return False, "Token has reached maximum uses"
        
        return True, None
    
    def create_submission(self, token: str, name: str, content: str, 
                         image_data: Optional[bytes] = None,
                         image_filename: Optional[str] = None,
                         ip_address: Optional[str] = None,
                         media_type: Optional[str] = None) -> Tuple[bool, str]:
        """Create a new message submission."""
        # Validate token
        is_valid, error = self.validate_token(token)
        if not is_valid:
            return False, error
        
        # Format the name (handle multiple names)
        formatted_name = self._format_names(name)
        
        # Sanitize content
        clean_content = self.sanitizer.sanitize(content)
        
        # Generate initials
        initials = self._generate_initials(formatted_name)
        
        # Handle media upload
        image_path, video_path, thumb_path = None, None, None
        if image_data and image_filename and media_type:
            try:
                if media_type == 'image':
                    image_path, thumb_path = self.image_processor.save_image(
                        image_data, image_filename
                    )
                elif media_type == 'video':
                    video_path, thumb_path = self.video_processor.save_video(
                        image_data, image_filename
                    )
            except Exception as e:
                return False, f"Media upload failed: {str(e)}"
        
        # Generate color hint
        color_hint = self._generate_color_hint(formatted_name)
        
        # Create message
        message = Message(
            uuid=str(uuid.uuid4()),
            name=formatted_name,
            initials=initials,
            content=clean_content,
            image_path=image_path,
            video_path=video_path,
            thumb_path=thumb_path,
            media_type=media_type,
            ip_address=ip_address,
            color_hint=color_hint,
            status='pending'
        )
        
        self.db.add(message)
        
        # Increment token usage
        link = self.db.query(InviteLink).filter(InviteLink.token == token).first()
        link.uses_count += 1
        
        self.db.commit()
        
        return True, "Submission successful"
    
    def _format_names(self, name: str) -> str:
        """Format multiple names according to the specified pattern.
        
        1 person: Person 1
        2 people: Person 1 & Person 2
        3+ people: Person 1, Person 2 & Person 3
        """
        # Split by comma and clean up whitespace
        names = [n.strip() for n in name.split(',') if n.strip()]
        
        if len(names) == 0:
            return "Unknown"
        elif len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} & {names[1]}"
        else:
            # Join all but last with commas, then add & before last
            return ", ".join(names[:-1]) + f" & {names[-1]}"
    
    def _generate_initials(self, name: str) -> str:
        """Generate initials from name.
        
        For formatted names with &, takes first letter of first name and first letter after &.
        """
        # Handle names with & (formatted multiple names)
        if ' & ' in name:
            parts = name.split(' & ')
            first_initial = parts[0].strip()[0].upper() if parts[0].strip() else '?'
            # Get the first letter of the last person's name
            last_name_words = parts[-1].strip().split()
            last_initial = last_name_words[0][0].upper() if last_name_words else '?'
            return first_initial + last_initial
        
        # Handle single name or names with commas
        if ',' in name:
            # If there are commas, get first name
            first_name = name.split(',')[0].strip()
            words = first_name.split()
        else:
            words = name.strip().split()
        
        if len(words) == 0:
            return "?"
        elif len(words) == 1:
            return words[0][0].upper()
        else:
            return (words[0][0] + words[-1][0]).upper()
    
    def _generate_color_hint(self, name: str) -> str:
        """Generate a deterministic color hint from name."""
        hash_val = 0
        for char in name:
            hash_val = (hash_val << 5) - hash_val + ord(char)
            hash_val = hash_val & 0xFFFFFFFF
        
        hue = abs(hash_val) % 360
        return f"hsl({hue} 60% 90%)"
