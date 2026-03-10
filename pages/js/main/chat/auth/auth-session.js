// ==========================================
// AUTH FUNCTIONS
// ==========================================

function redirectToLogin() {
    window.location.href = getAppRoutes().login;
}

async function fetchWithAuth(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
            ...(options.headers || {}),
        }
    });

    if (response.status === 401) {
        const refreshed = await refreshAccessToken();
        if (!refreshed) {
            redirectToLogin();
            return response;
        }

        return fetch(url, {
            ...options,
            credentials: 'include',
            headers: {
                ...(options.headers || {}),
            }
        });
    }

    return response;
}

async function refreshAccessToken() {
    try {
        const response = await fetch(`${getApiUrl()}/auth/refresh`, {
            method: 'POST',
            credentials: 'include'
        });

        if (response.ok) {
            console.log('Access token refreshed');
            return true;
        }

        return false;
    } catch (err) {
        console.error('Failed to refresh token:', err);
        return false;
    }
}

async function loadCurrentUser() {
    try {
        const response = await fetchWithAuth(`${getApiUrl()}/auth/me`);

        if (!response.ok) {
            redirectToLogin();
            return;
        }

        currentUser = await response.json();
        renderCurrentUser();
        console.log('Logged in as:', currentUser.username);
    } catch (err) {
        console.error('Failed to load user:', err);
        redirectToLogin();
    }
}
