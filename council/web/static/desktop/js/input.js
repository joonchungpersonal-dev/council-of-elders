/**
 * Input bar: auto-grow textarea, Cmd+Enter send, voice input, disabled during stream.
 */
window.InputComponent = (() => {
    let chatInput, sendBtn, voiceBtn;
    let onSendCallback = null;
    let recognition = null;
    let isRecording = false;

    function init(onSend) {
        chatInput = document.getElementById('chat-input');
        sendBtn = document.getElementById('send-btn');
        voiceBtn = document.getElementById('voice-btn');
        onSendCallback = onSend;

        // Auto-grow
        chatInput.addEventListener('input', autoGrow);

        // Enable/disable send based on content
        chatInput.addEventListener('input', updateSendButton);

        // Cmd/Ctrl+Enter to send
        chatInput.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                e.preventDefault();
                send();
            }
        });

        // Click send
        sendBtn.addEventListener('click', send);

        // Voice input
        initVoice();
        voiceBtn.addEventListener('click', toggleVoice);

        // Disable during streaming
        AppState.on('isStreaming', (streaming) => {
            chatInput.disabled = streaming;
            updateSendButton();
            if (!streaming) {
                chatInput.focus();
            }
        });
    }

    function initVoice() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            voiceBtn.style.display = 'none';
            return;
        }

        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        let finalTranscript = '';

        recognition.onresult = (event) => {
            let interim = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interim = transcript;
                }
            }
            // Show current text: what was there before + final so far + interim
            const before = chatInput.dataset.preVoice || '';
            chatInput.value = before + finalTranscript + interim;
            autoGrow();
            updateSendButton();
        };

        recognition.onend = () => {
            if (isRecording) {
                // Apply final transcript and stop
                isRecording = false;
                voiceBtn.classList.remove('recording');
                finalTranscript = '';
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            isRecording = false;
            voiceBtn.classList.remove('recording');
            finalTranscript = '';
        };
    }

    function toggleVoice() {
        if (!recognition) return;

        if (isRecording) {
            recognition.stop();
            isRecording = false;
            voiceBtn.classList.remove('recording');
        } else {
            // Save current text so voice appends to it
            chatInput.dataset.preVoice = chatInput.value;
            isRecording = true;
            voiceBtn.classList.add('recording');
            recognition.start();
        }
    }

    function autoGrow() {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
    }

    function updateSendButton() {
        const hasText = chatInput.value.trim().length > 0;
        const isStreaming = AppState.get('isStreaming');
        sendBtn.disabled = !hasText || isStreaming;
    }

    function send() {
        const text = chatInput.value.trim();
        if (!text || AppState.get('isStreaming')) return;

        // Stop voice if active
        if (isRecording && recognition) {
            recognition.stop();
            isRecording = false;
            voiceBtn.classList.remove('recording');
        }

        chatInput.value = '';
        chatInput.dataset.preVoice = '';
        chatInput.style.height = 'auto';
        updateSendButton();

        if (onSendCallback) {
            onSendCallback(text);
        }
    }

    function focus() {
        if (chatInput) chatInput.focus();
    }

    return { init, focus };
})();
