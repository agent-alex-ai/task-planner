// Task Planner - Frontend JavaScript with Authentication, Search, Filters, Dark Mode

const API_BASE = '/api';

// State
let tasks = [];
let users = [];
let currentTaskId = null;
let currentUser = null;
let accessToken = localStorage.getItem('access_token');
let isDarkMode = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
    applyTheme();
});

// Event Listeners
function setupEventListeners() {
    // Search with debounce
    let searchTimeout;
    document.getElementById('search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyFilters();
        }, 300);
    });
}

// Auth Functions
function checkAuth() {
    const requiresAuth = document.body.dataset.requiresAuth === 'true';
    const isLoginPage = document.body.dataset.loginPage === 'true';
    
    if (accessToken) {
        // Already have token - add authenticated class immediately
        document.body.classList.add('authenticated');
        fetchUser();
    } else if (requiresAuth || isLoginPage) {
        // Server says we need auth - show login modal only
        showLoginModal();
    } else {
        // Client-side check - show login modal
        showLoginModal();
    }
}

// Show main app after successful auth
function showMainApp() {
    document.getElementById('main-app').style.display = 'block';
    document.body.classList.add('authenticated');
}

// Hide main app
function hideMainApp() {
    document.getElementById('main-app').style.display = 'none';
    document.body.classList.remove('authenticated');
}

async function fetchUser() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        if (response.ok) {
            currentUser = await response.json();
            document.getElementById('current-user').textContent = currentUser.username;
            showMainApp();  // Show the main app
            loadTasks();
            loadUsers();
            loadActivities();
        } else {
            logout();
        }
    } catch (error) {
        console.error('Error fetching user:', error);
        logout();
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        if (response.ok) {
            accessToken = data.access_token;
            currentUser = data.user;
            localStorage.setItem('access_token', accessToken);
            document.getElementById('current-user').textContent = currentUser.username;
            closeModal('login-modal');
            showMainApp();  // Show main app after login
            loadTasks();
            loadUsers();
            loadActivities();
            showToast('Добро пожаловать, ' + currentUser.username + '!', 'success');
        } else {
            showToast(data.error || 'Ошибка входа', 'error');
        }
    } catch (error) {
        showToast('Ошибка соединения', 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        if (response.ok) {
            // Auto login after registration
            const loginResponse = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            if (loginResponse.ok) {
                const loginData = await loginResponse.json();
                accessToken = loginData.access_token;
                localStorage.setItem('access_token', accessToken);
                showToast('Добро пожаловать!', 'success');
                await fetchUser();
            } else {
                showToast('Регистрация успешна! Войдите.', 'success');
                closeRegisterModal();
            }
        } else {
            showToast(data.error || 'Ошибка регистрации', 'error');
        }
    } catch (error) {
        showToast('Ошибка соединения', 'error');
    }
}

function toggleUserMenu() {
    const dropdown = document.getElementById('user-dropdown');
    dropdown.classList.toggle('show');
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const userMenu = document.querySelector('.user-menu');
    const dropdown = document.getElementById('user-dropdown');
    if (userMenu && !userMenu.contains(e.target)) {
        dropdown.classList.remove('show');
    }
});

function logout() {
    accessToken = null;
    currentUser = null;
    localStorage.removeItem('access_token');
    hideMainApp();  // Hide main app
    document.body.classList.remove('authenticated');
    // Show login modal (not register)
    document.getElementById('login-modal').classList.add('active');
    document.getElementById('register-modal').classList.remove('active');
    tasks = [];
    renderTasks();
    updateStats();
}

function showLoginModal() {
    document.getElementById('register-modal').classList.remove('active');
    document.getElementById('login-modal').classList.add('active');
}

function showRegisterModal() {
    document.getElementById('login-modal').classList.remove('active');
    document.getElementById('register-modal').classList.add('active');
}

// Alias for compatibility with HTML onclick
function showRegister() {
    showRegisterModal();
}

function closeRegisterModal() {
    document.getElementById('register-modal').classList.remove('active');
    document.getElementById('login-modal').classList.add('active');
}

