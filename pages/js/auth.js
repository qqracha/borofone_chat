const API_URL = window.getApiUrl ? window.getApiUrl() : window.location.origin;
const APP_ROUTES = window.getAppRoutes
    ? window.getAppRoutes()
    : { main: '/main.html' };

const loginForm = document.getElementById('loginForm');
const errorText = document.getElementById('errorText');

loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorText.textContent = '';

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            errorText.textContent = data.detail || 'Ошибка входа';
            return;
        }

        window.location.href = APP_ROUTES.main;
    } catch (err) {
        errorText.textContent = 'Ошибка сети. Попробуйте позже.';
    }
});
