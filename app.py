"""
Task Planner Dashboard - Flask Application with PostgreSQL
Features: Authentication, Tasks, Comments, Activity Log, Search, Export
"""

import os
import csv
import io
import json
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://taskplanner:taskplanner_secret@localhost:5432/taskplanner'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# ============== MODELS ==============

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks_authored = db.relationship('Task', backref='author', lazy='dynamic', foreign_keys='Task.author_id')
    tasks_assigned = db.relationship('Task', backref='assignee', lazy='dynamic', foreign_keys='Task.assignee_id')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    activities = db.relationship('Activity', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'created_at': self.created_at.isoformat()
        }

class Task(db.Model):
    """Task model with priorities and due dates"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='todo')  # todo, in_progress, review, done
    priority = db.Column(db.Integer, default=1)  # 0=low, 1=medium, 2=high
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assignee_id': self.assignee_id,
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'author_id': self.author_id,
            'author': self.author.to_dict() if self.author else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'position': self.position,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'comments_count': self.comments.count()
        }

class Comment(db.Model):
    """Comment model for task discussions"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mentions = db.Column(db.String(500))  # JSON array of mentioned user IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'author_id': self.author_id,
            'author': self.author.to_dict() if self.author else None,
            'content': self.content,
            'mentions': self.mentions,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Activity(db.Model):
    """Activity log for tracking all changes"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created, updated, deleted, status_changed, commented
    entity_type = db.Column(db.String(20), nullable=False)  # task, comment, user
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON with additional details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        # Parse JSON string back to dict for SQLite
        details_parsed = None
        if self.details:
            try:
                details_parsed = json.loads(self.details)
            except (json.JSONDecodeError, TypeError):
                details_parsed = self.details
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': details_parsed,
            'created_at': self.created_at.isoformat()
        }

# ============== HELPERS ==============

def log_activity(user_id, action, entity_type, entity_id, details=None):
    """Log user activity"""
    # Convert dict to JSON string for SQLite compatibility
    details_json = json.dumps(details) if details else None
    activity = Activity(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details_json
    )
    db.session.add(activity)
    db.session.commit()

def notify_mentions(task_id, mentions, author_id, content):
    """Process mentions in comments"""
    if mentions:
        for mention in mentions:
            mention_user = User.query.get(mention)
            if mention_user and mention_user.id != author_id:
                # In production, send notification email/push
                pass

# ============== AUTH ROUTES ==============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
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

@app.route('/api/auth/login', methods=['POST'])
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

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    """Get current user"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict())

# ============== USER ROUTES ==============

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    users = User.query.filter_by(is_active=True).all()
    return jsonify([u.to_dict() for u in users])

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

# ============== TASK ROUTES ==============

@app.route('/api/tasks', methods=['GET'])
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
    
    if status:
        query = query.filter(Task.status == status)
    if assignee:
        query = query.filter(Task.assignee_id == assignee)
    if author:
        query = query.filter(Task.author_id == author)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term)
            )
        )
    
    tasks = query.order_by(Task.position, Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])

@app.route('/api/tasks', methods=['POST'])
@jwt_required()
def create_task():
    """Create new task"""
    user_id = get_jwt_identity()
    data = request.json or {}
    
    # Validate required fields
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    try:
        task = Task(
            title=title,
            description=data.get('description', '').strip() or None,
            status=data.get('status', 'todo'),
            priority=int(data.get('priority', 1)),
            assignee_id=data.get('assignee_id') or None,
            author_id=user_id,
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None
        )
        
        db.session.add(task)
        db.session.commit()
        
        log_activity(user_id, 'created', 'task', task.id, {'title': task.title})
        
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating task: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Get single task"""
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update task"""
    user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    old_status = task.status
    changes = {}
    
    if 'title' in data:
        changes['title'] = data['title']
        task.title = data['title']
    if 'description' in data:
        changes['description'] = data['description']
        task.description = data['description']
    if 'status' in data:
        changes['status'] = {'from': old_status, 'to': data['status']}
        task.status = data['status']
    if 'priority' in data:
        changes['priority'] = data['priority']
        task.priority = data['priority']
    if 'assignee_id' in data:
        changes['assignee'] = data['assignee_id']
        task.assignee_id = data['assignee_id']
    if 'due_date' in data:
        task.due_date = datetime.fromisoformat(data['due_date']) if data.get('due_date') else None
    if 'position' in data:
        task.position = data['position']
    
    db.session.commit()
    
    if changes:
        log_activity(user_id, 'updated', 'task', task.id, str(changes))
    
    return jsonify(task.to_dict())

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
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

