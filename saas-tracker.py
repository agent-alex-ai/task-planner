#!/usr/bin/env python3
"""
SaaS Ideas Tracker - Trello-подобная канбан доска
"""

import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# Конфигурация
SPREADSHEET_ID = "1uJPKiySknD887he1pv7YJ-kL_G_lGOQp7QvUOHqcKfA"
CREDS_FILE = "/home/user/clawd/credentials.json"

# Логи
LOG_STORAGE = []
LOG_STORAGE_MAX = 200

def log(action, details=""):
    entry = {"time": datetime.now().strftime("%H:%M:%S"), "action": action, "details": details}
    LOG_STORAGE.append(entry)
    if len(LOG_STORAGE) > LOG_STORAGE_MAX:
        LOG_STORAGE.pop(0)
    print(f"[{entry['time']}] {action}: {details}")

def get_sheets_service():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    return build('sheets', 'v4', credentials=creds).spreadsheets()

def get_all_ideas():
    service = get_sheets_service()
    result = service.values().get(spreadsheetId=SPREADSHEET_ID, range='Sheet1!A:K').execute()
    return result.get('values', [])

def add_idea_to_sheet(idea):
    service = get_sheets_service()
    rows = get_all_ideas()
    row_num = len(rows) + 1
    
    values = [str(row_num - 1), idea.get('name', ''), idea.get('description', ''),
              idea.get('github', ''), idea.get('tools', ''), idea.get('alternatives', ''),
              idea.get('monetization', ''), idea.get('cost', ''), idea.get('time', ''),
              idea.get('status', 'New'), datetime.now().strftime('%Y-%m-%d')]
    
    service.values().update(spreadsheetId=SPREADSHEET_ID, range=f'Sheet1!A{row_num}:L{row_num}',
                           valueInputOption='USER_ENTERED', body={'values': [values]}).execute()
    log("ADD", idea.get('name'))
    return {"success": True, "row": row_num}

def update_idea(row_num, idea):
    service = get_sheets_service()
    values = [str(row_num), idea.get('name', ''), idea.get('description', ''),
              idea.get('github', ''), idea.get('tools', ''), idea.get('alternatives', ''),
              idea.get('monetization', ''), idea.get('cost', ''), idea.get('time', ''),
              idea.get('status', 'New'), idea.get('date', datetime.now().strftime('%Y-%m-%d'))]
    
    service.values().update(spreadsheetId=SPREADSHEET_ID, range=f'Sheet1!A{row_num}:L{row_num}',
                           valueInputOption='USER_ENTERED', body={'values': [values]}).execute()
    log("UPDATE", f"#{row_num} {idea.get('name')}")
    return {"success": True}

def delete_idea(row_num):
    service = get_sheets_service()
    service.values().clear(spreadsheetId=SPREADSHEET_ID, range=f'Sheet1!A{row_num}:L{row_num}').execute()
    log("DELETE", f"#{row_num}")
    return {"success": True}

# Канбан колонки
COLUMNS = ['New', 'In Progress', 'Done']

