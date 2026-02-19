#!/usr/bin/env python3
"""
Канбан доска - использует PostgreSQL базу данных проекта
"""

import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Подключение к PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://taskplanner:taskplanner_secret@localhost:5432/taskplanner')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Логи в памяти
LOG_STORAGE = []

def log(action, details=""):
    entry = {"time": datetime.now().strftime("%H:%M:%S"), "action": action, "details": details}
    LOG_STORAGE.append(entry)
    print(f"[{entry['time']}] {action}: {details}")

# Маппинг статусов канбана на статусы в БД
COLUMN_STATUS_MAP = {
    'New': 'todo',
    'In Progress': 'in_progress', 
    'Done': 'done'
}

REVERSE_STATUS_MAP = {v: k for k, v in COLUMN_STATUS_MAP.items()}
COLUMNS = ['New', 'In Progress', 'Done']

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='todo')
    priority = db.Column(db.Integer, default=1)
    due_date = db.Column(db.Date)
    author_id = db.Column(db.Integer, nullable=False)
    assignee_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

HTML = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Канбан Доска</title>
<style>
:root{--bg:#1a1a2e;--bg2:#16213e;--bg3:#0f3460;--txt:#eee;--txt2:#aaa;--acc:#00d9ff;--err:#e94560;--ok:#00ff88;--new:#9b59b6;--prog:#f39c12;--done:#27ae60}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--txt);min-height:100vh;display:flex;flex-direction:column}
.header{background:var(--bg2);padding:15px 20px;display:flex;justify-content:space-between;align-items:center}
.header h1{font-size:20px;color:var(--acc)}
.add-btn{background:var(--acc);color:var(--bg);padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-weight:600}
.board{flex:1;display:flex;gap:20px;padding:20px;overflow-x:auto}
.column{background:var(--bg2);min-width:300px;max-width:350px;border-radius:12px;display:flex;flex-direction:column;max-height:calc(100vh - 140px)}
.column-header{padding:15px;border-bottom:1px solid var(--bg3);display:flex;justify-content:space-between;align-items:center}
.column-title{font-weight:600;font-size:14px;text-transform:uppercase}
.col-new .column-title{color:var(--new)}
.col-in-progress .column-title{color:var(--prog)}
.col-done .column-title{color:var(--done)}
.column-count{background:var(--bg3);padding:2px 8px;border-radius:10px;font-size:12px}
.column-cards{padding:10px;flex:1;overflow-y:auto;min-height:100px}
.card{background:var(--bg3);border-radius:8px;padding:12px;margin-bottom:10px;cursor:grab;transition:transform 0.2s}
.card:hover{transform:translateY(-2px)}
.card-title{font-weight:600;margin-bottom:8px}
.card-desc{font-size:12px;color:var(--txt2);margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.card-actions{display:flex;gap:5px;margin-top:10px;padding-top:10px;border-top:1px solid var(--bg2)}
.card-btn{background:var(--bg2);border:none;color:var(--txt);padding:4px 8px;border-radius:4px;cursor:pointer}
/* Log */
.log{position:fixed;bottom:0;left:0;right:0;background:var(--bg2);border-top:2px solid var(--acc);z-index:100}
.log-h{padding:10px 20px;background:var(--bg3);cursor:pointer;display:flex;justify-content:space-between}
.log-t{font-size:12px;color:var(--acc)}
.log-c{max-height:0;overflow:hidden;transition:max-height 0.3s}
.log-c.expanded{max-height:200px;overflow:auto}
.log-e{padding:6px 20px;font-family:monospace;font-size:11px;border-bottom:1px solid var(--bg3)}
.log-e .t{color:var(--acc)}.log-e .a{color:var(--err)}
/* Modal */
.modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);z-index:200;align-items:center;justify-content:center}
.modal.active{display:flex}
.modal-content{background:var(--bg2);padding:25px;border-radius:12px;width:90%;max-width:450px}
.modal h2{margin-bottom:20px;color:var(--acc)}
.form{margin-bottom:15px}
.form label{display:block;font-size:11px;color:var(--txt2);margin-bottom:6px}
.form input,.form textarea,.form select{width:100%;padding:12px;background:var(--bg3);border:1px solid var(--bg3);color:var(--txt);border-radius:6px}
.form textarea{height:80px}
.actions-m{display:flex;justify-content:flex-end;gap:10px;margin-top:20px}
.btn-cancel{background:var(--bg3);color:var(--txt);padding:12px 24px;border:none;border-radius:8px;cursor:pointer}
.btn-save{background:var(--acc);color:var(--bg);padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-weight:600}
.dropping{background:rgba(0,217,255,0.1);border:2px dashed var(--acc)}
</style>
</head>
<body>
<div class="header">
<h1>📋 Канбан Доска</h1>
<button class="add-btn" onclick="openModal()">+ Добавить</button>
</div>
<div class="board" id="board"></div>
<!-- Log -->
<div class="log">
<div class="log-h" onclick="tl()"><span class="log-t">📜 Лог</span><span>▲/▼</span></div>
<div class="log-c" id="lc"></div>
</div>
<!-- Modal -->
<div class="modal" id="md">
<div class="modal-content">
<h2 id="mt">Новая карточка</h2>
<form id="mf">
<input type="hidden" id="ir">
<div class="form"><label>Название</label><input type="text" id="in" required></div>
<div class="form"><label>Описание</label><textarea id="id"></textarea></div>
<div class="form"><label>Статус</label><select id="ist"><option value="New">New</option><option value="In Progress">In Progress</option><option value="Done">Done</option></select></div>
<div class="actions-m"><button type="button" class="btn-cancel" onclick="cl()">Отмена</button><button type="submit" class="btn-save">Сохранить</button></div>
</form>
</div>
</div>
<script>
const COLUMNS = ['New','In Progress','Done'];
let cards = [];
fetch('/api/cards').then(r=>r.json()).then(d=>{cards=d;render()});
function getStatus(col){
const map={'New':'todo','In Progress':'in_progress','Done':'done'};
return map[col]||'todo';
}
function render(){
document.getElementById('board').innerHTML=COLUMNS.map(col=>{
const colCards=cards.filter(c=>getStatus(col)===c.status);
return`<div class="column col-${col.toLowerCase().replace(' ','-')}" ondragover="drago(event)" ondrop="drop(event,'${col}')">
<div class="column-header"><span class="column-title">${col}</span><span class="column-count">${colCards.length}</span></div>
<div class="column-cards">
${colCards.map(c=>`<div class="card" draggable="true" ondragstart="drag(event,${c.id})">
<div class="card-title">#${c.id} ${c.title}</div>
<div class="card-desc">${c.description||''}</div>
<div class="card-actions">
<button class="card-btn" onclick="ed(${c.id})">✏️</button>
<button class="card-btn" onclick="dl(${c.id})">🗑️</button>
</div></div>`).join('')}
</div></div>`}).join('')}
let dragId=null;
function drag(e,id){dragId=id}
function drago(e){e.preventDefault();e.currentTarget.classList.add('dropping')}
function drop(e,col){e.preventDefault();e.currentTarget.classList.remove('dropping');if(dragId){fetch('/api/card/'+dragId,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:getStatus(col)})}).then(()=>fetch('/api/cards').then(r=>r.json()).then(d=>{cards=d;render()}))}}
function openModal(){document.getElementById('mt').textContent='Новая';document.getElementById('ir').value='';document.getElementById('mf').reset();document.getElementById('md').classList.add('active')}
function ed(id){fetch('/api/card/'+id).then(r=>r.json()).then(c=>{document.getElementById('mt').textContent='Редактировать #' + id;document.getElementById('ir').value=id;document.getElementById('in').value=c.title||'';document.getElementById('id').value=c.description||'';const revMap={'todo':'New','in_progress':'In Progress','done':'Done'};document.getElementById('ist').value=revMap[c.status]||'New';document.getElementById('md').classList.add('active'})}
function dl(id){if(confirm('Удалить?')){fetch('/api/card/'+id,{method:'DELETE'}).then(()=>fetch('/api/cards').then(r=>r.json()).then(d=>{cards=d;render()}))}}
document.getElementById('mf').onsubmit=function(e){e.preventDefault();const id=document.getElementById('ir').value;const data={title:document.getElementById('in').value,description:document.getElementById('id').value,status:getStatus(document.getElementById('ist').value)};fetch(id?'/api/card/'+id:'/api/card',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(()=>{cl();fetch('/api/cards').then(r=>r.json()).then(d=>{cards=d;render()})})}
function cl(){document.getElementById('md').classList.remove('active')}
function tl(){document.getElementById('lc').classList.toggle('expanded')}
setInterval(()=>fetch('/api/logs').then(r=>r.json()).then(l=>{document.getElementById('lc').innerHTML=l.slice(-5).reverse().map(e=>'<div class="log-e"><span class="t">'+e.time+'</span><span class="a">'+e.action+'</span> '+e.details+'</div>').join('')}),5000);
fetch('/api/logs').then(r=>r.json()).then(l=>{document.getElementById('lc').innerHTML=l.slice(-5).reverse().map(e=>'<div class="log-e"><span class="t">'+e.time+'</span><span class="a">'+e.action+'</span> '+e.details+'</div>').join('')});
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/cards', methods=['GET'])
def api_get_cards():
    tasks = Task.query.all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'status': t.status,
        'priority': t.priority,
        'created_at': t.created_at.isoformat() if t.created_at else None
    } for t in tasks])

