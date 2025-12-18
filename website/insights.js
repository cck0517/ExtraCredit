// Insights page JavaScript
(function() {
    'use strict';

    const PALETTE_RGB = [
        '59 130 246',  // blue-500
        '96 165 250',  // blue-400
        '56 189 248',  // sky-400
        '34 211 238',  // cyan-400
        '45 212 191',  // teal-400
        '52 211 153',  // emerald-400
        '163 230 53',  // lime-400
        '250 204 21',  // yellow-400
        '251 146 60',  // orange-400
        '248 113 113', // red-400
        '167 139 250', // violet-400
    ];

    document.addEventListener('DOMContentLoaded', function() {
        applyPillColors();

        const media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
        if (media) {
            if (typeof media.addEventListener === 'function') {
                media.addEventListener('change', applyPillColors);
            } else if (typeof media.addListener === 'function') {
                media.addListener(applyPillColors);
            }
        }
    });

    function applyPillColors() {
        const isDark = window.matchMedia &&
            window.matchMedia('(prefers-color-scheme: dark)').matches;

        // LLM badges (Homework Submission Breakdown)
        document.querySelectorAll('.llm-badge').forEach(el => {
            const label = normalizeLabel(extractLabel(el.textContent));
            applyColorToElement(el, label, { isDark, kind: 'llm' });
        });

        // Strength tags (LLM Performance Analysis)
        document.querySelectorAll('.llm-detail-card .tag').forEach(el => {
            const label = normalizeLabel(el.textContent);
            applyColorToElement(el, label, { isDark, kind: 'tag' });
        });
    }

    function applyColorToElement(el, label, { isDark, kind }) {
        const index = hashString(label) % PALETTE_RGB.length;
        const rgb = PALETTE_RGB[index];

        el.style.setProperty('--pill-rgb', rgb);

        // In light mode: keep text dark for readability (background provides color)
        // In dark mode: use the palette color as text for a more vivid look.
        el.style.setProperty('--pill-fg', isDark ? `rgb(${rgb.replace(/ /g, ', ')})` : '#0f172a');

        // Optional: slightly vary radius/spacing by kind if needed later.
        void kind;
    }

    function extractLabel(text) {
        if (!text) return '';
        // Strip trailing counts like " (3)" from LLM badges.
        return text.replace(/\s*\(\d+.*\)\s*$/, '').trim();
    }

    function normalizeLabel(text) {
        return (text || '').trim().toLowerCase();
    }

    function hashString(str) {
        // FNV-1a 32-bit hash
        let hash = 0x811c9dc5;
        for (let i = 0; i < str.length; i++) {
            hash ^= str.charCodeAt(i);
            hash = Math.imul(hash, 0x01000193);
        }
        return hash >>> 0;
    }
})();
