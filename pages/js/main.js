// ==========================================
// API CONFIGURATION
// ==========================================

function resolveApiBase() {
    const stored = localStorage.getItem('api_base');
    if (stored) return stored.replace(/\/$/, '');

    const url = new URL(window.location.href);

    if (url.protocol === 'file:') {
        return 'http://localhost:8000';
    }

    if (url.port && url.port !== '8000') {
        return `${url.protocol}//${url.hostname}:8000`;
    }

    return url.origin;
}

function resolveWsBase(apiBase) {
    const apiUrl = new URL(apiBase);
    const wsProtocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${wsProtocol}//${apiUrl.host}`;
}

const API_URL = resolveApiBase();
const WS_URL = resolveWsBase(API_URL);

// ==========================================
// STATE
// ==========================================

let currentRoom = null;
let ws = null;
let currentUser = null;
let rooms = [];

// ==========================================
// DOM ELEMENTS
// ==========================================

const roomsList = document.getElementById('roomsList');
const roomName = document.getElementById('roomName');
const messagesList = document.getElementById('messagesList');
const messageInput = document.getElementById('messageInput');
const messageForm = document.getElementById('messageForm');
const sendBtn = document.getElementById('sendBtn');
const connectionStatus = document.getElementById('connectionStatus');
const createRoomBtn = document.getElementById('createRoomBtn');
const createRoomModal = document.getElementById('createRoomModal');
const createRoomForm = document.getElementById('createRoomForm');
const roomNameInput = document.getElementById('roomNameInput');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const settingsBtn = document.getElementById('settingsBtn');

// ==========================================
// AUTH FUNCTIONS
// ==========================================

function getAccessToken() {
    return localStorage.getItem('access_token');
}

function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

function getAuthHeaders() {
    const token = getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function redirectToLogin() {
    window.location.href = './login.html';
}

async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    try {
        const response = await fetch(`${API_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) return false;

        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        return true;
    } catch (err) {
        console.error('Failed to refresh token:', err);
        return false;
    }
}

async function fetchWithAuth(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...(options.headers || {}),
            ...getAuthHeaders()
        }
    });

    if (response.status !== 401) return response;

    const refreshed = await refreshAccessToken();
    if (!refreshed) {
        redirectToLogin();
        return response;
    }

    return fetch(url, {
        ...options,
        headers: {
            ...(options.headers || {}),
            ...getAuthHeaders()
        }
    });
}

async function loadCurrentUser() {
    try {
        const response = await fetchWithAuth(`${API_URL}/auth/me`);
        if (!response.ok) return null;
        return await response.json();
    } catch (err) {
        console.error('Failed to load user:', err);
        return null;
    }
}

// ==========================================
// CONNECTION STATUS
// ==========================================

function updateConnectionStatus(status) {
    const statusDot = connectionStatus.querySelector('.status-dot');
    const statusText = connectionStatus.querySelector('.status-text');

    connectionStatus.className = 'connection-status';

    switch (status) {
        case 'connected':
            connectionStatus.classList.add('connected');
            statusText.textContent = 'Подключено';
            break;
        case 'connecting':
            connectionStatus.classList.add('connecting');
            statusText.textContent = 'Подключение...';
            break;
        case 'disconnected':
            connectionStatus.classList.add('disconnected');
            statusText.textContent = 'Нет связи';
            break;
    }
}

// ==========================================
// ROOMS
// ==========================================

function renderRooms() {
    if (rooms.length === 0) {
        roomsList.innerHTML = `
            <div class="placeholder-message">
                <span class="placeholder-icon">#</span>
                <p>Нет доступных комнат</p>
            </div>
        `;
        return;
    }

    roomsList.innerHTML = rooms.map(room => `
        <div class="room-item ${currentRoom === room.id ? 'active' : ''}" 
             onclick="selectRoom(${room.id})">
            <span class="room-hash">#</span>
            <span class="room-title">${escapeHtml(room.title)}</span>
        </div>
    `).join('');
}

async function loadRooms() {
    try {
        const response = await fetchWithAuth(`${API_URL}/rooms`);
        if (!response.ok) throw new Error('Failed to load rooms');

        rooms = await response.json();
        renderRooms();
    } catch (err) {
        console.error('Failed to load rooms:', err);
        // Fallback to default room
        rooms = [{ id: 1, title: 'general' }];
        renderRooms();
    }
}

async function createRoom(title) {
    try {
        const response = await fetchWithAuth(`${API_URL}/rooms`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create room');
        }

        const room = await response.json();
        rooms.push(room);
        renderRooms();
        selectRoom(room.id);
        closeModal();
    } catch (err) {
        console.error('Failed to create room:', err);
        alert(err.message);
    }
}

function selectRoom(roomId) {
    currentRoom = roomId;
    const room = rooms.find(r => r.id === roomId);

    if (room) {
        roomName.textContent = `# ${room.title}`;
        messageInput.placeholder = `Сообщение в #${room.title}`;
        messageInput.disabled = false;
    }

    renderRooms();
    loadMessages(roomId);
    connectWebSocket(roomId);
}

// ==========================================
// MESSAGES
// ==========================================

async function loadMessages(roomId) {
    try {
        const response = await fetchWithAuth(`${API_URL}/rooms/${roomId}/messages?limit=50`);
        if (!response.ok) throw new Error('Failed to load messages');

        const messages = await response.json();

        messagesList.innerHTML = '';
        messages.forEach(msg => addMessage(msg, false));
        scrollToBottom();
    } catch (err) {
        console.error('Failed to load messages:', err);
        messagesList.innerHTML = `
            <div class="placeholder-message">
                <span class="placeholder-icon">⚠</span>
                <p>Не удалось загрузить сообщения</p>
            </div>
        `;
    }
}

function addMessage(msg, animate = false) {
    const messageEl = document.createElement('div');
    messageEl.className = 'message' + (animate ? ' message-new' : '');

    const author = msg.user?.display_name || msg.author || 'Unknown';
    const username = msg.user?.username || 'unknown';
    const avatarUrl = msg.user?.avatar_url;
    const authorInitial = author[0].toUpperCase();

    const time = new Date(msg.created_at).toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
    });

    let avatarContent;
    if (avatarUrl) {
        // Исправляем путь, если он относительный
        const fullAvatarUrl = avatarUrl.startsWith('http') ? avatarUrl : `${API_URL}${avatarUrl}`;
        avatarContent = `<img src="${fullAvatarUrl}" alt="${authorInitial}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
    } else {
        avatarContent = authorInitial;
    }

    // ВОТ ТУТ ИЗМЕНЕНИЕ: добавили border: none; box-shadow: none;
    const avatarStyle = avatarUrl
        ? 'background: none; padding: 0; border: none; box-shadow: none;'
        : '';

    messageEl.innerHTML = `
        <div class="message-avatar" style="${avatarStyle}">
            ${avatarContent}
        </div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-author">${escapeHtml(author)}</span>
                <span class="message-username">@${escapeHtml(username)}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-text">${escapeHtml(msg.body)}</div>
        </div>
    `;

    messagesList.appendChild(messageEl);
    if (animate) scrollToBottom();
}

function scrollToBottom() {
    messagesList.scrollTop = messagesList.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || !currentRoom) return;

    // FIX: Generate a shorter nonce (< 25 chars).
    // Date.now() is 13 chars. Random string (8 chars) ensures uniqueness.
    // Total: ~21 chars, well within the 25-char limit.
    const nonce = Date.now().toString() + Math.random().toString(36).slice(2, 10);

    try {
        const response = await fetchWithAuth(`${API_URL}/rooms/${currentRoom}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                body: text,
                nonce: nonce,
                // Note: user_id is handled by the backend from the token
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to send message');
        }

        // Success
        messageInput.value = '';
        sendBtn.disabled = true;

        // Optimistically add message or wait for WebSocket/Polling
        // (If strictly REST without WS, you might want to call loadMessages(currentRoom) here)

    } catch (err) {
        console.error('Failed to send message:', err);
        alert('Не удалось отправить сообщение: ' + err.message);
    }
}


