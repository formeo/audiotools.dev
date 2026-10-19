// Shared by tool pages: GA4 events + a Boosty support line shown after a successful result.
// Events carry only the tool name / link placement — never file names or content.
(function () {
    const BOOSTY = 'https://boosty.to/formeo';
    const track = (name, params) => { if (typeof gtag === 'function') gtag('event', name, params); };

    // Call when a tool has successfully produced its result.
    // The support line is inserted once, right after `anchor`.
    window.toolSuccess = function (tool, anchor) {
        track('file_processed', { tool });
        if (!anchor || document.getElementById('support-cta')) return;
        const el = document.createElement('p');
        el.id = 'support-cta';
        el.style.cssText = 'margin-top:12px;font-size:14px;text-align:center;opacity:.85';
        el.innerHTML = 'Saved you time? <a href="' + BOOSTY + '" target="_blank" rel="noopener" style="color:var(--green, var(--accent))">☕ Support AudioTools.dev on Boosty</a>';
        anchor.after(el);
    };

    // Any Boosty link on the page: the line above or the footer link.
    document.addEventListener('click', (e) => {
        const a = e.target.closest && e.target.closest('a[href^="' + BOOSTY + '"]');
        if (a) track('donate_click', { placement: a.closest('#support-cta') ? 'after_success' : 'footer', page_path: location.pathname });
    });
})();
