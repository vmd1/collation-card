"""Shared database models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Message(Base):
    """Message submission model."""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    initials = Column(String(5), nullable=False)
    content = Column(Text, nullable=False)
    image_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    thumb_path = Column(String(500), nullable=True)
    media_type = Column(String(20), nullable=True) # 'image' or 'video'
    status = Column(String(20), default='pending', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    color_hint = Column(String(20), nullable=True)
    order_index = Column(Integer, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'initials': self.initials,
            'content': self.content,
            'image_path': self.image_path,
            'video_path': self.video_path,
            'thumb_path': self.thumb_path,
            'media_type': self.media_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'color_hint': self.color_hint,
            'order_index': self.order_index
        }


class InviteLink(Base):
    """Invite link token model."""
    __tablename__ = 'invite_links'
    
    token = Column(String(64), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=True)
    uses_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    note = Column(String(500), nullable=True)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'token': self.token,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'max_uses': self.max_uses,
            'uses_count': self.uses_count,
            'is_active': self.is_active,
            'note': self.note
        }


class CardCover(Base):
    """Card cover image model."""
    __tablename__ = 'card_covers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class Settings(Base):
    """Application settings model."""
    __tablename__ = 'settings'
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


def init_db(database_url: str):
    """Initialize database and return session factory."""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session, engine
