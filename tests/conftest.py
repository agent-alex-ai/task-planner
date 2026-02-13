"""
Test configuration for Task Planner
"""
import pytest
import os
# Set SQLite BEFORE importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import app, db, User, Task, Comment, Activity
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='function')
def client():
    """Create test client with SQLite - fresh database for each test"""
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
    
    # Cleanup after test
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def test_user(client):
    """Create test user and return dict for safe access outside app context"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('testpass123')
        )
        db.session.add(user)
        db.session.commit()
        # Return dict with id to avoid DetachedInstanceError
        return {'id': user.id, 'username': user.username, 'email': user.email}


@pytest.fixture(scope='function')
def auth_headers(client, test_user):
    """Get authorization headers"""
    response = client.post('/api/auth/login', json={
        'username': test_user['username'],
        'password': 'testpass123'
    })
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def sample_task(client, test_user, auth_headers):
    """Create sample task"""
    response = client.post('/api/tasks',
        headers=auth_headers,
        json={
            'title': 'Test Task',
            'description': 'Test Description',
            'status': 'todo',
            'priority': 1
        }
    )
    return response.get_json()