@app.route('/api/card/<int:card_id>', methods=['GET'])
def api_get_card(card_id):
    task = Task.query.get(card_id)
    if task:
        return jsonify({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority
        })
    return jsonify({"error": "Not found"}), 404

@app.route('/api/card', methods=['POST'])
def api_add_card():
    data = request.json
    # Для простоты используем author_id = 1
    task = Task(
        title=data.get('title', ''),
        description=data.get('description', ''),
        status=data.get('status', 'todo'),
        author_id=1
    )
    db.session.add(task)
    db.session.commit()
    log("ADD", task.title)
    return jsonify({"success": True, "id": task.id})

@app.route('/api/card/<int:card_id>', methods=['PUT'])
def api_update_card(card_id):
    task = Task.query.get(card_id)
    if task:
        data = request.json
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
        if 'priority' in data:
            task.priority = data['priority']
        db.session.commit()
        log("UPDATE", f"#{card_id} {task.title}")
        return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/card/<int:card_id>', methods=['DELETE'])
def api_delete_card(card_id):
    task = Task.query.get(card_id)
    if task:
        title = task.title
        db.session.delete(task)
        db.session.commit()
        log("DELETE", f"#{card_id} {title}")
        return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    return jsonify(LOG_STORAGE)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    log("START", "Канбан Доска запущена (PostgreSQL)")
    app.run(host='0.0.0.0', port=5000, debug=False)
