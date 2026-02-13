"""
API routes Blueprint
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models import db, User, Task, Comment, Activity
from utils import log_activity, notify_mentions
from sqlalchemy import func
import csv
import io

api = Blueprint('api', __name__, url_prefix='/api')


# ============== AUTH ROUTES ==============

@api.route('/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    log_activity(user.id, 'registered', 'user', user.id)
    
    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201


@api.route('/auth/login', methods=['POST'])
def login():
    """Login and get JWT token"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    access_token = create_access_token(identity=user.id)
    log_activity(user.id, 'logged_in', 'user', user.id)
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    })


@api.route('/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    """Get current user"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict())


# ============== USER ROUTES ==============

@api.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    users = User.query.filter_by(is_active=True).all()
    return jsonify([u.to_dict() for u in users])


@api.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


# ============== TASK ROUTES ==============

@api.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get tasks with filters and search"""
    user_id = get_jwt_identity()
    
    # Filters
    status = request.args.get('status')
    assignee = request.args.get('assignee')
    priority = request.args.get('priority', type=int)
    search = request.args.get('q')
    author = request.args.get('author', type=int)
    
    query = Task.query

    # Filter by author (tasks user created) OR assignee (tasks assigned to user)
    if author:
        query = query.filter(Task.author_id == author)
    elif assignee:
        query = query.filter(Task.assignee_id == assignee)
    else:
        # Default: show user's tasks (created or assigned)
        query = query.filter(
            (Task.author_id == user_id) | (Task.assignee_id == user_id)
        )
    
    if status:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if search:
        query = query.filter(Task.title.ilike(f'%{search}%'))
    
    tasks = query.order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])


@api.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    """Create new task"""
    user_id = get_jwt_identity()
    data = request.json
    
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    try:
        # Parse due_date if provided
        due_date = None
        if data.get('due_date'):
            from datetime import datetime
            due_date_str = data['due_date']
            # Try different formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                try:
                    due_date = datetime.strptime(due_date_str, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                # Default fallback
                due_date = datetime.strptime(due_date_str[:10], '%Y-%m-%d').date()
        
        task = Task(
            title=title,
            description=data.get('description'),
            status=data.get('status', 'todo'),
            priority=data.get('priority', 1),
            due_date=due_date,
            author_id=user_id,
            assignee_id=data.get('assignee_id')
        )
        db.session.add(task)
        db.session.commit()
        
        log_activity(user_id, 'created', 'task', task.id, {'title': task.title})
        
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Get single task"""
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())


@api.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update task"""
    user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    # Track changes for activity log
    changes = []
    
    if 'title' in data and data['title'] != task.title:
        changes.append(f"title: {task.title} → {data['title']}")
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data and data['status'] != task.status:
        changes.append(f"status: {task.status} → {data['status']}")
        task.status = data['status']
    if 'priority' in data and data['priority'] != task.priority:
        changes.append(f"priority: {task.priority} → {data['priority']}")
        task.priority = data['priority']
    if 'due_date' in data:
        # Parse date string to date object
        if data['due_date']:
            from datetime import datetime
            due_date_str = data['due_date']
            # Try different formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                try:
                    task.due_date = datetime.strptime(due_date_str, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                # Default fallback
                task.due_date = datetime.strptime(due_date_str[:10], '%Y-%m-%d').date()
        else:
            task.due_date = None
    if 'assignee_id' in data:
        task.assignee_id = data['assignee_id']
    
    db.session.commit()
    
    if changes:
        log_activity(user_id, 'updated', 'task', task.id, {'changes': changes})
    
    return jsonify(task.to_dict())


@api.route('/tasks/<int:task_id>/move', methods=['POST'])
@jwt_required()
def move_task(task_id):
    """Move task to another status (for Kanban drag-drop)"""
    user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    old_status = task.status
    new_status = data.get('status', task.status)
    position = data.get('position', 0)
    
    task.status = new_status
    db.session.commit()
    
    log_activity(user_id, 'status_changed', 'task', task.id, 
                 {'from': old_status, 'to': new_status, 'position': position})
    
    return jsonify(task.to_dict())


@api.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete task"""
    user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    
    task_title = task.title
    db.session.delete(task)
    db.session.commit()
    
    log_activity(user_id, 'deleted', 'task', task_id, {'title': task_title})
    
    return jsonify({'message': 'Task deleted'})


