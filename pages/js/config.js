// Определяем где мы — локально или через tunnel
const isLocalTunnel = window.location.hostname.includes('loca.lt');

// API URL
const API_URL = isLocalTunnel 
    ? window.location.origin  // https://borofone-chat.loca.lt
    : 'http://localhost:8000';

// WebSocket URL
const WS_URL = isLocalTunnel
    ? window.location.origin.replace('https://', 'wss://')  // wss://borofone-chat.loca.lt
    : 'ws://localhost:8000';

console.log('API URL:', API_URL);
console.log('WS URL:', WS_URL);