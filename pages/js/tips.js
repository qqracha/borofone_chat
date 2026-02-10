// ==========================================
// ЖИВЫЕ ПОДСКАЗКИ
// ==========================================

const tips = [
    'Используйте надёжный пароль длиной не менее 12 символов',
    'Включите двухфакторную аутентификацию для защиты аккаунта',
    'QR-код обновляется каждые 30 секунд для безопасности',
    'Вы можете войти с любого устройства синхронизированно',
    'Настройте тему интерфейса в личном кабинете'
];

let currentTipIndex = 0;
let tipTimeout;

// ==========================================
// ПОКАЗАТЬ ПОДСКАЗКУ
// ==========================================

function showTip() {
    const tipCard = document.getElementById('tipCard');
    const tipContent = document.getElementById('tipContent');
    const tipProgress = document.getElementById('tipProgress');

    // Устанавливаем контент
    tipContent.textContent = tips[currentTipIndex];

    // Показываем плавно
    tipCard.classList.remove('hide');
    tipCard.classList.add('show');

    // Запускаем прогресс бар
    tipProgress.classList.remove('animate');
    void tipProgress.offsetWidth; // Force reflow
    tipProgress.classList.add('animate');

    // Через 15 секунд прячем
    tipTimeout = setTimeout(() => {
        hideTip();
    }, 15000);
}

// ==========================================
// СКРЫТЬ ПОДСКАЗКУ
// ==========================================

function hideTip() {
    const tipCard = document.getElementById('tipCard');
    const tipProgress = document.getElementById('tipProgress');

    // Прячем плавно
    tipCard.classList.remove('show');
    tipCard.classList.add('hide');

    // Останавливаем прогресс бар
    tipProgress.classList.remove('animate');

    // Через 500ms показываем следующий
    setTimeout(() => {
        currentTipIndex = (currentTipIndex + 1) % tips.length;
        // Пауза 3 секунды перед следующим тип
        setTimeout(() => {
            showTip();
        }, 3000);
    }, 500);
}

// ==========================================
// ИНИЦИАЛИЗАЦИЯ
// ==========================================

// Показываем первый тип через 2 секунды после загрузки
setTimeout(() => {
    showTip();
}, 2000);