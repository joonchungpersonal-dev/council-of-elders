/**
 * Simple reactive state with subscribe/emit pattern.
 */
window.AppState = (() => {
    const state = {
        provider: 'ollama',        // 'ollama' | 'anthropic'
        mode: 'panel',            // 'panel' | 'roundtable' | 'ask' | 'intake'
        selectedElders: [],        // array of elder IDs
        status: 'disconnected',    // 'connected' | 'disconnected'
        currentModel: '',          // model name string
        isStreaming: false,        // true while SSE is active
        intakeQuestions: [],       // parsed from synthesis
        messages: [],              // chat message history for display
        dialecticTension: 50,      // 0 (collaborative) to 100 (debate)
        customElders: [],          // persisted custom elders
        enrichmentTasks: {},       // task_id -> status
        enrichmentEnabled: true,   // auto-enrich on nomination
        autoSelectElders: true,    // let LLM choose elders when none selected
        responseLength: 'moderate', // 'brief' | 'moderate' | 'detailed'
        autoSelectLimit: 5,         // max elders for auto-select (3-7)
        discussionLength: 'quick', // 'lightning' | 'quick' | 'short' | 'medium' | 'long' | 'extended'
        poetryForm: 'spoken_word',  // poetry type for poetry slam mode
        showAllModes: false,        // power-user: show all 7 mode buttons
    };

    const listeners = {};

    function get(key) {
        return state[key];
    }

    function set(key, value) {
        const old = state[key];
        state[key] = value;
        emit(key, value, old);
    }

    function on(key, callback) {
        if (!listeners[key]) listeners[key] = [];
        listeners[key].push(callback);
    }

    function emit(key, value, old) {
        (listeners[key] || []).forEach(cb => cb(value, old));
    }

    function getAll() {
        return { ...state };
    }

    return { get, set, on, getAll };
})();
