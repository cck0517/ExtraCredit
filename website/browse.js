// Browse page JavaScript
(function() {
    'use strict';

    // State
    let currentPage = 1;
    const perPage = 12;
    let filteredThreads = [];
    let currentFilters = {
        search: '',
        provider: 'all',
        llm: 'all',
        hw: 'all',
        sort: 'date-desc'
    };
    let lastFocusedElement = null;
    let activeModalThreadId = null;

    document.addEventListener('DOMContentLoaded', function() {
        if (typeof participationData === 'undefined') {
            console.error('Data not loaded');
            return;
        }
        initBrowsePage();
    });

    function initBrowsePage() {
        populateFilters();
        parseUrlParams();
        setupEventListeners();
        setupHistorySync();
        applyFiltersAndRender();
        syncModalToUrl();
    }

    function populateFilters() {
        const providerSelect = document.getElementById('providerFilter');
        const llmSelect = document.getElementById('llmFilter');
        const hwSelect = document.getElementById('hwFilter');

        // Get counts for each filter
        const providerCounts = {};
        const hwCounts = {};
        participationData.threads.forEach(t => {
            const provider = t.provider || 'Other';
            providerCounts[provider] = (providerCounts[provider] || 0) + 1;
            hwCounts[t.homework] = (hwCounts[t.homework] || 0) + 1;
        });

        // Populate providers with counts, sorted by count
        if (providerSelect && typeof uniqueProviders !== 'undefined') {
            const sortedProviders = [...uniqueProviders].sort((a, b) =>
                (providerCounts[b] || 0) - (providerCounts[a] || 0)
            );
            sortedProviders.forEach(provider => {
                const opt = document.createElement('option');
                opt.value = provider;
                opt.textContent = `${provider} (${providerCounts[provider] || 0})`;
                providerSelect.appendChild(opt);
            });
        }

        // Populate LLMs
        if (llmSelect) {
            updateLLMOptions();
        }

        // Populate homework with counts
        if (hwSelect) {
            uniqueHWs.forEach(hw => {
                const opt = document.createElement('option');
                opt.value = hw;
                opt.textContent = `${hw} (${hwCounts[hw] || 0})`;
                hwSelect.appendChild(opt);
            });
        }
    }

    function updateLLMOptions() {
        const llmSelect = document.getElementById('llmFilter');
        if (!llmSelect) return;

        const currentValue = llmSelect.value;

        // Clear existing options except "All"
        llmSelect.innerHTML = '<option value="all">All LLMs</option>';

        // Get LLM counts based on current provider filter
        const llmCounts = {};
        participationData.threads.forEach(t => {
            if (currentFilters.provider === 'all' || t.provider === currentFilters.provider) {
                llmCounts[t.llm_used] = (llmCounts[t.llm_used] || 0) + 1;
            }
        });

        // Filter LLMs based on selected provider
        let llmsToShow = uniqueLLMs;
        if (currentFilters.provider !== 'all') {
            llmsToShow = uniqueLLMs.filter(llm => llmCounts[llm] > 0);
        }

        // Sort by count
        llmsToShow = [...llmsToShow].sort((a, b) =>
            (llmCounts[b] || 0) - (llmCounts[a] || 0)
        );

        llmsToShow.forEach(llm => {
            const opt = document.createElement('option');
            opt.value = llm;
            opt.textContent = `${llm} (${llmCounts[llm] || 0})`;
            llmSelect.appendChild(opt);
        });

        // Restore selection if still valid
        if (llmsToShow.includes(currentValue)) {
            llmSelect.value = currentValue;
        } else {
            llmSelect.value = 'all';
            currentFilters.llm = 'all';
        }
    }

    function parseUrlParams() {
        const params = new URLSearchParams(window.location.search);

        if (params.has('provider')) {
            currentFilters.provider = params.get('provider');
            const providerSelect = document.getElementById('providerFilter');
            if (providerSelect) providerSelect.value = currentFilters.provider;
            updateLLMOptions();
        }

        if (params.has('llm')) {
            currentFilters.llm = params.get('llm');
            const llmSelect = document.getElementById('llmFilter');
            if (llmSelect) llmSelect.value = currentFilters.llm;
        }

        if (params.has('hw')) {
            currentFilters.hw = params.get('hw');
            const hwSelect = document.getElementById('hwFilter');
            if (hwSelect) hwSelect.value = currentFilters.hw;
        }

        if (params.has('search')) {
            currentFilters.search = params.get('search');
            const searchInput = document.getElementById('searchInput');
            if (searchInput) searchInput.value = currentFilters.search;
        }

        // Thread modal is handled by syncModalToUrl() after initial render.
    }

    function setupEventListeners() {
        const searchInput = document.getElementById('searchInput');
        const providerFilter = document.getElementById('providerFilter');
        const llmFilter = document.getElementById('llmFilter');
        const hwFilter = document.getElementById('hwFilter');
        const sortSelect = document.getElementById('sortSelect');
        const clearBtn = document.getElementById('clearFilters');

        if (searchInput) {
            searchInput.addEventListener('input', debounce(function() {
                currentFilters.search = this.value;
                currentPage = 1;
                applyFiltersAndRender();
            }, 300));
        }

        if (providerFilter) {
            providerFilter.addEventListener('change', function() {
                currentFilters.provider = this.value;
                currentFilters.llm = 'all'; // Reset LLM when provider changes
                updateLLMOptions();
                currentPage = 1;
                applyFiltersAndRender();
            });
        }

        if (llmFilter) {
            llmFilter.addEventListener('change', function() {
                currentFilters.llm = this.value;
                currentPage = 1;
                applyFiltersAndRender();
            });
        }

        if (hwFilter) {
            hwFilter.addEventListener('change', function() {
                currentFilters.hw = this.value;
                currentPage = 1;
                applyFiltersAndRender();
            });
        }

        if (sortSelect) {
            sortSelect.addEventListener('change', function() {
                currentFilters.sort = this.value;
                applyFiltersAndRender();
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', clearAllFilters);
        }

        // Modal close handlers
        const closeBtn = document.querySelector('.modal-close');
        const overlay = document.querySelector('.modal-overlay');

        if (closeBtn) closeBtn.addEventListener('click', () => closeModal());
        if (overlay) overlay.addEventListener('click', () => closeModal());

        document.addEventListener('keydown', function(e) {
            const modal = document.getElementById('modal');
            if (!modal || !modal.classList.contains('open')) return;

            if (e.key === 'Escape') {
                e.preventDefault();
                closeModal();
                return;
            }

            if (e.key === 'Tab') {
                trapFocus(e);
            }
        });
    }

    function applyFiltersAndRender() {
        filteredThreads = participationData.threads.filter(thread => {
            // Search filter
            if (currentFilters.search) {
                const search = currentFilters.search.toLowerCase();
                const matches =
                    thread.title.toLowerCase().includes(search) ||
                    thread.author.toLowerCase().includes(search) ||
                    thread.llm_used.toLowerCase().includes(search) ||
                    thread.homework.toLowerCase().includes(search) ||
                    thread.content.toLowerCase().includes(search) ||
                    (thread.provider && thread.provider.toLowerCase().includes(search));
                if (!matches) return false;
            }

            // Provider filter
            if (currentFilters.provider !== 'all' && thread.provider !== currentFilters.provider) {
                return false;
            }

            // LLM filter
            if (currentFilters.llm !== 'all' && thread.llm_used !== currentFilters.llm) {
                return false;
            }

            // Homework filter
            if (currentFilters.hw !== 'all' && thread.homework !== currentFilters.hw) {
                return false;
            }

            return true;
        });

        // Sort
        sortThreads();

        // Update URL
        updateUrl();

        // Render
        renderSubmissions();
        renderPagination();
        updateResultsInfo();
    }

    function sortThreads() {
        switch (currentFilters.sort) {
            case 'date-desc':
                filteredThreads.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                break;
            case 'date-asc':
                filteredThreads.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
                break;
            case 'views-desc':
                filteredThreads.sort((a, b) => b.view_count - a.view_count);
                break;
            case 'author-asc':
                filteredThreads.sort((a, b) => a.author.localeCompare(b.author));
                break;
            case 'llm-asc':
                filteredThreads.sort((a, b) => a.llm_used.localeCompare(b.llm_used));
                break;
        }
    }

    function updateUrl() {
        const params = new URLSearchParams();
        if (currentFilters.search) params.set('search', currentFilters.search);
        if (currentFilters.provider !== 'all') params.set('provider', currentFilters.provider);
        if (currentFilters.llm !== 'all') params.set('llm', currentFilters.llm);
        if (currentFilters.hw !== 'all') params.set('hw', currentFilters.hw);

        const currentParams = new URLSearchParams(window.location.search);
        if (currentParams.has('thread')) params.set('thread', currentParams.get('thread'));

        const newUrl = params.toString()
            ? `${window.location.pathname}?${params.toString()}`
            : window.location.pathname;

        history.replaceState(history.state, '', newUrl);

        // Update active filters and clear button
        const hasFilters = currentFilters.search ||
            currentFilters.provider !== 'all' ||
            currentFilters.llm !== 'all' ||
            currentFilters.hw !== 'all';

        const clearBtn = document.getElementById('clearFilters');
        if (clearBtn) {
            clearBtn.style.display = hasFilters ? 'inline-block' : 'none';
        }

        renderActiveFilters(hasFilters);
    }

    function renderActiveFilters(hasFilters) {
        const container = document.getElementById('activeFilters');
        if (!container) return;

        if (!hasFilters) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'flex';
        let html = '<span class="active-filters-label">Filtering by:</span>';

        if (currentFilters.search) {
            html += `<span class="filter-chip" data-filter="search">
                <span class="chip-icon">🔍</span>"${escapeHtml(currentFilters.search)}"
                <button class="chip-remove" data-type="search">&times;</button>
            </span>`;
        }

        if (currentFilters.provider !== 'all') {
            html += `<span class="filter-chip filter-chip-provider" data-filter="provider">
                ${escapeHtml(currentFilters.provider)}
                <button class="chip-remove" data-type="provider">&times;</button>
            </span>`;
        }

        if (currentFilters.llm !== 'all') {
            html += `<span class="filter-chip filter-chip-llm" data-filter="llm">
                ${escapeHtml(currentFilters.llm)}
                <button class="chip-remove" data-type="llm">&times;</button>
            </span>`;
        }

        if (currentFilters.hw !== 'all') {
            html += `<span class="filter-chip filter-chip-hw" data-filter="hw">
                ${escapeHtml(currentFilters.hw)}
                <button class="chip-remove" data-type="hw">&times;</button>
            </span>`;
        }

        container.innerHTML = html;

        // Add remove handlers
        container.querySelectorAll('.chip-remove').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const type = this.dataset.type;
                if (type === 'search') {
                    currentFilters.search = '';
                    document.getElementById('searchInput').value = '';
                } else if (type === 'provider') {
                    currentFilters.provider = 'all';
                    document.getElementById('providerFilter').value = 'all';
                    updateLLMOptions();
                } else if (type === 'llm') {
                    currentFilters.llm = 'all';
                    document.getElementById('llmFilter').value = 'all';
                } else if (type === 'hw') {
                    currentFilters.hw = 'all';
                    document.getElementById('hwFilter').value = 'all';
                }
                currentPage = 1;
                applyFiltersAndRender();
            });
        });
    }

    function renderSubmissions() {
        const container = document.getElementById('submissionsList');
        if (!container) return;

        const start = (currentPage - 1) * perPage;
        const end = start + perPage;
        const pageThreads = filteredThreads.slice(start, end);

        if (pageThreads.length === 0) {
            container.innerHTML = '<p class="no-results">No submissions found matching your criteria.</p>';
            return;
        }

        container.innerHTML = pageThreads.map(thread => createSubmissionCard(thread)).join('');

        // Add click handlers
        container.querySelectorAll('.submission-card').forEach(card => {
            card.addEventListener('click', function(e) {
                if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
                e.preventDefault();
                const threadId = parseInt(this.dataset.threadId);
                openThreadModal(threadId, this, { updateHistory: true });
            });
        });
    }

    function createSubmissionCard(thread) {
        const truncated = thread.content.length > 150
            ? thread.content.substring(0, 150) + '...'
            : thread.content;
        const date = formatDate(thread.created_at);

        const href = getThreadHref(thread.id);

        return `
            <a class="submission-card" data-thread-id="${thread.id}" href="${escapeHtml(href)}">
                <div class="card-tags">
                    <span class="tag tag-provider">${escapeHtml(thread.provider || 'Other')}</span>
                    <span class="tag tag-llm">${escapeHtml(thread.llm_used)}</span>
                    <span class="tag tag-hw">${escapeHtml(thread.homework)}</span>
                </div>
                <h3 class="card-title">${escapeHtml(thread.title)}</h3>
                <p class="card-author">by ${escapeHtml(thread.author)}</p>
                <p class="card-excerpt">${escapeHtml(truncated)}</p>
                <div class="card-footer">
                    <span class="card-date">${date}</span>
                    <span class="card-views">${thread.view_count} views</span>
                </div>
            </a>
        `;
    }

    function renderPagination() {
        const container = document.getElementById('pagination');
        if (!container) return;

        const totalPages = Math.ceil(filteredThreads.length / perPage);

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = '';

        // Previous
        if (currentPage > 1) {
            html += `<button class="page-btn" data-page="${currentPage - 1}">&laquo; Prev</button>`;
        }

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
                html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
            } else if (i === currentPage - 3 || i === currentPage + 3) {
                html += '<span class="page-dots">...</span>';
            }
        }

        // Next
        if (currentPage < totalPages) {
            html += `<button class="page-btn" data-page="${currentPage + 1}">Next &raquo;</button>`;
        }

        container.innerHTML = html;

        // Click handlers
        container.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                currentPage = parseInt(this.dataset.page);
                renderSubmissions();
                renderPagination();
                const prefersReducedMotion = window.matchMedia &&
                    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                window.scrollTo({ top: 0, behavior: prefersReducedMotion ? 'auto' : 'smooth' });
            });
        });
    }

    function updateResultsInfo() {
        const countEl = document.getElementById('results-count');
        if (countEl) {
            const count = filteredThreads.length;
            countEl.textContent = `${count} submission${count !== 1 ? 's' : ''}`;
        }
    }

    function clearAllFilters() {
        currentFilters = {
            search: '',
            provider: 'all',
            llm: 'all',
            hw: 'all',
            sort: 'date-desc'
        };
        currentPage = 1;

        document.getElementById('searchInput').value = '';
        document.getElementById('providerFilter').value = 'all';
        document.getElementById('llmFilter').value = 'all';
        document.getElementById('hwFilter').value = 'all';
        document.getElementById('sortSelect').value = 'date-desc';

        updateLLMOptions();
        applyFiltersAndRender();
    }

    function openThreadModal(threadId, triggerEl, { updateHistory = true } = {}) {
        const thread = participationData.threads.find(t => t.id === threadId);
        if (!thread) return;

        const modal = document.getElementById('modal');
        const title = document.getElementById('modalTitle');
        const meta = document.getElementById('modalMeta');
        const body = document.getElementById('modalBody');
        const footer = document.getElementById('modalFooter');

        if (activeModalThreadId === threadId && modal.classList.contains('open')) return;

        lastFocusedElement = triggerEl || document.activeElement;
        activeModalThreadId = threadId;

        title.textContent = thread.title;

        meta.innerHTML = `
            <span class="tag tag-provider">${escapeHtml(thread.provider || 'Other')}</span>
            <span class="tag tag-llm">${escapeHtml(thread.llm_used)}</span>
            <span class="tag tag-hw">${escapeHtml(thread.homework)}</span>
            <span class="modal-author">by ${escapeHtml(thread.author)}</span>
            <span class="modal-date">${formatDate(thread.created_at)}</span>
            <span class="modal-views">${thread.view_count} views</span>
        `;

        // Format content with line breaks
        const formattedContent = thread.content
            .split('\n')
            .map(p => p.trim())
            .filter(p => p)
            .map(p => `<p>${escapeHtml(p)}</p>`)
            .join('');

        body.innerHTML = formattedContent;

        // Footer with attachments and links
        let footerHtml = '';

        if (thread.attachments && thread.attachments.length > 0) {
            footerHtml += '<div class="modal-attachments"><strong>Attachments:</strong><ul>';
            thread.attachments.forEach(att => {
                footerHtml += `<li><a href="attachments/${encodeURIComponent(att)}" target="_blank" rel="noopener">${escapeHtml(att)}</a></li>`;
            });
            footerHtml += '</ul></div>';
        }

        if (thread.links && thread.links.length > 0) {
            footerHtml += '<div class="modal-links"><strong>External Links:</strong><ul>';
            thread.links.forEach(link => {
                footerHtml += `<li><a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">${escapeHtml(link)}</a></li>`;
            });
            footerHtml += '</ul></div>';
        }

        footer.innerHTML = footerHtml;

        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';

        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) closeBtn.focus();

        // Update URL
        if (updateHistory) {
            const params = new URLSearchParams(window.location.search);
            if (params.get('thread') !== String(threadId)) {
                params.set('thread', threadId);
                history.pushState({ threadId }, '', `${window.location.pathname}?${params.toString()}`);
            }
        }
    }

    function closeModal({ updateHistory = true } = {}) {
        const modal = document.getElementById('modal');
        if (!modal || !modal.classList.contains('open')) return;

        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        activeModalThreadId = null;

        // Remove thread from URL
        if (updateHistory) {
            const params = new URLSearchParams(window.location.search);
            params.delete('thread');
            const newUrl = params.toString()
                ? `${window.location.pathname}?${params.toString()}`
                : window.location.pathname;
            history.replaceState(null, '', newUrl);
        }

        if (lastFocusedElement && document.contains(lastFocusedElement)) {
            lastFocusedElement.focus();
        } else {
            const searchInput = document.getElementById('searchInput');
            if (searchInput) searchInput.focus();
        }

        lastFocusedElement = null;
    }

    function setupHistorySync() {
        window.addEventListener('popstate', syncModalToUrl);
    }

    function syncModalToUrl() {
        const params = new URLSearchParams(window.location.search);
        if (params.has('thread')) {
            const threadId = parseInt(params.get('thread'));
            if (Number.isFinite(threadId)) {
                openThreadModal(threadId, null, { updateHistory: false });
            }
            return;
        }

        closeModal({ updateHistory: false });
    }

    function getThreadHref(threadId) {
        const params = new URLSearchParams(window.location.search);
        params.set('thread', threadId);
        return `${window.location.pathname}?${params.toString()}`;
    }

    function trapFocus(e) {
        const modal = document.getElementById('modal');
        const container = modal ? modal.querySelector('.modal-container') : null;
        if (!container) return;

        const focusable = getFocusableElements(container);
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        const active = document.activeElement;

        if (e.shiftKey && active === first) {
            e.preventDefault();
            last.focus();
            return;
        }

        if (!e.shiftKey && active === last) {
            e.preventDefault();
            first.focus();
        }
    }

    function getFocusableElements(container) {
        return Array.from(container.querySelectorAll(
            'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )).filter(el => {
            if (el.hasAttribute('disabled')) return false;
            if (el.getAttribute('aria-hidden') === 'true') return false;
            return el.offsetParent !== null;
        });
    }

    function formatDate(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            });
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

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
})();
