"""
Test comment endpoints
"""
import pytest
from models import db, Comment


class TestComments:
    """Comment tests"""
    
    def test_add_comment(self, client, sample_task, auth_headers):
        """Test adding comment to task"""
        task_id = sample_task['id']
        response = client.post(f'/api/tasks/{task_id}/comments',
            headers=auth_headers,
            json={
                'content': 'This is a test comment',
                'author': 'testuser'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['content'] == 'This is a test comment'
    
    def test_get_comments(self, client, sample_task, auth_headers):
        """Test getting comments for task"""
        task_id = sample_task['id']
        
        # Add comment first
        client.post(f'/api/tasks/{task_id}/comments',
            headers=auth_headers,
            json={'content': 'Comment 1'}
        )
        client.post(f'/api/tasks/{task_id}/comments',
            headers=auth_headers,
            json={'content': 'Comment 2'}
        )
        
        response = client.get(f'/api/tasks/{task_id}/comments', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_comment_with_mentions(self, client, sample_task, auth_headers, test_user):
        """Test comment with user mentions"""
        task_id = sample_task['id']
        response = client.post(f'/api/tasks/{task_id}/comments',
            headers=auth_headers,
            json={
                'content': 'Hey @testuser check this!',
                'author': 'testuser'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        # Mentions should be parsed and stored
        assert data['content'] == 'Hey @testuser check this!'
