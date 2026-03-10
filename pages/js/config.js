// Runtime config comes from /app-config.js. Fall back to the current origin for local static usage.
(function bootstrapConfig() {
    const runtime = window.__BOROFONE_RUNTIME_CONFIG__ || {};
    const routes = runtime.routes || {};

    function normalizeBaseUrl(rawUrl) {
        return typeof rawUrl === 'string' ? rawUrl.replace(/\/$/, '') : '';
    }

    function resolveApiUrl() {
        const configured = normalizeBaseUrl(runtime.apiUrl);
        if (configured) {
            return configured;
        }

        if (window.location.protocol === 'file:') {
            return 'http://localhost:8000';
        }

        return window.location.origin;
    }

    function resolveWsUrl(apiUrl) {
        const configured = normalizeBaseUrl(runtime.wsUrl);
        if (configured) {
            return configured;
        }

        return apiUrl.replace(/^http/, 'ws');
    }

    const apiUrl = resolveApiUrl();
    const wsUrl = resolveWsUrl(apiUrl);

    window.BOROFONE_CONFIG = Object.freeze({
        apiUrl,
        wsUrl,
        routes: {
            main: routes.main || '/main.html',
            login: routes.login || '/login.html',
            register: routes.register || '/register.html',
        },
        uploads: {
            avatarsBasePath: runtime.uploads?.avatarsBasePath || '/uploads/avatars',
            attachmentsBasePath: runtime.uploads?.attachmentsBasePath || '/uploads/attachments',
        },
    });

    window.API_URL = apiUrl;
    window.WS_URL = wsUrl;
    window.getApiUrl = () => window.BOROFONE_CONFIG.apiUrl;
    window.getWsUrl = () => window.BOROFONE_CONFIG.wsUrl;
    window.getAppRoutes = () => window.BOROFONE_CONFIG.routes;
})();