// API Functions
async function loadTasks() {
    if (!accessToken) return;
    
    try {
        const params = new URLSearchParams();
        const status = document.getElementById('filter-status').value;
        const priority = document.getElementById('filter-priority').value;
        const search = document.getElementById('search-input').value;
        
        if (status) params.append('status', status);
        if (priority) params.append('priority', priority);
        if (search) params.append('q', search);
        
        const response = await fetch(`${API_BASE}/tasks?${params}`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        tasks = await response.json();
        renderTasks();
        updateStats();
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE}/users`);
        users = await response.json();
        populateAssigneeSelect();
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function loadActivities() {
    try {
        const response = await fetch(`${API_BASE}/activities?limit=20`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        const activities = await response.json();
        renderActivities(activities);
    } catch (error) {
        console.error('Error loading activities:', error);
    }
}

async function createTask(taskData) {
    try {
        const response = await fetch(`${API_BASE}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify(taskData)
        });
        const result = await response.json();
        if (response.ok) {
            loadTasks();
            return true;
        } else {
            showToast(result.error || 'Ошибка создания задачи', 'error');
        }
    } catch (error) {
        showToast('Ошибка соединения', 'error');
    }
    return false;
}

async function updateTask(taskId, taskData) {
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify(taskData)
        });
        const result = await response.json();
        if (response.ok) {
            loadTasks();
            loadActivities();
            return true;
        } else {
            showToast(result.error || 'Ошибка обновления', 'error');
        }
    } catch (error) {
        showToast('Ошибка соединения', 'error');
    }
    return false;
}

async function moveTask(taskId, newStatus, position = 0) {
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({ status: newStatus, position })
        });
        const result = await response.json();
        if (response.ok) {
            loadTasks();
            loadActivities();
        }
    } catch (error) {
        showToast('Ошибка перемещения', 'error');
    }
}

async function deleteTask(taskId) {
    if (!confirm('Удалить эту задачу?')) return false;
    
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        const result = await response.json();
        if (response.ok) {
            loadTasks();
            loadActivities();
            closeModal('task-modal');
            showToast('Задача удалена', 'success');
            return true;
        } else {
            showToast(result.error || 'Ошибка удаления', 'error');
        }
    } catch (error) {
        showToast('Ошибка соединения', 'error');
    }
    return false;
}

async function getComments(taskId) {
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}/comments`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        return await response.json();
    } catch (error) {
        console.error('Error loading comments:', error);
        return [];
    }
}

async function addComment(taskId, content) {
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({ 
                content,
                author: currentUser?.username || 'Alex'
            })
        });
        const result = await response.json();
        if (response.ok) {
            return true;
        }
    } catch (error) {
        showToast('Ошибка добавления комментария', 'error');
    }
    return false;
}

// Render Functions
function renderTasks() {
    // Clear all columns
    document.querySelectorAll('.task-list').forEach(list => {
        list.innerHTML = '';
    });
    
    // Reset counts
    const counts = { todo: 0, in_progress: 0, review: 0, done: 0 };
    
    // Render tasks
    tasks.forEach(task => {
        const card = createTaskCard(task);
        const column = document.querySelector(`#${task.status}-list`);
        if (column) {
            column.appendChild(card);
        }
        counts[task.status] = (counts[task.status] || 0) + 1;
    });
    
    // Update counts
    Object.keys(counts).forEach(status => {
        const countEl = document.getElementById(`count-${status}`);
        if (countEl) {
            countEl.textContent = counts[status] || 0;
        }
    });
}

