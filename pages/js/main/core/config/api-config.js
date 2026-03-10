// ==========================================
// API CONFIGURATION
// ==========================================

// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('[PWA] Service Worker зарегистрирован:', registration.scope);
            })
            .catch((error) => {
                console.error('[PWA] Ошибка регистрации Service Worker:', error);
            });
    });
}

// API_URL и WS_URL определяются в config.js
// Если config.js не загрузился, используем window.location.origin
function getApiUrl() {
    const sharedApiUrl = window.BorofoneApp?.utils?.getApiUrl;
    if (typeof sharedApiUrl === 'function') return sharedApiUrl();
    if (typeof API_URL !== 'undefined') return API_URL;
    return window.location.origin;
}

// Simple notification function (fallback if not defined elsewhere)
function showNotification(message, type = 'info') {
    const sharedNotify = window.BorofoneApp?.utils?.showNotification;
    if (typeof sharedNotify === 'function') {
        sharedNotify(message, type);
        return;
    }

    console.log(`[${type}] ${message}`);
    if (typeof window.createToast === 'function') {
        window.createToast(message, type);
    } else if (typeof window.showToast === 'function') {
        window.showToast(message, type);
    }
}

function getWsUrl() {
    const sharedWsUrl = window.BorofoneApp?.utils?.getWsUrl;
    if (typeof sharedWsUrl === 'function') return sharedWsUrl();
    if (typeof WS_URL !== 'undefined') return WS_URL;
    return window.location.origin.replace(/^http/, 'ws');
}
