import { getApiUrl, getWsUrl, showNotification } from './utils/api.js';
import { escapeHtml } from './utils/text.js';
import { normalizeAvatarUrl, withAvatarCacheBuster } from './utils/avatar.js';

const app = window.BorofoneApp || {};
app.utils = {
    ...(app.utils || {}),
    getApiUrl,
    getWsUrl,
    showNotification,
    escapeHtml,
    normalizeAvatarUrl,
    withAvatarCacheBuster,
};
app.modules = app.modules || {};
app.meta = {
    ...(app.meta || {}),
    mode: 'legacy-bridge',
    entry: '/js/app/bootstrap.js',
};

window.BorofoneApp = app;

export { app };
