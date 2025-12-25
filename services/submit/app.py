"""Submission Flask application."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from flask import Flask, render_template, request, jsonify, flash, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from shared.models import init_db, Settings
from config import Config
from services import SubmissionService


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # ProxyFix for correct URL generation
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=Config.RATELIMIT_STORAGE_URL,
        default_limits=["100 per hour"]
    )
    
    # Initialize database
    Config.init_paths()
    Session, engine = init_db(Config.DATABASE_URL)
    
    def get_db():
        """Get database session."""
        return Session()
    
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return jsonify({'status': 'healthy'})
    
    @app.route('/submit/<token>', methods=['GET'])
    def submit_form(token):
        """Show submission form."""
        db = get_db()
        try:
            service = SubmissionService(db, Config.MEDIA_PATH)
            is_valid, error = service.validate_token(token)
            
            if not is_valid:
                return render_template('error.html', error=error), 403
            
            # Get settings
            recipient_name = db.query(Settings).filter(Settings.key == 'recipient_name').first()
            submission_heading = db.query(Settings).filter(Settings.key == 'submission_heading').first()
            
            recipient = recipient_name.value if recipient_name else 'Bob'
            heading = submission_heading.value if submission_heading else 'Send a Message!'
            
            return render_template('submit.html', token=token, recipient_name=recipient, submission_heading=heading)
        finally:
            db.close()
    
    @app.route('/submit/<token>', methods=['POST'])
    @limiter.limit("5 per hour; 1 per minute")
    def submit_message(token):
        """Handle message submission."""
        db = get_db()
        try:
            name = request.form.get('name', '').strip()
            content = request.form.get('content', '').strip()
            
            if not name or not content:
                flash('Name and message are required', 'error')
                return redirect(request.url)
            
            # Handle image upload
            image_data = None
            image_filename = None
            media_type = None
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    # Simple check for video types
                    if file.mimetype.startswith('video/'):
                        media_type = 'video'
                    elif file.mimetype.startswith('image/'):
                        media_type = 'image'
                    
                    image_data = file.read()
                    image_filename = file.filename
            
            # Get IP address
            ip_address = get_remote_address()
            
            service = SubmissionService(db, Config.MEDIA_PATH)
            success, message = service.create_submission(
                token, name, content, image_data, image_filename, ip_address, media_type
            )
            
            if success:
                return render_template('success.html')
            else:
                flash(message, 'error')
                return redirect(request.url)
        finally:
            db.close()
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8001, debug=True)
