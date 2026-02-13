"""
Test authentication endpoints
"""
import pytest
from models import db, User
from werkzeug.security import generate_password_hash


class TestAuth:
    """Authentication tests"""
    
    def test_register_success(self, client):
        """Test successful registration"""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['user']['username'] == 'newuser'
        assert data['user']['email'] == 'new@example.com'
        assert 'id' in data['user']
    
    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'another@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 400
        assert 'already exists' in response.get_json()['error']
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post('/api/auth/register', json={
            'username': 'anotheruser',
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 400
        assert 'already exists' in response.get_json()['error']
    
    def test_login_success(self, client, test_user, auth_headers):
        """Test successful login"""
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert data['user']['username'] == 'testuser'
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        assert 'Invalid credentials' in response.get_json()['error']
    
    def test_get_me_authenticated(self, client, test_user, auth_headers):
        """Test get current user when authenticated"""
        response = client.get('/api/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == 'testuser'
    
    def test_get_me_unauthenticated(self, client):
        """Test get current user without authentication"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
