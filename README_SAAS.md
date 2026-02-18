# SaaS Ideas Tracker

Веб-сервис для отслеживания идей SaaS проектов с API.

## Функции

- 📊 Управление идеями через веб-интерфейс
- 🔌 REST API для автоматизации
- 📜 Компактный лог (5 строк, разворачивается при клике)
- 🔗 Интеграция с Google Sheets

## Запуск

```bash
pip install flask google-auth google-api-python-client
python saas-tracker.py
```

Откроется на http://localhost:5000

## API

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/ideas` | Все идеи |
| GET | `/api/idea/<id>` | Одна идея |
| POST | `/api/idea` | Добавить |
| PUT | `/api/idea/<id>` | Обновить |
| DELETE | `/api/idea/<id>` | Удалить |
| GET | `/api/logs` | Логи |
| POST | `/api/sync` | Синхронизация |

## Примеры

```bash
# Добавить идею
curl -X POST http://localhost:5000/api/idea \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","description":"Test idea"}'

# Получить все
curl http://localhost:5000/api/ideas
```

## Google Sheets

Требуется файл `credentials.json` с Service Account ключом.
