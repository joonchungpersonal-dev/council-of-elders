/**
 * Main app controller: init, send logic, SSE event routing, podcast generation.
 */
window.App = (() => {

    // Track conversation segments for podcast generation
    let podcastSegments = [];
    let lastQuestion = '';

    // Adaptive profile: implicit session tracking
    let sessionStartTime = 0;
    let sessionFollowUpCount = 0;
    let sessionPodcastGenerated = false;
    let sessionJournalSaved = false;
    let sessionWasAutoSelected = false;
    let sessionWasModeAutoSelected = false;
    let sessionResolvedMode = '';
    let sessionElderIds = [];
    let sessionOverrideCount = 0;

    // Map discussion length to max_turns
    const DISCUSSION_TURNS = {
        lightning: 2,
        quick: 4,
        short: 8,
        medium: 12,
        long: 18,
        extended: 24,
    };

    function init() {
        HeaderComponent.init();
        SidebarComponent.init();
        ChatComponent.init();
        InputComponent.init(handleSend);
        InputComponent.focus();

        if (typeof ElderProfileComponent !== 'undefined') {
            ElderProfileComponent.init();
        }
        if (typeof JournalComponent !== 'undefined') {
            JournalComponent.init();
        }

        // Load enrichment config
        API.getConfig().then(config => {
            AppState.set('enrichmentEnabled', config.enrichment_enabled !== false);
        }).catch(() => {});
    }

    async function handleSend(text) {
        const mode = AppState.get('mode');
        let elders = AppState.get('selectedElders');

        if (AppState.get('status') !== 'connected') {
            ChatComponent.addSystemMessage('Not connected. Check your provider setup in the sidebar.');
            return;
        }

        // Auto-select elders if none chosen and auto-select is enabled
        let wasAutoSelected = false;
        const multiElderModes = ['panel', 'salon', 'roundtable', 'intake', 'rap', 'poetry', 'council'];
        if (elders.length === 0 && multiElderModes.includes(mode) && AppState.get('autoSelectElders')) {
            ChatComponent.addUserMessage(text);
            const selectingMsg = ChatComponent.addSystemMessage('Selecting the best elders for your question...');
            try {
                const result = await API.autoSelectElders(text, AppState.get('autoSelectLimit'));
                if (result.elder_ids && result.elder_ids.length > 0) {
                    SidebarComponent.selectElders(result.elder_ids);
                    elders = result.elder_ids;
                    wasAutoSelected = true;
                    // Update the system message with who was chosen
                    const names = result.elder_ids
                        .map(id => {
                            const e = findElder(id);
                            return e ? e.name : id;
                        })
                        .join(', ');
                    selectingMsg.querySelector('.system-text').textContent =
                        `Selected: ${names}`;
                } else {
                    selectingMsg.querySelector('.system-text').textContent =
                        'Could not auto-select elders. Please choose manually.';
                    return;
                }
            } catch (e) {
                selectingMsg.querySelector('.system-text').textContent =
                    'Auto-select failed. Please choose elders manually.';
                return;
            }
        } else if (elders.length === 0) {
            ChatComponent.addSystemMessage(
                mode === 'ask'
                    ? 'Please select an elder from the sidebar.'
                    : 'Please select elders or enable Auto-select.'
            );
            return;
        } else {
            ChatComponent.addUserMessage(text);
        }

        AppState.set('isStreaming', true);
        AppState.set('wasAutoSelected', wasAutoSelected);
        lastQuestion = text;

        // Reset session tracking for new discussion
        sessionStartTime = Date.now();
        sessionFollowUpCount = 0;
        sessionPodcastGenerated = false;
        sessionJournalSaved = false;
        sessionWasAutoSelected = wasAutoSelected;
        sessionWasModeAutoSelected = false;
        sessionElderIds = [...elders];
        sessionOverrideCount = 0;

        // Smart mode: auto-select the best format when "council" is chosen
        let resolvedMode = mode;
        if (mode === 'council') {
            const modeMsg = ChatComponent.addSystemMessage('Choosing discussion format...');
            try {
                const modeResult = await API.selectMode(text);
                resolvedMode = modeResult.mode || 'panel';
                sessionWasModeAutoSelected = true;
                const modeLabels = {
                    roundtable: 'Roundtable', panel: 'Panel', salon: 'Salon',
                    intake: 'Intake', rap: 'Rap Battle', poetry: 'Poetry Slam',
                };
                const label = modeLabels[resolvedMode] || resolvedMode;
                modeMsg.querySelector('.system-text').textContent =
                    `Starting a ${label} discussion...`;
            } catch (e) {
                resolvedMode = 'panel';
                modeMsg.querySelector('.system-text').textContent =
                    'Starting a Panel discussion...';
            }
        }

        sessionResolvedMode = resolvedMode;

        try {
            switch (resolvedMode) {
                case 'ask':
                    await handleAsk(text, elders[0]);
                    break;
                case 'roundtable':
                    await handleRoundtable(text, elders);
                    break;
                case 'panel':
                    await handlePanel(text, elders);
                    break;
                case 'salon':
                    await handleSalon(text, elders);
                    break;
                case 'intake':
                    await handleIntake(text, elders);
                    break;
                case 'rap':
                    await handleRapBattle(text, elders);
                    break;
                case 'poetry':
                    await handlePoetrySlam(text, elders);
                    break;
            }
        } catch (err) {
            ChatComponent.addSystemMessage(`Error: ${err.message}`);
        } finally {
            AppState.set('isStreaming', false);
        }
    }

    /**
     * Ask a single elder.
     */
    async function handleAsk(question, elderId) {
        const elderData = findElder(elderId);
        const handle = ChatComponent.startElderMessage(elderData);

        // Reset podcast segments for new session
        podcastSegments = [
            { type: 'narrator', text: 'The question posed to the council.' },
            { type: 'user', text: question },
        ];

        const response = await API.startStream('/api/ask', {
            elder_id: elderId,
            question,
        });

        for await (const data of API.streamSSE(response)) {
            if (data.chunk) {
                handle.appendChunk(data.chunk);
            }
            if (data.done) {
                handle.finish(data.html);
                podcastSegments.push({
                    type: 'elder',
                    elder_id: elderId,
                    name: elderData.name,
                    text: data.raw,
                });
                showPodcastOption();
            }
        }
    }

    /**
     * Roundtable discussion with multiple elders.
     */
    async function handleRoundtable(question, elderIds) {
        ChatComponent.addSystemMessage('The council is deliberating...');

        // Reset podcast segments
        podcastSegments = [
            { type: 'narrator', text: 'A question has been brought before the Council of Elders.' },
            { type: 'user', text: question },
        ];

        const response = await API.startStream('/api/roundtable', {
            question,
            elders: elderIds,
            turns: 1,
        });

        await processRoundtableStream(response);
        showPodcastOption();
    }

    /**
     * Panel discussion: moderator-directed academic seminar.
     * All elders participate; moderator opens, directs, and wraps up.
     */
    async function handlePanel(question, elderIds) {
        if (elderIds.length < 2) {
            ChatComponent.addSystemMessage('Panel mode requires at least 2 elders.');
            return;
        }

        ChatComponent.addSystemMessage('The moderator is convening the panel...');

        // Reset podcast segments
        podcastSegments = [
            { type: 'narrator', text: 'An expert panel has been convened to discuss the following question.' },
            { type: 'user', text: question },
        ];

        // Track conversation history for continuation after ask_user
        const panelHistory = [{ role: 'user', text: question }];

        let stopHandle = null;

        async function runPanelStream(endpoint, body) {
            const response = await API.startStream(endpoint, body);

            let currentHandle = null;
            let moderatorHandle = null;
            const nominatedElders = {};
            let stopped = false;

            // Show stop button after first elder speaks
            let elderCount = 0;

            for await (const data of API.streamSSE(response)) {
                if (stopped) break;
                // Moderator starts speaking
                if (data.moderator_start) {
                    moderatorHandle = ChatComponent.startModeratorMessage(data.phase || '');
                    currentHandle = null;
                }

                // Streaming chunks
                if (data.chunk) {
                    if (data.elder_id === '__moderator__' && moderatorHandle) {
                        moderatorHandle.appendChunk(data.chunk);
                    } else if (currentHandle) {
                        currentHandle.appendChunk(data.chunk);
                    }
                }

                // Moderator finishes
                if (data.moderator_done && moderatorHandle) {
                    moderatorHandle.finish(data.html);
                    panelHistory.push({ role: 'moderator', text: data.raw });
                    podcastSegments.push({
                        type: 'narrator',
                        text: data.raw,
                    });
                    moderatorHandle = null;
                }

                // Elder starts speaking
                if (data.elder_start) {
                    const elderData = findElder(data.elder_id) || nominatedElders[data.elder_id] || {
                        name: data.name, title: data.title, era: data.era, color: ''
                    };
                    currentHandle = ChatComponent.startElderMessage(elderData);
                }

                // Elder finishes
                if (data.elder_done && currentHandle) {
                    currentHandle.finish(data.html);
                    panelHistory.push({
                        role: 'elder',
                        elder_id: data.elder_id,
                        name: data.name,
                        text: data.raw,
                    });
                    podcastSegments.push({
                        type: 'elder',
                        elder_id: data.elder_id,
                        name: data.name,
                        text: data.raw,
                    });
                    currentHandle = null;

                    // Show stop button after first elder speaks
                    elderCount++;
                    if (elderCount === 1 && !stopHandle) {
                        stopHandle = ChatComponent.showStopButton(() => {
                            stopped = true;
                            API.abortStream();
                        });
                    }
                }

                // Nomination
                if (data.nomination) {
                    nominatedElders[data.guest_id] = {
                        id: data.guest_id,
                        name: data.guest_name,
                        title: data.expertise,
                        era: '',
                        color: '',
                    };
                    handleNominationEvent(data);
                }

                // Moderator asks user for clarification
                if (data.ask_user) {
                    sessionFollowUpCount++;
                    AppState.set('isStreaming', false);
                    const answer = await ChatComponent.showModeratorQuestion();
                    ChatComponent.addUserMessage(answer);
                    panelHistory.push({ role: 'user', text: answer });
                    AppState.set('isStreaming', true);

                    ChatComponent.addSystemMessage('The panel continues with your clarification...');

                    // Continue the panel
                    await runPanelStream('/api/panel-continue', {
                        question,
                        elders: elderIds,
                        max_turns: Math.max(DISCUSSION_TURNS[AppState.get('discussionLength')] || 12, elderIds.length),
                        dialectic_tension: AppState.get('dialecticTension'),
                        response_length: AppState.get('responseLength'),
                        continuation: {
                            user_answer: answer,
                            history: panelHistory,
                            speakers_so_far: data.state.speakers_so_far,
                            turns_used: data.state.turns_used,
                        },
                    });
                    return;
                }

                // Panel complete
                if (data.panel_done) {
                    if (stopHandle) { stopHandle.remove(); stopHandle = null; }
                }
            }
        }

        try {
            await runPanelStream('/api/panel', {
                question,
                elders: elderIds,
                max_turns: Math.max(DISCUSSION_TURNS[AppState.get('discussionLength')] || 12, elderIds.length),
                dialectic_tension: AppState.get('dialecticTension'),
                allow_nominations: AppState.get('wasAutoSelected'),
                response_length: AppState.get('responseLength'),
            });
        } catch (e) {
            // AbortError is expected when user clicks Stop
            if (e.name !== 'AbortError') throw e;
        }
        if (stopHandle) { stopHandle.remove(); stopHandle = null; }

        showPodcastOption();
    }

    /**
     * Salon discussion: assertive moderator with dynamic sentence budgets and interruptions.
     */
    async function handleSalon(question, elderIds) {
        if (elderIds.length < 2) {
            ChatComponent.addSystemMessage('Salon mode requires at least 2 elders.');
            return;
        }

        ChatComponent.addSystemMessage('The moderator is opening the salon...');

        podcastSegments = [
            { type: 'narrator', text: 'A salon discussion has been convened to explore the following question.' },
            { type: 'user', text: question },
        ];

        const salonHistory = [{ role: 'user', text: question }];

        let stopHandle = null;

        async function runSalonStream(endpoint, body) {
            const response = await API.startStream(endpoint, body);

            let currentHandle = null;
            let moderatorHandle = null;
            const nominatedElders = {};
            let stopped = false;
            let elderCount = 0;

            for await (const data of API.streamSSE(response)) {
                if (stopped) break;
                if (data.moderator_start) {
                    moderatorHandle = ChatComponent.startModeratorMessage(data.phase || '');
                    currentHandle = null;
                }

                if (data.chunk) {
                    if (data.elder_id === '__moderator__' && moderatorHandle) {
                        moderatorHandle.appendChunk(data.chunk);
                    } else if (currentHandle) {
                        currentHandle.appendChunk(data.chunk);
                    }
                }

                if (data.moderator_done && moderatorHandle) {
                    moderatorHandle.finish(data.html);
                    salonHistory.push({ role: 'moderator', text: data.raw });
                    podcastSegments.push({ type: 'narrator', text: data.raw });
                    moderatorHandle = null;
                }

                if (data.elder_start) {
                    const elderData = findElder(data.elder_id) || nominatedElders[data.elder_id] || {
                        name: data.name, title: data.title, era: data.era, color: ''
                    };
                    currentHandle = ChatComponent.startElderMessage(elderData);
                }

                // Elder interrupted — mark the current card
                if (data.elder_interrupted && currentHandle) {
                    currentHandle.element.classList.add('elder-interrupted');
                }

                if (data.elder_done && currentHandle) {
                    currentHandle.finish(data.html);
                    salonHistory.push({
                        role: 'elder',
                        elder_id: data.elder_id,
                        name: data.name,
                        text: data.raw,
                    });
                    podcastSegments.push({
                        type: 'elder',
                        elder_id: data.elder_id,
                        name: data.name,
                        text: data.raw,
                    });
                    currentHandle = null;

                    elderCount++;
                    if (elderCount === 1 && !stopHandle) {
                        stopHandle = ChatComponent.showStopButton(() => {
                            stopped = true;
                            API.abortStream();
                        });
                    }
                }

                if (data.nomination) {
                    nominatedElders[data.guest_id] = {
                        id: data.guest_id,
                        name: data.guest_name,
                        title: data.expertise,
                        era: '',
                        color: '',
                    };
                    handleNominationEvent(data);
                }

                if (data.ask_user) {
                    sessionFollowUpCount++;
                    AppState.set('isStreaming', false);
                    const answer = await ChatComponent.showModeratorQuestion();
                    ChatComponent.addUserMessage(answer);
                    salonHistory.push({ role: 'user', text: answer });
                    AppState.set('isStreaming', true);

                    ChatComponent.addSystemMessage('The salon continues with your clarification...');

                    await runSalonStream('/api/salon-continue', {
                        question,
                        elders: elderIds,
                        max_turns: Math.max(DISCUSSION_TURNS[AppState.get('discussionLength')] || 12, elderIds.length),
                        dialectic_tension: AppState.get('dialecticTension'),
                        response_length: AppState.get('responseLength'),
                        continuation: {
                            user_answer: answer,
                            history: salonHistory,
                            speakers_so_far: data.state.speakers_so_far,
                            turns_used: data.state.turns_used,
                        },
                    });
                    return;
                }

                if (data.panel_done) {
                    if (stopHandle) { stopHandle.remove(); stopHandle = null; }
                }
            }
        }

        try {
            await runSalonStream('/api/salon', {
                question,
                elders: elderIds,
                max_turns: Math.max(DISCUSSION_TURNS[AppState.get('discussionLength')] || 12, elderIds.length),
                dialectic_tension: AppState.get('dialecticTension'),
                allow_nominations: AppState.get('wasAutoSelected'),
                response_length: AppState.get('responseLength'),
            });
        } catch (e) {
            if (e.name !== 'AbortError') throw e;
        }
        if (stopHandle) { stopHandle.remove(); stopHandle = null; }

        showPodcastOption();
    }

    /**
     * Intake mode: debate + synthesis + questions + roundtable with context.
     */
    async function handleIntake(question, elderIds) {
        ChatComponent.addSystemMessage('The elders are debating what to ask you...');

        // Reset podcast segments
        podcastSegments = [
            { type: 'narrator', text: 'A question has been brought before the Council of Elders. The elders will first deliberate on what to ask.' },
            { type: 'user', text: question },
        ];

        // Phase 1: Intake debate
        const debateResponse = await API.startStream('/api/intake-debate', {
            question,
            elders: elderIds.slice(0, 4),
            num_questions: 3,
        });

        let synthesisRaw = '';
        let currentHandle = null;

        for await (const data of API.streamSSE(debateResponse)) {
            if (data.elder_start) {
                const elderData = findElder(data.elder_id) || {
                    name: data.name, title: data.title, era: data.era, color: ''
                };
                currentHandle = ChatComponent.startElderMessage(elderData);
            }

            if (data.synthesis_start) {
                currentHandle = ChatComponent.startSynthesisMessage();
            }

            if (data.chunk && currentHandle) {
                currentHandle.appendChunk(data.chunk);
            }

            if (data.elder_done && currentHandle) {
                currentHandle.finish(data.html);
                podcastSegments.push({
                    type: 'elder',
                    elder_id: data.elder_id,
                    name: data.name,
                    text: data.raw,
                });
                currentHandle = null;
            }

            if (data.synthesis_done) {
                currentHandle.finish(data.html);
                synthesisRaw = data.raw;
                podcastSegments.push({
                    type: 'narrator',
                    text: 'The synthesis of the elders\' deliberation: ' + data.raw,
                });
                currentHandle = null;
            }

            if (data.debate_done) {
                const questions = parseIntakeQuestions(synthesisRaw);

                if (questions.length > 0) {
                    AppState.set('isStreaming', false);
                    const answers = await ChatComponent.showIntakeForm(questions);
                    AppState.set('isStreaming', true);

                    const answerSummary = answers
                        .map((a, i) => `Q${i + 1}: ${a.answer || '(no answer)'}`)
                        .join('\n');
                    ChatComponent.addUserMessage(answerSummary);

                    podcastSegments.push({
                        type: 'narrator',
                        text: 'The questioner has provided their answers. The council now deliberates with this additional context.',
                    });

                    ChatComponent.addSystemMessage('The council is now deliberating with your answers...');
                    const rtResponse = await API.startStream('/api/roundtable-with-context', {
                        question,
                        elders: elderIds,
                        intake_answers: answers,
                        turns: 1,
                    });
                    await processRoundtableStream(rtResponse);
                } else {
                    const rtResponse = await API.startStream('/api/roundtable', {
                        question,
                        elders: elderIds,
                        turns: 1,
                    });
                    await processRoundtableStream(rtResponse);
                }
                showPodcastOption();
            }
        }
    }

    /**
     * Rap Battle mode: two elders trade philosophical bars.
     */
    async function handleRapBattle(question, elderIds) {
        if (elderIds.length < 2) {
            ChatComponent.addSystemMessage('Rap Battle requires at least 2 elders.');
            return;
        }

        ChatComponent.addSystemMessage('The Battle Host is setting up the arena...');

        podcastSegments = [
            { type: 'narrator', text: 'A rap battle has been called. Two elders will trade bars on the following topic.' },
            { type: 'user', text: question },
        ];

        const response = await API.startStream('/api/rap-battle', {
            question,
            elders: elderIds,
            rounds: 3,
            response_length: AppState.get('responseLength'),
        });

        let currentHandle = null;
        let moderatorHandle = null;

        for await (const data of API.streamSSE(response)) {
            if (data.moderator_start) {
                moderatorHandle = ChatComponent.startModeratorMessage(data.phase || '');
                currentHandle = null;
            }

            if (data.chunk) {
                if (data.elder_id === '__moderator__' && moderatorHandle) {
                    moderatorHandle.appendChunk(data.chunk);
                } else if (currentHandle) {
                    currentHandle.appendChunk(data.chunk);
                }
            }

            if (data.moderator_done && moderatorHandle) {
                moderatorHandle.finish(data.html);
                podcastSegments.push({ type: 'narrator', text: data.raw });
                moderatorHandle = null;
            }

            if (data.elder_start) {
                const elderData = findElder(data.elder_id) || {
                    name: data.name, title: data.title, era: data.era, color: ''
                };
                currentHandle = ChatComponent.startElderMessage(elderData);
                // Add rap battle styling
                if (currentHandle.element) {
                    currentHandle.element.classList.add('rap-battle-card');
                }
            }

            if (data.elder_done && currentHandle) {
                currentHandle.finish(data.html);
                podcastSegments.push({
                    type: 'elder',
                    elder_id: data.elder_id,
                    name: data.name,
                    text: data.raw,
                });
                currentHandle = null;
            }

            if (data.panel_done) {
                // done
            }
        }

        showPodcastOption();
    }

    /**
     * Poetry Slam mode: elders perform spoken-word poems.
     */
    async function handlePoetrySlam(question, elderIds) {
        if (elderIds.length < 2) {
            ChatComponent.addSystemMessage('Poetry Slam requires at least 2 elders.');
            return;
        }

        ChatComponent.addSystemMessage('The Slam MC is preparing the stage...');

        podcastSegments = [
            { type: 'narrator', text: 'A poetry slam has been called. The elders will perform spoken-word poetry on the following theme.' },
            { type: 'user', text: question },
        ];

        const response = await API.startStream('/api/poetry-slam', {
            question,
            elders: elderIds,
            response_length: AppState.get('responseLength'),
            poetry_form: AppState.get('poetryForm'),
        });

        let currentHandle = null;
        let moderatorHandle = null;

        for await (const data of API.streamSSE(response)) {
            if (data.moderator_start) {
                moderatorHandle = ChatComponent.startModeratorMessage(data.phase || '');
                currentHandle = null;
            }

            if (data.chunk) {
                if (data.elder_id === '__moderator__' && moderatorHandle) {
                    moderatorHandle.appendChunk(data.chunk);
                } else if (currentHandle) {
                    currentHandle.appendChunk(data.chunk);
                }
            }

            if (data.moderator_done && moderatorHandle) {
                moderatorHandle.finish(data.html);
                podcastSegments.push({ type: 'narrator', text: data.raw });
                moderatorHandle = null;
            }

            if (data.elder_start) {
                const elderData = findElder(data.elder_id) || {
                    name: data.name, title: data.title, era: data.era, color: ''
                };
                currentHandle = ChatComponent.startElderMessage(elderData);
                // Add poetry styling
                if (currentHandle.element) {
                    currentHandle.element.classList.add('poetry-card');
                }
            }

            if (data.elder_done && currentHandle) {
                currentHandle.finish(data.html);
                podcastSegments.push({
                    type: 'elder',
                    elder_id: data.elder_id,
                    name: data.name,
                    text: data.raw,
                });
                currentHandle = null;
            }

            if (data.panel_done) {
                // done
            }
        }

        showPodcastOption();
    }

    /**
     * Process a roundtable SSE stream (shared by roundtable and intake phase 2).
     */
    async function processRoundtableStream(response) {
        let currentHandle = null;
        const nominatedElders = {};

        for await (const data of API.streamSSE(response)) {
            if (data.nomination) {
                nominatedElders[data.guest_id] = {
                    id: data.guest_id,
                    name: data.guest_name,
                    title: data.expertise,
                    era: '',
                    color: '',
                };
                handleNominationEvent(data);
            }

            if (data.elder_start) {
                const elderData = findElder(data.elder_id) || nominatedElders[data.elder_id] || {
                    name: data.name, title: data.title, era: data.era, color: ''
                };
                currentHandle = ChatComponent.startElderMessage(elderData);
            }

            if (data.chunk && currentHandle) {
                currentHandle.appendChunk(data.chunk);
            }

            if (data.elder_done && currentHandle) {
                currentHandle.finish(data.html);
                podcastSegments.push({
                    type: 'elder',
                    elder_id: data.elder_id,
                    name: data.name,
                    text: data.raw,
                });
                currentHandle = null;
            }

            if (data.roundtable_done) {
                // done
            }
        }
    }

    /**
     * Send implicit session feedback to the adaptive profile backend.
     * Fire-and-forget: never blocks UI or shows errors.
     */
    function sendSessionFeedback() {
        if (!lastQuestion) return;
        const durationSec = sessionStartTime ? Math.round((Date.now() - sessionStartTime) / 1000) : 0;
        const payload = {
            question: lastQuestion,
            mode: sessionResolvedMode,
            elder_ids: sessionElderIds,
            was_auto_selected: sessionWasAutoSelected,
            was_mode_auto_selected: sessionWasModeAutoSelected,
            follow_up_count: sessionFollowUpCount,
            podcast_generated: sessionPodcastGenerated,
            journal_saved: sessionJournalSaved,
            duration_sec: durationSec,
            override_count: sessionOverrideCount,
            settings: {
                dialectic_tension: AppState.get('dialecticTension'),
                response_length: AppState.get('responseLength'),
                discussion_length: AppState.get('discussionLength'),
            },
        };
        fetch('/api/session-feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        }).catch(() => {}); // fire-and-forget
    }

    /**
     * Show the "Download Podcast" button and journal save prompt after a session finishes.
     */
    function showPodcastOption() {
        if (podcastSegments.length < 3) return; // need at least question + 1 response

        // Send adaptive profile feedback
        sendSessionFeedback();

        // Show journal save prompt
        if (typeof JournalComponent !== 'undefined') {
            const transcript = podcastSegments
                .filter(s => s.type === 'elder' || s.type === 'narrator')
                .map(s => s.name ? `${s.name}: ${s.text}` : s.text)
                .join('\n\n');
            JournalComponent.showSavePrompt(transcript, lastQuestion, () => {
                sessionJournalSaved = true;
                // Update the already-sent feedback with journal saved
                sendSessionFeedback();
            });
        }

        ChatComponent.showPodcastButton(async (btn, container) => {
            const resp = await fetch('/api/podcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ segments: podcastSegments, mode: AppState.get('mode') || '' }),
            });
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({ error: resp.statusText }));
                throw new Error(err.error || resp.statusText);
            }

            // Stream progress events
            for await (const data of API.streamSSE(resp)) {
                if (data.progress) {
                    const remaining = Math.ceil(data.remaining);
                    btn.innerHTML = `Generating audio... ${data.current}/${data.total} (~${remaining}s left)`;
                }
                if (data.error) {
                    throw new Error(data.error);
                }
                if (data.done) {
                    sessionPodcastGenerated = true;
                    // Update feedback with podcast generated
                    sendSessionFeedback();
                    ChatComponent.showAudioPlayer(container, data.download_url);
                }
            }
        });
    }

    /**
     * Parse numbered questions from synthesis text.
     */
    function parseIntakeQuestions(text) {
        const questionRegex = /(\d+)\.\s*([^\n]+(?:\n(?!\d+\.).*)*)/g;
        const questions = [];
        let match;

        while ((match = questionRegex.exec(text)) !== null) {
            const q = match[2].trim().split('\n')[0].trim();
            if (q.length > 10) questions.push(q);
        }

        if (questions.length === 0) {
            const lines = text.split('\n').filter(l =>
                l.trim().length > 20 && (l.includes('?') || /^\d+\./.test(l.trim()))
            );
            return lines.slice(0, 3).map(l => l.replace(/^\d+\.\s*/, '').trim());
        }

        return questions;
    }

    /**
     * Handle a nomination event: show biography card + auto-trigger enrichment.
     */
    function handleNominationEvent(data) {
        ChatComponent.addNomination(data.nominated_by, data.guest_name, data.expertise);

        podcastSegments.push({
            type: 'narrator',
            text: `${data.nominated_by} nominates ${data.guest_name}, an expert in ${data.expertise}.`,
        });

        // Show biography card if we have biography data
        if (data.biography && data.biography.summary) {
            ChatComponent.showBiographyCard(
                {
                    id: data.guest_id,
                    name: data.guest_name,
                    title: data.is_existing_elder
                        ? `Panel Member — ${data.expertise}`
                        : `Guest Expert — ${data.expertise}`,
                    expertise: data.expertise,
                    nominated_by: data.nominated_by,
                    prompt: '',
                },
                data.biography,
                { showSaveButton: !data.is_existing_elder, showBooksButton: true }
            );
        }

        // Auto-trigger enrichment if enabled
        if (AppState.get('enrichmentEnabled') !== false &&
            typeof EnrichmentComponent !== 'undefined') {
            EnrichmentComponent.startEnrichment(
                data.guest_id,
                data.guest_name,
                data.expertise
            );
        }
    }

    /**
     * Find elder data from the injected __ELDERS__ list.
     */
    function findElder(elderId) {
        return (window.__ELDERS__ || []).find(e => e.id === elderId) ||
            (AppState.get('customElders') || []).find(e => e.id === elderId);
    }

    /**
     * Reset chat for a new conversation.
     */
    function newChat() {
        if (AppState.get('isStreaming')) return;
        podcastSegments = [];
        sessionStartTime = 0;
        sessionFollowUpCount = 0;
        sessionPodcastGenerated = false;
        sessionJournalSaved = false;
        sessionOverrideCount = 0;
        ChatComponent.clear();
        if (typeof ElderProfileComponent !== 'undefined') {
            ElderProfileComponent.clearCache();
        }
        InputComponent.focus();
        SidebarComponent.loadHistory();
        if (typeof JournalComponent !== 'undefined') {
            JournalComponent.loadJournals();
        }
    }

    return { init, newChat };
})();

// Boot
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
