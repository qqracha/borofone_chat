// ==========================================
// PRESENCE (онлайн пользователи)
// ==========================================

let presenceInterval = null;
let currentSearch = '';
let currentPage = 1;
const usersPerPage = 30;
let totalUsers = 0;

/**
 * Загрузить список всех пользователей с разделением на онлайн/оффлайн.
 */
async function loadAllUsers() {
    if (!currentRoom) {
        document.getElementById('usersCount').textContent = '0';
        document.getElementById('usersList').innerHTML = `
            <div class="placeholder-message">
                <span class="placeholder-icon">👥</span>
                <p>Выберите комнату</p>
            </div>
        `;
        return;
    }

    try {
        const offset = (currentPage - 1) * usersPerPage;
        let url = `${getApiUrl()}/rooms/${currentRoom.id}/users?limit=${usersPerPage}&offset=${offset}&sort_by=last_seen&sort_order=desc`;
        
        // Add search query
        if (currentSearch) {
            url += `&search=${encodeURIComponent(currentSearch)}`;
        }

        const response = await fetchWithAuth(url);

        if (!response.ok) {
            throw new Error('Failed to load users');
        }

        const data = await response.json();
        const users = data.users || [];
        totalUsers = data.total || 0;

        // Обновляем счётчик
        document.getElementById('usersCount').textContent = totalUsers;

        // Обновляем пагинацию
        updatePagination();

        // Отображаем список
        const usersList = document.getElementById('usersList');

        if (users.length === 0) {
            usersList.innerHTML = `
                <div class="placeholder-message">
                    <span class="placeholder-icon">👤</span>
                    <p>${currentSearch ? 'Пользователи не найдены' : 'Никого нет в списке'}</p>
                </div>
            `;
            return;
        }

        // Просто показываем всех пользователей одним списком
        usersList.innerHTML = users.map(user => renderUserItem(user)).join('');
        
        // Обновляем мобильный счётчик пользователей
        if (window.renderMobileUsers) {
            window.renderMobileUsers();
        }
        
        // Attach click handlers to user items
        attachClickHandlersToUserList();
    } catch (err) {
        console.error('Failed to load users:', err);
        // Fallback to old online-only endpoint
        loadOnlineUsers();
    }
}

/**
 * Render a single user item.
 */
function renderUserItem(user) {
    const displayName = user.display_name || user.username;
    const avatarUrl = withAvatarCacheBuster(
        normalizeAvatarUrl(user.avatar_url),
        user.id
    );
    const initial = displayName[0]?.toUpperCase() || 'U';

    const avatarHtml = avatarUrl
        ? `<img src="${escapeHtml(avatarUrl)}" alt="${escapeHtml(displayName)}" class="avatar-media">`
        : `<span>${initial}</span>`;

    const statusClass = user.is_online ? 'online' : 'offline';
    const itemClass = user.is_online ? 'user-item' : 'user-item offline';
    const lastSeenText = user.is_online ? '' : (user.last_seen_formatted || '');

    return `
        <div class="${itemClass}" data-user-id="${user.id}">
            <div class="user-avatar">${avatarHtml}</div>
            <div class="user-info">
                <div class="user-display-name">${escapeHtml(displayName)}</div>
                <div class="user-username">@${escapeHtml(user.username)}</div>
                ${!user.is_online ? `<div class="user-last-seen offline">${escapeHtml(lastSeenText)}</div>` : ''}
            </div>
            <div class="user-status ${statusClass}"></div>
        </div>
    `;
}

/**
 * Update pagination controls.
 */
function updatePagination() {
    const totalPages = Math.ceil(totalUsers / usersPerPage);
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');

    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
    if (pageInfo) pageInfo.textContent = `${currentPage} / ${totalPages || 1}`;
}

/**
 * Загрузить список онлайн пользователей в текущей комнате (legacy).
 */