function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = `task-card priority-${task.priority || 1}`;
    card.dataset.status = task.status;
    card.dataset.id = task.id;
    card.draggable = true;
    card.ondragstart = drag;
    
    const priorityLabels = ['📉', '⭐', '🔥'];
    const date = task.due_date ? new Date(task.due_date).toLocaleDateString('ru-RU') : '';
    const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';
    
    card.innerHTML = `
        <div class="priority-badge">${priorityLabels[task.priority || 1]}</div>
        <div class="task-drag-handle">⋮⋮</div>
        <div class="task-title">${escapeHtml(task.title)}</div>
        <div class="task-meta">
            <div class="task-meta-left">
                <span class="task-assignee">${task.assignee?.username || '🤖 AI'}</span>
                ${date ? `<span class="task-due-date ${isOverdue ? 'overdue' : ''}">📅 ${date}</span>` : ''}
            </div>
            <div class="task-meta-right">
                <span class="task-comments-badge">💬 ${task.comments_count || 0}</span>
            </div>
        </div>
    `;
    
    card.onclick = () => openTaskDetails(task.id);
    
    return card;
}

function updateStats() {
    const stats = {
        total: tasks.length,
        done: tasks.filter(t => t.status === 'done').length,
        progress: tasks.filter(t => t.status === 'in_progress').length,
        overdue: tasks.filter(t => t.due_date && new Date(t.due_date) < new Date() && t.status !== 'done').length
    };
    
    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-done').textContent = stats.done;
    document.getElementById('stat-progress').textContent = stats.progress;
    document.getElementById('stat-overdue').textContent = stats.overdue;
}

function renderActivities(activities) {
    const container = document.getElementById('activity-list');
    
    if (activities.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">Нет активности</p>';
        return;
    }
    
    const actionLabels = {
        'created': 'создал(а)',
        'updated': 'обновил(а)',
        'deleted': 'удалить(а)',
        'status_changed': 'изменил(а) статус',
        'commented': 'прокомментировал(а)'
    };
    
    container.innerHTML = activities.map(activity => {
        const time = new Date(activity.created_at).toLocaleString('ru-RU');
        return `
            <div class="activity-item">
                <div class="activity-content">
                    <strong>${escapeHtml(activity.user?.username || 'Unknown')}</strong> 
                    ${actionLabels[activity.action] || activity.action}
                    ${activity.entity_type === 'task' ? 'задачу' : activity.entity_type}
                </div>
                <div class="activity-time">${time}</div>
            </div>
        `;
    }).join('');
}

function populateAssigneeSelect() {
    const select = document.getElementById('task-assignee');
    select.innerHTML = '<option value="">🤖 AI</option>';
    
    users.forEach(user => {
        if (user.id !== currentUser?.id) {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.username;
            select.appendChild(option);
        }
    });
}

// Modal Functions
function openModal(mode, taskId = null) {
    const modal = document.getElementById('task-modal');
    const form = document.getElementById('task-form');
    const title = document.getElementById('modal-title');
    const deleteBtn = document.getElementById('delete-task-btn');
    
    if (mode === 'add') {
        title.textContent = 'Новая задача';
        form.reset();
        document.getElementById('task-id').value = '';
        deleteBtn.style.display = 'none';
    } else if (mode === 'edit' && taskId) {
        title.textContent = 'Редактировать задачу';
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            document.getElementById('task-id').value = task.id;
            document.getElementById('task-title').value = task.title;
            document.getElementById('task-description').value = task.description || '';
            document.getElementById('task-status').value = task.status;
            document.getElementById('task-priority').value = task.priority || 1;
            document.getElementById('task-assignee').value = task.assignee_id || '';
            document.getElementById('task-due-date').value = task.due_date ? 
                task.due_date.slice(0, 16) : '';
            deleteBtn.style.display = 'inline-flex';
        }
    }
    
    modal.classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId || 'task-modal').classList.remove('active');
}

function handleTaskSubmit(event) {
    event.preventDefault();
    
    const taskId = document.getElementById('task-id').value;
    const taskData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value,
        status: document.getElementById('task-status').value,
        priority: parseInt(document.getElementById('task-priority').value),
        assignee_id: document.getElementById('task-assignee').value || null,
        due_date: document.getElementById('task-due-date').value || null
    };
    
    if (taskId) {
        updateTask(parseInt(taskId), taskData);
    } else {
        createTask(taskData);
    }
    
    closeModal();
}

function deleteCurrentTask() {
    const taskId = document.getElementById('task-id').value;
    if (taskId) {
        deleteTask(parseInt(taskId));
    }
}

