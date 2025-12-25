"""Card service layer."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import List, Optional
from sqlalchemy.orm import Session
from shared.models import Message, CardCover


class CardService:
    """Handle card display operations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_approved_messages(self) -> List[Message]:
        """Get all approved messages ordered by creation date."""
        return self.db.query(Message).filter(
            Message.status == 'approved'
        ).order_by(Message.created_at.asc()).all()
    
    def get_active_cover(self) -> Optional[CardCover]:
        """Get the currently active cover."""
        return self.db.query(CardCover).filter(
            CardCover.is_active == True
        ).first()
    
    def get_messages_json(self) -> List[dict]:
        """Get approved messages as JSON-serializable dicts."""
        messages = self.get_approved_messages()
        return [
            {
                'uuid': msg.uuid,
                'name': msg.name,
                'initials': msg.initials,
                'content_html': msg.content,
                'thumb_url': f'/media/{msg.thumb_path}' if msg.thumb_path else None,
                'image_url': f'/media/{msg.image_path}' if msg.image_path else None,
                'video_url': f'/media/{msg.video_path}' if msg.video_path else None,
                'media_type': msg.media_type,
                'color_hint': msg.color_hint,
                'created_at': msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
