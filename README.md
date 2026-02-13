# Task Planner Dashboard

A beautiful Kanban board for task management built with Flask and PostgreSQL. Features authentication, drag & drop, comments, activity log, and more.

![Task Planner](https://via.placeholder.com/800x400?text=Task+Planner+Dashboard)

## ✨ Features

- **Kanban Board** - Drag & drop tasks between columns
- **User Authentication** - Login/Register with JWT tokens
- **Task Management** - Create, edit, delete, prioritize tasks
- **Comments** - Discuss tasks with mentions support
- **Activity Log** - Track all changes in real-time
- **Search & Filters** - Find tasks quickly
- **Statistics** - Daily, weekly, and all-time summaries
- **Export** - Export tasks to CSV
- **Dark Mode** - Beautiful dark theme
- **Responsive** - Works on desktop and mobile
- **Docker Ready** - Easy deployment with Docker Compose

## 🚀 Quick Start

### With Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/agent-alex-ai/task-planner.git
cd task-planner

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Start with Docker Compose
docker-compose up -d

# Access at http://localhost:5000
```

### Manual Installation

```bash
# Clone and enter directory
git clone https://github.com/agent-alex-ai/task-planner.git
cd task-planner

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL (or use SQLite for development)
export DATABASE_URL="postgresql://user:password@localhost/taskplanner"

# Initialize database
python app.py

# Run development server
python app.py

# Access at http://localhost:5000
```

## 📁 Project Structure

```
task-planner/
├── app.py                 # Main Flask application
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker services
├── Dockerfile             # Container build
├── nginx.conf             # Nginx configuration
├── .env.example           # Environment template
├── static/
│   ├── css/
│   │   ├── styles.css     # Main styles
│   │   └── dark-theme.css # Dark mode
│   └── js/
│       └── app.js         # Frontend logic
└── templates/
    └── index.html         # Main dashboard
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `SECRET_KEY` | Flask secret key | dev key |
| `JWT_SECRET_KEY` | JWT signing key | - |
| `REDIS_URL` | Redis connection string | - |
| `FLASK_ENV` | Environment mode | development |

### Docker Services

1. **PostgreSQL** - Database (port 5432)
2. **Redis** - Cache/Broker (port 6379)
3. **Flask App** - API & UI (port 5000)
4. **Nginx** - Reverse proxy (port 80)

## 📚 API Documentation

### Authentication
```
POST /api/auth/register - Register new user
POST /api/auth/login    - Login and get token
GET  /api/auth/me       - Get current user
```

### Tasks
```
GET    /api/tasks           - List tasks (with filters)
POST   /api/tasks          - Create task
GET    /api/tasks/<id>     - Get task
PUT    /api/tasks/<id>     - Update task
DELETE /api/tasks/<id>     - Delete task
POST   /api/tasks/<id>/move - Move task (drag & drop)
```

### Comments
```
GET  /api/tasks/<id>/comments     - List comments
POST /api/tasks/<id>/comments     - Add comment
```

### Other
```
GET /api/stats          - Task statistics
GET /api/activities     - Activity log
GET /api/export/csv     - Export to CSV
GET /health            - Health check
```

## 🎨 Screenshots

### Kanban Board
![Kanban](https://via.placeholder.com/600x400?text=Kanban+Board)

### Task Details
![Task](https://via.placeholder.com/600x400?text=Task+Details)

### Dark Mode
![Dark](https://via.placeholder.com/600x400?text=Dark+Mode)

## 🛠️ Development

### Running Tests
```bash
pytest
```

### Database Migrations
```bash
# Create migration
alembic revision -m "description"

# Run migrations
alembic upgrade head
```

### Docker Development
```bash
# Development with hot reload
docker-compose up app

# With full stack
docker-compose up -d
```

## 🚢 Deployment

### Production with Docker
```bash
# Build images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment
```bash
# Set production environment variables
export FLASK_ENV=production
export SECRET_KEY=<strong-secret-key>
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions

---

Built with ❤️ using Flask, PostgreSQL, and Vanilla JS