// Task Details Modal
async function openTaskDetails(taskId) {
    currentTaskId = taskId;
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    document.getElementById('comments-title').textContent = task.title;
    await renderComments(taskId);
    document.getElementById('comments-modal').classList.add('active');
}

function closeCommentsModal() {
    document.getElementById('comments-modal').classList.remove('active');
    currentTaskId = null;
}

async function renderComments(taskId) {
    const comments = await getComments(taskId);
    const container = document.getElementById('comments-list');
    
    if (comments.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">Нет комментариев</p>';
        return;
    }
    
    container.innerHTML = comments.map(comment => {
        // Parse mentions
        let content = escapeHtml(comment.content);
        if (comment.mentions) {
            try {
                const mentionedIds = JSON.parse(comment.mentions);
                mentionedIds.forEach(id => {
                    const mentionedUser = users.find(u => u.id === id);
                    if (mentionedUser) {
                        content = content.replace(
                            `@${mentionedUser.username}`,
                            `<span class="mention">@${mentionedUser.username}</span>`
                        );
                    }
                });
            } catch (e) {}
        }
        
        return `
            <div class="comment">
                <div class="comment-header">
                    <span class="comment-author">${escapeHtml(comment.author?.username || 'Unknown')}</span>
                    <span class="comment-date">${new Date(comment.created_at).toLocaleString('ru-RU')}</span>
                </div>
                <div class="comment-content">${content}</div>
            </div>
        `;
    }).join('');
}

async function addComment() {
    const textarea = document.getElementById('new-comment');
    const content = textarea.value.trim();
    
    if (!content || !currentTaskId) return;
    
    await addComment(currentTaskId, content);
    textarea.value = '';
    await renderComments(currentTaskId);
    loadActivities();
}

// Filters
function applyFilters() {
    loadTasks();
}

// Drag and Drop
function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.dataset.id);
    ev.target.classList.add('dragging');
}

function allowDrop(ev) {
    ev.preventDefault();
    const column = ev.target.closest('.column');
    if (column) {
        column.classList.add('drag-over');
    }
}

function drop(ev) {
    ev.preventDefault();
    
    // Remove drag-over styles
    document.querySelectorAll('.column').forEach(col => {
        col.classList.remove('drag-over');
    });
    
    const taskId = parseInt(ev.dataTransfer.getData("text"));
    const column = ev.target.closest('.column');
    
    if (!column) return;
    
    const newStatus = column.dataset.status;
    const task = tasks.find(t => t.id === taskId);
    
    if (task && task.status !== newStatus) {
        moveTask(taskId, newStatus);
    }
    
    document.querySelectorAll('.task-card.dragging').forEach(card => {
        card.classList.remove('dragging');
    });
}

// Dark Mode
function toggleDarkMode() {
    isDarkMode = !isDarkMode;
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    localStorage.setItem('dark_mode', isDarkMode);
    applyTheme();
}

function applyTheme() {
    isDarkMode = localStorage.getTheme === 'true' || 
                 (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
}

// Export
function exportCSV() {
    window.location.href = `${API_BASE}/export/csv`;
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Utility
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modals on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        // Don't close login/register modal if not authenticated
        const loginModal = document.getElementById('login-modal');
        const registerModal = document.getElementById('register-modal');
        if (loginModal && loginModal.classList.contains('active') && !currentUser) {
            return;  // Can't close login modal without being logged in
        }
        if (registerModal && registerModal.classList.contains('active') && !currentUser) {
            return;  // Can't close register modal without being logged in
        }
        e.target.classList.remove('active');
    }
});

// Close modals on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        // Don't close login/register modal if not authenticated
        const loginModal = document.getElementById('login-modal');
        const registerModal = document.getElementById('register-modal');
        if ((loginModal && loginModal.classList.contains('active') && !currentUser) ||
            (registerModal && registerModal.classList.contains('active') && !currentUser)) {
            return;  // Can't close login/register modal without being logged in
        }
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});

// Add fadeOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(10px); }
    }
`;
document.head.appendChild(style);
