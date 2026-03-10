// ==========================================
// LOADING SCREEN
// ==========================================

let loadingTasks = [];
let loadingCompleted = 0;
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingProgressBar = document.getElementById('loadingProgressBar');
const loadingStatus = document.getElementById('loadingStatus');

function updateLoadingProgress(status, progress = null) {
    if (loadingStatus) {
        loadingStatus.textContent = status;
    }
    if (progress !== null && loadingProgressBar) {
        loadingProgressBar.style.width = progress + '%';
    }
}

function addLoadingTask(name) {
    loadingTasks.push(name);
    updateLoadingProgress(name, Math.round((loadingCompleted / (loadingTasks.length + 1)) * 100));
}

function completeLoadingTask(name) {
    loadingCompleted++;
    const progress = Math.round((loadingCompleted / loadingTasks.length) * 100);
    updateLoadingProgress('Загрузка завершена', progress);
}

function hideLoadingScreen() {
    if (loadingOverlay) {
        updateLoadingProgress('Добро пожаловать!', 100);
        // Ждём немного, чтобы пользователь увидел 100% загрузку
        setTimeout(() => {
            loadingOverlay.classList.add('hidden');
            setTimeout(() => {
                if (loadingOverlay.parentNode) {
                    loadingOverlay.parentNode.removeChild(loadingOverlay);
                }
            }, 700);
        }, 600);
    }
}

// Инициализация экрана загрузки
function initLoadingScreen() {
    // Добавляем задачи загрузки
    addLoadingTask('Загрузка стилей');
    addLoadingTask('Загрузка конфигурации');
    addLoadingTask('Загрузка интерфейса');
    addLoadingTask('Подключение к серверу');
    
    // Скрываем экран загрузки при ошибке window.onerror
    window.onerror = function(msg, url, lineNo, columnNo, error) {
        console.error('Ошибка:', msg, 'на строке', lineNo);
        completeLoadingTask('Ошибка загрузки');
        hideLoadingScreen();
        return false;
    };
}