# ============== COMMENT ROUTES ==============

@api.route('/tasks/<int:task_id>/comments', methods=['GET'])
@jwt_required()
def get_comments(task_id):
    """Get comments for a task"""
    Task.query.get_or_404(task_id)
    comments = Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at.asc()).all()
    return jsonify([c.to_dict() for c in comments])


@api.route('/tasks/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(task_id):
    """Add comment to task"""
    user_id = get_jwt_identity()
    Task.query.get_or_404(task_id)
    data = request.json
    
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    # Parse mentions from content (@username format)
    import re
    mentions = []
    mention_pattern = r'@(\w+)'
    for match in re.finditer(mention_pattern, content):
        username = match.group(1)
        user = User.query.filter_by(username=username).first()
        if user:
            mentions.append(user.id)
    
    comment = Comment(
        task_id=task_id,
        author_id=user_id,
        content=content,
        mentions=str(mentions) if mentions else None
    )
    db.session.add(comment)
    db.session.commit()
    
    if mentions:
        notify_mentions(task_id, mentions, user_id, content)
    
    log_activity(user_id, 'commented', 'task', task_id)
    
    return jsonify(comment.to_dict()), 201


# ============== ACTIVITY & STATS ==============

@api.route('/activities', methods=['GET'])
@jwt_required()
def get_activities():
    """Get activity log"""
    user_id = get_jwt_identity()
    
    # Get user's activities
    activities = Activity.query.filter_by(user_id=user_id).order_by(
        Activity.created_at.desc()
    ).limit(50).all()
    
    return jsonify([a.to_dict() for a in activities])


@api.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get task statistics"""
    from datetime import datetime, timedelta
    user_id = get_jwt_identity()
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=now.weekday())
    
    # Tasks created by user
    created_count = Task.query.filter_by(author_id=user_id).count()
    
    # Tasks assigned to user
    assigned_count = Task.query.filter_by(assignee_id=user_id).count()
    
    # Tasks created today
    today_count = Task.query.filter(
        Task.author_id == user_id,
        Task.created_at >= today_start
    ).count()
    
    # Tasks created this week
    week_count = Task.query.filter(
        Task.author_id == user_id,
        Task.created_at >= week_start
    ).count()
    
    # Tasks by status
    status_counts = db.session.query(
        Task.status,
        func.count(Task.id)
    ).filter(
        (Task.author_id == user_id) | (Task.assignee_id == user_id)
    ).group_by(Task.status).all()
    
    status_dict = {s: c for s, c in status_counts}
    
    return jsonify({
        'total': created_count + assigned_count,
        'created': created_count,
        'assigned': assigned_count,
        'today': today_count,
        'week': week_count,
        'by_status': status_dict,
        'todo': status_dict.get('todo', 0),
        'in_progress': status_dict.get('in_progress', 0),
        'review': status_dict.get('review', 0),
        'done': status_dict.get('done', 0)
    })


# ============== EXPORT ==============

@api.route('/export/csv', methods=['GET'])
@jwt_required()
def export_csv():
    """Export tasks as CSV"""
    user_id = get_jwt_identity()
    
    tasks = Task.query.filter(
        (Task.author_id == user_id) | (Task.assignee_id == user_id)
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Title', 'Description', 'Status', 'Priority', 'Due Date', 'Author', 'Assignee'])
    
    # Data
    for task in tasks:
        writer.writerow([
            task.id,
            task.title,
            task.description or '',
            task.status,
            task.priority,
            task.due_date or '',
            task.author.username if task.author else '',
            task.assignee.username if task.assignee else ''
        ])
    
    output.seek(0)
    
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=tasks_{user_id}.csv'
    
    return response


# ============== HEALTH CHECK ==============

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'database': str(e)}), 500
