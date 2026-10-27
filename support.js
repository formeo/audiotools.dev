// Shared by tool pages: GA4 events + a Boosty support line shown after a successful result.
// Events carry only tool names, how the user got to the tool and link placement — never file names, file content or typed text.
(function () {
    const BOOSTY = 'https://boosty.to/formeo';
    const track = (name, params) => { if (typeof gtag === 'function') gtag('event', name, params); };

    // Call when a tool has successfully produced its result.
    // The support line is inserted once, right after `anchor`.
    // via: how the user got here with this file ('assistant' / 'next', set by assistant.js) or 'direct'.
    window.toolSuccess = function (tool, anchor) {
        let via = 'direct';
        try { via = sessionStorage.getItem('at_via:' + location.pathname) || 'direct'; } catch (e) { /* private mode */ }
        track('file_processed', { tool, via });
        document.dispatchEvent(new CustomEvent('at:processed', { detail: { tool } }));
        if (!anchor || document.getElementById('support-cta')) return;
        const el = document.createElement('p');
        el.id = 'support-cta';
        el.style.cssText = 'margin-top:12px;font-size:14px;text-align:center;opacity:.85';
        const zh = document.documentElement.lang.startsWith('zh');
        el.innerHTML = (zh ? '节省了时间？' : 'Saved you time? ') + '<a href="' + BOOSTY + '" target="_blank" rel="noopener" style="color:var(--accent2)">'
            + (zh ? '在 Boosty 上支持 AudioTools.dev' : 'Support AudioTools.dev on Boosty') + '</a>';
        anchor.after(el);
    };

    // While a dropped file is being read (decoding a long one takes seconds), its drop zone says so.
    window.readingFile = function (zone, on) {
        if (!zone) return;
        zone.dataset.reading = document.documentElement.lang.startsWith('zh') ? '正在读取文件…' : 'Reading the file…';
        zone.classList.toggle('reading', on);
        zone.setAttribute('aria-busy', on ? 'true' : 'false');
    };

    // Any Boosty link on the page: the line above or the footer link.
    document.addEventListener('click', (e) => {
        const a = e.target.closest && e.target.closest('a[href^="' + BOOSTY + '"]');
        if (a) track('donate_click', { placement: a.closest('#support-cta') ? 'after_success' : 'footer', page_path: location.pathname });
    });
})();
