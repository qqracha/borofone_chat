export function normalizeAvatarUrl(url) {
    if (!url) return null;
    if (/^(https?:)?\/\//.test(url) || url.startsWith('data:')) return url;
    return url.startsWith('/') ? url : `/${url}`;
}

export function withAvatarCacheBuster(url, userId, stamp = Date.now()) {
    if (!url) return null;
    const cacheKey = userId ? `${userId}-${stamp}` : String(stamp);
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}v=${cacheKey}`;
}