HTML = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SaaS Ideas Board</title>
<style>
:root{--bg:#1a1a2e;--bg2:#16213e;--bg3:#0f3460;--txt:#eee;--txt2:#aaa;--acc:#00d9ff;--err:#e94560;--ok:#00ff88;--new:#9b59b6;--prog:#f39c12;--done:#27ae60}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--txt);min-height:100vh;display:flex;flex-direction:column}
.header{background:var(--bg2);padding:15px 20px;display:flex;justify-content:space-between;align-items:center}
.header h1{font-size:20px;color:var(--acc)}
.header .stats{font-size:14px;color:var(--txt2)}
.add-btn{background:var(--acc);color:var(--bg);padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:14px}
.board{flex:1;display:flex;gap:20px;padding:20px;overflow-x:auto}
.column{background:var(--bg2);min-width:320px;max-width:350px;border-radius:12px;display:flex;flex-direction:column;max-height:calc(100vh - 140px)}
.column-header{padding:15px;border-bottom:1px solid var(--bg3);display:flex;justify-content:space-between;align-items:center}
.column-title{font-weight:600;font-size:14px;text-transform:uppercase;letter-spacing:1px}
.col-new .column-title{color:var(--new)}
.col-progress .column-title{color:var(--prog)}
.col-done .column-title{color:var(--done)}
.column-count{background:var(--bg3);padding:2px 8px;border-radius:10px;font-size:12px}
.column-cards{padding:10px;flex:1;overflow-y:auto;min-height:100px}
.card{background:var(--bg3);border-radius:8px;padding:12px;margin-bottom:10px;cursor:grab;transition:transform 0.2s,box-shadow 0.2s}
.card:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,0.3)}
.card:active{cursor:grabbing}
.card-title{font-weight:600;margin-bottom:8px;font-size:14px}
.card-desc{font-size:12px;color:var(--txt2);margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.card-meta{font-size:11px;color:var(--txt2);display:flex;gap:10px;flex-wrap:wrap}
.card-tag{background:var(--bg2);padding:2px 6px;border-radius:4px}
.card-actions{display:flex;gap:5px;margin-top:10px;padding-top:10px;border-top:1px solid var(--bg2)}
.card-btn{background:var(--bg2);border:none;color:var(--txt);padding:4px 8px;border-radius:4px;cursor:pointer;font-size:12px}
.card-btn:hover{background:var(--acc);color:var(--bg)}
/* Log */
.log{position:fixed;bottom:0;left:0;right:0;background:var(--bg2);border-top:2px solid var(--acc);z-index:100}
.log-h{padding:10px 20px;background:var(--bg3);cursor:pointer;display:flex;justify-content:space-between}
.log-t{font-size:12px;color:var(--acc);font-weight:600}
.log-to{font-size:10px;color:var(--txt2)}
.log-c{max-height:0;overflow:hidden;transition:max-height 0.3s}
.log-c.expanded{max-height:200px;overflow:auto}
.log-e{padding:6px 20px;font-family:monospace;font-size:11px;border-bottom:1px solid var(--bg3);display:flex;gap:15px}
.log-e .t{color:var(--acc)}.log-e .a{color:var(--err)}.log-e .x{color:var(--txt2)}
/* Modal */
.modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);z-index:200;align-items:center;justify-content:center}
.modal.active{display:flex}
.modal-content{background:var(--bg2);padding:25px;border-radius:12px;width:90%;max-width:500px}
.modal h2{margin-bottom:20px;color:var(--acc)}
.form{margin-bottom:15px}
.form label{display:block;font-size:11px;color:var(--txt2);margin-bottom:6px}
.form input,.form textarea,.form select{width:100%;padding:12px;background:var(--bg3);border:1px solid var(--bg3);color:var(--txt);border-radius:6px;font-size:14px}
.form textarea{height:80px;resize:vertical}
.actions-m{display:flex;justify-content:flex-end;gap:10px;margin-top:20px}
.btn-cancel{background:var(--bg3);color:var(--txt);padding:12px 24px;border:none;border-radius:8px;cursor:pointer}
.btn-save{background:var(--acc);color:var(--bg);padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-weight:600}
.dropping{background:rgba(0,217,255,0.1);border:2px dashed var(--acc)}
</style>
</head>
<body>
<div class="header">
<h1>📋 SaaS Ideas Board</h1>
<div class="stats" id="stats">Загрузка...</div>
<button class="add-btn" onclick="openModal()">+ Добавить</button>
</div>
<div class="board" id="board"></div>
<!-- Log -->
<div class="log">
<div class="log-h" onclick="tl()"><span class="log-t">📜 Лог</span><span class="log-to">▲/▼</span></div>
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
<div class="form"><label>GitHub</label><input type="text" id="ig"></div>
<div class="form"><label>Инструменты</label><input type="text" id="it"></div>
<div class="form"><label>Аналоги</label><input type="text" id="ia"></div>
<div class="form"><label>Монетизация</label><input type="text" id="im"></div>
<div class="form"><label>Затраты ($)</label><input type="text" id="ic"></div>
<div class="form"><label>Время (дней)</label><input type="text" id="iti"></div>
<div class="form"><label>Статус</label><select id="ist"><option value="New">New</option><option value="In Progress">In Progress</option><option value="Done">Done</option></select></div>
<div class="actions-m"><button type="button" class="btn-cancel" onclick="cl()">Отмена</button><button type="submit" class="btn-save">Сохранить</button></div>
</form>
</div>
</div>
<script>
const COLUMNS = ['New','In Progress','Done'];
let cards = [];
fetch('/api/cards').then(r=>r.json()).then(d=>{cards=d;render()});
function render(){
const board=document.getElementById('board');
board.innerHTML=COLUMNS.map(col=>{
const colCards=cards.filter(c=>c.status===col);
return`<div class="column col-${col.toLowerCase().replace(' ','-')}" ondragover="drago(event)" ondrop="drop(event,'${col}')">
<div class="column-header"><span class="column-title">${col}</span><span class="column-count">${colCards.length}</span></div>
<div class="column-cards" data-col="${col}">
${colCards.map(c=>cardHTML(c)).join('')}
</div>
</div>`}).join('');
updateStats();
}
function cardHTML(c){
return`<div class="card" draggable="true" ondragstart="drag(event,${c.id})" data-id="${c.id}">
<div class="card-title">${c.name}</div>
<div class="card-desc">${c.description||''}</div>
<div class="card-meta">
${c.tools?`<span class="card-tag">${c.tools}</span>`:''}
${c.monetization?`<span class="card-tag">${c.monetization}</span>`:''}
</div>
<div class="card-actions">
<button class="card-btn" onclick="ed(${c.id})">✏️</button>
<button class="card-btn" onclick="dl(${c.id})">🗑️</button>
</div>
</div>`}
function updateStats(){
document.getElementById('stats').innerHTML=COLUMNS.map(col=>{
const n=cards.filter(c=>c.status===col).length;
return`<span style="margin-left:15px">${col}: <strong>${n}</strong></span>`}).join('')}
let dragId=null;
function drag(e,id){dragId=id;e.dataTransfer.effectAllowed='move'}
function drago(e){e.preventDefault();e.currentTarget.classList.add('dropping')}
function drop(e,col){e.preventDefault();e.currentTarget.classList.remove('dropping');if(dragId){fetch('/api/card/'+dragId,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:col})}).then(()=>location.reload())}}
function openModal(){document.getElementById('mt').textContent='Новая карточка';document.getElementById('ir').value='';document.getElementById('mf').reset();document.getElementById('md').classList.add('active')}
function ed(id){fetch('/api/card/'+id).then(r=>r.json()).then(c=>{document.getElementById('mt').textContent='Редактировать';document.getElementById('ir').value=id;document.getElementById('in').value=c.name||'';document.getElementById('id').value=c.description||'';document.getElementById('ig').value=c.github||'';document.getElementById('it').value=c.tools||'';document.getElementById('ia').value=c.alternatives||'';document.getElementById('im').value=c.monetization||'';document.getElementById('ic').value=c.cost||'';document.getElementById('iti').value=c.time||'';document.getElementById('ist').value=c.status||'New';document.getElementById('md').classList.add('active'})}
function dl(id){if(confirm('Удалить карточку?')){fetch('/api/card/'+id,{method:'DELETE'}).then(()=>location.reload())}}
document.getElementById('mf').onsubmit=function(e){e.preventDefault();const id=document.getElementById('ir').value;const data={name:document.getElementById('in').value,description:document.getElementById('id').value,github:document.getElementById('ig').value,tools:document.getElementById('it').value,alternatives:document.getElementById('ia').value,monetization:document.getElementById('im').value,cost:document.getElementById('ic').value,time:document.getElementById('iti').value,status:document.getElementById('ist').value};fetch(id?'/api/card/'+id:'/api/card',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(()=>{cl();location.reload()})}
function cl(){document.getElementById('md').classList.remove('active')}
setInterval(()=>fetch('/api/logs').then(r=>r.json()).then(l=>{document.getElementById('lc').innerHTML=l.slice(-5).reverse().map(e=>'<div class="log-e"><span class="t">'+e.time+'</span><span class="a">'+e.action+'</span><span class="x">'+e.details+'</span></div>').join('')}),5000);
fetch('/api/logs').then(r=>r.json()).then(l=>{document.getElementById('lc').innerHTML=l.slice(-5).reverse().map(e=>'<div class="log-e"><span class="t">'+e.time+'</span><span class="a">'+e.action+'</span><span class="x">'+e.details+'</span></div>').join('')});
function tl(){document.getElementById('lc').classList.toggle('expanded')}
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/cards', methods=['GET'])
def api_get_cards():
    rows = get_all_ideas()
    if len(rows) <= 1:
        return jsonify([])
    cards = []
    for i, row in enumerate(rows[1:], 1):
        if len(row) >= 10:
            cards.append({
                "id": i,
                "name": row[1] if len(row) > 1 else "",
                "description": row[2] if len(row) > 2 else "",
                "github": row[3] if len(row) > 3 else "",
                "tools": row[4] if len(row) > 4 else "",
                "alternatives": row[5] if len(row) > 5 else "",
                "monetization": row[6] if len(row) > 6 else "",
                "cost": row[7] if len(row) > 7 else "",
                "time": row[8] if len(row) > 8 else "",
                "status": row[9] if len(row) > 9 else "New",
                "date": row[10] if len(row) > 10 else ""
            })
    return jsonify(cards)

@app.route('/api/card/<int:row>', methods=['GET'])
def api_get_card(row):
    rows = get_all_ideas()
    if row + 1 >= len(rows):
        return jsonify({"error": "Not found"}), 404
    r = rows[row + 1]
    return jsonify({
        "name": r[1] if len(r) > 1 else "",
        "description": r[2] if len(r) > 2 else "",
        "github": r[3] if len(r) > 3 else "",
        "tools": r[4] if len(r) > 4 else "",
        "alternatives": r[5] if len(r) > 5 else "",
        "monetization": r[6] if len(r) > 6 else "",
        "cost": r[7] if len(r) > 7 else "",
        "time": r[8] if len(r) > 8 else "",
        "status": r[9] if len(r) > 9 else "New",
        "date": r[10] if len(r) > 10 else ""
    })

@app.route('/api/card', methods=['POST'])
def api_add_card():
    return jsonify(add_idea_to_sheet(request.json))

@app.route('/api/card/<int:row>', methods=['PUT'])
def api_update_card(row):
    return jsonify(update_idea(row, request.json))

@app.route('/api/card/<int:row>', methods=['DELETE'])
def api_delete_card(row):
    return jsonify(delete_idea(row))

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    return jsonify(LOG_STORAGE)

if __name__ == '__main__':
    log("START", "SaaS Ideas Board запущен")
    app.run(host='0.0.0.0', port=5000, debug=False)
