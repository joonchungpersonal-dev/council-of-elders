window.ElderAvatars = (() => {
    const BUILTIN_IDS = new Set([
        'aurelius', 'franklin', 'buffett', 'munger', 'bruce_lee', 'musashi',
        'sun_tzu', 'buddha', 'branden', 'kabatzinn', 'clear', 'greene',
        'naval', 'rubin', 'oprah', 'thich', 'jung', 'laotzu', 'davinci',
        'kahneman', 'tubman', 'tetlock', 'klein', 'meadows', 'hannibal',
        'boudicca', 'genghis', 'lauder'
    ]);

    // Cache for wiki thumbnails (custom/nominated elders)
    const wikiCache = {};

    function getUrl(elderId, wikiThumbnail) {
        if (BUILTIN_IDS.has(elderId)) {
            return `/static/desktop/img/avatars/${elderId}.jpg`;
        }
        if (wikiThumbnail) return wikiThumbnail;
        if (wikiCache[elderId]) return wikiCache[elderId];
        return null;
    }

    function cacheWikiThumbnail(elderId, url) {
        if (url) wikiCache[elderId] = url;
    }

    function _esc(s) {
        const el = document.createElement('span');
        el.textContent = s;
        return el.innerHTML;
    }

    function initialHtml(name, color, size) {
        const initial = (name || '?')[0].toUpperCase();
        const sizeClass = size <= 24 ? 'sm' : size >= 56 ? 'lg' : 'md';
        return `<span class="elder-avatar-initial elder-avatar-initial--${sizeClass}" `
            + `style="background:${_esc(color)};width:${size}px;height:${size}px">`
            + `${_esc(initial)}</span>`;
    }

    function renderHtml(elderId, name, color, opts) {
        opts = opts || {};
        const size = opts.size || 32;
        const sizeClass = size <= 24 ? 'sm' : size >= 56 ? 'lg' : 'md';
        const url = getUrl(elderId, opts.wikiThumbnail);
        const fallback = initialHtml(name, color, size);

        if (!url) return fallback;

        // img with onerror fallback to initial
        return `<img class="elder-avatar elder-avatar--${sizeClass}" `
            + `src="${_esc(url)}" alt="${_esc(name)}" `
            + `width="${size}" height="${size}" `
            + `onerror="this.outerHTML=ElderAvatars.initialHtml('${_esc(name).replace(/'/g, "\\'")}','${_esc(color).replace(/'/g, "\\'")}',${size})">`;
    }

    return { BUILTIN_IDS, getUrl, cacheWikiThumbnail, initialHtml, renderHtml };
})();