// ==========================================
// WEBSOCKET
// ==========================================

function connectWebSocket(roomId) {
    if (ws) ws.close();

    const token = getAccessToken();
    const wsUrl = `${WS_URL}/ws/rooms/${roomId}?token=${token}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        updateConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'message') {
                addMessage(data, true);
            } else if (data.type === 'error') {
                console.error('WebSocket error:', data.detail);
            }
        } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus('disconnected');
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus('disconnected');

        // Reconnect after 3 seconds
        setTimeout(() => {
            if (currentRoom) {
                updateConnectionStatus('connecting');
                connectWebSocket(currentRoom);
            }
        }, 3000);
    };
}

// ==========================================
// MODAL
// ==========================================

function openModal() {
    createRoomModal.classList.add('active');
    roomNameInput.focus();
}

function closeModal() {
    createRoomModal.classList.remove('active');
    roomNameInput.value = '';
}

// ==========================================
// EVENT LISTENERS
// ==========================================

messageForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage();
});

messageInput.addEventListener('input', (e) => {
    sendBtn.disabled = !e.target.value.trim();
});

createRoomBtn.addEventListener('click', openModal);
closeModalBtn.addEventListener('click', closeModal);
cancelModalBtn.addEventListener('click', closeModal);

createRoomForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const title = roomNameInput.value.trim();
    if (title) createRoom(title);
});

createRoomModal.addEventListener('click', (e) => {
    if (e.target === createRoomModal) closeModal();
});

settingsBtn.addEventListener('click', () => {
    alert('Настройки будут доступны в следующем обновлении');
});

// ==========================================
// INITIALIZATION
// ==========================================

async function init() {
    // Check auth
    if (!getAccessToken()) {
        redirectToLogin();
        return;
    }

    // Load user
    currentUser = await loadCurrentUser();
    if (!currentUser) {
        redirectToLogin();
        return;
    }

    console.log('Logged in as:', currentUser.username);

    // Load rooms and select first one
    await loadRooms();

    if (rooms.length > 0) {
        selectRoom(rooms[0].id);
    }
}

// Start app
init();
