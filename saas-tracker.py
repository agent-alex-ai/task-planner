#!/usr/bin/env python3
"""
SaaS Ideas Tracker - Web Service с API v2
Улучшенная версия с поиском, фильтрацией, сортировкой и экспортом
"""

import os
import json
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template_string
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# Конфигурация
SPREADSHEET_ID = "1uJPKiySknD887he1pv7YJ-kL_G_lGOQp7QvUOHqcKfA"
CREDS_FILE = "/home/user/clawd/credentials.json"

# Логи в памяти
LOG_STORAGE = []
LOG_STORAGE_MAX = 200

def log(action, details=""):
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "details": details
    }
    LOG_STORAGE.append(entry)
    if len(LOG_STORAGE) > LOG_STORAGE_MAX:
        LOG_STORAGE.pop(0)
    print(f"[{entry['date']} {entry['time']}] {action}: {details}")

def get_sheets_service():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    return build('sheets', 'v4', credentials=creds).spreadsheets()

def get_all_ideas():
    service = get_sheets_service()
    result = service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A:K'
    ).execute()
    return result.get('values', [])

def add_idea_to_sheet(idea):
    service = get_sheets_service()
    rows = get_all_ideas()
    row_num = len(rows) + 1
    
    values = [
        str(row_num - 1),
        idea.get('name', ''),
        idea.get('description', ''),
        idea.get('github', ''),
        idea.get('tools', ''),
        idea.get('alternatives', ''),
        idea.get('monetization', ''),
        idea.get('cost', ''),
        idea.get('time', ''),
        idea.get('interested', 'Нет'),
        datetime.now().strftime('%Y-%m-%d')
    ]
    
    service.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'Sheet1!A{row_num}:K{row_num}',
        valueInputOption='USER_ENTERED',
        body={'values': [values]}
    ).execute()
    
    log("ADD_IDEA", f"Добавлена: {idea.get('name')}")
    return {"success": True, "row": row_num}

def update_idea(row_num, idea):
    service = get_sheets_service()
    
    values = [
        str(row_num),
        idea.get('name', ''),
        idea.get('description', ''),
        idea.get('github', ''),
        idea.get('tools', ''),
        idea.get('alternatives', ''),
        idea.get('monetization', ''),
        idea.get('cost', ''),
        idea.get('time', ''),
        idea.get('interested', 'Нет'),
        idea.get('date_added', datetime.now().strftime('%Y-%m-%d'))
    ]
    
    service.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'Sheet1!A{row_num}:K{row_num}',
        valueInputOption='USER_ENTERED',
        body={'values': [values]}
    ).execute()
    
    log("UPDATE_IDEA", f"Обновлена строка {row_num}: {idea.get('name')}")
    return {"success": True}

def delete_idea(row_num):
    service = get_sheets_service()
    service.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f'Sheet1!A{row_num}:K{row_num}'
    ).execute()
    log("DELETE_IDEA", f"Удалена строка {row_num}")
    return {"success": True}