@app.route('/api/tasks/<int:task_id>/move', methods=['POST'])
@jwt_required()
def move_task(task_id):
    """Move task to different status (drag & drop)"""
    user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    old_status = task.status
    new_status = data.get('status')
    
    if new_status and new_status != old_status:
        task.status = new_status
        
        # Reorder tasks in target column
        position = data.get('position', 0)
        Task.query.filter(
            Task.status == new_status,
            Task.id != task_id
        ).filter(Task.position >= position).update({
            Task.position: Task.position + 1
        })
        task.position = position
    
    db.session.commit()
    
    log_activity(user_id, 'status_changed', 'task', task.id, 
                 {'from': old_status, 'to': new_status})
    
    return jsonify(task.to_dict())

# ============== COMMENT ROUTES ==============

@app.route('/api/tasks/<int:task_id>/comments', methods=['GET'])
@jwt_required()
def get_comments(task_id):
    """Get comments for a task"""
    comments = Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at).all()
    return jsonify([c.to_dict() for c in comments])

@app.route('/api/tasks/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(task_id):
    """Add comment to task"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Parse mentions from content (@username)
    mentions = []
    import re
    for mention in re.finditer(r'@(\w+)', data.get('content', '')):
        username = mention.group(1)
        user = User.query.filter_by(username=username).first()
        if user:
            mentions.append(user.id)
    
    comment = Comment(
        task_id=task_id,
        author_id=user_id,
        content=data.get('content'),
        mentions=str(mentions) if mentions else None
    )
    
    db.session.add(comment)
    db.session.commit()
    
    log_activity(user_id, 'commented', 'comment', comment.id)
    
    # Notify mentioned users
    notify_mentions(task_id, mentions, user_id, data.get('content'))
    
    return jsonify(comment.to_dict()), 201

# ============== ACTIVITY ROUTES ==============

@app.route('/api/activities', methods=['GET'])
@jwt_required()
def get_activities():
    """Get activity log"""
    user_id = get_jwt_identity()
    
    limit = request.args.get('limit', 50, type=int)
    entity_type = request.args.get('entity_type')
    
    query = Activity.query
    
    if entity_type:
        query = query.filter(Activity.entity_type == entity_type)
    
    activities = query.order_by(Activity.created_at.desc()).limit(limit).all()
    return jsonify([a.to_dict() for a in activities])

# ============== STATS ROUTES ==============

@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get task statistics"""
    user_id = get_jwt_identity()
    
    # Total tasks
    total = Task.query.count()
    
    # By status
    by_status = db.session.query(
        Task.status, func.count(Task.id)
    ).group_by(Task.status).all()
    status_counts = {s: c for s, c in by_status}
    
    # Today's tasks
    today = datetime.now().date()
    today_count = Task.query.filter(
        func.date(Task.created_at) == today
    ).count()
    
    # This week's tasks
    week_ago = today - timedelta(days=7)
    week_count = Task.query.filter(
        func.date(Task.created_at) >= week_ago
    ).count()
    
    # Overdue tasks
    overdue = Task.query.filter(
        Task.due_date < datetime.now(),
        Task.status != 'done'
    ).count()
    
    # Tasks by priority
    by_priority = db.session.query(
        Task.priority, func.count(Task.id)
    ).group_by(Task.priority).all()
    priority_counts = {p: c for p, c in by_priority}
    
    return jsonify({
        'total': total,
        'by_status': status_counts,
        'by_priority': priority_counts,
        'today': today_count,
        'week': week_count,
        'overdue': overdue,
        'completed': status_counts.get('done', 0),
        'in_progress': status_counts.get('in_progress', 0),
        'review': status_counts.get('review', 0)
    })

# ============== EXPORT ROUTES ==============

@app.route('/api/export/csv', methods=['GET'])
@jwt_required()
def export_csv():
    """Export tasks to CSV"""
    user_id = get_jwt_identity()
    
    tasks = Task.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Title', 'Description', 'Status', 'Priority', 'Assignee', 'Author', 'Due Date', 'Created'])
    
    for task in tasks:
        writer.writerow([
            task.id,
            task.title,
            task.description or '',
            task.status,
            ['Low', 'Medium', 'High'][task.priority],
            task.assignee.username if task.assignee else '',
            task.author.username if task.author else '',
            task.due_date.isoformat() if task.due_date else '',
            task.created_at.isoformat()
        ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'tasks_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

# ============== HEALTH CHECK ==============

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# ============== UI ROUTES ==============

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/api/docs')
def docs():
    """API documentation"""
    return render_template('docs.html')

# ============== INIT ==============

def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@taskplanner.local',
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Created default admin user (admin/admin123)")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
