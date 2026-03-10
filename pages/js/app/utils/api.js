export function getApiUrl() {
    if (typeof window.API_URL !== 'undefined') return window.API_URL;
    return window.location.origin;
}

export function getWsUrl() {
    if (typeof window.WS_URL !== 'undefined') return window.WS_URL;
    return window.location.origin.replace(/^http/, 'ws');
}

export function showNotification(message, type = 'info') {
    console.log(`[${type}] ${message}`);
    if (typeof window.createToast === 'function') {
        window.createToast(message, type);
    } else if (typeof window.showToast === 'function') {
        window.showToast(message, type);
    }
}
