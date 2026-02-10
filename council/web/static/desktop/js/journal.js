/**
 * Wisdom Journal: persistent per-topic document that accumulates insights.
 * Sidebar list + slide-out viewer panel + post-discussion save prompt.
 */
window.JournalComponent = (() => {
    let journalList, journalPanel, journalPanelContent, journalPanelClose;
    let journals = [];

    function init() {
        journalList = document.getElementById('journal-list');
        journalPanel = document.getElementById('journal-panel');
        journalPanelContent = document.getElementById('journal-panel-content');
        journalPanelClose = document.getElementById('journal-panel-close');

        if (journalPanelClose) {
            journalPanelClose.addEventListener('click', closePanel);
        }

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && journalPanel && journalPanel.classList.contains('open')) {
                closePanel();
            }
        });

        loadJournals();
    }

    async function loadJournals() {
        try {
            journals = await API.getJournals();
            renderJournalList();
        } catch (e) {
            journals = [];
            renderJournalList();
        }
    }

    function renderJournalList() {
        if (!journalList) return;
        const section = document.getElementById('journal-section');

        if (journals.length === 0) {
            if (section) section.style.display = 'none';
            return;
        }

        if (section) section.style.display = '';
        journalList.innerHTML = '';

        journals.forEach(j => {
            const item = document.createElement('div');
            item.className = 'journal-item';
            item.innerHTML = `
                <span class="journal-item-title">${escapeHtml(j.title)}</span>
                <span class="journal-item-date">${j.updated || j.created || ''}</span>
                <button class="journal-item-delete" data-slug="${escapeHtml(j.slug)}" title="Delete journal">&times;</button>
            `;
            item.addEventListener('click', (e) => {
                if (e.target.closest('.journal-item-delete')) return;
                openJournal(j.slug);
            });
            journalList.appendChild(item);
        });

        // Wire delete buttons
        journalList.querySelectorAll('.journal-item-delete').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const slug = btn.dataset.slug;
                if (!confirm('Delete this journal?')) return;
                await API.deleteJournal(slug);
                loadJournals();
            });
        });
    }

    async function openJournal(slug) {
        if (!journalPanel || !journalPanelContent) return;

        journalPanelContent.innerHTML = '<div class="journal-loading">Loading...</div>';
        journalPanel.classList.add('open');

        try {
            const journal = await API.getJournal(slug);
            renderJournalContent(journal);
        } catch (e) {
            journalPanelContent.innerHTML = '<div class="journal-loading">Error loading journal.</div>';
        }
    }

    function renderJournalContent(journal) {
        if (!journalPanelContent) return;

        // Simple markdown-to-HTML rendering
        let html = journal.content || '';
        // Headers
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Blockquote
        html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
        // List items
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        // Wrap consecutive <li> in <ul>
        html = html.replace(/(<li>.*?<\/li>\n?)+/g, '<ul>$&</ul>');
        // Line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = '<p>' + html + '</p>';
        // Clean up empty paragraphs
        html = html.replace(/<p>\s*<\/p>/g, '');

        journalPanelContent.innerHTML = `
            <div class="journal-viewer">
                <div class="journal-viewer-actions">
                    <button class="journal-export-btn" title="Export as Markdown">Export .md</button>
                </div>
                <div class="journal-viewer-body">${html}</div>
            </div>
        `;

        // Wire export button
        const exportBtn = journalPanelContent.querySelector('.journal-export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                const blob = new Blob([journal.content], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${journal.slug}.md`;
                a.click();
                URL.revokeObjectURL(url);
            });
        }
    }

    function closePanel() {
        if (journalPanel) journalPanel.classList.remove('open');
    }

    /**
     * Show a "Save to Journal" prompt after a discussion ends.
     * @param {string} transcript - Raw text of the discussion
     * @param {string} topic - The original question
     * @returns {Promise} Resolves when the user saves or dismisses
     */
    function showSavePrompt(transcript, topic, onSave) {
        return new Promise((resolve) => {
            const chatMessages = document.getElementById('chat-messages');
            if (!chatMessages) { resolve(); return; }

            const msg = document.createElement('div');
            msg.className = 'message message-journal-prompt';
            msg.innerHTML = `
                <div class="journal-prompt-card">
                    <div class="journal-prompt-header">
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                            <path d="M2 2H10L14 6V14H2V2Z" stroke="currentColor" stroke-width="1.5" fill="none"/>
                            <path d="M10 2V6H14" stroke="currentColor" stroke-width="1.5"/>
                            <path d="M5 9H11M5 11.5H9" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>
                        </svg>
                        <span>Save insights to your Wisdom Journal?</span>
                    </div>
                    <div class="journal-prompt-body">
                        <select class="journal-prompt-select" id="journal-prompt-select">
                            <option value="">Select a journal...</option>
                            <option value="__new__">+ Create new journal</option>
                        </select>
                        <input type="text" class="journal-prompt-new-input" id="journal-prompt-new-input"
                            placeholder="New journal title..." style="display: none;">
                        <div class="journal-prompt-actions">
                            <button class="journal-prompt-save-btn" disabled>Save Insights</button>
                            <button class="journal-prompt-dismiss-btn">Dismiss</button>
                        </div>
                        <div class="journal-prompt-status" id="journal-prompt-status"></div>
                    </div>
                </div>
            `;
            chatMessages.appendChild(msg);

            const select = msg.querySelector('.journal-prompt-select');
            const newInput = msg.querySelector('.journal-prompt-new-input');
            const saveBtn = msg.querySelector('.journal-prompt-save-btn');
            const dismissBtn = msg.querySelector('.journal-prompt-dismiss-btn');
            const statusEl = msg.querySelector('.journal-prompt-status');

            // Populate existing journals
            journals.forEach(j => {
                const opt = document.createElement('option');
                opt.value = j.slug;
                opt.textContent = j.title;
                select.insertBefore(opt, select.lastElementChild);
            });

            select.addEventListener('change', () => {
                const val = select.value;
                newInput.style.display = val === '__new__' ? '' : 'none';
                saveBtn.disabled = !val || (val === '__new__' && !newInput.value.trim());
            });

            newInput.addEventListener('input', () => {
                saveBtn.disabled = !newInput.value.trim();
            });

            dismissBtn.addEventListener('click', () => {
                msg.remove();
                resolve();
            });

            saveBtn.addEventListener('click', async () => {
                saveBtn.disabled = true;
                saveBtn.textContent = 'Extracting insights...';
                statusEl.textContent = '';

                try {
                    // Extract insights via LLM
                    const extracted = await API.extractInsights(transcript, topic);

                    let slug = select.value;

                    // Create new journal if needed
                    if (slug === '__new__') {
                        const title = newInput.value.trim();
                        const meta = await API.createJournal(title);
                        slug = meta.slug;
                    }

                    // Append to journal
                    saveBtn.textContent = 'Saving...';
                    await API.appendToJournal(slug, extracted);

                    saveBtn.textContent = 'Saved!';
                    saveBtn.classList.add('journal-prompt-saved');
                    statusEl.textContent = `Insights saved to journal.`;

                    if (typeof onSave === 'function') onSave();

                    // Refresh journal list
                    loadJournals();

                    setTimeout(() => { msg.remove(); resolve(); }, 2000);
                } catch (e) {
                    saveBtn.textContent = 'Error';
                    statusEl.textContent = e.message || 'Failed to save';
                    saveBtn.disabled = false;
                }
            });

            // Scroll to the prompt
            if (typeof ChatComponent !== 'undefined') {
                ChatComponent.scrollToBottom();
            }
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    return { init, loadJournals, openJournal, closePanel, showSavePrompt };
})();
