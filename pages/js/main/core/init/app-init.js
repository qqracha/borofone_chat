// ==========================================
// INITIALIZATION
// ==========================================

async function init() {
    // Инициализируем тему
    initTheme();
    initDiscordTooltips();
    completeLoadingTask('Стили');
    
    await loadCurrentUser();
    completeLoadingTask('Конфигурация');
    
    await loadRooms();
    completeLoadingTask('Интерфейс');
    
    await loadVoiceRooms();
    
    // Подключаемся к глобальному WebSocket ОДИН РАЗ
    connectWebSocket();
    completeLoadingTask('Подключение');
    
    // Add click listener for connection stats popup
    if (connectionStatus) {
        connectionStatus.addEventListener('click', toggleConnectionStatsPopup);
    }
    
    // Инициализируем сайдбар пользователей
    initUsersSidebar();
    
    // Инициализируем emoji picker
    initEmojiPicker();
    
    // Инициализируем Twemoji для Discord-подобных эмодзи
    if (typeof twemoji !== 'undefined') {
        twemoji.parse(document.body, {
            base: 'https://twemoji.maxcdn.com/v/latest/',
            ext: '.svg',
            size: '36x36'
        });
    }
    
    // Глобальный keyboard shortcut для открытия emoji picker
    document.addEventListener('keydown', (e) => {
        // Ctrl+E or Cmd+E anywhere to open emoji picker
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'e') {
            // Don't interfere if user is typing in an input
            const target = e.target;
            const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;
            
            if (isInput && target.id !== 'emojiSearch') {
                // If in message input, just prevent default and toggle
                e.preventDefault();
            }
            toggleEmojiPicker();
        }
    });
    
    // Ждём подключения WebSocket перед скрытием экрана загрузки
    // Добавляем safety timeout на случай, если WebSocket не подключится
    const loadingTimeout = setTimeout(() => {
        console.warn('[Loading] Timeout waiting for WebSocket, proceeding anyway');
        hideLoadingScreen();
    }, 15000); // Максимум 15 секунд ожидания
    
    wsReady.then(() => {
        clearTimeout(loadingTimeout);
        // Скрываем экран загрузки только после подключения WebSocket
        hideLoadingScreen();
    });
}

// Инициализируем экран загрузки
initLoadingScreen();
