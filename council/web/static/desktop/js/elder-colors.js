/**
 * Map Rich terminal color names to CSS hex values.
 */
window.ElderColors = {
    // Mapping from Python Rich color names used in elder profiles
    dark_orange: '#ff8c00',
    deep_sky_blue3: '#0087d7',
    green3: '#00af00',
    purple: '#800080',
    medium_purple: '#af87d7',
    medium_purple3: '#8700af',
    dark_red: '#870000',
    red3: '#d70000',
    bright_red: '#ff0000',
    gold: '#ffd700',
    gold3: '#d7af00',
    steel_blue: '#5f87af',
    bright_blue: '#5f87ff',
    cyan: '#00ffff',
    cyan3: '#00d7af',
    orange3: '#d78700',
    dark_orange3: '#d75f00',
    dark_goldenrod: '#af8700',
    dark_sea_green: '#87af87',
    deep_pink3: '#d7005f',
    yellow: '#ffff00',
    white: '#d0d0d0',

    /**
     * Get the CSS hex color for a Rich color name.
     * Falls back to the accent color if not mapped.
     */
    get(richColorName) {
        // Replace hyphens/spaces with underscores to normalize
        const key = (richColorName || '').replace(/[-\s]/g, '_').toLowerCase();
        return this[key] || '#6366f1';
    }
};
