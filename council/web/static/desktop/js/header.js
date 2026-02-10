/**
 * Top bar: status polling, model dropdown, theme toggle.
 */
window.HeaderComponent = (() => {
    let statusDot, statusText, modelSelect, themeToggle;

    function init() {
        statusDot = document.getElementById('status-dot');
        statusText = document.getElementById('status-text');
        modelSelect = document.getElementById('model-select');
        themeToggle = document.getElementById('theme-toggle');

        themeToggle.addEventListener('click', () => {
            const newTheme = ThemeManager.toggle();
            updateThemeIcon(newTheme);
        });

        modelSelect.addEventListener('change', async () => {
            const model = modelSelect.value;
            if (!model) return;
            // Set the correct config key based on provider
            const provider = AppState.get('provider') || 'ollama';
            if (provider === 'anthropic') {
                await API.setConfig({ anthropic_model: model });
            } else {
                await API.setConfig({ model });
            }
            AppState.set('currentModel', model);
        });

        updateThemeIcon(ThemeManager.current());
        pollStatus();
        loadModels();
        setInterval(pollStatus, 30000);
    }

    function updateThemeIcon(theme) {
        const icon = themeToggle.querySelector('.theme-icon');
        icon.textContent = theme === 'dark' ? '☀' : '◑';
    }

    async function pollStatus() {
        try {
            const data = await API.checkStatus();
            if (data.ollama_available) {
                statusDot.className = 'status-dot connected';
                statusText.textContent = 'Connected';
                AppState.set('status', 'connected');
                AppState.set('currentModel', data.model);
            } else {
                statusDot.className = 'status-dot disconnected';
                statusText.textContent = data.message || 'Disconnected';
                AppState.set('status', 'disconnected');
            }
        } catch (e) {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'Connection error';
            AppState.set('status', 'disconnected');
        }
    }

    async function loadModels() {
        try {
            const data = await API.getModels();
            modelSelect.innerHTML = '';

            if (data.models && data.models.length > 0) {
                data.models.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = m;
                    if (m === data.current) opt.selected = true;
                    modelSelect.appendChild(opt);
                });
            } else {
                const opt = document.createElement('option');
                opt.value = data.current;
                opt.textContent = data.current;
                modelSelect.appendChild(opt);
            }
        } catch (e) {
            modelSelect.innerHTML = '<option>Error loading models</option>';
        }
    }

    /** Called by sidebar when provider changes — re-poll status and reload model list. */
    function refresh() {
        pollStatus();
        loadModels();
    }

    return { init, refresh };
})();
