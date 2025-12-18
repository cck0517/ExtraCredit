// Insights page JavaScript
(function() {
    'use strict';

    const FALLBACK_PROVIDER_RGB = {
        'OpenAI': '16 163 127',
        'Google': '251 191 36',
        'Anthropic': '248 113 113',
        'DeepSeek': '59 130 246',
        'Mistral AI': '251 146 60',
        'xAI': '168 85 247',
        'Alibaba': '139 92 246',
        'Moonshot AI': '14 165 233',
        'Perplexity': '100 116 139',
        'Meta': '148 163 184',
        'Other': '100 116 139',
        'Unknown': '100 116 139',
    };

    const MODEL_VARIANTS = [-0.16, -0.12, -0.08, -0.04, 0, 0.04, 0.08, 0.12, 0.16];

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
            const modelName = extractLabel(el.textContent);
            const rgb = getModelRgb(modelName);
            applyRgbToPill(el, rgb, { isDark });
        });

        // Strength tags (LLM Performance Analysis): color by the model's provider/model color.
        document.querySelectorAll('.llm-detail-card').forEach(card => {
            const modelName = getCardModelName(card);
            const rgb = getModelRgb(modelName);

            card.querySelectorAll('.tag').forEach(tagEl => {
                applyRgbToPill(tagEl, rgb, { isDark });
            });

            const countEl = card.querySelector('.count');
            if (countEl && rgb) {
                const rgbCsv = rgbToCssRgb(rgb);
                countEl.style.background = rgbCsv;
                countEl.style.color = getReadableTextColor(rgbCsv);
            }
        });
    }

    function applyRgbToPill(el, rgb, { isDark }) {
        if (!rgb) return;
        el.style.setProperty('--pill-rgb', rgb);
        el.style.setProperty('--pill-fg', isDark ? rgbToCssRgb(rgb) : '#0f172a');
    }

    function extractLabel(text) {
        if (!text) return '';
        // Strip trailing counts like " (3)" from LLM badges.
        return text.replace(/\s*\(\d+.*\)\s*$/, '').trim();
    }

    function getCardModelName(card) {
        const heading = card.querySelector('h4');
        if (!heading) return '';

        const clone = heading.cloneNode(true);
        const count = clone.querySelector('.count');
        if (count) count.remove();
        return clone.textContent.trim();
    }

    function getModelRgb(modelName) {
        const normalized = normalizeKey(modelName);
        if (!normalized) return null;

        const palette = window.INSIGHTS_PALETTE && window.INSIGHTS_PALETTE.llms
            ? window.INSIGHTS_PALETTE
            : null;

        if (palette && palette.llms && palette.llms[normalized] && palette.llms[normalized].rgb) {
            return palette.llms[normalized].rgb;
        }

        const provider = inferProvider(modelName);
        const providerRgb = (palette && palette.providers && palette.providers[provider])
            ? palette.providers[provider]
            : (FALLBACK_PROVIDER_RGB[provider] || FALLBACK_PROVIDER_RGB.Unknown);

        return variantRgb(providerRgb, modelName);
    }

    function normalizeKey(text) {
        return (text || '').trim().toLowerCase();
    }

    function inferProvider(modelName) {
        const name = normalizeKey(modelName);
        if (!name) return 'Unknown';

        if (name.includes('gpt') || name.includes('chatgpt') || name.includes('o1') || name.includes('o3')) return 'OpenAI';
        if (name.includes('claude')) return 'Anthropic';
        if (name.includes('gemini') || name.includes('gemma')) return 'Google';
        if (name.includes('deepseek')) return 'DeepSeek';
        if (name.includes('mistral')) return 'Mistral AI';
        if (name.includes('grok')) return 'xAI';
        if (name.includes('qwen')) return 'Alibaba';
        if (name.includes('kimi')) return 'Moonshot AI';
        if (name.includes('perplexity')) return 'Perplexity';
        if (name.includes('llama')) return 'Meta';

        return 'Other';
    }

    function variantRgb(baseRgb, modelName) {
        const base = parseRgb(baseRgb);
        if (!base) return null;

        const variant = MODEL_VARIANTS[hashString(normalizeKey(modelName)) % MODEL_VARIANTS.length];
        if (variant === 0) return `${base[0]} ${base[1]} ${base[2]}`;

        const mix = variant > 0 ? [255, 255, 255] : [0, 0, 0];
        const t = Math.abs(variant);
        const out = [
            Math.round(base[0] * (1 - t) + mix[0] * t),
            Math.round(base[1] * (1 - t) + mix[1] * t),
            Math.round(base[2] * (1 - t) + mix[2] * t),
        ];

        return `${out[0]} ${out[1]} ${out[2]}`;
    }

    function parseRgb(rgb) {
        if (!rgb) return null;
        const parts = String(rgb).trim().split(/\s+/).slice(0, 3).map(n => Number.parseInt(n, 10));
        if (parts.length !== 3 || parts.some(n => !Number.isFinite(n))) return null;
        return parts;
    }

    function rgbToCssRgb(rgb) {
        return `rgb(${String(rgb).trim().split(/\s+/).slice(0, 3).join(', ')})`;
    }

    function getReadableTextColor(cssRgb) {
        const match = /^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/.exec(cssRgb);
        if (!match) return '#ffffff';
        const r = Number(match[1]) / 255;
        const g = Number(match[2]) / 255;
        const b = Number(match[3]) / 255;
        const luminance = relativeLuminance([r, g, b]);
        return luminance > 0.6 ? '#0f172a' : '#ffffff';
    }

    function relativeLuminance([r, g, b]) {
        const R = srgbToLinear(r);
        const G = srgbToLinear(g);
        const B = srgbToLinear(b);
        return 0.2126 * R + 0.7152 * G + 0.0722 * B;
    }

    function srgbToLinear(c) {
        return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
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
