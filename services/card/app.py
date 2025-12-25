"""Card Flask application."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from flask import Flask, render_template, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from shared.models import init_db
from config import Config
from services import CardService


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # ProxyFix for correct URL generation
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Initialize database
    Config.init_paths()
    Session, engine = init_db(Config.DATABASE_URL)
    
    def get_db():
        """Get database session."""
        return Session()
    
    @app.route('/')
    def index():
        """Show card cover page."""
        db = get_db()
        try:
            service = CardService(db)
            cover = service.get_active_cover()
            return render_template('index.html', cover=cover)
        finally:
            db.close()
    
    @app.route('/api/messages')
    def api_messages():
        """Return approved messages as JSON."""
        db = get_db()
        try:
            service = CardService(db)
            messages = service.get_messages_json()
            return jsonify(messages)
        finally:
            db.close()
    
    @app.route('/media/<path:filename>')
    def serve_media(filename):
        """Serve media files."""
        return send_from_directory(Config.MEDIA_PATH, filename)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8002, debug=True)
