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
        if (page === 'channels') loadChannels();
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

// Load Channels
async function loadChannels() {
    try {
        const response = await fetch(`${API_BASE}/api/channels`);
        
        if (!response.ok) {
            if (response.status === 404) {
                document.getElementById('channels-list').innerHTML = `
                    <tr><td colspan="7" class="text-muted">
                        ⚠️ API каналов недоступно. Обновите сервер:<br>
                        <code>git pull && docker-compose exec news_service python migrate_multichannel.py</code>
                    </td></tr>
                `;
                return;
            }
            throw new Error(`HTTP ${response.status}`);
        }
        
        const channels = await response.json();
        renderChannelsList(channels);
    } catch (error) {
        console.error('Error loading channels:', error);
        document.getElementById('channels-list').innerHTML = `
            <tr><td colspan="7" class="text-danger">Ошибка загрузки: ${error.message}</td></tr>
        `;
    }
}

function renderChannelsList(channels) {
    const container = document.getElementById('channels-list');
    if (!channels || channels.length === 0) {
        container.innerHTML = '<tr><td colspan="7" class="text-muted">Нет каналов</td></tr>';
        return;
    }

    container.innerHTML = channels.map(channel => `
        <tr>
            <td><strong>${escapeHtml(channel.name)}</strong></td>
            <td><a href="https://t.me/${channel.channel_id.replace('@', '')}" target="_blank">${escapeHtml(channel.channel_id)}</a></td>
            <td><code>${escapeHtml(channel.bot_token)}</code></td>
            <td><small class="text-muted">${channel.ai_prompt ? escapeHtml(channel.ai_prompt.substring(0, 40)) + '...' : '—'}</small></td>
            <td><span class="badge bg-info">${channel.sources_count || 0}</span></td>
            <td>
                <span class="badge ${channel.is_active ? 'bg-success' : 'bg-secondary'}">
                    ${channel.is_active ? 'Активен' : 'Неактивен'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editChannel(${channel.id})" title="Редактировать">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteChannel(${channel.id})" title="Удалить">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function showAddChannelModal() {
    document.getElementById('add-channel-form').reset();
    document.querySelector('#addChannelModal .modal-title').textContent = 'Добавить канал';
    document.querySelector('#addChannelModal .btn-primary').textContent = 'Добавить';
    document.querySelector('#addChannelModal .btn-primary').onclick = addChannel;
    new bootstrap.Modal(document.getElementById('addChannelModal')).show();
}

async function addChannel() {
    const data = {
        name: document.getElementById('channel-name').value,
        bot_token: document.getElementById('channel-bot-token').value,
        channel_id: document.getElementById('channel-channel-id').value,
        ai_prompt: document.getElementById('channel-ai-prompt').value,
        logo_position: document.getElementById('channel-logo-position').value,
        logo_opacity: parseFloat(document.getElementById('channel-logo-opacity').value),
    };

    try {
        const response = await fetch(`${API_BASE}/api/channels`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addChannelModal')).hide();
            loadChannels();
            alert('Канал добавлен');
        } else {
            const error = await response.json();
            alert(`Ошибка: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error adding channel:', error);
        alert('Ошибка при добавлении канала');
    }
}

async function editChannel(channelId) {
    try {
        const channel = await fetch(`${API_BASE}/api/channels/${channelId}`).then(r => r.json());
        
        document.getElementById('channel-name').value = channel.name;
        document.getElementById('channel-bot-token').value = channel.bot_token;
        document.getElementById('channel-channel-id').value = channel.channel_id;
        document.getElementById('channel-ai-prompt').value = channel.ai_prompt || '';
        document.getElementById('channel-logo-position').value = channel.logo_position;
        document.getElementById('channel-logo-opacity').value = channel.logo_opacity;
        
        document.querySelector('#addChannelModal .modal-title').textContent = 'Редактировать канал';
        document.querySelector('#addChannelModal .btn-primary').textContent = 'Сохранить';
        document.querySelector('#addChannelModal .btn-primary').onclick = () => updateChannel(channelId);
        
        new bootstrap.Modal(document.getElementById('addChannelModal')).show();
    } catch (error) {
        console.error('Error loading channel:', error);
        alert('Ошибка при загрузке канала');
    }
}

