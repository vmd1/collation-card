"""HTML content sanitization."""
import bleach


class ContentSanitizer:
    """Sanitize user-submitted HTML content."""
    
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3',
        'ul', 'ol', 'li', 'blockquote', 'a', 'span'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'span': ['style'],
    }
    
    ALLOWED_STYLES = ['color', 'background-color', 'font-weight']
    
    @classmethod
    def sanitize(cls, html: str) -> str:
        """Sanitize HTML content to prevent XSS."""
        return bleach.clean(
            html,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            strip=True
        )
