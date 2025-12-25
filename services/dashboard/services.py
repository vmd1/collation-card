"""Dashboard service layer."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from shared.models import Message, InviteLink, CardCover, Settings
from shared.utils import TokenGenerator, ImageProcessor


class MessageService:
    """Handle message operations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_pending_messages(self, limit: int = 50, offset: int = 0) -> List[Message]:
        """Get pending messages."""
        return self.db.query(Message).filter(
            Message.status == 'pending'
        ).order_by(Message.created_at.desc()).limit(limit).offset(offset).all()
    
    def get_all_messages(self, limit: int = 100, offset: int = 0) -> List[Message]:
        """Get all messages."""
        return self.db.query(Message).order_by(
            Message.created_at.desc()
        ).limit(limit).offset(offset).all()
    
    def approve_message(self, message_id: int) -> bool:
        """Approve a message."""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if message and message.status == 'pending':
            message.status = 'approved'
            message.approved_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def reject_message(self, message_id: int) -> bool:
        """Reject a message."""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if message:
            message.status = 'rejected'
            self.db.commit()
            return True
        return False
    
    def update_message(self, message_id: int, name: str = None, content: str = None) -> bool:
        """Update a message's name and/or content."""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if message:
            if name is not None:
                # Format the name (handle multiple names)
                formatted_name = self._format_names(name)
                message.name = formatted_name
                # Regenerate initials when name changes
                message.initials = self._generate_initials(formatted_name)
                message.color_hint = self._generate_color_hint(formatted_name)
            if content is not None:
                message.content = content
            self.db.commit()
            return True
        return False
    
    def delete_message(self, message_id: int) -> bool:
        """Delete a message."""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if message:
            self.db.delete(message)
            self.db.commit()
            return True
        return False
    
    def unapprove_message(self, message_id: int) -> bool:
        """Unapprove a message (set back to pending)."""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if message and message.status == 'approved':
            message.status = 'pending'
            message.approved_at = None
            self.db.commit()
            return True
        return False
    
    def get_approved_messages(self, limit: int = 100, offset: int = 0) -> List[Message]:
        """Get approved messages."""
        return self.db.query(Message).filter(
            Message.status == 'approved'
        ).order_by(Message.approved_at.desc()).limit(limit).offset(offset).all()
    
    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """Get a message by ID."""
        return self.db.query(Message).filter(Message.id == message_id).first()
    
    def get_pending_count(self) -> int:
        """Get count of pending messages."""
        return self.db.query(Message).filter(Message.status == 'pending').count()
    
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


class InviteLinkService:
    """Handle invite link operations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_link(self, note: Optional[str] = None, 
                    max_uses: Optional[int] = None,
                    expires_hours: Optional[int] = None) -> InviteLink:
        """Create a new invite link."""
        token = TokenGenerator.generate_short_token()
        expires_at = None
        if expires_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        link = InviteLink(
            token=token,
            note=note,
            max_uses=max_uses,
            expires_at=expires_at
        )
        self.db.add(link)
        self.db.commit()
        return link
    
    def get_all_links(self) -> List[InviteLink]:
        """Get all invite links."""
        return self.db.query(InviteLink).order_by(
            InviteLink.created_at.desc()
        ).all()
    
    def deactivate_link(self, token: str) -> bool:
        """Deactivate an invite link."""
        link = self.db.query(InviteLink).filter(InviteLink.token == token).first()
        if link:
            link.is_active = False
            self.db.commit()
            return True
        return False


class CoverService:
    """Handle card cover operations."""
    
    def __init__(self, db_session: Session, media_path: str):
        self.db = db_session
        self.image_processor = ImageProcessor(media_path)
    
    def upload_cover(self, file_data: bytes, filename: str) -> str:
        """Upload a new card cover image."""
        # Deactivate current cover
        self.db.query(CardCover).update({'is_active': False})
        
        # Save new cover
        full_path, _ = self.image_processor.save_image(file_data, filename)
        
        cover = CardCover(image_path=full_path, is_active=True)
        self.db.add(cover)
        self.db.commit()
        
        return full_path
    
    def get_active_cover(self) -> Optional[CardCover]:
        """Get the currently active cover."""
        return self.db.query(CardCover).filter(
            CardCover.is_active == True
        ).first()


class SettingsService:
    """Handle application settings."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value by key."""
        setting = self.db.query(Settings).filter(Settings.key == key).first()
        return setting.value if setting else default
    
    def set_setting(self, key: str, value: str) -> bool:
        """Set a setting value."""
        setting = self.db.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = Settings(key=key, value=value)
            self.db.add(setting)
        self.db.commit()
        return True
    
    def get_all_settings(self) -> dict:
        """Get all settings as a dictionary."""
        settings = self.db.query(Settings).all()
        return {s.key: s.value for s in settings}
