"""
Test task endpoints
"""
import pytest
from app import db, Task


class TestTasks:
    """Task CRUD tests"""
    
    def test_create_task_success(self, client, test_user, auth_headers):
        """Test successful task creation"""
        response = client.post('/api/tasks',
            headers=auth_headers,
            json={
                'title': 'New Task',
                'description': 'Task description',
                'status': 'todo',
                'priority': 2
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['title'] == 'New Task'
        assert data['description'] == 'Task description'
        assert data['status'] == 'todo'
        assert data['priority'] == 2
        assert data['author']['username'] == 'testuser'
    
    def test_create_task_without_title(self, client, auth_headers):
        """Test task creation without title"""
        response = client.post('/api/tasks',
            headers=auth_headers,
            json={
                'description': 'No title task',
                'status': 'todo'
            }
        )
        
        assert response.status_code == 400
        assert 'Title is required' in response.get_json()['error']
    
    def test_create_task_unauthorized(self, client):
        """Test task creation without authentication"""
        response = client.post('/api/tasks', json={
            'title': 'Unauthorized Task'
        })
        
        assert response.status_code == 401
    
    def test_get_tasks(self, client, sample_task, auth_headers):
        """Test get all tasks"""
        response = client.get('/api/tasks', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_tasks_with_filters(self, client, sample_task, auth_headers):
        """Test get tasks with filters"""
        # Filter by status
        response = client.get('/api/tasks?status=todo', headers=auth_headers)
        assert response.status_code == 200
        
        # Filter by priority
        response = client.get('/api/tasks?priority=1', headers=auth_headers)
        assert response.status_code == 200
    
    def test_get_tasks_with_search(self, client, sample_task, auth_headers):
        """Test get tasks with search"""
        response = client.get('/api/tasks?q=Test', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_get_single_task(self, client, sample_task, auth_headers):
        """Test get single task"""
        task_id = sample_task['id']
        response = client.get(f'/api/tasks/{task_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == task_id
        assert data['title'] == 'Test Task'
    
    def test_update_task(self, client, sample_task, auth_headers):
        """Test update task"""
        task_id = sample_task['id']
        response = client.put(f'/api/tasks/{task_id}',
            headers=auth_headers,
            json={
                'title': 'Updated Task',
                'status': 'in_progress',
                'priority': 2
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['title'] == 'Updated Task'
        assert data['status'] == 'in_progress'
    
    def test_update_task_status(self, client, sample_task, auth_headers):
        """Test update task status via move endpoint"""
        task_id = sample_task['id']
        response = client.post(f'/api/tasks/{task_id}/move',
            headers=auth_headers,
            json={
                'status': 'done',
                'position': 0
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'done'
    
    def test_delete_task(self, client, sample_task, auth_headers):
        """Test delete task"""
        task_id = sample_task['id']
        response = client.delete(f'/api/tasks/{task_id}', headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify deleted
        response = client.get(f'/api/tasks/{task_id}', headers=auth_headers)
        assert response.status_code == 404
    
    def test_task_with_due_date(self, client, auth_headers):
        """Test task creation with due date"""
        response = client.post('/api/tasks',
            headers=auth_headers,
            json={
                'title': 'Task with Due Date',
                'due_date': '2026-12-31T23:59:00'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['due_date'] is not None
        assert '2026-12-31' in data['due_date']
    
    def test_task_with_assignee(self, client, test_user, auth_headers):
        """Test task creation with assignee"""
        response = client.post('/api/tasks',
            headers=auth_headers,
            json={
                'title': 'Assigned Task',
                'assignee_id': test_user['id']
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['assignee_id'] == test_user['id']
