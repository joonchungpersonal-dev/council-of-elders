/**
 * Theme management: system preference detection, manual toggle, localStorage.
 */
window.ThemeManager = (() => {
    const STORAGE_KEY = 'council-theme';

    function getSystemPreference() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function getSavedTheme() {
        return localStorage.getItem(STORAGE_KEY);
    }

    function apply(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
    }

    function init() {
        const saved = getSavedTheme();
        const theme = saved || getSystemPreference();
        apply(theme);

        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!getSavedTheme()) {
                apply(e.matches ? 'dark' : 'light');
            }
        });
    }

    function toggle() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        apply(next);
        return next;
    }

    function current() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }

    return { init, toggle, current };
})();

// Initialize theme immediately to prevent flash
ThemeManager.init();
