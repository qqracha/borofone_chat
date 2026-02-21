// ==========================================
// NOTIFICATIONS & SOUNDS
// ==========================================

/**
 * Модуль уведомлений и звуков для чата.
 *
 * Функции:
 * - playNotificationSound() - воспроизведение звука при новом сообщении
 * - Хранение последнего прочитанного сообщения в localStorage
 * - Подсчёт и отображение непрочитанных сообщений (badge)
 */

// ── Audio Context ─────────────────────────────────────────────────
let notificationAudio = null;

function getNotificationAudio() {
    if (!notificationAudio) {
        notificationAudio = new Audio('/sounds/notification.mp3');
        notificationAudio.volume = 0.3; // 30% громкости
    }
    return notificationAudio;
}

// ── Notification Sound ────────────────────────────────────────────
/**
 * Воспроизводит звук уведомления.
 *
 * Использует mp3 файл из /sounds/notification.mp3
 */
function playNotificationSound() {
    try {
        const audio = getNotificationAudio();
        audio.currentTime = 0; // сброс на начало если уже играет
        audio.play().catch(err => {
            console.warn('[Notifications] Sound playback failed:', err);
        });
    } catch (err) {
        console.warn('[Notifications] Sound playback failed:', err);
    }
}

// ── Unread Messages Tracking ──────────────────────────────────────
/**
 * Хранит ID последнего прочитанного сообщения для каждой комнаты.
 *
 * Формат в localStorage:
 * {
 *   "lastReadMessage": {
 *     "1": 42,   // room_id: message_id
 *     "2": 13,
 *   }
 * }
 */

const STORAGE_KEY = 'lastReadMessage';

/**
 * Получить ID последнего прочитанного сообщения в комнате.
 */
function getLastReadMessageId(roomId) {
    try {
        const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        return data[roomId] || 0;
    } catch {
        return 0;
    }
}

/**
 * Сохранить ID последнего прочитанного сообщения в комнате.
 */
function setLastReadMessageId(roomId, messageId) {
    try {
        const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        data[roomId] = messageId;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (err) {
        console.warn('[Notifications] Failed to save last read message:', err);
    }
}

/**
 * Подсчитать количество непрочитанных сообщений в комнате.
 *
 * @param {Array} messages - массив сообщений комнаты (с полем id)
 * @param {number} roomId - ID комнаты
 * @returns {number} количество непрочитанных
 */
function countUnreadMessages(messages, roomId) {
    const lastRead = getLastReadMessageId(roomId);
    if (!lastRead) return 0;

    // Считаем сообщения с id > lastRead
    return messages.filter(msg => msg.id > lastRead).length;
}

/**
 * Отметить комнату как прочитанную (когда пользователь открыл её).
 *
 * @param {Array} messages - массив сообщений комнаты
 * @param {number} roomId - ID комнаты
 */
function markRoomAsRead(messages, roomId) {
    if (messages.length === 0) return;

    // Берём ID последнего сообщения
    const lastMessage = messages[messages.length - 1];
    setLastReadMessageId(roomId, lastMessage.id);
}

/**
 * Обновить badge (счётчик непрочитанных) на элементе комнаты.
 *
 * @param {HTMLElement} roomElement - элемент .room-item
 * @param {number} count - количество непрочитанных
 */
function updateRoomBadge(roomElement, count) {
    if (!roomElement) return;

    let badge = roomElement.querySelector('.unread-badge');

    if (count > 0) {
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'unread-badge';
            roomElement.appendChild(badge);
        }
        badge.textContent = count > 99 ? '99+' : count;
    } else {
        if (badge) badge.remove();
    }
}

// ── Export ────────────────────────────────────────────────────────
window.notifications = {
    playNotificationSound,
    getLastReadMessageId,
    setLastReadMessageId,
    countUnreadMessages,
    markRoomAsRead,
    updateRoomBadge,
};
