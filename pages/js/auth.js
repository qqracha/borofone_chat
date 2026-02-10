// ==========================================
// API КОНФИГУРАЦИЯ
// ==========================================

function resolveApiBase() {
    const stored = localStorage.getItem('api_base');
    if (stored) return stored.replace(/\/$/, '');

    const url = new URL(window.location.href);

    if (url.protocol === 'file:') {
        return 'http://localhost:8000';
    }

    if (url.port && url.port !== '8000') {
        return `${url.protocol}//${url.hostname}:8000`;
    }

    return url.origin;
}

const API_URL = resolveApiBase();

// ==========================================
// УПРАВЛЕНИЕ ТОКЕНАМИ
// ==========================================

function storeTokens(data) {
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
}

// ==========================================
// ОБРАБОТКА ФОРМЫ ВХОДА
// ==========================================

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
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            errorText.textContent = data.detail || 'Ошибка входа';
            return;
        }

        storeTokens(data);
        window.location.href = './main.html';
    } catch (err) {
        errorText.textContent = 'Ошибка сети. Попробуйте позже.';
    }
});