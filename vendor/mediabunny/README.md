# Mediabunny (vendored)

Unmodified browser bundles of [Mediabunny](https://mediabunny.dev) 1.61.3 and its encoder extensions,
self-hosted so the tools don't depend on a third-party CDN. License: MPL-2.0 (see LICENSE).

| File | npm package |
|------|-------------|
| `mediabunny.min.mjs` | `mediabunny@1.61.3` — `dist/bundles/mediabunny.min.mjs` |
| `mp3-encoder.min.mjs` | `@mediabunny/mp3-encoder@1.61.3` — LAME in WebAssembly, runs in a worker |
| `flac-encoder.min.mjs` | `@mediabunny/flac-encoder@1.61.3` |
| `aac-encoder.min.mjs` | `@mediabunny/aac-encoder@1.61.3` — loaded only where the browser has no AAC encoder |

The encoder bundles import the bare specifier `mediabunny`; pages map it with an import map:
`<script type="importmap">{"imports":{"mediabunny":"/vendor/mediabunny/mediabunny.min.mjs"}}</script>`.

To update: `npm pack mediabunny@X @mediabunny/mp3-encoder@X @mediabunny/flac-encoder@X @mediabunny/aac-encoder@X`
and copy the same files from each package's `dist/bundles/`.
