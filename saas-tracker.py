#!/usr/bin/env python3
"""
SaaS Ideas Tracker - Web Service с API
"""

import os
import json
import logging
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template_string
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# Конфигурация
SPREADSHEET_ID = "1uJPKiySknD887he1pv7YJ-kL_G_lGOQp7QvUOHqcKfA"
CREDS_FILE = "/home/user/clawd/credentials.json"

# Логи в памяти (последние 100)
LOG_STORAGE = []
LOG_STORAGE_MAX = 100

def log(action, details=""):
    """Добавить запись в лог"""
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "details": details
    }
    LOG_STORAGE.append(entry)
    if len(LOG_STORAGE) > LOG_STORAGE_MAX:
        LOG_STORAGE.pop(0)
    print(f"[{entry['time']}] {action}: {details}")

def get_sheets_service():
    """Подключение к Google Sheets API"""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    return build('sheets', 'v4', credentials=creds).spreadsheets()

def get_all_ideas():
    """Получить все идеи из таблицы"""
    service = get_sheets_service()
    result = service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A:K'
    ).execute()
    return result.get('values', [])

def add_idea_to_sheet(idea):
    """Добавить идею в таблицу"""
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
    """Обновить идею в таблице"""
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
    """Удалить идею из таблицы (очистить строку)"""
    service = get_sheets_service()
    service.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f'Sheet1!A{row_num}:K{row_num}'
    ).execute()
    log("DELETE_IDEA", f"Удалена строка {row_num}")
    return {"success": True}

