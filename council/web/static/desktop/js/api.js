/**
 * All Flask API calls + SSE streaming helpers.
 */
window.API = (() => {

    async function fetchJSON(url, options = {}) {
        const resp = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ error: resp.statusText }));
            throw new Error(err.error || resp.statusText);
        }
        return resp.json();
    }

    function checkStatus() {
        return fetchJSON('/api/status');
    }

    function getElders() {
        return fetchJSON('/api/elders');
    }

    function getModels() {
        return fetchJSON('/api/models');
    }

    function getConfig() {
        return fetchJSON('/api/config');
    }

    function setConfig(data) {
        return fetchJSON('/api/config', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    function getHistory(limit = 20) {
        return fetchJSON(`/api/history?limit=${limit}`);
    }

    function clearHistory() {
        return fetchJSON('/api/history/clear', { method: 'POST' });
    }

    async function generatePodcast(segments) {
        const resp = await fetch('/api/podcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ segments }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ error: resp.statusText }));
            throw new Error(err.error || resp.statusText);
        }
        return resp.blob();
    }

    function pullOllamaModel(modelName) {
        return fetch('/api/ollama/pull', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: modelName }),
        });
    }

    /**
     * Parse an SSE stream and yield parsed JSON events.
     * Usage: for await (const data of streamSSE(response)) { ... }
     */
    async function* streamSSE(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                // Keep the last potentially incomplete line in the buffer
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            yield JSON.parse(line.slice(6));
                        } catch (e) {
                            // Skip malformed JSON
                        }
                    }
                }
            }
            // Process any remaining buffer
            if (buffer.startsWith('data: ')) {
                try {
                    yield JSON.parse(buffer.slice(6));
                } catch (e) {}
            }
        } finally {
            reader.releaseLock();
        }
    }

    /**
     * Start an SSE request and return the response for streaming.
     * Pass an AbortController signal to allow cancellation.
     */
    let _currentAbort = null;
    function startStream(endpoint, body) {
        _currentAbort = new AbortController();
        return fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            signal: _currentAbort.signal,
        });
    }

    function abortStream() {
        if (_currentAbort) {
            _currentAbort.abort();
            _currentAbort = null;
        }
    }

    // --- Auto-select Elders ---

    function autoSelectElders(question, maxElders) {
        return fetchJSON('/api/select-elders', {
            method: 'POST',
            body: JSON.stringify({ question, max_elders: maxElders || 5 }),
        });
    }

    function selectMode(question) {
        return fetchJSON('/api/select-mode', {
            method: 'POST',
            body: JSON.stringify({ question }),
        });
    }

    // --- Journals ---

    function getJournals() {
        return fetchJSON('/api/journals');
    }

    function getJournal(slug) {
        return fetchJSON(`/api/journals/${encodeURIComponent(slug)}`);
    }

    function createJournal(title) {
        return fetchJSON('/api/journals', {
            method: 'POST',
            body: JSON.stringify({ title }),
        });
    }

    function appendToJournal(slug, entry) {
        return fetchJSON(`/api/journals/${encodeURIComponent(slug)}/append`, {
            method: 'POST',
            body: JSON.stringify(entry),
        });
    }

    function deleteJournal(slug) {
        return fetchJSON(`/api/journals/${encodeURIComponent(slug)}`, {
            method: 'DELETE',
        });
    }

    function extractInsights(transcript, topic) {
        return fetchJSON('/api/journals/extract', {
            method: 'POST',
            body: JSON.stringify({ transcript, topic }),
        });
    }

    // --- Custom Elders ---

    function getCustomElders() {
        return fetchJSON('/api/custom-elders');
    }

    function saveCustomElder(elderData) {
        return fetchJSON('/api/custom-elders', {
            method: 'POST',
            body: JSON.stringify(elderData),
        });
    }

    function deleteCustomElder(elderId) {
        return fetchJSON(`/api/custom-elders/${encodeURIComponent(elderId)}`, {
            method: 'DELETE',
        });
    }

    // --- Background Tasks ---

    function getTaskStatus(taskId) {
        return fetchJSON(`/api/tasks/${encodeURIComponent(taskId)}`);
    }

    // --- Enrichment ---

    function startEnrichment(elderId, name, expertise) {
        return fetchJSON('/api/enrich', {
            method: 'POST',
            body: JSON.stringify({ elder_id: elderId, name, expertise }),
        });
    }

    // --- Books ---

    function getElderBooks(elderId, name, expertise) {
        const params = new URLSearchParams();
        if (name) params.set('name', name);
        if (expertise) params.set('expertise', expertise);
        return fetchJSON(`/api/elder/${encodeURIComponent(elderId)}/books?${params}`);
    }

    // --- Videos ---

    function getElderVideos(elderId, name, expertise) {
        const params = new URLSearchParams();
        if (name) params.set('name', name);
        if (expertise) params.set('expertise', expertise);
        return fetchJSON(`/api/elder/${encodeURIComponent(elderId)}/videos?${params}`);
    }

    // --- Memorabilia ---

    function getElderMemorabilia(elderId, name, expertise) {
        const params = new URLSearchParams();
        if (name) params.set('name', name);
        if (expertise) params.set('expertise', expertise);
        return fetchJSON(`/api/elder/${encodeURIComponent(elderId)}/memorabilia?${params}`);
    }

    // --- Biography ---

    function getBiography(name, expertise) {
        const params = new URLSearchParams({ name });
        if (expertise) params.set('expertise', expertise);
        return fetchJSON(`/api/biography?${params}`);
    }

    // --- Kindle Import ---

    async function importKindleFile(file, elderId) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('elder_id', elderId);
        const resp = await fetch('/api/kindle/import', {
            method: 'POST',
            body: formData,
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ error: resp.statusText }));
            throw new Error(err.error || resp.statusText);
        }
        return resp.json();
    }

    return {
        checkStatus, getElders, getModels, getConfig, setConfig,
        getHistory, clearHistory, generatePodcast, pullOllamaModel,
        streamSSE, startStream, abortStream, autoSelectElders, selectMode,
        getJournals, getJournal, createJournal, appendToJournal, deleteJournal, extractInsights,
        getCustomElders, saveCustomElder, deleteCustomElder,
        getTaskStatus, startEnrichment,
        getElderBooks, getElderVideos, getElderMemorabilia,
        getBiography, importKindleFile,
    };
})();