async function loadOnlineUsers() {
    if (!currentRoom) {
        document.getElementById('usersCount').textContent = '0';
        document.getElementById('usersList').innerHTML = `
            <div class="placeholder-message">
                <span class="placeholder-icon">👥</span>
                <p>Выберите комнату</p>
            </div>
        `;
        return;
    }

    try {
        const response = await fetchWithAuth(`${getApiUrl()}/rooms/${currentRoom.id}/online`);

        if (!response.ok) {
            throw new Error('Failed to load online users');
        }

        const users = await response.json();

        // Обновляем счётчик
        document.getElementById('usersCount').textContent = users.length;

        // Отображаем список
        const usersList = document.getElementById('usersList');

        if (users.length === 0) {
            usersList.innerHTML = `
                <div class="placeholder-message">
                    <span class="placeholder-icon">👤</span>
                    <p>Никого нет онлайн</p>
                </div>
            `;
            return;
        }

        usersList.innerHTML = users.map(user => {
            const displayName = user.display_name || user.username;
            const avatarUrl = withAvatarCacheBuster(
        normalizeAvatarUrl(user.avatar_url),
        user.id
    );
            const initial = displayName[0]?.toUpperCase() || 'U';

            const avatarHtml = avatarUrl
                ? `<img src="${escapeHtml(avatarUrl)}" alt="${escapeHtml(displayName)}" class="avatar-media">`
                : `<span>${initial}</span>`;

            return `
                <div class="user-item" data-user-id="${user.id}">
                    <div class="user-avatar">${avatarHtml}</div>
                    <div class="user-info">
                        <div class="user-display-name">${escapeHtml(displayName)}</div>
                        <div class="user-username">@${escapeHtml(user.username)}</div>
                    </div>
                    <div class="user-status online"></div>
                </div>
            `;
        }).join('');
        
        // Attach click handlers to user items
        attachClickHandlersToUserList();
    } catch (err) {
        console.error('Failed to load online users:', err);
    }
    
    // Обновляем мобильный счётчик пользователей
    if (window.renderMobileUsers) {
        window.renderMobileUsers();
    }
}

/**
 * Handle search input.
 */
let searchTimeout = null;
function handleSearchInput(event) {
    const input = event.target;
    clearTimeout(searchTimeout);
    
    searchTimeout = setTimeout(() => {
        currentSearch = input.value.trim();
        currentPage = 1;
        loadAllUsers();
    }, 300);
}

/**
 * Handle pagination.
 */
function handlePrevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadAllUsers();
    }
}

function handleNextPage() {
    const totalPages = Math.ceil(totalUsers / usersPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        loadAllUsers();
    }
}

/**
 * Heartbeat — сообщаем серверу что мы ещё здесь.
 */
async function sendPresenceHeartbeat() {
    if (!currentRoom || !ws || ws.readyState !== WebSocket.OPEN) return;

    try {
        ws.send(JSON.stringify({
            type: 'heartbeat',
            room_id: currentRoom.id,
        }));
    } catch (err) {
        console.warn('[Presence] Heartbeat failed:', err);
    }
}

/**
 * Начать отслеживание присутствия в комнате.
 */
function startPresenceTracking() {
    if (presenceInterval) return;

    // Загружаем всех пользователей сразу
    loadAllUsers();

    // Обновляем каждые 10 секунд
    presenceInterval = setInterval(() => {
        loadAllUsers();
        sendPresenceHeartbeat();
    }, 10000);
}

/**
 * Остановить отслеживание присутствия.
 */
function stopPresenceTracking() {
    if (presenceInterval) {
        clearInterval(presenceInterval);
        presenceInterval = null;
    }
    // Reset search state when leaving room
    currentSearch = '';
    currentPage = 1;
    
    // Clear search input
    const searchInput = document.getElementById('usersSearch');
    if (searchInput) searchInput.value = '';
}

/**
 * Initialize users sidebar event listeners.
 */
function initUsersSidebar() {
    // Search input
    const searchInput = document.getElementById('usersSearch');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearchInput);
    }
    
    // Pagination buttons
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    
    if (prevBtn) prevBtn.addEventListener('click', handlePrevPage);
    if (nextBtn) nextBtn.addEventListener('click', handleNextPage);
}
