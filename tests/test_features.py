"""
Test activity and statistics endpoints
"""
import pytest
from app import db, Activity


class TestActivities:
    """Activity log tests"""
    
    def test_get_activities(self, client, sample_task, auth_headers):
        """Test getting activity log"""
        # Create some activity by updating task
        client.put(f"/api/tasks/{sample_task['id']}",
            headers=auth_headers,
            json={'status': 'in_progress'}
        )
        
        response = client.get('/api/activities?limit=10', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_activity_logged_on_task_create(self, client, auth_headers):
        """Test that activity is logged when task is created"""
        # Create task
        client.post('/api/tasks',
            headers=auth_headers,
            json={'title': 'Activity Test Task'}
        )
        
        # Check activities
        response = client.get('/api/activities', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        # Should have created activity
        assert len(data) > 0


class TestStats:
    """Statistics tests"""
    
    def test_get_stats(self, client, sample_task, auth_headers):
        """Test getting statistics"""
        response = client.get('/api/stats', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should have required fields
        assert 'total' in data
        assert 'by_status' in data
        assert 'today' in data
        assert 'week' in data
    
    def test_stats_reflect_tasks(self, client, auth_headers):
        """Test statistics reflect actual tasks"""
        # Create more tasks
        for i in range(3):
            client.post('/api/tasks',
                headers=auth_headers,
                json={'title': f'Stats Test Task {i}'}
            )
        
        response = client.get('/api/stats', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        # 3 new tasks created in this test
        assert data['total'] >= 3


class TestExport:
    """Export tests"""
    
    def test_export_csv(self, client, sample_task, auth_headers):
        """Test CSV export"""
        response = client.get('/api/export/csv', headers=auth_headers)
        
        assert response.status_code == 200
        assert 'text/csv' in response.content_type
        # Access header directly (Flask test client limitation)
        assert 'attachment' in response.headers.get('Content-Disposition', '')
    
    def test_export_contains_task_data(self, client, sample_task, auth_headers):
        """Test CSV export contains task data"""
        response = client.get('/api/export/csv', headers=auth_headers)
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        assert 'Test Task' in content


class TestHealth:
    """Health check tests"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
