"""
Test user and filter endpoints
"""
import pytest
from app import db, User


class TestUsers:
    """User tests"""
    
    def test_get_users(self, client, test_user, auth_headers):
        """Test getting all users"""
        response = client.get('/api/users', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_single_user(self, client, test_user, auth_headers):
        """Test getting single user"""
        response = client.get(f'/api/users/{test_user["id"]}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == 'testuser'


class TestFilters:
    """Filter and search tests"""
    
    def test_filter_by_status(self, client, auth_headers):
        """Test filtering by status"""
        # Create tasks with different statuses
        client.post('/api/tasks', headers=auth_headers, json={'title': 'Task 1', 'status': 'todo'})
        client.post('/api/tasks', headers=auth_headers, json={'title': 'Task 2', 'status': 'in_progress'})
        client.post('/api/tasks', headers=auth_headers, json={'title': 'Task 3', 'status': 'done'})
        
        # Filter by todo
        response = client.get('/api/tasks?status=todo', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        for task in data:
            assert task['status'] == 'todo'
    
    def test_filter_by_priority(self, client, auth_headers):
        """Test filtering by priority"""
        # Create tasks with different priorities
        client.post('/api/tasks', headers=auth_headers, json={'title': 'Low', 'priority': 0})
        client.post('/api/tasks', headers=auth_headers, json={'title': 'High', 'priority': 2})
        
        # Filter by high priority
        response = client.get('/api/tasks?priority=2', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        for task in data:
            assert task['priority'] == 2
    
    def test_search_by_title(self, client, auth_headers):
        """Test search by title"""
        client.post('/api/tasks', headers=auth_headers, json={'title': 'UniqueSearchTerm123'})
        
        response = client.get('/api/tasks?q=UniqueSearchTerm123', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert any('UniqueSearchTerm123' in t['title'] for t in data)
    
    def test_combined_filters(self, client, auth_headers):
        """Test combined filters"""
        response = client.get('/api/tasks?status=todo&priority=1&q=test', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
