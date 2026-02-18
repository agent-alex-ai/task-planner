#!/usr/bin/env python3
"""
SaaS Ideas Tracker - Web Service с API v2
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template
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
    
    log("UPDATE_IDEA", f"Обновлена строка {row_num}")
    return {"success": True}

def delete_idea(row_num):
    service = get_sheets_service()
    service.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f'Sheet1!A{row_num}:K{row_num}'
    ).execute()
    log("DELETE_IDEA", f"Удалена строка {row_num}")
    return {"success": True}

@app.route('/')
def index():
    ideas = get_all_ideas()
    return render_template('index.html', ideas=ideas, logs=LOG_STORAGE[-5:])

# API
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

@app.route('/api/stats', methods=['GET'])
def api_stats():
    ideas = get_all_ideas()[1:]
    total = len(ideas)
    interesting = len([r for r in ideas if r[9] == 'Да'])
    return jsonify({"total": total, "interesting": interesting, "not_interesting": total - interesting})

@app.route('/api/sync', methods=['POST'])
def api_sync():
    ideas = get_all_ideas()
    log("SYNC", f"Синхронизировано, {len(ideas)-1} идей")
    return jsonify({"success": True, "count": len(ideas) - 1})

if __name__ == '__main__':
    log("START", "SaaS Ideas Tracker v2 запущен")
    app.run(host='0.0.0.0', port=5000, debug=False)
