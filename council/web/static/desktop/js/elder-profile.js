/**
 * Elder Profile Panel — slide-out drawer with Bio, Videos, Books, and Memorabilia tabs.
 */
window.ElderProfileComponent = (() => {

    let overlay, panel, headerEl, tabsEl, contentEl, ftcEl;
    let currentElder = null;
    const cache = {};  // elderId -> { bio, videos, books, memorabilia }
    const cacheOrder = [];  // LRU tracking: most recently accessed elder IDs
    const MAX_CACHE_SIZE = 10;

    function init() {
        // Create the overlay and panel DOM
        overlay = document.createElement('div');
        overlay.className = 'elder-profile-overlay';
        overlay.addEventListener('click', close);

        panel = document.createElement('div');
        panel.className = 'elder-profile-panel';
        panel.innerHTML = `
            <div class="profile-header">
                <div class="profile-thumb-placeholder" id="profile-thumb-area">?</div>
                <div class="profile-info">
                    <div class="profile-name" id="profile-name"></div>
                    <div class="profile-title" id="profile-title"></div>
                </div>
                <button class="profile-close-btn" id="profile-close-btn">&times;</button>
            </div>
            <div class="profile-tabs" id="profile-tabs">
                <button class="profile-tab active" data-tab="bio">Bio</button>
                <button class="profile-tab" data-tab="videos">Videos</button>
                <button class="profile-tab" data-tab="books">Books</button>
                <button class="profile-tab" data-tab="memorabilia">Memorabilia</button>
            </div>
            <div class="profile-tab-content" id="profile-tab-content">
                <div class="profile-tab-pane active" data-pane="bio" id="pane-bio">
                    <div class="profile-loading">Loading biography...</div>
                </div>
                <div class="profile-tab-pane" data-pane="videos" id="pane-videos">
                    <div class="profile-loading">Loading videos...</div>
                </div>
                <div class="profile-tab-pane" data-pane="books" id="pane-books">
                    <div class="profile-loading">Loading books...</div>
                </div>
                <div class="profile-tab-pane" data-pane="memorabilia" id="pane-memorabilia">
                    <div class="profile-loading">Loading memorabilia...</div>
                </div>
            </div>
            <div class="profile-ftc-disclosure">
                As an Amazon Associate, we earn from qualifying purchases.
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.appendChild(panel);

        headerEl = panel.querySelector('.profile-header');
        tabsEl = panel.querySelector('#profile-tabs');
        contentEl = panel.querySelector('#profile-tab-content');
        ftcEl = panel.querySelector('.profile-ftc-disclosure');

        // Close button
        panel.querySelector('#profile-close-btn').addEventListener('click', close);

        // Tab switching
        tabsEl.addEventListener('click', (e) => {
            const tab = e.target.closest('.profile-tab');
            if (!tab) return;
            const tabName = tab.dataset.tab;
            activateTab(tabName);
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && panel.classList.contains('open')) {
                close();
            }
        });
    }

    function open(elderData) {
        currentElder = elderData;
        const elderId = elderData.id;

        // Set header
        panel.querySelector('#profile-name').textContent = elderData.name || '';
        panel.querySelector('#profile-title').textContent =
            [elderData.title, elderData.era].filter(Boolean).join(' \u00b7 ');

        // Thumbnail — use static avatar for built-ins, then wiki, then initial
        const thumbArea = panel.querySelector('#profile-thumb-area');
        const avatarUrl = ElderAvatars.getUrl(elderId, elderData.thumbnail);
        if (avatarUrl) {
            thumbArea.outerHTML = `<img class="profile-thumb" id="profile-thumb-area" src="${_esc(avatarUrl)}" alt="${_esc(elderData.name)}" onerror="this.outerHTML='<div class=\\'profile-thumb-placeholder\\' id=\\'profile-thumb-area\\'>'+(this.alt||'?')[0].toUpperCase()+'</div>'">`;
        } else {
            const initial = (elderData.name || '?')[0].toUpperCase();
            thumbArea.outerHTML = `<div class="profile-thumb-placeholder" id="profile-thumb-area">${initial}</div>`;
        }

        // Reset all panes to loading
        contentEl.querySelectorAll('.profile-tab-pane').forEach(pane => {
            pane.innerHTML = '<div class="profile-loading">Loading...</div>';
        });

        // Activate Bio tab
        activateTab('bio');

        // Show
        overlay.classList.add('open');
        panel.classList.add('open');

        // Lazy-load bio tab
        loadTab('bio', elderId);
    }

    function openToTab(elderData, tabName) {
        open(elderData);
        activateTab(tabName);
    }

    function close() {
        overlay.classList.remove('open');
        panel.classList.remove('open');
        currentElder = null;
    }

    function activateTab(tabName) {
        tabsEl.querySelectorAll('.profile-tab').forEach(t =>
            t.classList.toggle('active', t.dataset.tab === tabName)
        );
        contentEl.querySelectorAll('.profile-tab-pane').forEach(p =>
            p.classList.toggle('active', p.dataset.pane === tabName)
        );

        // Lazy-load if not cached
        if (currentElder) {
            loadTab(tabName, currentElder.id);
        }
    }

    function _touchCache(elderId) {
        const idx = cacheOrder.indexOf(elderId);
        if (idx !== -1) cacheOrder.splice(idx, 1);
        cacheOrder.push(elderId);
        // Evict oldest if over limit
        while (cacheOrder.length > MAX_CACHE_SIZE) {
            const evicted = cacheOrder.shift();
            delete cache[evicted];
        }
    }

    function clearCache() {
        for (const key of Object.keys(cache)) delete cache[key];
        cacheOrder.length = 0;
    }

    function loadTab(tabName, elderId) {
        const cacheKey = elderId;
        if (!cache[cacheKey]) cache[cacheKey] = {};
        _touchCache(elderId);

        // Skip if already loaded
        if (cache[cacheKey][tabName]) {
            return;
        }

        const elder = currentElder;
        const name = elder.name || '';
        const expertise = elder.expertise || elder.title || '';

        switch (tabName) {
            case 'bio':
                loadBio(elderId, name, expertise);
                break;
            case 'videos':
                loadVideos(elderId, name, expertise);
                break;
            case 'books':
                loadBooks(elderId, name, expertise);
                break;
            case 'memorabilia':
                loadMemorabilia(elderId, name, expertise);
                break;
        }
    }

    async function loadBio(elderId, name, expertise) {
        const pane = contentEl.querySelector('#pane-bio');
        try {
            const bio = await API.getBiography(name, expertise);
            cache[elderId] = cache[elderId] || {};
            cache[elderId].bio = bio;

            // Cache wiki thumbnail for non-builtin elders and update if needed
            if (bio.thumbnail) {
                ElderAvatars.cacheWikiThumbnail(elderId, bio.thumbnail);
                if (currentElder && currentElder.id === elderId && !ElderAvatars.BUILTIN_IDS.has(elderId)) {
                    const thumbArea = panel.querySelector('#profile-thumb-area');
                    thumbArea.outerHTML = `<img class="profile-thumb" id="profile-thumb-area" src="${_esc(bio.thumbnail)}" alt="${_esc(name)}">`;
                }
                currentElder.thumbnail = bio.thumbnail;
            }

            let html = `<div class="profile-bio-text">${_esc(bio.summary || 'No biography available.')}</div>`;
            if (bio.url) {
                html += `<div class="profile-bio-source"><a href="${_esc(bio.url)}" target="_blank" rel="noopener">Wikipedia</a></div>`;
            } else if (bio.source === 'llm') {
                html += `<div class="profile-bio-source">AI-generated biography</div>`;
            }
            pane.innerHTML = html;
        } catch (e) {
            pane.innerHTML = '<div class="profile-loading">Could not load biography.</div>';
        }
    }

    async function loadVideos(elderId, name, expertise) {
        const pane = contentEl.querySelector('#pane-videos');
        try {
            const data = await API.getElderVideos(elderId, name, expertise);
            cache[elderId] = cache[elderId] || {};
            cache[elderId].videos = data;

            let html = '';

            // Show LLM error for documentaries if present
            if (data.error) {
                html += `<div class="profile-error">${_esc(data.error)}</div>`;
            }

            // YouTube videos
            if (data.youtube && data.youtube.length > 0) {
                html += '<div class="profile-video-section">';
                html += '<div class="profile-video-section-label">YouTube</div>';
                data.youtube.forEach(v => {
                    const duration = v.duration ? `${Math.floor(v.duration / 60)}:${String(v.duration % 60).padStart(2, '0')}` : '';
                    html += `
                        <div class="profile-video-item">
                            ${v.thumbnail ? `<img class="profile-video-thumb" src="${_esc(v.thumbnail)}" alt="">` : ''}
                            <div class="profile-video-info">
                                <a class="profile-video-title" href="${_esc(v.url)}" target="_blank" rel="noopener">${_esc(v.title)}</a>
                                <div class="profile-video-meta">${_esc(v.channel)}${duration ? ' \u00b7 ' + duration : ''}</div>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            // Documentaries
            if (data.documentaries && data.documentaries.length > 0) {
                html += '<div class="profile-video-section">';
                html += '<div class="profile-video-section-label">Documentaries & Lectures</div>';
                data.documentaries.forEach(d => {
                    html += `
                        <div class="profile-doc-item">
                            <a class="profile-doc-title" href="${_esc(d.amazon_url)}" target="_blank" rel="noopener">
                                ${_esc(d.title)}
                                <span class="profile-doc-badge">${_esc(d.type)}</span>
                            </a>
                            <div class="profile-doc-desc">${_esc(d.description)}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            if (!html) {
                html = '<div class="profile-loading">No videos found for this elder.</div>';
            }

            pane.innerHTML = html;
        } catch (e) {
            pane.innerHTML = e.message === 'Failed to fetch'
                ? '<div class="profile-error">Could not reach the server.</div>'
                : '<div class="profile-error">Something went wrong loading videos.</div>';
        }
    }

    async function loadBooks(elderId, name, expertise) {
        const pane = contentEl.querySelector('#pane-books');
        try {
            const data = await API.getElderBooks(elderId, name, expertise);
            cache[elderId] = cache[elderId] || {};
            cache[elderId].books = data;

            // Check for LLM error response
            if (data.error) {
                pane.innerHTML = `<div class="profile-error">${_esc(data.error)}</div>`;
                return;
            }

            const books = Array.isArray(data) ? data : (data.items || []);

            if (books.length === 0) {
                pane.innerHTML = '<div class="profile-loading">No books found.</div>';
                return;
            }

            const byBooks = books.filter(b => b.type === 'by');
            const aboutBooks = books.filter(b => b.type === 'about');
            let html = '';

            if (byBooks.length > 0) {
                html += `<div class="profile-books-section-label">Works by ${_esc(name)}</div>`;
                byBooks.forEach(b => { html += _bookHtml(b); });
            }
            if (aboutBooks.length > 0) {
                html += `<div class="profile-books-section-label">Books about ${_esc(name)}</div>`;
                aboutBooks.forEach(b => { html += _bookHtml(b); });
            }

            pane.innerHTML = html;
        } catch (e) {
            pane.innerHTML = e.message === 'Failed to fetch'
                ? '<div class="profile-error">Could not reach the server.</div>'
                : '<div class="profile-error">Something went wrong loading books.</div>';
        }
    }

    async function loadMemorabilia(elderId, name, expertise) {
        const pane = contentEl.querySelector('#pane-memorabilia');
        try {
            const data = await API.getElderMemorabilia(elderId, name, expertise);
            cache[elderId] = cache[elderId] || {};
            cache[elderId].memorabilia = data;

            // Check for LLM error response
            if (data.error) {
                pane.innerHTML = `<div class="profile-error">${_esc(data.error)}</div>`;
                return;
            }

            const items = Array.isArray(data) ? data : (data.items || []);

            if (items.length === 0) {
                pane.innerHTML = '<div class="profile-loading">No memorabilia found.</div>';
                return;
            }

            let html = '';
            items.forEach(item => {
                html += `
                    <div class="profile-memorabilia-item">
                        <div class="profile-memorabilia-header">
                            <a class="profile-memorabilia-title" href="${_esc(item.affiliate_url)}" target="_blank" rel="noopener">${_esc(item.title)}</a>
                            <span class="profile-memorabilia-category">${_esc(item.category)}</span>
                        </div>
                        <div class="profile-memorabilia-desc">${_esc(item.description)}</div>
                    </div>
                `;
            });

            pane.innerHTML = html;
        } catch (e) {
            pane.innerHTML = e.message === 'Failed to fetch'
                ? '<div class="profile-error">Could not reach the server.</div>'
                : '<div class="profile-error">Something went wrong loading memorabilia.</div>';
        }
    }

    function _bookHtml(book) {
        return `
            <div class="profile-book-item">
                <div class="profile-book-info">
                    <div class="profile-book-title">${_esc(book.title)}</div>
                    <div class="profile-book-author">by ${_esc(book.author)}</div>
                </div>
                <div class="profile-book-actions">
                    <a class="profile-book-link" href="${_esc(book.affiliate_url)}" target="_blank" rel="noopener">Amazon</a>
                    ${book.kindle_url ? `<a class="profile-book-link profile-book-link-kindle" href="${_esc(book.kindle_url)}" target="_blank" rel="noopener">Kindle</a>` : ''}
                </div>
            </div>
        `;
    }

    function _esc(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    return { init, open, openToTab, close, clearCache };
})();
