const loadedScripts = new Map();

export function loadClassicScript(src) {
    if (loadedScripts.has(src)) return loadedScripts.get(src);

    const promise = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.async = false;
        script.onload = () => resolve(src);
        script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
        document.body.appendChild(script);
    });

    loadedScripts.set(src, promise);
    return promise;
}

export async function loadScriptsSequentially(scripts) {
    for (const src of scripts) {
        await loadClassicScript(src);
    }
}