# HTML шаблон v2 - компактный
HTML = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SaaS Ideas Tracker</title>
<style>
:root{--bg:#1a1a2e;--bg2:#16213e;--bg3:#0f3460;--txt:#eee;--txt2:#aaa;--acc:#00d9ff;--err:#e94560;--ok:#00ff88}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--txt);margin:0;min-height:100vh;display:flex;flex-direction:column}
.header{background:var(--bg2);padding:15px 20px;display:flex;justify-content:space-between;align-items:center}
.header h1{font-size:18px;color:var(--acc)}
.stats{font-size:12px;color:var(--txt2)}
.stats span{background:var(--bg3);padding:4px 10px;border-radius:12px;margin-left:10px}
.controls{background:var(--bg2);padding:15px 20px;display:flex;gap:10px;flex-wrap:wrap}
.search{flex:1;min-width:200px}
.search input{width:100%;padding:10px 15px;background:var(--bg3);border:1px solid var(--bg3);color:var(--txt);border-radius:8px;font-size:14px}
.search input:focus{outline:none;border-color:var(--acc)}
select{padding:10px 15px;background:var(--bg3);border:1px solid var(--bg3);color:var(--txt);border-radius:8px;cursor:pointer}
.btn{padding:10px 15px;border:none;border-radius:8px;cursor:pointer;font-size:13px}
.btn-add{background:var(--acc);color:var(--bg)}
.btn-export{background:var(--ok);color:var(--bg)}
.btn-theme{background:var(--bg3);color:var(--txt)}
.main{flex:1;padding:20px;overflow:auto}
table{width:100%;border-collapse:collapse;background:var(--bg2);border-radius:12px;overflow:hidden}
th,td{padding:14px 12px;text-align:left;border-bottom:1px solid var(--bg3)}
th{background:var(--bg3);font-weight:600;font-size:12px;color:var(--acc);cursor:pointer}
th:hover{background:#1a4a7a}
td{font-size:13px}
tr:hover{background:var(--bg3)}
.yes{color:var(--ok);font-weight:600}
.no{color:var(--err)}
.actions{display:flex;gap:5px}
.btni{padding:6px 10px}
.empty{text-align:center;padding:40px;color:var(--txt2)}
.pagination{display:flex;justify-content:center;gap:5px;padding:20px}
.pagination button{padding:8px 12px;background:var(--bg2);border:1px solid var(--bg3);color:var(--txt);border-radius:6px;cursor:pointer}
.pagination button.active{background:var(--acc);color:var(--bg)}
/* Log Panel */
.log{position:fixed;bottom:0;left:0;right:0;background:var(--bg2);border-top:2px solid var(--acc);z-index:100}
.log-h{padding:10px 20px;background:var(--bg3);cursor:pointer;display:flex;justify-content:space-between}
.log-h:hover{opacity:0.9}
.log-t{font-size:12px;color:var(--acc);font-weight:600}
.log-to{font-size:10px;color:var(--txt2)}
.log-c{max-height:0;overflow:hidden;transition:max-height 0.3s}
.log-c.expanded{max-height:250px;overflow:auto}
.log-e{padding:6px 20px;font-family:monospace;font-size:11px;border-bottom:1px solid var(--bg3);display:flex;gap:15px}
.log-e .d{color:var(--txt2)}.log-e .t{color:var(--acc)}.log-e .a{color:var(--err)}.log-e .x{color:var(--txt2)}
/* Modal */
.modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);z-index:200;align-items:center;justify-content:center}
.modal.active{display:flex}
.modal-content{background:var(--bg2);padding:25px;border-radius:12px;width:90%;max-width:550px;max-height:90vh;overflow:auto}
.modal h2{margin-bottom:20px;color:var(--acc)}
.f{display:grid;grid-template-columns:1fr 1fr;gap:15px}
.form{margin-bottom:15px}
.form label{display:block;font-size:11px;color:var(--txt2);margin-bottom:6px;text-transform:uppercase}
.form input,.form textarea,.form select{width:100%;padding:12px;background:var(--bg3);border:1px solid var(--bg3);color:var(--txt);border-radius:6px;font-size:14px}
.form input:focus,.form textarea:focus{outline:none;border-color:var(--acc)}
.form textarea{height:70px;resize:vertical}
.form-full{grid-column:1/-1}
.actions-m{display:flex;justify-content:flex-end;gap:10px;margin-top:20px}
.actions-m .btn{padding:12px 24px}
.btn-cancel{background:var(--bg3);color:var(--txt)}
@media(max-width:768px){.f{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="header">
<h1>📊 SaaS Ideas Tracker</h1>
<div class="stats">
<span>📚 Всего: <strong id="tc">0</strong></span>
<span>❤️ Интересно: <strong id="ic">0</strong></span>
</div>
</div>
<div class="controls">
<div class="search"><input type="text" id="si" placeholder="🔍 Поиск..."></div>
<select id="fs"><option value="">Все</option><option value="Да">Интересные</option><option value="Нет">Неинтересные</option></select>
<button class="btn btn-export" onclick="exp()">📥 CSV</button>
<button class="btn btn-theme" onclick="thm()">🌓</button>
<button class="btn btn-add" onclick="op()">+ Добавить</button>
</div>
<div class="main">
<table><thead><tr><th data-s="0">№</th><th data-s="1">Название</th><th data-s="2">Описание</th><th data-s="4">Инструменты</th><th data-s="6">Монетизация</th><th data-s="9">Интересно?</th><th>Действия</th></tr></thead>
<tbody id="tb"></tbody></table>
<div class="empty" id="es" style="display:none">Ничего не найдено</div>
</div>
<div class="pagination" id="pg"></div>
<!-- Log -->
<div class="log">
<div class="log-h" onclick="tl()"><span class="log-t">📜 Лог (5)</span><span class="log-to">▲/▼</span></div>
<div class="log-c" id="lc"></div>
</div>
<!-- Modal -->
<div class="modal" id="md">
<div class="modal-content">
<h2 id="mt">Добавить идею</h2>
<form id="mf">
<input type="hidden" id="ir">
<div class="f">
<div class="form form-full"><label>Название</label><input type="text" id="in" required></div>
<div class="form form-full"><label>Описание</label><textarea id="id"></textarea></div>
<div class="form"><label>GitHub</label><input type="text" id="ig"></div>
<div class="form"><label>Инструменты</label><input type="text" id="it"></div>
<div class="form"><label>Аналоги</label><input type="text" id="ia"></div>
<div class="form"><label>Монетизация</label><input type="text" id="im"></div>
<div class="form"><label>Затраты ($)</label><input type="text" id="icst"></div>
<div class="form"><label>Время (дней)</label><input type="text" id="iti"></div>
<div class="form"><label>Интересно?</label><select id="ii"><option value="Да">Да</option><option value="Нет">Нет</option></select></div>
</div>
<div class="actions-m"><button type="button" class="btn btn-cancel" onclick="cl()">Отмена</button><button type="submit" class="btn btn-add">Сохранить</button></div>
</form>
</div>
</div>
<script>
let all=[],fl=[],cp=1,pp=15,sc=0,sa=false;
fetch('/api/ideas').then(r=>r.json()).then(d=>{all=d.slice(1);fl=[...all];upSt();rt()});
function upSt(){document.getElementById('tc').textContent=all.length;document.getElementById('ic').textContent=all.filter(r=>r[9]==='Да').length}
function fls(){
const s=document.getElementById('si').value.toLowerCase();
const f=document.getElementById('fs').value;
fl=all.filter(r=>{const m=!s||(r[1]||'').toLowerCase().includes(s)||(r[2]||'').toLowerCase().includes(s);const g=!f||r[9]===f;return m&&g});
fl.sort((a,b)=>{let va=a[sc]||'',vb=b[sc]||'';if(!isNaN(va)&&!isNaN(vb)){va=Number(va);vb=Number(vb)}return sa?va>vb?1:-1:va<vb?1:-1});cp=1;rt()
}
document.getElementById('si').addEventListener('input',fls);
document.getElementById('fs').addEventListener('change',fls);
document.querySelectorAll('th[data-s]').forEach(th=>{th.addEventListener('click',()=>{const c=parseInt(th.dataset.s);if(sc===c)sa=!sa;else{sc=c;sa=true}document.querySelectorAll('th').forEach(t=>t.style.color='');th.style.color=sa?'var(--ok)':'var(--err)';fls()})});
function rt(){const tb=document.getElementById('tb');const st=(cp-1)*pp;const p=fl.slice(st,st+pp);if(p.length===0){tb.innerHTML='';document.getElementById('es').style.display='block';document.getElementById('pg').style.display='none';return}
document.getElementById('es').style.display='none';document.getElementById('pg').style.display='flex';
tb.innerHTML=p.map((r,i)=>{const n=st+i+1;const y=r[9]==='Да'?'yes':'no';return`<tr><td>${r[0]||n}</td><td><strong>${r[1]||''}</strong></td><td>${(r[2]||'').slice(0,60)}${r[2]?.length>60?'...':''}</td><td>${(r[4]||'').slice(0,30)}</td><td>${r[6]||''}</td><td class="${y}">${r[9]||'Нет'}</td><td class="actions"><button class="btn btni" onclick="ed(${r[0]||n})">✏️</button><button class="btn btni" onclick="dl(${r[0]||n})">🗑️</button></td></tr>`}).join('');pg()}}
function pg(){const tp=Math.ceil(fl.length/pp);const p=document.getElementById('pg');if(tp<=1){p.innerHTML='';return}
let h=`<button ${cp===1?'disabled':''} onclick="gp(${cp-1})">←</button>`;for(let i=1;i<=tp;i++){if(i===1||i===tp||Math.abs(i-cp)<=2){h+=`<button class="${i===cp?'active':''}" onclick="gp(${i})">${i}</button>`}}
h+=`<button ${cp===tp?'disabled':''} onclick="gp(${cp+1})">→</button>`;p.innerHTML=h}
function gp(n){cp=n;rt()}
function thm(){document.body.classList.toggle('light');localStorage.setItem('thm',document.body.classList.contains('light')?'l':'d')}
if(localStorage.getItem('thm')==='l')document.body.classList.add('light');
function tl(){document.getElementById('lc').classList.toggle('expanded')}
function op(){document.getElementById('mt').textContent='Добавить идею';document.getElementById('ir').value='';document.getElementById('mf').reset();document.getElementById('md').classList.add('active')}
function ed(row){fetch('/api/idea/'+row).then(r=>r.json()).then(i=>{document.getElementById('mt').textContent='Редактировать';document.getElementById('ir').value=row;document.getElementById('in').value=i['название проекта']||'';document.getElementById('id').value=i['описание']||'';document.getElementById('ig').value=i['ссылка на github']||'';document.getElementById('it').value=i['инструменты']||'';document.getElementById('ia').value=i['аналоги/конкуренты']||'';document.getElementById('im').value=i['монетизация']||'';document.getElementById('icst').value=i['затраты ($)']||'';document.getElementById('iti').value=i['время (дней)']||'';document.getElementById('ii').value=i['интересно?']||'Нет';document.getElementById('md').classList.add('active')})}
function dl(row){if(confirm('Удалить #'+row+'?')){fetch('/api/idea/'+row,{method:'DELETE'}).then(()=>location.reload())}}
document.getElementById('mf').onsubmit=function(e){e.preventDefault();const row=document.getElementById('ir').value;const data={name:document.getElementById('in').value,description:document.getElementById('id').value,github:document.getElementById('ig').value,tools:document.getElementById('it').value,alternatives:document.getElementById('ia').value,monetization:document.getElementById('im').value,cost:document.getElementById('icst').value,time:document.getElementById('iti').value,interested:document.getElementById('ii').value};fetch(row?'/api/idea/'+row:'/api/idea',{method:row?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(()=>{cl();location.reload()})}
function cl(){document.getElementById('md').classList.remove('active')}
function exp(){let csv='№,Название,Описание,GitHub,Инструменты,Аналоги,Монетизация,Затраты,Время,Интересно,Дата\\n';fl.forEach(r=>{csv+=r.map(c=>'"'+(c||'').replace(/"/g,'""')+'"').join(',')+'\\n'});const b=new Blob([csv],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='saas-ideas-'+new Date().toISOString().slice(0,10)+'.csv';a.click()}
setInterval(()=>fetch('/api/logs').then(r=>r.json()).then(l=>{document.getElementById('lc').innerHTML=l.slice(-5).reverse().map(e=>'<div class="log-e"><span class="d">'+e.date+'</span><span class="t">'+e.time+'</span><span class="a">'+e.action+'</span><span class="x">'+e.details+'</span></div>').join('')}),5000);
fetch('/api/logs').then(r=>r.json()).then(l=>{document.getElementById('lc').innerHTML=l.slice(-5).reverse().map(e=>'<div class="log-e"><span class="d">'+e.date+'</span><span class="t">'+e.time+'</span><span class="a">'+e.action+'</span><span class="x">'+e.details+'</span></div>').join('')});
</script>
</body>
</html>
'''

@app.route('/')
def index():
    ideas = get_all_ideas()
    return render_template_string(HTML, ideas=ideas, logs=LOG_STORAGE)

@app.route('/api/ideas', methods=['GET'])
def api_get_ideas():
    return jsonify(get_all_ideas())

@app.route('/api/idea/<int:row>', methods=['GET'])
def api_get_idea(row):
    ideas = get_all_ideas()
    if row + 1 >= len(ideas):
        return jsonify({"error": "Not found"}), 404
    headers = ideas[0]
    values = ideas[row]
    idea = {headers[i].lower(): values[i] if i < len(values) else "" for i in range(len(headers))}
    return jsonify(idea)

@app.route('/api/idea', methods=['POST'])
def api_add_idea():
    return jsonify(add_idea_to_sheet(request.json))

@app.route('/api/idea/<int:row>', methods=['PUT'])
def api_update_idea(row):
    return jsonify(update_idea(row, request.json))

@app.route('/api/idea/<int:row>', methods=['DELETE'])
def api_delete_idea(row):
    return jsonify(delete_idea(row))

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    return jsonify(LOG_STORAGE)

@app.route('/api/logs', methods=['DELETE'])
def api_clear_logs():
    LOG_STORAGE.clear()
    return jsonify({"success": True})

@app.route('/api/sync', methods=['POST'])
def api_sync():
    ideas = get_all_ideas()
    log("SYNC", f"Синхронизировано, {len(ideas)-1} идей")
    return jsonify({"success": True, "count": len(ideas) - 1})

@app.route('/api/stats', methods=['GET'])
def api_stats():
    ideas = get_all_ideas()
    rows = ideas[1:]
    total = len(rows)
    interesting = len([r for r in rows if r[9] == 'Да'])
    return jsonify({"total": total, "interesting": interesting, "not_interesting": total - interesting})

if __name__ == '__main__':
    log("START", "SaaS Ideas Tracker v2 запущен")
    app.run(host='0.0.0.0', port=5000, debug=False)
