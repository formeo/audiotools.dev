# Mediabunny (vendored)

Browser bundles of [Mediabunny](https://mediabunny.dev) 1.61.3 and its encoder extensions,
self-hosted so the tools don't depend on a third-party CDN. License: MPL-2.0 (see LICENSE).

| File | npm package |
|------|-------------|
| `mediabunny.min.mjs` | `mediabunny@1.61.3` — `dist/bundles/mediabunny.min.mjs` |
| `mp3-encoder.min.mjs` | `@mediabunny/mp3-encoder@1.61.3` — LAME in WebAssembly, runs in a worker |
| `flac-encoder.min.mjs` | `@mediabunny/flac-encoder@1.61.3` |
| `aac-encoder.min.mjs` | `@mediabunny/aac-encoder@1.61.3` — loaded only where the browser has no AAC encoder |

One change from the published files: the encoder bundles import `"mediabunny"`, which is rewritten to
`"./mediabunny.min.mjs"`, so no import map is needed (Safari supports import maps only from 16.4).

To update: `npm pack mediabunny@X @mediabunny/mp3-encoder@X @mediabunny/flac-encoder@X @mediabunny/aac-encoder@X`
and copy the same files from each package's `dist/bundles/`, then:
`sed -i 's#from"mediabunny"#from"./mediabunny.min.mjs"#g' vendor/mediabunny/*-encoder.min.mjs`