# HTML шаблон с компактным логом
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SaaS Ideas Tracker</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; display: flex; flex-direction: column; }
        .header { background: #16213e; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 18px; color: #00d9ff; }
        .header .stats { font-size: 12px; color: #888; }
        .main { flex: 1; padding: 20px; overflow: auto; }
        table { width: 100%; border-collapse: collapse; background: #16213e; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #0f3460; }
        th { background: #0f3460; font-weight: 600; font-size: 12px; color: #00d9ff; }
        td { font-size: 13px; }
        tr:hover { background: #1f4068; }
        .btn { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; margin-right: 5px; }
        .btn-add { background: #00d9ff; color: #1a1a2e; }
        .btn-edit { background: #e94560; color: white; }
        .btn-delete { background: #ff6b6b; color: white; }
        
        /* Compact Log Panel */
        .log-panel { position: fixed; bottom: 0; left: 0; right: 0; background: #0f0f23; border-top: 2px solid #00d9ff; z-index: 100; }
        .log-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 15px; background: #16213e; cursor: pointer; }
        .log-header:hover { background: #1f4068; }
        .log-title { font-size: 12px; color: #00d9ff; font-weight: 600; }
        .log-toggle { font-size: 10px; color: #888; }
        .log-content { max-height: 0; overflow: hidden; transition: max-height 0.3s; }
        .log-content.expanded { max-height: 300px; overflow: auto; }
        .log-entry { padding: 4px 15px; font-family: monospace; font-size: 11px; border-bottom: 1px solid #1f4068; }
        .log-entry .time { color: #00d9ff; margin-right: 10px; }
        .log-entry .action { color: #e94560; margin-right: 10px; }
        .log-entry .details { color: #aaa; }
        
        /* Modal */
        .modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 200; align-items: center; justify-content: center; }
        .modal.active { display: flex; }
        .modal-content { background: #16213e; padding: 20px; border-radius: 8px; width: 90%; max-width: 500px; }
        .modal h2 { margin-bottom: 15px; color: #00d9ff; }
        .form-group { margin-bottom: 12px; }
        .form-group label { display: block; font-size: 11px; color: #888; margin-bottom: 4px; }
        .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 8px; background: #0f3460; border: 1px solid #1f4068; color: #eee; border-radius: 4px; font-size: 13px; }
        .form-group textarea { height: 60px; resize: vertical; }
        .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 SaaS Ideas Tracker</h1>
        <span class="stats">Всего идей: {{ ideas|length - 1 }}</span>
    </div>
    
    <div class="main">
        <table>
            <thead>
                <tr>
                    <th>№</th>
                    <th>Название</th>
                    <th>Описание</th>
                    <th>Инструменты</th>
                    <th>Монетизация</th>
                    <th>Интересно?</th>
                    <th>Действия</th>
                </tr>
            </thead>
            <tbody>
                {% for idea in ideas[1:] %}
                <tr>
                    <td>{{ idea[0] }}</td>
                    <td>{{ idea[1] }}</td>
                    <td>{{ idea[2][:50] }}{% if idea[2]|length > 50 %}...{% endif %}</td>
                    <td>{{ idea[4][:30] }}{% if idea[4]|length > 30 %}...{% endif %}</td>
                    <td>{{ idea[6] }}</td>
                    <td>{{ idea[9] }}</td>
                    <td>
                        <button class="btn btn-edit" onclick="editIdea({{ idea[0] }})">✏️</button>
                        <button class="btn btn-delete" onclick="deleteIdea({{ idea[0] }})">🗑️</button>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <button class="btn btn-add" style="position:fixed;bottom:60px;right:20px;font-size:16px;padding:12px 20px;" onclick="openModal()">+ Добавить идею</button>
    
    <!-- Compact Log Panel -->
    <div class="log-panel">
        <div class="log-header" onclick="toggleLog()">
            <span class="log-title">📜 Лог (последние 5)</span>
            <span class="log-toggle">▲ развернуть / ▼ свернуть</span>
        </div>
        <div class="log-content" id="logContent">
            {% for entry in logs[-5:] %}
            <div class="log-entry">
                <span class="time">{{ entry.time }}</span>
                <span class="action">{{ entry.action }}</span>
                <span class="details">{{ entry.details }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <!-- Modal -->
    <div class="modal" id="ideaModal">
        <div class="modal-content">
            <h2 id="modalTitle">Добавить идею</h2>
            <form id="ideaForm">
                <input type="hidden" id="ideaRow">
                <div class="form-group">
                    <label>Название</label>
                    <input type="text" id="ideaName" required>
                </div>
                <div class="form-group">
                    <label>Описание</label>
                    <textarea id="ideaDesc"></textarea>
                </div>
                <div class="form-group">
                    <label>GitHub</label>
                    <input type="text" id="ideaGithub">
                </div>
                <div class="form-group">
                    <label>Инструменты</label>
                    <input type="text" id="ideaTools">
                </div>
                <div class="form-group">
                    <label>Аналоги</label>
                    <input type="text" id="ideaAlternatives">
                </div>
                <div class="form-group">
                    <label>Монетизация</label>
                    <input type="text" id="ideaMonetization">
                </div>
                <div class="form-group">
                    <label>Затраты ($)</label>
                    <input type="text" id="ideaCost">
                </div>
                <div class="form-group">
                    <label>Время (дней)</label>
                    <input type="text" id="ideaTime">
                </div>
                <div class="form-group">
                    <label>Интересно?</label>
                    <select id="ideaInterested">
                        <option value="Да">Да</option>
                        <option value="Нет">Нет</option>
                    </select>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn" style="background:#444;" onclick="closeModal()">Отмена</button>
                    <button type="submit" class="btn btn-add">Сохранить</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function toggleLog() {
            document.getElementById('logContent').classList.toggle('expanded');
        }
        
        function openModal() {
            document.getElementById('modalTitle').textContent = 'Добавить идею';
            document.getElementById('ideaRow').value = '';
            document.getElementById('ideaForm').reset();
            document.getElementById('ideaModal').classList.add('active');
        }
        
        function editIdea(row) {
            fetch('/api/idea/' + row)
                .then(r => r.json())
                .then(idea => {
                    document.getElementById('modalTitle').textContent = 'Редактировать идею';
                    document.getElementById('ideaRow').value = row;
                    document.getElementById('ideaName').value = idea.name || '';
                    document.getElementById('ideaDesc').value = idea.description || '';
                    document.getElementById('ideaGithub').value = idea.github || '';
                    document.getElementById('ideaTools').value = idea.tools || '';
                    document.getElementById('ideaAlternatives').value = idea.alternatives || '';
                    document.getElementById('ideaMonetization').value = idea.monetization || '';
                    document.getElementById('ideaCost').value = idea.cost || '';
                    document.getElementById('ideaTime').value = idea.time || '';
                    document.getElementById('ideaInterested').value = idea.interested || 'Нет';
                    document.getElementById('ideaModal').classList.add('active');
                });
        }
        
        function deleteIdea(row) {
            if (confirm('Удалить идею #' + row + '?')) {
                fetch('/api/idea/' + row, {method: 'DELETE'})
                    .then(r => r.json())
                    .then(() => location.reload());
            }
        }
        
        document.getElementById('ideaForm').onsubmit = function(e) {
            e.preventDefault();
            const row = document.getElementById('ideaRow').value;
            const data = {
                name: document.getElementById('ideaName').value,
                description: document.getElementById('ideaDesc').value,
                github: document.getElementById('ideaGithub').value,
                tools: document.getElementById('ideaTools').value,
                alternatives: document.getElementById('ideaAlternatives').value,
                monetization: document.getElementById('ideaMonetization').value,
                cost: document.getElementById('ideaCost').value,
                time: document.getElementById('ideaTime').value,
                interested: document.getElementById('ideaInterested').value
            };
            
            const method = row ? 'PUT' : 'POST';
            const url = row ? '/api/idea/' + row : '/api/idea';
            
            fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(r => r.json()).then(() => {
                closeModal();
                location.reload();
            });
        };
        
        function closeModal() {
            document.getElementById('ideaModal').classList.remove('active');
        }
        
        // Обновление лога каждые 5 секунд
        setInterval(() => {
            fetch('/api/logs').then(r => r.json()).then(logs => {
                const container = document.getElementById('logContent');
                container.innerHTML = logs.slice(-5).map(e => 
                    '<div class="log-entry"><span class="time">' + e.time + '</span><span class="action">' + e.action + '</span><span class="details">' + e.details + '</span></div>'
                ).join('');
            });
        }, 5000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Главная страница"""
    ideas = get_all_ideas()
    return render_template_string(HTML_TEMPLATE, ideas=ideas, logs=LOG_STORAGE)

# ============ API ROUTES ============

@app.route('/api/ideas', methods=['GET'])
def api_get_ideas():
    """Получить все идеи"""
    ideas = get_all_ideas()
    return jsonify(ideas)

@app.route('/api/idea/<int:row>', methods=['GET'])
def api_get_idea(row):
    """Получить одну идею по номеру строки"""
    ideas = get_all_ideas()
    if row + 1 >= len(ideas):
        return jsonify({"error": "Not found"}), 404
    
    headers = ideas[0]
    values = ideas[row]
    
    idea = {}
    for i, h in enumerate(headers):
        idea[h.lower()] = values[i] if i < len(values) else ""
    
    return jsonify(idea)

@app.route('/api/idea', methods=['POST'])
def api_add_idea():
    """Добавить новую идею"""
    data = request.json
    result = add_idea_to_sheet(data)
    return jsonify(result)

@app.route('/api/idea/<int:row>', methods=['PUT'])
def api_update_idea(row):
    """Обновить идею"""
    data = request.json
    result = update_idea(row, data)
    return jsonify(result)

@app.route('/api/idea/<int:row>', methods=['DELETE'])
def api_delete_idea(row):
    """Удалить идею"""
    result = delete_idea(row)
    return jsonify(result)

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    """Получить логи"""
    return jsonify(LOG_STORAGE)

@app.route('/api/logs', methods=['DELETE'])
def api_clear_logs():
    """Очистить логи"""
    LOG_STORAGE.clear()
    return jsonify({"success": True})

@app.route('/api/sync', methods=['POST'])
def api_sync():
    """Синхронизировать (перечитать из Google Sheets)"""
    ideas = get_all_ideas()
    log("SYNC", f"Синхронизировано, {len(ideas)-1} идей")
    return jsonify({"success": True, "count": len(ideas) - 1})

if __name__ == '__main__':
    log("START", "SaaS Ideas Tracker запущен")
    app.run(host='0.0.0.0', port=5000, debug=False)
