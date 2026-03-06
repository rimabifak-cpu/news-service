/**
 * News Service - Admin Panel JavaScript
 */

const API_BASE = '';

// Navigation
document.querySelectorAll('.sidebar-menu a').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = e.target.closest('a').dataset.page;
        
        document.querySelectorAll('.sidebar-menu a').forEach(l => l.classList.remove('active'));
        e.target.closest('a').classList.add('active');
        
        document.querySelectorAll('.page').forEach(p => p.classList.add('d-none'));
        document.getElementById(`page-${page}`).classList.remove('d-none');
        
        if (page === 'dashboard') loadDashboard();
        if (page === 'posts') loadPosts('all');
        if (page === 'sources') loadSources();
        if (page === 'settings') loadSettings();
    });
});

// Load Dashboard
async function loadDashboard() {
    try {
        const stats = await fetch(`${API_BASE}/api/stats`).then(r => r.json());
        
        document.getElementById('stat-sources').textContent = stats.sources_count || 0;
        document.getElementById('stat-pending').textContent = stats.posts_by_status?.pending || 0;
        document.getElementById('stat-ready').textContent = stats.posts_by_status?.ready || 0;
        document.getElementById('stat-published').textContent = stats.posts_by_status?.published || 0;
        
        // Load recent posts
        const posts = await fetch(`${API_BASE}/api/posts?limit=5`).then(r => r.json());
        renderRecentPosts(posts);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load Settings
async function loadSettings() {
    try {
        const settings = await fetch(`${API_BASE}/api/settings`).then(r => r.json());
        
        document.getElementById('ai-api-key').value = settings.ai_api_key || 'Не настроен';
        document.getElementById('ai-api-url').value = settings.ai_api_url || '';
        document.getElementById('ai-model').value = settings.ai_model || '';
        document.getElementById('bot-token').value = settings.telegram_bot_token || 'Не настроен';
        document.getElementById('channel-id').value = settings.telegram_channel_id || '';
        document.getElementById('logo-path').value = settings.logo_path || '';
        document.getElementById('logo-position').value = settings.logo_position || '';
        document.getElementById('logo-opacity').value = settings.logo_opacity || '';
        document.getElementById('parser-interval').value = settings.parser_interval || '';
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

function renderRecentPosts(posts) {
    const container = document.getElementById('recent-posts');
    if (!posts || posts.length === 0) {
        container.innerHTML = '<p class="text-muted">Нет постов</p>';
        return;
    }
    
    container.innerHTML = posts.map(post => `
        <div class="post-card">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="post-title">${escapeHtml(post.adapted_title || post.original_title)}</div>
                    <div class="post-content">${escapeHtml(post.adapted_content || post.original_content || '')}</div>
                </div>
                <span class="status-badge status-${post.status}">${post.status}</span>
            </div>
            ${post.status === 'ready' ? `
                <div class="mt-3">
                    <button class="btn btn-publish btn-sm" onclick="publishPost(${post.id})">
                        <i class="bi bi-send"></i> Опубликовать
                    </button>
                    <button class="btn btn-reject btn-sm" onclick="rejectPost(${post.id})">
                        <i class="bi bi-x-lg"></i> Отклонить
                    </button>
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Load Posts
async function loadPosts(statusFilter = 'all') {
    const url = statusFilter === 'all' 
        ? `${API_BASE}/api/posts?limit=50`
        : `${API_BASE}/api/posts?status_filter=${statusFilter}&limit=50`;
    
    try {
        const posts = await fetch(url).then(r => r.json());
        renderPostsList(posts);
    } catch (error) {
        console.error('Error loading posts:', error);
    }
}

function renderPostsList(posts) {
    const container = document.getElementById('posts-list');
    if (!posts || posts.length === 0) {
        container.innerHTML = '<p class="text-muted">Нет постов</p>';
        return;
    }
    
    container.innerHTML = posts.map(post => `
        <div class="post-card">
            <div class="row">
                ${post.processed_image_path ? `
                    <div class="col-md-3">
                        <img src="${post.processed_image_path}" alt="Post image">
                    </div>
                ` : ''}
                <div class="${post.processed_image_path ? 'col-md-9' : 'col-md-12'}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="post-title">${escapeHtml(post.adapted_title || post.original_title)}</div>
                        <span class="status-badge status-${post.status}">${post.status}</span>
                    </div>
                    <p class="text-muted small mb-2">
                        <i class="bi bi-clock"></i> ${new Date(post.created_at).toLocaleString('ru-RU')}
                    </p>
                    <div class="post-content mb-3">${escapeHtml(post.adapted_content || post.original_content || '')}</div>
                    ${post.status === 'ready' ? `
                        <button class="btn btn-publish btn-sm" onclick="publishPost(${post.id})">
                            <i class="bi bi-send"></i> Опубликовать
                        </button>
                        <button class="btn btn-reject btn-sm" onclick="rejectPost(${post.id})">
                            <i class="bi bi-x-lg"></i> Отклонить
                        </button>
                    ` : ''}
                    ${post.status === 'published' ? `
                        <span class="text-success"><i class="bi bi-check-circle"></i> Опубликовано</span>
                    ` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

// Load Sources
async function loadSources() {
    try {
        const sources = await fetch(`${API_BASE}/api/sources`).then(r => r.json());
        renderSourcesList(sources);
    } catch (error) {
        console.error('Error loading sources:', error);
    }
}

function renderSourcesList(sources) {
    const container = document.getElementById('sources-list');
    if (!sources || sources.length === 0) {
        container.innerHTML = '<tr><td colspan="6" class="text-muted">Нет источников</td></tr>';
        return;
    }
    
    container.innerHTML = sources.map(source => `
        <tr>
            <td><strong>${escapeHtml(source.name)}</strong></td>
            <td><a href="${escapeHtml(source.url)}" target="_blank">${escapeHtml(source.url)}</a></td>
            <td>${source.source_type}</td>
            <td>${source.ai_enabled ? '<i class="bi bi-check-circle-fill text-success"></i>' : '<i class="bi bi-x-circle-fill text-muted"></i>'}</td>
            <td>
                <span class="badge ${source.is_active ? 'bg-success' : 'bg-secondary'}">
                    ${source.is_active ? 'Активен' : 'Неактивен'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="parseSource(${source.id})">
                    <i class="bi bi-arrow-clockwise"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteSource(${source.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Actions
function showAddSourceModal() {
    new bootstrap.Modal(document.getElementById('addSourceModal')).show();
}

async function addSource() {
    const data = {
        name: document.getElementById('source-name').value,
        url: document.getElementById('source-url').value,
        source_type: document.getElementById('source-type').value,
        ai_prompt: document.getElementById('source-ai-prompt').value,
        ai_enabled: document.getElementById('source-ai-enabled').checked,
        selector_title: document.getElementById('source-selector-title').value,
        selector_content: document.getElementById('source-selector-content').value,
        selector_image: document.getElementById('source-selector-image').value,
        selector_date: document.getElementById('source-selector-date').value,
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/sources`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addSourceModal')).hide();
            loadSources();
            alert('Источник добавлен');
        } else {
            alert('Ошибка при добавлении источника');
        }
    } catch (error) {
        console.error('Error adding source:', error);
        alert('Ошибка при добавлении источника');
    }
}

async function parseSource(sourceId) {
    try {
        const response = await fetch(`${API_BASE}/api/sources/${sourceId}/parse`, { method: 'POST' });
        const result = await response.json();
        alert(result.message);
        loadDashboard();
    } catch (error) {
        console.error('Error parsing source:', error);
        alert('Ошибка при парсинге');
    }
}

async function parseAllSources() {
    if (!confirm('Запустить парсинг всех источников?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/parse-all`, { method: 'POST' });
        const result = await response.json();
        alert(result.message);
        loadDashboard();
        loadSources();
    } catch (error) {
        console.error('Error parsing all sources:', error);
        alert('Ошибка при парсинге');
    }
}

async function deleteSource(sourceId) {
    if (!confirm('Вы уверены, что хотите удалить этот источник?')) return;
    
    try {
        await fetch(`${API_BASE}/api/sources/${sourceId}`, { method: 'DELETE' });
        loadSources();
        alert('Источник удалён');
    } catch (error) {
        console.error('Error deleting source:', error);
        alert('Ошибка при удалении');
    }
}

async function publishPost(postId) {
    if (!confirm('Опубликовать этот пост в Telegram?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/posts/${postId}/publish`, { method: 'POST' });
        if (response.ok) {
            alert('Пост опубликован');
            loadDashboard();
            loadPosts();
        } else {
            const error = await response.json();
            alert(`Ошибка: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error publishing post:', error);
        alert('Ошибка при публикации');
    }
}

async function rejectPost(postId) {
    if (!confirm('Отклонить этот пост?')) return;
    
    try {
        await fetch(`${API_BASE}/api/posts/${postId}/reject`, { method: 'POST' });
        loadDashboard();
        loadPosts();
        alert('Пост отклонён');
    } catch (error) {
        console.error('Error rejecting post:', error);
        alert('Ошибка при отклонении');
    }
}

// Utility
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Settings functions
function showEditSettingsModal() {
    new bootstrap.Modal(document.getElementById('editSettingsModal')).show();
}

async function restartService() {
    if (!confirm('Перезапустить сервис? Это займёт около 10-15 секунд.')) return;
    
    try {
        // Показываем уведомление (так как нет API для перезапуска)
        alert('Для перезапуска выполните на сервере:\n\ncd /opt/news_service\ndocker-compose restart\n\nИли нажмите OK, чтобы скопировать команду.');
        
        // Копируем команду в буфер
        const cmd = 'cd /opt/news_service && docker-compose restart';
        await navigator.clipboard.writeText(cmd);
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при перезапуске');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

// Auto-refresh every 30 seconds
setInterval(() => {
    const activePage = document.querySelector('.sidebar-menu a.active').dataset.page;
    if (activePage === 'dashboard') loadDashboard();
    if (activePage === 'posts') loadPosts('all');
}, 30000);
