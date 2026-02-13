"""
Task Planner Dashboard - Flask Application
Refactored with Blueprint and modular structure
"""
import os
from datetime import timedelta

from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from models import db
from routes.api import api


def create_app(testing: bool = False):
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    if testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
            'DATABASE_URL', 
            'postgresql://taskplanner:taskplanner_secret@localhost:5432/taskplanner'
        )
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    JWTManager(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Templates
    @app.route('/')
    def index():
        """Main page - requires authentication"""
        from flask_jwt_extended import verify_jwt_in_request
        try:
            verify_jwt_in_request()
            return render_template('index.html')
        except Exception:
            return render_template('index.html', requires_auth=True)
    
    @app.route('/login')
    def login_page():
        """Login page - no auth required"""
        return render_template('index.html', login_page=True)
    
    # Create tables (only if not testing)
    if not testing:
        with app.app_context():
            db.create_all()
    
    return app


# Don't create app at import time - use create_app()
# app = create_app()  # Commented out to avoid auto-connection


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)


# Export app for gunicorn
app = create_app()
