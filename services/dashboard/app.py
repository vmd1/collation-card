"""Dashboard Flask application."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from shared.models import init_db
from config import Config
from services import MessageService, InviteLinkService, CoverService, SettingsService


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # ProxyFix for correct URL generation behind Traefik
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Initialize database
    Config.init_paths()
    Session, engine = init_db(Config.DATABASE_URL)
    
    def get_db():
        """Get database session."""
        return Session()
    
    @app.route('/')
    def index():
        """Dashboard overview."""
        db = get_db()
        try:
            msg_service = MessageService(db)
            pending_count = msg_service.get_pending_count()
            recent_messages = msg_service.get_all_messages(limit=10)
            return render_template('index.html', 
                                 pending_count=pending_count,
                                 recent_messages=recent_messages)
        finally:
            db.close()
    
    @app.route('/messages/pending')
    def pending_messages():
        """List pending messages."""
        db = get_db()
        try:
            msg_service = MessageService(db)
            messages = msg_service.get_pending_messages()
            return render_template('pending.html', messages=messages)
        finally:
            db.close()
    
    @app.route('/messages/<int:message_id>/approve', methods=['POST'])
    def approve_message(message_id):
        """Approve a message."""
        db = get_db()
        try:
            msg_service = MessageService(db)
            success = msg_service.approve_message(message_id)
            if success:
                flash('Message approved successfully', 'success')
            else:
                flash('Failed to approve message', 'error')
        finally:
            db.close()
        return redirect(request.referrer or url_for('pending_messages'))
    
    @app.route('/messages/<int:message_id>/reject', methods=['POST'])
    def reject_message(message_id):
        """Reject a message."""
        db = get_db()
        try:
            msg_service = MessageService(db)
            success = msg_service.reject_message(message_id)
            if success:
                flash('Message rejected successfully', 'success')
            else:
                flash('Failed to reject message', 'error')
        finally:
            db.close()
        return redirect(request.referrer or url_for('pending_messages'))
    
    @app.route('/messages/<int:message_id>/edit', methods=['GET', 'POST'])
    def edit_message(message_id):
        """Edit a message."""
        db = get_db()
        try:
            msg_service = MessageService(db)
            message = msg_service.get_message_by_id(message_id)
            
            if not message:
                flash('Message not found', 'error')
                return redirect(url_for('pending_messages'))
            
            if request.method == 'POST':
                name = request.form.get('name', '').strip()
                content = request.form.get('content', '').strip()
                
                if not name or not content:
                    flash('Name and message are required', 'error')
                    return redirect(request.url)
                
                success = msg_service.update_message(message_id, name, content)
                if success:
                    flash('Message updated successfully', 'success')
                    # Redirect based on message status
                    if message.status == 'pending':
                        return redirect(url_for('pending_messages'))
                    elif message.status == 'approved':
                        return redirect(url_for('approved_messages'))
                else:
                    flash('Failed to update message', 'error')
            
            return render_template('edit_message.html', message=message)
        finally:
            db.close()
    
    @app.route('/messages/<int:message_id>/delete', methods=['POST'])
    def delete_message(message_id):
        """Delete a message."""
        db = get_db()
        try:
            msg_service = MessageService(db)
            success = msg_service.delete_message(message_id)
            if success:
                flash('Message deleted successfully', 'success')
            else:
                flash('Failed to delete message', 'error')
        finally:
            db.close()
        return redirect(request.referrer or url_for('index'))
    
    @app.route('/messages/<int:message_id>/unapprove', methods=['POST'])
    def unapprove_message(message_id):
        """Unapprove a message."""
        db = get_db()
        try:
            msg_service = MessageService(db)
            success = msg_service.unapprove_message(message_id)
            if success:
                flash('Message unapproved successfully', 'success')
            else:
                flash('Failed to unapprove message', 'error')
        finally:
            db.close()
        return redirect(request.referrer or url_for('approved_messages'))
    
    @app.route('/messages/approved')
    def approved_messages():
        """List approved messages."""
        db = get_db()
        try:
            msg_service = MessageService(db)
            messages = msg_service.get_approved_messages()
            return render_template('approved.html', messages=messages)
        finally:
            db.close()
    
    @app.route('/invite-links', methods=['GET', 'POST'])
    def invite_links():
        """Manage invite links."""
        db = get_db()
        try:
            link_service = InviteLinkService(db)
            
            if request.method == 'POST':
                note = request.form.get('note')
                max_uses = request.form.get('max_uses', type=int)
                expires_hours = request.form.get('expires_hours', type=int)
                
                link = link_service.create_link(note, max_uses, expires_hours)
                flash(f'Invite link created: {link.token}', 'success')
                return redirect(url_for('invite_links'))
            
            links = link_service.get_all_links()
            return render_template('invite_links.html', links=links)
        finally:
            db.close()
    
    @app.route('/invite-links/<token>/deactivate', methods=['POST'])
    def deactivate_link(token):
        """Deactivate an invite link."""
        db = get_db()
        try:
            link_service = InviteLinkService(db)
            success = link_service.deactivate_link(token)
            if success:
                flash('Link deactivated successfully', 'success')
            else:
                flash('Failed to deactivate link', 'error')
        finally:
            db.close()
        return redirect(url_for('invite_links'))
    
    @app.route('/cover', methods=['GET', 'POST'])
    def cover():
        """Manage card cover."""
        db = get_db()
        try:
            cover_service = CoverService(db, Config.MEDIA_PATH)
            
            if request.method == 'POST':
                if 'cover' not in request.files:
                    flash('No file uploaded', 'error')
                    return redirect(url_for('cover'))
                
                file = request.files['cover']
                if file.filename == '':
                    flash('No file selected', 'error')
                    return redirect(url_for('cover'))
                
                try:
                    file_data = file.read()
                    path = cover_service.upload_cover(file_data, file.filename)
                    flash(f'Cover uploaded successfully', 'success')
                except Exception as e:
                    flash(f'Failed to upload cover: {str(e)}', 'error')
                
                return redirect(url_for('cover'))
            
            current_cover = cover_service.get_active_cover()
            return render_template('cover.html', cover=current_cover)
        finally:
            db.close()
    
    @app.route('/media/<path:filename>')
    def serve_media(filename):
        """Serve media files."""
        return send_from_directory(Config.MEDIA_PATH, filename)
    
    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        """Manage application settings."""
        db = get_db()
        try:
            settings_service = SettingsService(db)
            
            if request.method == 'POST':
                submission_heading = request.form.get('submission_heading', '').strip()
                recipient_name = request.form.get('recipient_name', '').strip()
                
                if submission_heading and recipient_name:
                    settings_service.set_setting('submission_heading', submission_heading)
                    settings_service.set_setting('recipient_name', recipient_name)
                    flash('Settings saved successfully', 'success')
                else:
                    flash('All fields are required', 'error')
                return redirect(url_for('settings'))
            
            current_settings = settings_service.get_all_settings()
            return render_template('settings.html', settings=current_settings)
        finally:
            db.close()
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)
