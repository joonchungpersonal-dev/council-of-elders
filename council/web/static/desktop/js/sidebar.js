/**
 * Sidebar: provider selector, mode selector, elder checkboxes, session history.
 */
window.SidebarComponent = (() => {
    let modeSelector, elderList, historyList, newChatBtn, clearHistoryBtn;
    let providerSelector;
    let anthropicKeyRow, anthropicKeyInput, anthropicKeySave;
    let openaiKeyRow, openaiKeyInput, openaiKeySave;
    let googleKeyRow, googleKeyInput, googleKeySave;
    let modelPullRow, modelPullInput, modelPullBtn, pullProgress, pullProgressFill, pullProgressText;
    let discussionStyleSection, tensionSlider;
    let customEldersSection, customElderList;
    let autoSelectCheckbox;
    let ttsProviderSelector, elevenlabsSettings, elevenlabsKeyInput, elevenlabsKeySave, elevenlabsModelSelect;
    let responseLengthSelect, discussionLengthSelect, autoSelectLimitSelect, autoSelectLimitRow;
    let poetryFormSelect, poetryFormRow;
    let settingsOverlay, settingsGearBtn, settingsModalClose, durationRow;
    let addElderBtn, addElderOverlay, addElderForm, addElderModalClose;
    let showAllModesCheckbox, modeSimple, modeAll;

    function init() {
        modeSelector = document.getElementById('mode-selector');
        elderList = document.getElementById('elder-list');
        historyList = document.getElementById('history-list');
        newChatBtn = document.getElementById('btn-new-chat');
        clearHistoryBtn = document.getElementById('btn-clear-history');
        providerSelector = document.getElementById('provider-selector');
        anthropicKeyRow = document.getElementById('anthropic-key-row');
        anthropicKeyInput = document.getElementById('anthropic-key-input');
        anthropicKeySave = document.getElementById('anthropic-key-save');
        openaiKeyRow = document.getElementById('openai-key-row');
        openaiKeyInput = document.getElementById('openai-key-input');
        openaiKeySave = document.getElementById('openai-key-save');
        googleKeyRow = document.getElementById('google-key-row');
        googleKeyInput = document.getElementById('google-key-input');
        googleKeySave = document.getElementById('google-key-save');
        modelPullRow = document.getElementById('model-pull-row');
        modelPullInput = document.getElementById('model-pull-input');
        modelPullBtn = document.getElementById('model-pull-btn');
        pullProgress = document.getElementById('pull-progress');
        pullProgressFill = document.getElementById('pull-progress-fill');
        pullProgressText = document.getElementById('pull-progress-text');

        discussionStyleSection = document.getElementById('discussion-style-section');
        tensionSlider = document.getElementById('tension-slider');

        // Tension slider
        tensionSlider.addEventListener('input', (e) => {
            AppState.set('dialecticTension', parseInt(e.target.value, 10));
        });

        // Show/hide slider based on mode
        const modesWithSlider = ['panel', 'salon'];
        AppState.on('mode', (mode) => {
            discussionStyleSection.style.display = modesWithSlider.includes(mode) ? 'block' : 'none';
        });

        // Initialize slider visibility
        const initialMode = AppState.get('mode');
        discussionStyleSection.style.display =
            modesWithSlider.includes(initialMode) ? 'block' : 'none';

        // Provider buttons
        providerSelector.addEventListener('click', (e) => {
            const btn = e.target.closest('.mode-btn');
            if (!btn) return;
            providerSelector.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const provider = btn.dataset.provider;
            switchProvider(provider);
        });

        // API key save — per-provider
        wireKeySave(anthropicKeyInput, anthropicKeySave, 'anthropic_api_key');
        wireKeySave(openaiKeyInput, openaiKeySave, 'openai_api_key');
        wireKeySave(googleKeyInput, googleKeySave, 'google_api_key');

        // Model pull
        modelPullBtn.addEventListener('click', pullModel);
        modelPullInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') pullModel();
        });

        // Mode buttons
        modeSelector.addEventListener('click', (e) => {
            const btn = e.target.closest('.mode-btn');
            if (!btn) return;
            modeSelector.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            AppState.set('mode', btn.dataset.mode);
        });

        // Elder checkboxes
        elderList.addEventListener('change', updateSelectedElders);

        // Elder name click → open profile panel
        elderList.addEventListener('click', (e) => {
            const nameEl = e.target.closest('.elder-name');
            if (!nameEl) return;
            // Don't open profile when clicking checkbox
            if (e.target.tagName === 'INPUT') return;
            e.preventDefault();
            e.stopPropagation();

            const item = nameEl.closest('.elder-item');
            if (!item) return;
            const elderId = item.dataset.elderId;
            const elderData = (window.__ELDERS__ || []).find(el => el.id === elderId);
            if (elderData && typeof ElderProfileComponent !== 'undefined') {
                ElderProfileComponent.open(elderData);
            }
        });

        // New chat button
        newChatBtn.addEventListener('click', () => {
            if (typeof App !== 'undefined' && App.newChat) {
                App.newChat();
            }
        });

        // Clear history button
        clearHistoryBtn.addEventListener('click', async () => {
            if (!confirm('Clear all session history?')) return;
            await API.clearHistory();
            loadHistory();
        });

        customEldersSection = document.getElementById('custom-elders-section');
        customElderList = document.getElementById('custom-elder-list');

        autoSelectCheckbox = document.getElementById('auto-select-checkbox');
        if (autoSelectCheckbox) {
            autoSelectCheckbox.addEventListener('change', () => {
                AppState.set('autoSelectElders', autoSelectCheckbox.checked);
            });
        }

        // TTS provider
        ttsProviderSelector = document.getElementById('tts-provider-selector');
        elevenlabsSettings = document.getElementById('elevenlabs-settings');
        elevenlabsKeyInput = document.getElementById('elevenlabs-key-input');
        elevenlabsKeySave = document.getElementById('elevenlabs-key-save');
        elevenlabsModelSelect = document.getElementById('elevenlabs-model-select');

        if (ttsProviderSelector) {
            ttsProviderSelector.addEventListener('click', (e) => {
                const btn = e.target.closest('.mode-btn');
                if (!btn) return;
                ttsProviderSelector.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                switchTTSProvider(btn.dataset.tts);
            });
        }

        if (elevenlabsKeySave) {
            elevenlabsKeySave.addEventListener('click', saveElevenLabsKey);
            elevenlabsKeyInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') saveElevenLabsKey();
            });
        }

        if (elevenlabsModelSelect) {
            elevenlabsModelSelect.addEventListener('change', () => {
                API.setConfig({ elevenlabs_model: elevenlabsModelSelect.value });
            });
        }

        // Settings controls
        responseLengthSelect = document.getElementById('response-length-select');
        discussionLengthSelect = document.getElementById('discussion-length-select');
        autoSelectLimitSelect = document.getElementById('auto-select-limit-select');
        autoSelectLimitRow = document.getElementById('auto-select-limit-row');

        if (responseLengthSelect) {
            responseLengthSelect.addEventListener('change', () => {
                AppState.set('responseLength', responseLengthSelect.value);
            });
        }

        if (discussionLengthSelect) {
            discussionLengthSelect.addEventListener('change', () => {
                AppState.set('discussionLength', discussionLengthSelect.value);
            });
        }

        if (autoSelectLimitSelect) {
            autoSelectLimitSelect.addEventListener('change', () => {
                AppState.set('autoSelectLimit', parseInt(autoSelectLimitSelect.value, 10));
            });
        }

        poetryFormSelect = document.getElementById('poetry-form-select');
        poetryFormRow = document.getElementById('poetry-form-row');

        if (poetryFormSelect) {
            poetryFormSelect.addEventListener('change', () => {
                AppState.set('poetryForm', poetryFormSelect.value);
            });
        }

        // Show/hide poetry form based on mode
        if (poetryFormRow) {
            AppState.on('mode', (mode) => {
                poetryFormRow.style.display = mode === 'poetry' ? 'flex' : 'none';
            });
        }

        // Show/hide auto-select limit based on auto-select checkbox
        if (autoSelectCheckbox && autoSelectLimitRow) {
            autoSelectLimitRow.style.display = autoSelectCheckbox.checked ? 'flex' : 'none';
            autoSelectCheckbox.addEventListener('change', () => {
                autoSelectLimitRow.style.display = autoSelectCheckbox.checked ? 'flex' : 'none';
            });
        }

        // Settings modal
        settingsOverlay = document.getElementById('settings-overlay');
        settingsGearBtn = document.getElementById('settings-gear-btn');
        settingsModalClose = document.getElementById('settings-modal-close');
        durationRow = document.getElementById('duration-row');

        if (settingsGearBtn && settingsOverlay) {
            settingsGearBtn.addEventListener('click', () => {
                settingsOverlay.classList.add('open');
            });
            settingsModalClose.addEventListener('click', () => {
                settingsOverlay.classList.remove('open');
            });
            // Close on overlay background click
            settingsOverlay.addEventListener('click', (e) => {
                if (e.target === settingsOverlay) {
                    settingsOverlay.classList.remove('open');
                }
            });
            // Close on Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && settingsOverlay.classList.contains('open')) {
                    settingsOverlay.classList.remove('open');
                }
            });
        }

        // Contextual visibility: hide Duration for ask/intake modes
        const modesWithDuration = ['panel', 'salon', 'roundtable', 'rap', 'poetry'];
        if (durationRow) {
            AppState.on('mode', (mode) => {
                durationRow.style.display = modesWithDuration.includes(mode) ? 'flex' : 'none';
            });
            // Initialize
            durationRow.style.display = modesWithDuration.includes(initialMode) ? 'flex' : 'none';
        }

        // Add Elder modal
        addElderBtn = document.getElementById('add-elder-btn');
        addElderOverlay = document.getElementById('add-elder-overlay');
        addElderForm = document.getElementById('add-elder-form');
        addElderModalClose = document.getElementById('add-elder-modal-close');

        if (addElderBtn && addElderOverlay) {
            addElderBtn.addEventListener('click', () => {
                addElderOverlay.classList.add('open');
            });
            addElderModalClose.addEventListener('click', () => {
                addElderOverlay.classList.remove('open');
            });
            addElderOverlay.addEventListener('click', (e) => {
                if (e.target === addElderOverlay) {
                    addElderOverlay.classList.remove('open');
                }
            });
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && addElderOverlay.classList.contains('open')) {
                    addElderOverlay.classList.remove('open');
                }
            });
            addElderForm.addEventListener('submit', handleAddElderSubmit);
        }

        // Show all modes toggle
        showAllModesCheckbox = document.getElementById('show-all-modes-checkbox');
        modeSimple = document.getElementById('mode-simple');
        modeAll = document.getElementById('mode-all');

        if (showAllModesCheckbox) {
            showAllModesCheckbox.addEventListener('change', () => {
                const show = showAllModesCheckbox.checked;
                AppState.set('showAllModes', show);
                updateModeVisibility(show);
            });
        }

        // Restore persisted preferences from localStorage
        restorePreferences();

        // Initialize selected elders
        updateSelectedElders();
        loadHistory();
        loadProviderState();
        loadCustomElders();
    }

    const KEY_ROW_MAP = {
        anthropic: () => anthropicKeyRow,
        openai: () => openaiKeyRow,
        google: () => googleKeyRow,
    };

    function showKeyRowForProvider(provider) {
        // Hide all key rows
        [anthropicKeyRow, openaiKeyRow, googleKeyRow].forEach(r => {
            if (r) r.style.display = 'none';
        });
        // Show the matching one (if cloud provider)
        const getter = KEY_ROW_MAP[provider];
        if (getter) {
            const row = getter();
            if (row) row.style.display = 'flex';
        }
        // Model pull row is only for ollama
        modelPullRow.style.display = provider === 'ollama' ? 'flex' : 'none';
    }

    async function loadProviderState() {
        try {
            const config = await API.getConfig();
            const provider = config.provider || 'ollama';
            providerSelector.querySelectorAll('.mode-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.provider === provider);
            });
            showKeyRowForProvider(provider);
            if (config.anthropic_api_key_set && anthropicKeyInput) {
                anthropicKeyInput.placeholder = 'Key saved (enter new to replace)';
            }
            if (config.openai_api_key_set && openaiKeyInput) {
                openaiKeyInput.placeholder = 'Key saved (enter new to replace)';
            }
            if (config.google_api_key_set && googleKeyInput) {
                googleKeyInput.placeholder = 'Key saved (enter new to replace)';
            }
            AppState.set('provider', provider);

            // TTS provider state
            const ttsProvider = config.tts_provider || 'macos';
            if (ttsProviderSelector) {
                ttsProviderSelector.querySelectorAll('.mode-btn').forEach(b => {
                    b.classList.toggle('active', b.dataset.tts === ttsProvider);
                });
            }
            if (elevenlabsSettings) {
                elevenlabsSettings.style.display = ttsProvider === 'elevenlabs' ? 'block' : 'none';
            }
            if (config.elevenlabs_api_key_set && elevenlabsKeyInput) {
                elevenlabsKeyInput.placeholder = 'Key saved (enter new to replace)';
            }
            if (config.elevenlabs_model && elevenlabsModelSelect) {
                elevenlabsModelSelect.value = config.elevenlabs_model;
            }
        } catch (e) {
            // Fallback — keep defaults
        }
    }

    async function switchProvider(provider) {
        showKeyRowForProvider(provider);
        pullProgress.style.display = 'none';
        AppState.set('provider', provider);
        await API.setConfig({ provider });
        // Reload status and models for the new provider
        if (typeof HeaderComponent !== 'undefined') {
            HeaderComponent.refresh();
        }
    }

    async function switchTTSProvider(ttsProvider) {
        if (elevenlabsSettings) {
            elevenlabsSettings.style.display = ttsProvider === 'elevenlabs' ? 'block' : 'none';
        }
        await API.setConfig({ tts_provider: ttsProvider });
    }

    async function saveElevenLabsKey() {
        const key = elevenlabsKeyInput.value.trim();
        if (!key) return;

        elevenlabsKeySave.textContent = '...';
        elevenlabsKeySave.disabled = true;

        try {
            await API.setConfig({ elevenlabs_api_key: key });
            elevenlabsKeyInput.value = '';
            elevenlabsKeyInput.placeholder = 'Key saved (enter new to replace)';
            elevenlabsKeySave.textContent = 'Saved';
            elevenlabsKeySave.classList.add('api-key-saved');
            setTimeout(() => {
                elevenlabsKeySave.textContent = 'Save';
                elevenlabsKeySave.classList.remove('api-key-saved');
            }, 2000);
        } catch (e) {
            elevenlabsKeySave.textContent = 'Error';
            setTimeout(() => { elevenlabsKeySave.textContent = 'Save'; }, 2000);
        } finally {
            elevenlabsKeySave.disabled = false;
        }
    }

    async function pullModel() {
        const modelName = modelPullInput.value.trim();
        if (!modelName) return;

        modelPullBtn.disabled = true;
        modelPullBtn.textContent = '...';
        pullProgress.style.display = 'block';
        pullProgressFill.style.width = '0%';
        pullProgressText.textContent = 'Starting download...';

        try {
            const response = await API.pullOllamaModel(modelName);
            for await (const data of API.streamSSE(response)) {
                if (data.error) {
                    pullProgressText.textContent = `Error: ${data.error}`;
                    break;
                }
                if (data.done) {
                    pullProgressFill.style.width = '100%';
                    pullProgressText.textContent = `${modelName} ready!`;
                    modelPullInput.value = '';
                    // Refresh models list
                    if (typeof HeaderComponent !== 'undefined') {
                        HeaderComponent.refresh();
                    }
                    setTimeout(() => {
                        pullProgress.style.display = 'none';
                    }, 3000);
                    break;
                }
                if (data.percent !== undefined) {
                    pullProgressFill.style.width = data.percent + '%';
                    pullProgressText.textContent = data.status || `Downloading... ${data.percent}%`;
                }
            }
        } catch (e) {
            pullProgressText.textContent = `Error: ${e.message}`;
        } finally {
            modelPullBtn.disabled = false;
            modelPullBtn.textContent = 'Pull';
        }
    }

    function wireKeySave(input, saveBtn, configKey) {
        const handler = async () => {
            const key = input.value.trim();
            if (!key) return;

            saveBtn.textContent = '...';
            saveBtn.disabled = true;

            try {
                await API.setConfig({ [configKey]: key });
                input.value = '';
                input.placeholder = 'Key saved (enter new to replace)';
                saveBtn.textContent = 'Saved';
                saveBtn.classList.add('api-key-saved');
                setTimeout(() => {
                    saveBtn.textContent = 'Save';
                    saveBtn.classList.remove('api-key-saved');
                }, 2000);
                if (typeof HeaderComponent !== 'undefined') {
                    HeaderComponent.refresh();
                }
            } catch (e) {
                saveBtn.textContent = 'Error';
                setTimeout(() => { saveBtn.textContent = 'Save'; }, 2000);
            } finally {
                saveBtn.disabled = false;
            }
        };
        saveBtn.addEventListener('click', handler);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') handler();
        });
    }

    function updateSelectedElders() {
        const selected = [];
        elderList.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
            selected.push(cb.value);
        });
        if (customElderList) {
            customElderList.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
                selected.push(cb.value);
            });
        }
        AppState.set('selectedElders', selected);
    }

    /**
     * Programmatically select elders by ID (used by auto-select).
     */
    function selectElders(elderIds) {
        elderList.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = elderIds.includes(cb.value);
        });
        if (customElderList) {
            customElderList.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                cb.checked = elderIds.includes(cb.value);
            });
        }
        updateSelectedElders();
    }

    async function loadHistory() {
        try {
            const sessions = await API.getHistory();
            historyList.innerHTML = '';

            if (sessions.length === 0) {
                historyList.innerHTML = '<div class="history-empty">No sessions yet</div>';
                return;
            }

            sessions.forEach(s => {
                const item = document.createElement('div');
                item.className = 'history-item';

                const date = new Date(s.timestamp);
                const dateStr = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

                item.innerHTML = `
                    <div class="history-topic">${escapeHtml(s.topic)}</div>
                    <div class="history-meta">${dateStr} &middot; ${s.elders.length} elder${s.elders.length !== 1 ? 's' : ''}</div>
                `;
                historyList.appendChild(item);
            });
        } catch (e) {
            historyList.innerHTML = '<div class="history-empty">Could not load history</div>';
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async function loadCustomElders() {
        try {
            const elders = await API.getCustomElders();
            AppState.set('customElders', elders);

            if (!customEldersSection || !customElderList) return;

            if (elders.length === 0) {
                customEldersSection.style.display = 'none';
                return;
            }

            customEldersSection.style.display = '';
            customElderList.innerHTML = '';

            elders.forEach(elder => {
                const item = document.createElement('label');
                item.className = 'elder-item custom-elder-item';
                item.dataset.elderId = elder.id;

                const isChecked = AppState.get('selectedElders').includes(elder.id);
                const color = ElderColors.get(elder.color || 'bright_magenta');
                const avatarHtml = ElderAvatars.renderHtml(elder.id, elder.name, color, {size: 24});
                item.innerHTML = `
                    <input type="checkbox" value="${elder.id}" ${isChecked ? 'checked' : ''}>
                    ${avatarHtml}
                    <span class="elder-name">${escapeHtml(elder.name)}</span>
                    <button class="custom-elder-delete" data-elder-id="${elder.id}" title="Delete custom elder">&times;</button>
                `;
                customElderList.appendChild(item);
            });

            // Handle checkbox changes for custom elders
            customElderList.addEventListener('change', updateSelectedElders);

            // Handle delete buttons
            customElderList.addEventListener('click', async (e) => {
                const btn = e.target.closest('.custom-elder-delete');
                if (!btn) return;
                e.preventDefault();
                e.stopPropagation();
                const elderId = btn.dataset.elderId;
                if (!confirm(`Delete custom elder "${elderId}"?`)) return;
                await API.deleteCustomElder(elderId);
                loadCustomElders();
            });
        } catch (e) {
            if (customEldersSection) customEldersSection.style.display = 'none';
        }
    }

    function updateModeVisibility(showAll) {
        if (modeSimple) modeSimple.style.display = showAll ? 'none' : '';
        if (modeAll) modeAll.style.display = showAll ? '' : 'none';

        // When switching back to simple mode, ensure mode is ask or council
        if (!showAll) {
            const currentMode = AppState.get('mode');
            if (currentMode !== 'ask' && currentMode !== 'council') {
                AppState.set('mode', 'council');
                if (modeSimple) {
                    modeSimple.querySelectorAll('.mode-btn').forEach(b => {
                        b.classList.toggle('active', b.dataset.mode === 'council');
                    });
                }
            }
        }
    }

    // --- localStorage preference persistence ---
    const PREFS_KEY = 'council-prefs';
    const PERSISTED_KEYS = [
        'mode', 'responseLength', 'discussionLength', 'dialecticTension',
        'autoSelectElders', 'autoSelectLimit', 'poetryForm', 'showAllModes'
    ];

    function savePreferences() {
        const prefs = {};
        PERSISTED_KEYS.forEach(k => { prefs[k] = AppState.get(k); });
        try { localStorage.setItem(PREFS_KEY, JSON.stringify(prefs)); } catch (e) { /* ignore */ }
    }

    function restorePreferences() {
        let prefs;
        try { prefs = JSON.parse(localStorage.getItem(PREFS_KEY)); } catch (e) { return; }
        if (!prefs) return;

        // Restore mode
        if (prefs.mode) {
            AppState.set('mode', prefs.mode);
            if (modeSelector) {
                modeSelector.querySelectorAll('.mode-btn').forEach(b => {
                    b.classList.toggle('active', b.dataset.mode === prefs.mode);
                });
            }
        }

        // Restore tension slider
        if (prefs.dialecticTension != null && tensionSlider) {
            tensionSlider.value = prefs.dialecticTension;
            AppState.set('dialecticTension', prefs.dialecticTension);
        }

        // Restore selects
        if (prefs.responseLength && responseLengthSelect) {
            responseLengthSelect.value = prefs.responseLength;
            AppState.set('responseLength', prefs.responseLength);
        }
        if (prefs.discussionLength && discussionLengthSelect) {
            discussionLengthSelect.value = prefs.discussionLength;
            AppState.set('discussionLength', prefs.discussionLength);
        }
        if (prefs.autoSelectLimit && autoSelectLimitSelect) {
            autoSelectLimitSelect.value = prefs.autoSelectLimit;
            AppState.set('autoSelectLimit', prefs.autoSelectLimit);
        }
        if (prefs.poetryForm && poetryFormSelect) {
            poetryFormSelect.value = prefs.poetryForm;
            AppState.set('poetryForm', prefs.poetryForm);
        }

        // Restore auto-select checkbox
        if (prefs.autoSelectElders != null && autoSelectCheckbox) {
            autoSelectCheckbox.checked = prefs.autoSelectElders;
            AppState.set('autoSelectElders', prefs.autoSelectElders);
            if (autoSelectLimitRow) {
                autoSelectLimitRow.style.display = prefs.autoSelectElders ? 'flex' : 'none';
            }
        }

        // Restore show all modes
        if (prefs.showAllModes != null && showAllModesCheckbox) {
            showAllModesCheckbox.checked = prefs.showAllModes;
            AppState.set('showAllModes', prefs.showAllModes);
            updateModeVisibility(prefs.showAllModes);
        }

        // Re-trigger visibility updates
        if (discussionStyleSection) {
            const m = AppState.get('mode');
            discussionStyleSection.style.display = ['panel', 'salon'].includes(m) ? 'block' : 'none';
        }
        if (poetryFormRow) {
            poetryFormRow.style.display = AppState.get('mode') === 'poetry' ? 'flex' : 'none';
        }
        if (durationRow) {
            const modesWithDur = ['panel', 'salon', 'roundtable', 'rap', 'poetry'];
            durationRow.style.display = modesWithDur.includes(AppState.get('mode')) ? 'flex' : 'none';
        }
    }

    // Auto-save whenever any persisted key changes
    PERSISTED_KEYS.forEach(k => {
        AppState.on(k, () => savePreferences());
    });

    async function handleAddElderSubmit(e) {
        e.preventDefault();
        const name = document.getElementById('add-elder-name').value.trim();
        if (!name) return;

        const elderData = {
            name,
            title: document.getElementById('add-elder-title').value.trim(),
            era: document.getElementById('add-elder-era').value.trim(),
            expertise: document.getElementById('add-elder-expertise').value.trim(),
            prompt: document.getElementById('add-elder-prompt').value.trim(),
            color: document.getElementById('add-elder-color').value,
        };

        const submitBtn = addElderForm.querySelector('.add-elder-submit');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';

        try {
            await API.saveCustomElder(elderData);
            addElderOverlay.classList.remove('open');
            addElderForm.reset();
            loadCustomElders();
        } catch (err) {
            alert('Could not create elder: ' + err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Elder';
        }
    }

    return { init, loadHistory, loadCustomElders, selectElders };
})();
