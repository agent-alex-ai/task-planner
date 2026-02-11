import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_PATH = 'tasks.db'

def init_db():
    """Initialize database with tasks and comments tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'todo',
        assignee TEXT,
        priority INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        author TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    )''')
    
    conn.commit()
    conn.close()

# Task endpoints
@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM tasks ORDER BY created_at DESC')
    tasks = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO tasks (title, description, status, assignee, priority)
                  VALUES (?, ?, ?, ?, ?)''',
              (data.get('title'), data.get('description'), 
               data.get('status', 'todo'), data.get('assignee'), 
               data.get('priority', 0)))
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': task_id, 'status': 'created'}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update task status, assignee, etc."""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    updates = []
    params = []
    for key in ['title', 'description', 'status', 'assignee', 'priority']:
        if key in data:
            updates.append(f'{key}=?')
            params.append(data[key])
    
    if updates:
        updates.append("updated_at=CURRENT_TIMESTAMP")
        params.append(task_id)
        c.execute(f'UPDATE tasks SET {",".join(updates)} WHERE id=?', params)
        conn.commit()
    
    conn.close()
    return jsonify({'status': 'updated'})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM comments WHERE task_id=?', (task_id,))
    c.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

# Comments endpoints
@app.route('/api/tasks/<int:task_id>/comments', methods=['GET'])
def get_comments(task_id):
    """Get all comments for a task"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM comments WHERE task_id=? ORDER BY created_at', (task_id,))
    comments = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(comments)

@app.route('/api/tasks/<int:task_id>/comments', methods=['POST'])
def add_comment(task_id):
    """Add a comment to a task"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO comments (task_id, author, content)
                  VALUES (?, ?, ?)''',
              (task_id, data.get('author'), data.get('content')))
    c.execute("UPDATE tasks SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'comment_added'}), 201

# Statistics endpoints
@app.route('/api/stats')
def get_stats():
    """Get task statistics"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Total tasks
    c.execute('SELECT COUNT(*) as total FROM tasks')
    total = c.fetchone()['total']
    
    # By status
    c.execute('SELECT status, COUNT(*) as count FROM tasks GROUP BY status')
    by_status = {row['status']: row['count'] for row in c.fetchall()}
    
    # Today's tasks
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) as today FROM tasks WHERE date(created_at)=?', (today,))
    today_count = c.fetchone()['today']
    
    # This week's tasks
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) as week FROM tasks WHERE date(created_at)>=?', (week_ago,))
    week_count = c.fetchone()['week']
    
    conn.close()
    
    return jsonify({
        'total': total,
        'by_status': by_status,
        'today': today_count,
        'week': week_count,
        'completed': by_status.get('done', 0),
        'in_progress': by_status.get('in_progress', 0)
    })

if __name__ == '__main__':
    init_db()
    # Serve static files
    import os
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    app.run(host='0.0.0.0', port=5000, debug=True, static_folder=static_folder)