async function updateChannel(channelId) {
    const data = {
        name: document.getElementById('channel-name').value,
        bot_token: document.getElementById('channel-bot-token').value,
        channel_id: document.getElementById('channel-channel-id').value,
        ai_prompt: document.getElementById('channel-ai-prompt').value,
        logo_position: document.getElementById('channel-logo-position').value,
        logo_opacity: parseFloat(document.getElementById('channel-logo-opacity').value),
    };

    try {
        const response = await fetch(`${API_BASE}/api/channels/${channelId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addChannelModal')).hide();
            loadChannels();
            alert('Канал обновлён');
        } else {
            const error = await response.json();
            alert(`Ошибка: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error updating channel:', error);
        alert('Ошибка при обновлении канала');
    }
}

async function deleteChannel(channelId) {
    if (!confirm('Удалить этот канал? Источники должны быть удалены заранее.')) return;

    try {
        const response = await fetch(`${API_BASE}/api/channels/${channelId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadChannels();
            alert('Канал удалён');
        } else {
            const error = await response.json();
            alert(`Ошибка: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error deleting channel:', error);
        alert('Ошибка при удалении канала');
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
let currentStatusFilter = 'all';

async function loadPosts(statusFilter = 'all') {
    currentStatusFilter = statusFilter;
    
    // Загружаем каналы для фильтра
    await loadChannelsForFilter();
    
    const channelFilter = document.getElementById('channel-filter')?.value || '';
    const adFilter = document.getElementById('ad-filter')?.value || '';
    
    // Строим URL с параметрами
    let url = `${API_BASE}/api/posts?limit=50`;
    
    if (statusFilter !== 'all') {
        url += `&status_filter=${statusFilter}`;
    }
    
    if (channelFilter) {
        url += `&channel_id=${channelFilter}`;
    }
    
    if (adFilter !== '') {
        url += `&is_advertisement=${adFilter}`;
    }

    try {
        const posts = await fetch(url).then(r => r.json());
        renderPostsList(posts);
    } catch (error) {
        console.error('Error loading posts:', error);
    }
}

async function loadChannelsForFilter() {
    const select = document.getElementById('channel-filter');
    if (!select || select.options.length > 1) return;  // Уже загружено
    
    try {
        const response = await fetch(`${API_BASE}/api/channels`);
        
        if (!response.ok) {
            console.warn('API /api/channels недоступен (404). Возможно, сервер не обновлён.');
            return;
        }
        
        const channels = await response.json();
        
        if (!Array.isArray(channels)) {
            console.error('Ожидался массив каналов, получено:', channels);
            return;
        }
        
        channels.forEach(channel => {
            const option = document.createElement('option');
            option.value = channel.id;
            option.textContent = channel.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading channels for filter:', error);
    }
}

function renderPostsList(posts) {
    const container = document.getElementById('posts-list');
    if (!posts || posts.length === 0) {
        container.innerHTML = '<p class="text-muted">Нет постов</p>';
        return;
    }

    container.innerHTML = posts.map(post => `
        <div class="post-card" style="border-left: ${post.is_advertisement ? '4px solid #ffc107' : '4px solid transparent'}">
            <div class="row">
                ${post.processed_image_path ? `
                    <div class="col-md-3">
                        <img src="${post.processed_image_path.replace('/app/static/uploads', '/uploads')}" alt="Post image">
                    </div>
                ` : ''}
                <div class="${post.processed_image_path ? 'col-md-9' : 'col-md-12'}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="post-title">
                            ${escapeHtml(post.adapted_title || post.original_title)}
                            ${post.is_advertisement ? '<span class="badge bg-warning text-dark ms-2">#реклама</span>' : ''}
                        </div>
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
                        <button class="btn btn-sm ${post.is_advertisement ? 'btn-outline-warning' : 'btn-outline-secondary'} ms-2" onclick="toggleAd(${post.id}, ${post.is_advertisement})">
                            <i class="bi bi-tag"></i> ${post.is_advertisement ? 'Не реклама' : 'Реклама'}
                        </button>
                    ` : ''}
                    ${post.status === 'published' ? `
                        <span class="text-success"><i class="bi bi-check-circle"></i> Опубликовано</span>
                        <button class="btn btn-sm ${post.is_advertisement ? 'btn-outline-warning' : 'btn-outline-secondary'} ms-2" onclick="toggleAd(${post.id}, ${post.is_advertisement})">
                            <i class="bi bi-tag"></i> ${post.is_advertisement ? 'Не реклама' : 'Реклама'}
                        </button>
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
        container.innerHTML = '<tr><td colspan="8" class="text-muted">Нет источников</td></tr>';
        return;
    }

    container.innerHTML = sources.map(source => `
        <tr>
            <td><strong>${escapeHtml(source.name)}</strong></td>
            <td><a href="${escapeHtml(source.url)}" target="_blank">${escapeHtml(source.url)}</a></td>
            <td>${source.source_type}</td>
            <td>${source.ai_enabled ? '<i class="bi bi-check-circle-fill text-success"></i>' : '<i class="bi bi-x-circle-fill text-muted"></i>'}</td>
            <td><small class="text-muted">${source.ai_prompt ? escapeHtml(source.ai_prompt.substring(0, 50)) + '...' : '—'}</small></td>
            <td>
                ${source.auto_publish ? '<span class="badge bg-danger"><i class="bi bi-rocket-takeoff"></i> Авто</span>' : '<span class="badge bg-secondary">Ручная</span>'}
            </td>
            <td>
                <span class="badge ${source.is_active ? 'bg-success' : 'bg-secondary'}">
                    ${source.is_active ? 'Активен' : 'Неактивен'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editSource(${source.id})" title="Редактировать">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-success me-1" onclick="parseSource(${source.id})" title="Парсить">
                    <i class="bi bi-arrow-clockwise"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteSource(${source.id})" title="Удалить">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Actions
function showAddSourceModal() {
    // Очищаем форму
    document.getElementById('add-source-form').reset();
    document.querySelector('#addSourceModal .modal-title').textContent = 'Добавить источник';
    document.querySelector('#addSourceModal .btn-primary').textContent = 'Добавить';
    document.querySelector('#addSourceModal .btn-primary').onclick = addSource;
    
    // Загружаем список каналов
    loadChannelsForSelect();
    
    new bootstrap.Modal(document.getElementById('addSourceModal')).show();
}

async function toggleAd(postId, currentIsAd) {
    try {
        const response = await fetch(`${API_BASE}/api/posts/${postId}/toggle-ad`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            alert(`Пометка обновлена: ${result.is_advertisement ? 'Реклама' : 'Не реклама'}`);
            loadPosts(currentStatusFilter);
        } else {
            const error = await response.json();
            alert(`Ошибка: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error toggling ad:', error);
        alert('Ошибка при обновлении пометки');
    }
}

async function loadChannelsForSelect() {
    try {
        const channels = await fetch(`${API_BASE}/api/channels`).then(r => r.json());
        const select = document.getElementById('source-channel-id');
        select.innerHTML = '<option value="">Выберите канал...</option>';
        
        channels.forEach(channel => {
            const option = document.createElement('option');
            option.value = channel.id;
            option.textContent = channel.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading channels for select:', error);
    }
}

async function addSource() {
    const data = {
        name: document.getElementById('source-name').value,
        url: document.getElementById('source-url').value,
        source_type: document.getElementById('source-type').value,
        channel_id: parseInt(document.getElementById('source-channel-id').value),
        ai_prompt: document.getElementById('source-ai-prompt').value,
        ai_enabled: document.getElementById('source-ai-enabled').checked,
        auto_publish: document.getElementById('source-auto-publish')?.checked || false,
        selector_title: document.getElementById('source-selector-title')?.value || '',
        selector_content: document.getElementById('source-selector-content')?.value || '',
        selector_image: document.getElementById('source-selector-image')?.value || '',
        selector_date: document.getElementById('source-selector-date')?.value || '',
    };

    if (!data.channel_id) {
        alert('Выберите канал');
        return;
    }

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
            const error = await response.json();
            alert(`Ошибка: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error adding source:', error);
        alert('Ошибка при добавлении источника');
    }
}

// Глобальная переменная для хранения ID редактируемого источника
let editingSourceId = null;

async function editSource(sourceId) {
    try {
        // Получаем данные источника
        const source = await fetch(`${API_BASE}/api/sources/${sourceId}`).then(r => r.json());
        
        // Загружаем список каналов
        await loadChannelsForSelect();
        
        // Заполняем форму
        document.getElementById('source-name').value = source.name;
        document.getElementById('source-url').value = source.url;
        document.getElementById('source-type').value = source.source_type;
        document.getElementById('source-channel-id').value = source.channel_id;
        document.getElementById('source-ai-prompt').value = source.ai_prompt || '';
        document.getElementById('source-ai-enabled').checked = source.ai_enabled;
        
        // Автопубликация - проверяем существование элемента
        const autoPublishCheckbox = document.getElementById('source-auto-publish');
        if (autoPublishCheckbox) {
            autoPublishCheckbox.checked = source.auto_publish || false;
        }
        
        document.getElementById('source-selector-title').value = source.selector_title || '';
        document.getElementById('source-selector-content').value = source.selector_content || '';
        document.getElementById('source-selector-image').value = source.selector_image || '';
        document.getElementById('source-selector-date').value = source.selector_date || '';
        
        // Меняем заголовок и кнопку
        document.querySelector('#addSourceModal .modal-title').textContent = 'Редактировать источник';
        document.querySelector('#addSourceModal .btn-primary').textContent = 'Сохранить';
        document.querySelector('#addSourceModal .btn-primary').onclick = () => updateSource(sourceId);
        
        editingSourceId = sourceId;
        new bootstrap.Modal(document.getElementById('addSourceModal')).show();
    } catch (error) {
        console.error('Error loading source:', error);
        alert('Ошибка при загрузке источника');
    }
}

async function updateSource(sourceId) {
    const data = {
        name: document.getElementById('source-name').value,
        url: document.getElementById('source-url').value,
        source_type: document.getElementById('source-type').value,
        channel_id: parseInt(document.getElementById('source-channel-id').value),
        ai_prompt: document.getElementById('source-ai-prompt').value,
        ai_enabled: document.getElementById('source-ai-enabled').checked,
        auto_publish: document.getElementById('source-auto-publish')?.checked || false,
        selector_title: document.getElementById('source-selector-title')?.value || '',
        selector_content: document.getElementById('source-selector-content')?.value || '',
        selector_image: document.getElementById('source-selector-image')?.value || '',
        selector_date: document.getElementById('source-selector-date')?.value || '',
    };

    if (!data.channel_id) {
        alert('Выберите канал');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/sources/${sourceId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addSourceModal')).hide();
            loadSources();
            alert('Источник обновлён');
        } else {
            const error = await response.json();
            alert(`Ошибка: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error updating source:', error);
        alert('Ошибка при обновлении источника');
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
