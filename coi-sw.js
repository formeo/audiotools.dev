// Cross-origin isolation for the Vocal Remover pages, which GitHub Pages can't give with headers.
// ONNX Runtime needs SharedArrayBuffer to run on several CPU threads, and the browser allows it only when the page
// (and every worker it starts) is served with COOP and COEP. Registered with the scopes /vocal-remover/,
// /zh/vocal-remover/ and /vendor/neural/ (ONNX Runtime's thread workers) only, so no other page is touched. COEP "credentialless" lets cross-origin files without CORP
// headers (fonts, analytics) still load, just without cookies.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', (e) => {
    const req = e.request;
    if (new URL(req.url).origin !== self.location.origin) return;   // cross-origin: as the browser does it
    if (req.cache === 'only-if-cached' && req.mode !== 'same-origin') return;
    e.respondWith(fetch(req).then((res) => {
        if (res.status === 0) return res;
        const headers = new Headers(res.headers);
        headers.set('Cross-Origin-Embedder-Policy', 'credentialless');
        headers.set('Cross-Origin-Opener-Policy', 'same-origin');
        headers.set('Cross-Origin-Resource-Policy', 'same-origin');
        return new Response(res.body, { status: res.status, statusText: res.statusText, headers });
    }));
});
