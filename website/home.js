// Home page JavaScript
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        if (typeof participationData === 'undefined') {
            console.error('Data not loaded');
            return;
        }
        initHomePage();
    });

    function initHomePage() {
        updateStats();
        renderProviderTags();
        renderLLMTags();
        renderHWTags();
        renderRecentSubmissions();
    }

    function updateStats() {
        const total = participationData.total_count;
        const students = new Set(participationData.threads.map(t => t.author)).size;
        const llms = uniqueLLMs.length;
        const hws = uniqueHWs.length;

        animateNumber('stat-submissions', total);
        animateNumber('stat-students', students);
        animateNumber('stat-llms', llms);
        animateNumber('stat-homeworks', hws);
    }

    function animateNumber(id, target) {
        const el = document.getElementById(id);
        if (!el) return;

        if (!Number.isFinite(target)) {
            el.textContent = target;
            return;
        }

        const prefersReducedMotion = window.matchMedia &&
            window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (prefersReducedMotion) {
            el.textContent = target;
            return;
        }

        let current = 0;
        const duration = 1000;
        const step = target / (duration / 16);

        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                el.textContent = target;
                clearInterval(timer);
            } else {
                el.textContent = Math.floor(current);
            }
        }, 16);
    }

    function renderProviderTags() {
        const container = document.getElementById('provider-tags');
        if (!container) return;

        // Get counts and sort by popularity
        const counts = {};
        participationData.threads.forEach(t => {
            const provider = t.provider || 'Other';
            counts[provider] = (counts[provider] || 0) + 1;
        });

        const sorted = Object.entries(counts)
            .sort((a, b) => b[1] - a[1]);

        container.innerHTML = sorted.map(([provider, count], index) =>
            `<a href="browse.html?provider=${encodeURIComponent(provider)}" class="tag-link" style="animation-delay: ${index * 0.05}s">
                ${escapeHtml(provider)} <span class="tag-count">${count}</span>
            </a>`
        ).join('');
    }

    function renderLLMTags() {
        const container = document.getElementById('llm-tags');
        if (!container) return;

        // Get counts and sort by popularity
        const counts = {};
        participationData.threads.forEach(t => {
            counts[t.llm_used] = (counts[t.llm_used] || 0) + 1;
        });

        const sorted = Object.entries(counts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 12); // Top 12

        container.innerHTML = sorted.map(([llm, count], index) =>
            `<a href="browse.html?llm=${encodeURIComponent(llm)}" class="tag-link" style="animation-delay: ${index * 0.05}s">
                ${escapeHtml(llm)} <span class="tag-count">${count}</span>
            </a>`
        ).join('');
    }

    function renderHWTags() {
        const container = document.getElementById('hw-tags');
        if (!container) return;

        // Get counts
        const counts = {};
        participationData.threads.forEach(t => {
            counts[t.homework] = (counts[t.homework] || 0) + 1;
        });

        // Sort by homework number
        const sorted = Object.entries(counts).sort((a, b) => {
            const numA = parseInt(a[0].replace(/\D/g, '')) || 999;
            const numB = parseInt(b[0].replace(/\D/g, '')) || 999;
            return numA - numB;
        });

        container.innerHTML = sorted.map(([hw, count], index) =>
            `<a href="browse.html?hw=${encodeURIComponent(hw)}" class="tag-link" style="animation-delay: ${index * 0.05}s">
                ${escapeHtml(hw)} <span class="tag-count">${count}</span>
            </a>`
        ).join('');
    }

    function renderRecentSubmissions() {
        const container = document.getElementById('recent-submissions');
        if (!container) return;

        // Get 6 most recent
        const recent = [...participationData.threads]
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .slice(0, 6);

        container.innerHTML = recent.map(thread => createSubmissionCard(thread)).join('');
    }

    function createSubmissionCard(thread) {
        const truncated = thread.content.length > 120
            ? thread.content.substring(0, 120) + '...'
            : thread.content;
        const date = formatDate(thread.created_at);

        return `
            <a href="browse.html?thread=${thread.id}" class="submission-card">
                <div class="card-tags">
                    <span class="tag tag-provider">${escapeHtml(thread.provider || 'Other')}</span>
                    <span class="tag tag-llm">${escapeHtml(thread.llm_used)}</span>
                    <span class="tag tag-hw">${escapeHtml(thread.homework)}</span>
                </div>
                <h4 class="card-title">${escapeHtml(thread.title)}</h4>
                <p class="card-author">by ${escapeHtml(thread.author)}</p>
                <p class="card-excerpt">${escapeHtml(truncated)}</p>
                <div class="card-footer">
                    <span class="card-date">${date}</span>
                    <span class="card-views">${thread.view_count} views</span>
                </div>
            </a>
        `;
    }

    function formatDate(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch {
            return '';
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
