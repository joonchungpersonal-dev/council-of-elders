/**
 * Enrichment UI: background progress polling, toast notifications, re-engagement.
 */
window.EnrichmentComponent = (() => {

    const POLL_INTERVAL = 3000; // 3 seconds

    /**
     * Start enrichment for an elder and begin polling.
     */
    async function startEnrichment(elderId, name, expertise) {
        try {
            const resp = await API.startEnrichment(elderId, name, expertise);
            const taskId = resp.task_id;
            AppState.set('enrichmentTasks', {
                ...AppState.get('enrichmentTasks'),
                [elderId]: { taskId, status: 'running' },
            });

            // Show inline progress indicator
            const indicator = showProgressIndicator(name);

            // Start polling
            pollTaskStatus(taskId, indicator, elderId, name, expertise);

            return taskId;
        } catch (e) {
            console.error('Enrichment start failed:', e);
            return null;
        }
    }

    /**
     * Poll a background task until completion.
     */
    function pollTaskStatus(taskId, indicator, elderId, name, expertise) {
        const poll = async () => {
            try {
                const status = await API.getTaskStatus(taskId);

                // Update indicator
                if (indicator) {
                    updateProgressIndicator(indicator, status);
                }

                if (status.status === 'completed') {
                    // Update state
                    const tasks = { ...AppState.get('enrichmentTasks') };
                    tasks[elderId] = { taskId, status: 'completed', result: status.result };
                    AppState.set('enrichmentTasks', tasks);

                    // Show completion toast
                    showEnrichmentToast(name, elderId, expertise, status.result);

                    // Refresh custom elders sidebar
                    if (typeof SidebarComponent !== 'undefined') {
                        SidebarComponent.loadCustomElders();
                    }

                    return; // Stop polling
                }

                if (status.status === 'failed') {
                    if (indicator) {
                        indicator.querySelector('.enrichment-progress-text').textContent =
                            `Enrichment failed: ${status.error || 'unknown error'}`;
                        indicator.querySelector('.enrichment-progress-bar-fill').style.background = '#ef4444';
                    }
                    return; // Stop polling
                }

                // Continue polling
                setTimeout(poll, POLL_INTERVAL);
            } catch (e) {
                // Retry on network errors
                setTimeout(poll, POLL_INTERVAL * 2);
            }
        };

        setTimeout(poll, POLL_INTERVAL);
    }

    /**
     * Show an inline progress indicator in the chat.
     */
    function showProgressIndicator(name) {
        const el = document.createElement('div');
        el.className = 'message message-enrichment-progress';
        el.innerHTML = `
            <div class="enrichment-progress-card">
                <div class="enrichment-progress-header">
                    <span class="enrichment-spinner"></span>
                    <span class="enrichment-progress-text">Researching ${_esc(name)} in background...</span>
                </div>
                <div class="enrichment-progress-bar">
                    <div class="enrichment-progress-bar-fill" style="width: 5%"></div>
                </div>
                <div class="enrichment-substeps"></div>
            </div>
        `;

        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.appendChild(el);
            ChatComponent.scrollToBottom();
        }

        return el;
    }

    /**
     * Update the progress indicator with new task status.
     */
    function updateProgressIndicator(el, status) {
        const textEl = el.querySelector('.enrichment-progress-text');
        const fillEl = el.querySelector('.enrichment-progress-bar-fill');
        const substepsEl = el.querySelector('.enrichment-substeps');

        if (textEl) textEl.textContent = status.message || 'Working...';
        if (fillEl) fillEl.style.width = Math.round((status.progress || 0) * 100) + '%';

        if (substepsEl && status.substeps && status.substeps.length > 0) {
            substepsEl.innerHTML = status.substeps
                .map(s => {
                    const icon = s.status === 'done' ? '&check;' :
                        s.status === 'running' ? '&bull;' :
                        s.status.startsWith('skipped') ? '&ndash;' :
                        s.status.startsWith('failed') || s.status.startsWith('error') ? '&times;' : '&bull;';
                    const cls = s.status === 'done' ? 'done' :
                        s.status === 'running' ? 'running' : 'other';
                    const label = s.title || s.step || '';
                    return `<span class="enrichment-substep enrichment-substep-${cls}">${icon} ${_esc(label)}</span>`;
                })
                .join('');
        }

        if (status.status === 'completed') {
            el.querySelector('.enrichment-spinner')?.classList.add('enrichment-spinner-done');
            if (textEl) textEl.textContent = status.message || 'Complete';
        }
    }

    /**
     * Show a toast notification when enrichment completes.
     */
    function showEnrichmentToast(name, elderId, expertise, result) {
        const toast = document.createElement('div');
        toast.className = 'enrichment-toast';

        let detailText = '';
        if (result) {
            const parts = [];
            if (result.youtube_transcripts) parts.push(`${result.youtube_transcripts} videos`);
            if (result.books_discovered) parts.push(`${result.books_discovered} books`);
            if (parts.length) detailText = ` (${parts.join(', ')})`;
        }

        toast.innerHTML = `
            <div class="enrichment-toast-content">
                <span class="enrichment-toast-icon">&check;</span>
                <span>${_esc(name)}'s knowledge is now enriched${_esc(detailText)}</span>
            </div>
            <div class="enrichment-toast-actions">
                <button class="enrichment-toast-btn enrichment-reengage-btn">Re-engage with enriched knowledge</button>
                <button class="enrichment-toast-btn enrichment-books-btn">View Books</button>
            </div>
        `;

        document.body.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add('enrichment-toast-visible'));

        // Auto-dismiss after 15s
        const dismissTimer = setTimeout(() => dismissToast(toast), 15000);

        // Re-engage button
        toast.querySelector('.enrichment-reengage-btn')?.addEventListener('click', () => {
            clearTimeout(dismissTimer);
            dismissToast(toast);
            // The user can simply ask a new question -- the enriched knowledge
            // is automatically picked up by ChromaDB/file-based retrieval.
            ChatComponent.addSystemMessage(
                `${name}'s knowledge has been enriched with YouTube transcripts. ` +
                `Ask a new question to engage with their enhanced perspective.`
            );
        });

        // Books button
        toast.querySelector('.enrichment-books-btn')?.addEventListener('click', async () => {
            clearTimeout(dismissTimer);
            dismissToast(toast);
            try {
                const books = await API.getElderBooks(elderId, name, expertise);
                ChatComponent.showBookRecommendations({ name, id: elderId }, books);
            } catch (e) {
                ChatComponent.addSystemMessage('Could not load book recommendations.');
            }
        });
    }

    function dismissToast(el) {
        el.classList.remove('enrichment-toast-visible');
        setTimeout(() => el.remove(), 300);
    }

    function _esc(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    return { startEnrichment };
})();
