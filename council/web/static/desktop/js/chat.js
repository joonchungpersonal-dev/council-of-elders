/**
 * Chat renderer: message cards, streaming swap, auto-scroll.
 */
window.ChatComponent = (() => {
    let chatMessages, chatArea, welcomeMessage;

    function init() {
        chatMessages = document.getElementById('chat-messages');
        chatArea = document.getElementById('chat-area');
        welcomeMessage = document.getElementById('welcome-message');
    }

    function clear() {
        chatMessages.innerHTML = '';
        if (welcomeMessage) {
            chatMessages.appendChild(welcomeMessage);
            welcomeMessage.style.display = '';
        }
    }

    function hideWelcome() {
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
    }

    function scrollToBottom() {
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // --- Message rendering ---

    function addUserMessage(text) {
        hideWelcome();
        const msg = document.createElement('div');
        msg.className = 'message message-user';
        msg.innerHTML = `<div class="message-bubble">${escapeHtml(text)}</div>`;
        chatMessages.appendChild(msg);
        scrollToBottom();
    }

    function addSystemMessage(text) {
        const msg = document.createElement('div');
        msg.className = 'message message-system';
        msg.innerHTML = `<span class="system-text">${escapeHtml(text)}</span>`;
        chatMessages.appendChild(msg);
        scrollToBottom();
        return msg;
    }

    function addNomination(nominatedBy, guestName, expertise) {
        const msg = document.createElement('div');
        msg.className = 'message message-nomination';
        msg.innerHTML = `
            <div class="nomination-banner">
                <span class="nomination-arrow">&raquo;</span>
                ${escapeHtml(nominatedBy)} nominates <strong>${escapeHtml(guestName)}</strong>
                (${escapeHtml(expertise)})
            </div>
        `;
        chatMessages.appendChild(msg);
        scrollToBottom();
    }

    /**
     * Create an elder message card and return a handle for streaming.
     */
    function startElderMessage(elderData) {
        hideWelcome();
        const color = ElderColors.get(elderData.color || '');
        const avatarHtml = ElderAvatars.renderHtml(elderData.id, elderData.name, color, {size: 32});
        const msg = document.createElement('div');
        msg.className = 'message message-elder';
        msg.innerHTML = `
            <div class="message-card" style="--elder-color: ${color}">
                <div class="elder-header">
                    ${avatarHtml}
                    <span class="elder-name-label">${escapeHtml(elderData.name)}</span>
                    <span class="elder-title-label">${escapeHtml(elderData.title)} &middot; ${escapeHtml(elderData.era)}</span>
                </div>
                <div class="elder-content streaming-cursor"></div>
            </div>
        `;
        chatMessages.appendChild(msg);

        const contentEl = msg.querySelector('.elder-content');
        let rawText = '';

        return {
            element: msg,
            appendChunk(chunk) {
                rawText += chunk;
                contentEl.textContent = rawText;
                scrollToBottom();
            },
            finish(html) {
                contentEl.classList.remove('streaming-cursor');
                contentEl.classList.add('elder-html');
                contentEl.innerHTML = html;
                scrollToBottom();
            },
            getRawText() {
                return rawText;
            }
        };
    }

    /**
     * Create a synthesis message card and return a handle for streaming.
     */
    function startSynthesisMessage() {
        const msg = document.createElement('div');
        msg.className = 'message message-synthesis';
        msg.innerHTML = `
            <div class="synthesis-card">
                <div class="synthesis-header">Synthesis</div>
                <div class="synthesis-content streaming-cursor"></div>
            </div>
        `;
        chatMessages.appendChild(msg);

        const contentEl = msg.querySelector('.synthesis-content');
        let rawText = '';

        return {
            element: msg,
            appendChunk(chunk) {
                rawText += chunk;
                contentEl.textContent = rawText;
                scrollToBottom();
            },
            finish(html) {
                contentEl.classList.remove('streaming-cursor');
                contentEl.classList.add('elder-html');
                contentEl.innerHTML = html;
                scrollToBottom();
            },
            getRawText() {
                return rawText;
            }
        };
    }

    /**
     * Create a moderator message card and return a handle for streaming.
     * @param {string} phase - "opening", "transition", "acknowledge", or "takeaways"
     */
    function startModeratorMessage(phase) {
        const label = phase === 'takeaways'
            ? 'Moderator &mdash; Key Takeaways'
            : 'Moderator';
        const isTransition = phase === 'transition';

        const msg = document.createElement('div');
        msg.className = 'message message-moderator' + (isTransition ? ' moderator-transition' : '');
        msg.innerHTML = `
            <div class="moderator-card">
                <div class="moderator-header">
                    <span class="moderator-icon">
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                            <path d="M8 1L10 5.5L15 6L11.5 9.5L12.5 14.5L8 12L3.5 14.5L4.5 9.5L1 6L6 5.5L8 1Z" fill="currentColor"/>
                        </svg>
                    </span>
                    <span class="moderator-label">${label}</span>
                </div>
                <div class="moderator-content streaming-cursor"></div>
            </div>
        `;
        chatMessages.appendChild(msg);

        const contentEl = msg.querySelector('.moderator-content');
        let rawText = '';

        return {
            element: msg,
            appendChunk(chunk) {
                rawText += chunk;
                contentEl.textContent = rawText;
                scrollToBottom();
            },
            finish(html) {
                contentEl.classList.remove('streaming-cursor');
                contentEl.classList.add('elder-html');
                contentEl.innerHTML = html;
                scrollToBottom();
            },
            getRawText() {
                return rawText;
            }
        };
    }

    /**
     * Show a moderator clarification prompt with an input field.
     * Returns a Promise that resolves with the user's answer.
     */
    function showModeratorQuestion() {
        return new Promise((resolve) => {
            const msg = document.createElement('div');
            msg.className = 'message message-moderator-ask';
            msg.innerHTML = `
                <div class="moderator-ask-card">
                    <div class="moderator-ask-header">
                        <span class="moderator-icon">
                            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                                <path d="M8 1.5C4.4 1.5 1.5 4.4 1.5 8C1.5 11.6 4.4 14.5 8 14.5C11.6 14.5 14.5 11.6 14.5 8C14.5 4.4 11.6 1.5 8 1.5ZM8.75 11.5H7.25V10H8.75V11.5ZM8.75 8.75H7.25V4.5H8.75V8.75Z" fill="currentColor"/>
                            </svg>
                        </span>
                        <span>Moderator &mdash; Clarification Needed</span>
                    </div>
                    <textarea class="intake-answer-input" placeholder="Your answer..."></textarea>
                    <button class="intake-submit-btn">Submit &amp; Continue Panel</button>
                </div>
            `;
            chatMessages.appendChild(msg);
            scrollToBottom();

            const textarea = msg.querySelector('textarea');
            textarea.focus();

            const submitBtn = msg.querySelector('.intake-submit-btn');
            submitBtn.addEventListener('click', () => {
                const answer = textarea.value.trim();
                if (!answer) return;
                submitBtn.disabled = true;
                submitBtn.textContent = 'Continuing...';
                textarea.disabled = true;
                resolve(answer);
            });
        });
    }

    /**
     * Render an intake form with clarifying questions.
     * Returns a Promise that resolves with the answers when the user submits.
     */
    function showIntakeForm(questions) {
        return new Promise((resolve) => {
            const msg = document.createElement('div');
            msg.className = 'message message-intake-form';

            let formHtml = `
                <div class="intake-form-card">
                    <div class="intake-form-title">Please answer these clarifying questions:</div>
            `;

            questions.forEach((q, i) => {
                formHtml += `
                    <div class="intake-question-group">
                        <div class="intake-question-label">Q${i + 1}: ${escapeHtml(q)}</div>
                        <textarea class="intake-answer-input" data-index="${i}" placeholder="Your answer..."></textarea>
                    </div>
                `;
            });

            formHtml += `
                    <button class="intake-submit-btn">Submit Answers & Get Counsel</button>
                </div>
            `;

            msg.innerHTML = formHtml;
            chatMessages.appendChild(msg);
            scrollToBottom();

            const submitBtn = msg.querySelector('.intake-submit-btn');
            submitBtn.addEventListener('click', () => {
                const answers = [];
                msg.querySelectorAll('.intake-answer-input').forEach((ta, i) => {
                    answers.push({
                        question: questions[i],
                        answer: ta.value.trim(),
                    });
                });
                submitBtn.disabled = true;
                submitBtn.textContent = 'Submitting...';
                // Disable textareas
                msg.querySelectorAll('.intake-answer-input').forEach(ta => {
                    ta.disabled = true;
                });
                resolve(answers);
            });
        });
    }

    /**
     * Show a "Stop & Summarize" button during streaming discussions.
     * Returns a handle to remove it when no longer needed.
     */
    function showStopButton(onStop) {
        const msg = document.createElement('div');
        msg.className = 'message message-system stop-btn-container';
        msg.innerHTML = `
            <button class="stop-discussion-btn">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none" style="margin-right:6px">
                    <rect x="3" y="3" width="10" height="10" rx="2" fill="currentColor"/>
                </svg>
                Stop &amp; Summarize
            </button>
        `;
        chatMessages.appendChild(msg);
        scrollToBottom();

        msg.querySelector('.stop-discussion-btn').addEventListener('click', () => {
            msg.remove();
            onStop();
        });

        return { remove() { msg.remove(); } };
    }

    /**
     * Show a "Download Podcast" button at the end of a session.
     */
    function showPodcastButton(onClickCallback) {
        const msg = document.createElement('div');
        msg.className = 'message message-system';
        msg.innerHTML = `
            <div class="session-complete-banner">
                <span class="session-complete-text">Discussion complete</span>
                <button class="podcast-generate-btn">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="margin-right:6px">
                        <path d="M4 2L14 8L4 14V2Z" fill="currentColor"/>
                    </svg>
                    Generate Podcast
                </button>
            </div>
        `;
        chatMessages.appendChild(msg);
        scrollToBottom();

        msg.querySelector('.podcast-generate-btn').addEventListener('click', async (e) => {
            const btn = e.currentTarget;
            btn.disabled = true;
            btn.innerHTML = '<span class="thinking-dots">Generating audio</span>';
            try {
                await onClickCallback(btn, msg);
            } catch (err) {
                btn.textContent = 'Error: ' + err.message;
                btn.disabled = false;
            }
        });
    }

    /**
     * Show an in-app audio player (like NotebookLM).
     * @param {Element} container - parent element to append the player to
     * @param {string} audioUrl - server URL to the audio file
     */
    function showAudioPlayer(container, audioUrl) {
        // Replace the banner contents with the player
        const banner = container.querySelector('.session-complete-banner');
        if (banner) banner.remove();

        const player = document.createElement('div');
        player.className = 'podcast-player';
        player.innerHTML = `
            <div class="podcast-player-header">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M4 2L14 8L4 14V2Z" fill="currentColor"/>
                </svg>
                <span>Council Podcast</span>
            </div>
            <div class="podcast-player-body">
                <button class="player-play-btn" title="Play">
                    <svg class="icon-play" width="20" height="20" viewBox="0 0 16 16" fill="none">
                        <path d="M4 2L14 8L4 14V2Z" fill="currentColor"/>
                    </svg>
                    <svg class="icon-pause" width="20" height="20" viewBox="0 0 16 16" fill="none" style="display:none">
                        <rect x="3" y="2" width="4" height="12" rx="1" fill="currentColor"/>
                        <rect x="9" y="2" width="4" height="12" rx="1" fill="currentColor"/>
                    </svg>
                </button>
                <div class="player-progress-area">
                    <div class="player-time"><span class="player-current">0:00</span> / <span class="player-duration">0:00</span></div>
                    <div class="player-track">
                        <div class="player-track-fill"></div>
                        <input type="range" class="player-seek" min="0" max="100" value="0" step="0.1">
                    </div>
                </div>
                <div class="player-speed-btn" title="Playback speed">1x</div>
                <a class="player-download-link" href="${audioUrl}?dl=1" download title="Download">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M8 1V10M8 10L5 7M8 10L11 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M2 12V14H14V12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </a>
            </div>
        `;
        container.appendChild(player);

        const audio = new Audio(audioUrl);
        const playBtn = player.querySelector('.player-play-btn');
        const iconPlay = player.querySelector('.icon-play');
        const iconPause = player.querySelector('.icon-pause');
        const currentEl = player.querySelector('.player-current');
        const durationEl = player.querySelector('.player-duration');
        const trackFill = player.querySelector('.player-track-fill');
        const seekInput = player.querySelector('.player-seek');
        const speedBtn = player.querySelector('.player-speed-btn');
        const speeds = [1, 1.25, 1.5, 1.75, 2, 0.75];
        let speedIdx = 0;

        function fmt(s) {
            const m = Math.floor(s / 60);
            const sec = Math.floor(s % 60);
            return m + ':' + (sec < 10 ? '0' : '') + sec;
        }

        audio.addEventListener('loadedmetadata', () => {
            durationEl.textContent = fmt(audio.duration);
        });

        audio.addEventListener('timeupdate', () => {
            if (!audio.duration) return;
            const pct = (audio.currentTime / audio.duration) * 100;
            trackFill.style.width = pct + '%';
            seekInput.value = pct;
            currentEl.textContent = fmt(audio.currentTime);
        });

        audio.addEventListener('ended', () => {
            iconPlay.style.display = '';
            iconPause.style.display = 'none';
            playBtn.classList.remove('playing');
        });

        playBtn.addEventListener('click', () => {
            if (audio.paused) {
                audio.play();
                iconPlay.style.display = 'none';
                iconPause.style.display = '';
                playBtn.classList.add('playing');
            } else {
                audio.pause();
                iconPlay.style.display = '';
                iconPause.style.display = 'none';
                playBtn.classList.remove('playing');
            }
        });

        seekInput.addEventListener('input', () => {
            if (!audio.duration) return;
            audio.currentTime = (seekInput.value / 100) * audio.duration;
        });

        speedBtn.addEventListener('click', () => {
            speedIdx = (speedIdx + 1) % speeds.length;
            audio.playbackRate = speeds[speedIdx];
            speedBtn.textContent = speeds[speedIdx] + 'x';
        });

        scrollToBottom();
    }

    /**
     * Show a biography card for a nominated/custom elder.
     * @param {Object} elderData - { id, name, title, expertise, nominated_by }
     * @param {Object} biography - { summary, source, url, thumbnail }
     * @param {Object} [options] - { showSaveButton, showBooksButton }
     */
    function showBiographyCard(elderData, biography, options = {}) {
        const { showSaveButton = true, showBooksButton = true } = options;
        const msg = document.createElement('div');
        msg.className = 'message message-biography';

        let thumbHtml = '';
        if (biography.thumbnail) {
            thumbHtml = `<img class="biography-thumb" src="${escapeHtml(biography.thumbnail)}" alt="${escapeHtml(elderData.name)}">`;
        }

        let sourceHtml = '';
        if (biography.url) {
            sourceHtml = `<a class="biography-source-link" href="${escapeHtml(biography.url)}" target="_blank" rel="noopener">Wikipedia</a>`;
        } else if (biography.source === 'llm') {
            sourceHtml = '<span class="biography-source-tag">AI-generated</span>';
        }

        let actionsHtml = '';
        if (showSaveButton || showBooksButton) {
            actionsHtml = '<div class="biography-actions">';
            if (showSaveButton) {
                actionsHtml += `<button class="biography-action-btn save-custom-elder-btn" data-elder='${JSON.stringify(elderData).replace(/'/g, "&#39;")}'>Save as Custom Elder</button>`;
            }
            if (showBooksButton) {
                actionsHtml += `<button class="biography-action-btn browse-books-btn" data-elder-id="${escapeHtml(elderData.id)}" data-name="${escapeHtml(elderData.name)}" data-expertise="${escapeHtml(elderData.expertise || '')}">Browse Books</button>`;
            }
            actionsHtml += `<button class="biography-action-btn videos-btn" data-elder-id="${escapeHtml(elderData.id)}" data-name="${escapeHtml(elderData.name)}" data-expertise="${escapeHtml(elderData.expertise || elderData.title || '')}">Videos</button>`;
            actionsHtml += `<button class="biography-action-btn memorabilia-btn" data-elder-id="${escapeHtml(elderData.id)}" data-name="${escapeHtml(elderData.name)}" data-expertise="${escapeHtml(elderData.expertise || elderData.title || '')}">Memorabilia</button>`;
            actionsHtml += '</div>';
        }

        msg.innerHTML = `
            <div class="biography-card">
                <div class="biography-header">
                    ${thumbHtml}
                    <div class="biography-info">
                        <div class="biography-name">${escapeHtml(elderData.name)}</div>
                        <div class="biography-title">${escapeHtml(elderData.title || elderData.expertise || '')}</div>
                    </div>
                    ${sourceHtml}
                </div>
                <div class="biography-summary">${escapeHtml(biography.summary || '')}</div>
                ${actionsHtml}
            </div>
        `;
        chatMessages.appendChild(msg);
        scrollToBottom();

        // Wire up action buttons
        const saveBtn = msg.querySelector('.save-custom-elder-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                saveBtn.disabled = true;
                saveBtn.textContent = 'Saving...';
                try {
                    const data = JSON.parse(saveBtn.dataset.elder);
                    data.biography = biography;
                    await API.saveCustomElder(data);
                    saveBtn.textContent = 'Saved';
                    saveBtn.classList.add('biography-action-saved');
                    if (typeof SidebarComponent !== 'undefined') {
                        SidebarComponent.loadCustomElders();
                    }
                } catch (e) {
                    saveBtn.textContent = 'Error';
                }
            });
        }

        const booksBtn = msg.querySelector('.browse-books-btn');
        if (booksBtn) {
            booksBtn.addEventListener('click', async () => {
                booksBtn.disabled = true;
                booksBtn.textContent = 'Loading...';
                try {
                    const books = await API.getElderBooks(
                        booksBtn.dataset.elderId,
                        booksBtn.dataset.name,
                        booksBtn.dataset.expertise
                    );
                    showBookRecommendations(
                        { name: booksBtn.dataset.name, id: booksBtn.dataset.elderId },
                        books
                    );
                    booksBtn.textContent = 'Books shown below';
                } catch (e) {
                    booksBtn.textContent = 'Error loading books';
                    booksBtn.disabled = false;
                }
            });
        }

        // Videos button → opens profile panel to Videos tab
        const videosBtn = msg.querySelector('.videos-btn');
        if (videosBtn && typeof ElderProfileComponent !== 'undefined') {
            videosBtn.addEventListener('click', () => {
                ElderProfileComponent.openToTab({
                    id: videosBtn.dataset.elderId,
                    name: videosBtn.dataset.name,
                    expertise: videosBtn.dataset.expertise,
                    title: elderData.title || elderData.expertise || '',
                    era: elderData.era || '',
                }, 'videos');
            });
        }

        // Memorabilia button → opens profile panel to Memorabilia tab
        const memBtn = msg.querySelector('.memorabilia-btn');
        if (memBtn && typeof ElderProfileComponent !== 'undefined') {
            memBtn.addEventListener('click', () => {
                ElderProfileComponent.openToTab({
                    id: memBtn.dataset.elderId,
                    name: memBtn.dataset.name,
                    expertise: memBtn.dataset.expertise,
                    title: elderData.title || elderData.expertise || '',
                    era: elderData.era || '',
                }, 'memorabilia');
            });
        }

        return msg;
    }

    /**
     * Show book recommendations with affiliate links.
     */
    function showBookRecommendations(elderData, books) {
        if (!books || books.length === 0) return;

        const msg = document.createElement('div');
        msg.className = 'message message-books';

        const byBooks = books.filter(b => b.type === 'by');
        const aboutBooks = books.filter(b => b.type === 'about');

        let booksHtml = '';

        if (byBooks.length > 0) {
            booksHtml += `<div class="books-section-label">Works by ${escapeHtml(elderData.name)}</div>`;
            byBooks.forEach(b => {
                booksHtml += _bookItemHtml(b, elderData);
            });
        }

        if (aboutBooks.length > 0) {
            booksHtml += `<div class="books-section-label">Books about ${escapeHtml(elderData.name)}</div>`;
            aboutBooks.forEach(b => {
                booksHtml += _bookItemHtml(b, elderData);
            });
        }

        msg.innerHTML = `
            <div class="books-card">
                <div class="books-header">Recommended Reading</div>
                ${booksHtml}
                <div class="affiliate-disclosure">As an Amazon Associate, we earn from qualifying purchases.</div>
            </div>
        `;
        chatMessages.appendChild(msg);
        scrollToBottom();

        // Wire up Kindle import buttons
        msg.querySelectorAll('.kindle-import-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const elderId = btn.dataset.elderId;
                const fileInput = document.createElement('input');
                fileInput.type = 'file';
                fileInput.accept = '.epub,.txt';
                fileInput.addEventListener('change', async () => {
                    if (!fileInput.files[0]) return;
                    btn.disabled = true;
                    btn.textContent = 'Importing...';
                    try {
                        await API.importKindleFile(fileInput.files[0], elderId);
                        btn.textContent = 'Imported!';
                        btn.classList.add('kindle-imported');
                    } catch (e) {
                        btn.textContent = 'Error';
                        btn.disabled = false;
                    }
                });
                fileInput.click();
            });
        });

        return msg;
    }

    function _bookItemHtml(book, elderData) {
        return `
            <div class="book-item">
                <div class="book-info">
                    <span class="book-title">${escapeHtml(book.title)}</span>
                    <span class="book-author">by ${escapeHtml(book.author)}</span>
                </div>
                <div class="book-actions">
                    <a class="book-link" href="${escapeHtml(book.affiliate_url)}" target="_blank" rel="noopener">Amazon</a>
                    ${book.kindle_url ? `<a class="book-link book-link-kindle" href="${escapeHtml(book.kindle_url)}" target="_blank" rel="noopener">Kindle</a>` : ''}
                    <button class="kindle-import-btn" data-elder-id="${escapeHtml(elderData.id)}">Import</button>
                </div>
            </div>
        `;
    }

    return {
        init, clear, hideWelcome, scrollToBottom,
        addUserMessage, addSystemMessage, addNomination,
        startElderMessage, startSynthesisMessage, startModeratorMessage,
        showModeratorQuestion, showIntakeForm, showPodcastButton, showAudioPlayer,
        showStopButton, showBiographyCard, showBookRecommendations,
    };
})();
