// Task Planner - Frontend JavaScript
const API_BASE = '/api';

// State
let tasks = [];
let currentTaskId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadTasks();
    setupDragAndDrop();
});

// API Functions
async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE}/tasks`);
        tasks = await response.json();
        renderTasks();
        updateStats();
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

async function createTask(taskData) {
    try {
        const response = await fetch(`${API_BASE}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        const result = await response.json();
        if (result.status === 'created') {
            loadTasks();
            return true;
        }
    } catch (error) {
        console.error('Error creating task:', error);
    }
    return false;
}

async function updateTask(taskId, taskData) {
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        const result = await response.json();
        if (result.status === 'updated') {
            loadTasks();
            return true;
        }
    } catch (error) {
        console.error('Error updating task:', error);
    }
    return false;
}

async function deleteTask(taskId) {
    if (!confirm('Удалить эту задачу?')) return false;
    
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        if (result.status === 'deleted') {
            loadTasks();
            return true;
        }
    } catch (error) {
        console.error('Error deleting task:', error);
    }
    return false;
}

async function getComments(taskId) {
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}/comments`);
        return await response.json();
    } catch (error) {
        console.error('Error loading comments:', error);
        return [];
    }
}

async function addComment(taskId, content, author = 'Alex') {
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ author, content })
        });
        const result = await response.json();
        if (result.status === 'comment_added') {
            return true;
        }
    } catch (error) {
        console.error('Error adding comment:', error);
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
    card.className = `task-card ${task.priority == 1 ? 'priority-high' : ''}`;
    card.dataset.status = task.status;
    card.dataset.id = task.id;
    card.onclick = () => openTaskDetails(task.id);
    
    const date = new Date(task.created_at).toLocaleDateString('ru-RU');
    
    card.innerHTML = `
        <div class="task-title">${escapeHtml(task.title)}</div>
        <div class="task-meta">
            <span class="task-assignee">${task.assignee || '🤖 AI'}</span>
            <span class="task-date">${date}</span>
        </div>
    `;
    
    return card;
}

function updateStats() {
    const stats = {
        total: tasks.length,
        done: tasks.filter(t => t.status === 'done').length,
        progress: tasks.filter(t => t.status === 'in_progress').length
    };
    
    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-done').textContent = stats.done;
    document.getElementById('stat-progress').textContent = stats.progress;
}

// Modal Functions
function openModal(mode, taskId = null) {
    const modal = document.getElementById('task-modal');
    const form = document.getElementById('task-form');
    const title = document.getElementById('modal-title');
    
    if (mode === 'add') {
        title.textContent = 'Новая задача';
        form.reset();
        document.getElementById('task-id').value = '';
    } else if (mode === 'edit' && taskId) {
        title.textContent = 'Редактировать задачу';
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            document.getElementById('task-id').value = task.id;
            document.getElementById('task-title').value = task.title;
            document.getElementById('task-description').value = task.description || '';
            document.getElementById('task-status').value = task.status;
            document.getElementById('task-priority').value = task.priority || 0;
        }
    }
    
    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('task-modal').classList.remove('active');
}

function handleTaskSubmit(event) {
    event.preventDefault();
    
    const taskId = document.getElementById('task-id').value;
    const taskData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value,
        status: document.getElementById('task-status').value,
        priority: parseInt(document.getElementById('task-priority').value)
    };
    
    if (taskId) {
        updateTask(parseInt(taskId), taskData);
    } else {
        createTask(taskData);
    }
    
    closeModal();
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
    
    container.innerHTML = comments.map(comment => `
        <div class="comment">
            <div class="comment-header">
                <span class="comment-author">${escapeHtml(comment.author)}</span>
                <span class="comment-date">${new Date(comment.created_at).toLocaleString('ru-RU')}</span>
            </div>
            <div class="comment-content">${escapeHtml(comment.content)}</div>
        </div>
    `).join('');
}

async function addComment() {
    const textarea = document.getElementById('new-comment');
    const content = textarea.value.trim();
    
    if (!content || !currentTaskId) return;
    
    await addComment(currentTaskId, content);
    textarea.value = '';
    await renderComments(currentTaskId);
}

// Drag and Drop
function setupDragAndDrop() {
    const columns = document.querySelectorAll('.column');
    const cards = document.querySelectorAll('.task-list');
    
    cards.forEach(list => {
        list.addEventListener('dragover', (e) => {
            e.preventDefault();
            list.style.background = '#e8ebf0';
        });
        
        list.addEventListener('dragleave', () => {
            list.style.background = '';
        });
        
        list.addEventListener('drop', async (e) => {
            e.preventDefault();
            list.style.background = '';
            
            const card = document.querySelector('.task-card.dragging');
            if (!card) return;
            
            const taskId = parseInt(card.dataset.id);
            const newStatus = list.closest('.column').dataset.status;
            
            card.classList.remove('dragging');
            await updateTask(taskId, { status: newStatus });
        });
    });
    
    document.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('task-card')) {
            e.target.classList.add('dragging');
        }
    });
    
    document.addEventListener('dragend', (e) => {
        if (e.target.classList.contains('task-card')) {
            e.target.classList.remove('dragging');
        }
    });
}

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modals on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// Close modals on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});
