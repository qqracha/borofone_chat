// ==========================================
// RATE LIMITING (Discord-like)
// ==========================================

const RATE_LIMIT_WINDOW_MS = 2000;    // 5 seconds window to detect rapid messages
const RATE_LIMIT_WARNING_THRESHOLD = 5;  // 3 messages in window triggers warning
const RATE_LIMIT_TIMEOUT_MS = 5000;     // 10 second timeout after exceeding limit

let messageTimestamps = [];  // Array of timestamps for recent messages
let isRateLimited = false;   // Whether user is currently rate limited
let rateLimitTimeout = null; // Timer for auto-clearing rate limit
let rateLimitWarningEl = null;  // Warning message DOM element
