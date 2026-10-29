# 🎵 AudioTools.dev

**Free open source audio processing ecosystem** — [audiotools.dev](https://audiotools.dev)

Privacy-first audio tools that run entirely in your browser. No uploads, no accounts, no usage limits.

## Online Tools

| Tool | URL | Technology |
|------|-----|------------|
| **Audio Converter** | [/converter/](https://audiotools.dev/converter/) | Mediabunny (WebCodecs + WASM encoders); MPEG-PS via `mpeg-ps.js` + mpg123 |
| **Voice to Text** | [/voice-to-text/](https://audiotools.dev/voice-to-text/) | Web Speech API + Whisper (Transformers.js) |
| **Text to Speech** | [/text-to-speech/](https://audiotools.dev/text-to-speech/) | Web Speech Synthesis API |
| **Audio Trimmer** | [/audio-trimmer/](https://audiotools.dev/audio-trimmer/) | Web Audio API |
| **Speed Changer** | [/audio-speed-changer/](https://audiotools.dev/audio-speed-changer/) | WSOLA time-stretching |
| **Volume Booster** | [/volume-booster/](https://audiotools.dev/volume-booster/) | Web Audio API, soft limiter |
| **Audio Joiner** | [/audio-joiner/](https://audiotools.dev/audio-joiner/) | Web Audio API, crossfade |
| **Audio Compressor** | [/audio-compressor/](https://audiotools.dev/audio-compressor/) | Web Audio API + Mediabunny MP3 |
| **Vocal Remover** | [/vocal-remover/](https://audiotools.dev/vocal-remover/) | SCNet, or SCNet-large as "Cleaner" on computers (MIT weights), via [@audio/neural-separate](https://github.com/audiojs/neural) on ONNX Runtime Web (WebAssembly) |

Chinese pages: [/zh/](https://audiotools.dev/zh/) and a /zh/ version of every tool, for example [/zh/converter/](https://audiotools.dev/zh/converter/) and [/zh/voice-to-text/](https://audiotools.dev/zh/voice-to-text/).

## Architecture

```
audiotools.dev/
├── index.html, zh/         ← Home page (EN, ZH) with the tool helper
├── <tool>/index.html       ← One folder per tool; tool-specific styles inline
├── style.css               ← Shared look: tokens, nav, footer, tool header and panel, sections
├── assistant.js            ← Home helper + "continue with this file" hand-off between tools
├── media.js                ← Shared decoding/encoding on Mediabunny: convertFile (streams, video in), encodeBuffer
├── mpeg-ps.js              ← MPEG program streams (.mpg/.mpeg/.vob): takes the MPEG audio out, decodes MP1/MP2 with mpg123
├── vendor/mediabunny/      ← Self-hosted Mediabunny + MP3/FLAC/AAC encoder bundles (MPL-2.0)
├── vendor/mpg123/          ← mpg123 MP1/MP2/MP3 decoder in WebAssembly (wrapper MIT, mpg123 LGPL-2.1)
├── batch.js                ← Several files at once: per-file list + ZIP download (Converter, Compressor)
├── audio-export.js         ← MP3 (192 kbps) or WAV download for edited audio
├── support.js              ← GA4 events + support line after a successful result
├── voice-to-text/whisper-worker.js ← Whisper in a Web Worker
├── about/, changelog/, privacy/, terms/, 404.html
├── sitemap.xml, robots.txt, llms.txt
└── CNAME
```

## How it works

### Audio tools

- **Decoding**: Web Audio API (WAV, MP3, FLAC, OGG, AAC, M4A, WebM, or anything else the browser can decode)
- **WAV encoding**: custom JS encoder (lossless)
- **Converter**: [Mediabunny](https://mediabunny.dev) reads audio and video containers in pieces and decodes with WebCodecs; output MP3, M4A (AAC), WAV or FLAC. Browsers without WebCodecs fall back to Web Audio decoding. MPEG program streams, which neither opens, are demuxed by `mpeg-ps.js` (file read in 4 MB pieces); MP3 sound is decoded by the browser, MP1/MP2 by mpg123 in WebAssembly; AC-3 is reported as not supported.
- **MP3 / FLAC / AAC encoding**: Mediabunny encoder extensions (LAME and FLAC in WebAssembly, in a worker; AAC only where the browser has no encoder)
- The other tools save MP3 or WAV. Nothing is uploaded; there is no server.

### Voice to Text

- **Live dictation** uses the browser's built-in Web Speech Recognition API (Chrome/Safari may process audio on the vendor's servers).
- **Private mode** transcribes audio files and microphone recordings with Whisper (Base and Small; large-v3-turbo where the browser has WebGPU with 16-bit floats) via [Transformers.js](https://github.com/huggingface/transformers.js) in a Web Worker (`voice-to-text/whisper-worker.js`). It runs on WebGPU when available and falls back to WebAssembly; text appears as it is recognized, with progress by 30-second part. Audio is decoded and resampled to 16 kHz mono in the browser; only the model weights are downloaded from Hugging Face and cached. Where Hugging Face or jsDelivr can't be reached (a download fails or stalls for 30 s, common in China), the worker switches to copies served by the site itself: Transformers.js in `vendor/transformers/` and Whisper Base (q8, ~77 MB) in `models/Xenova/whisper-base/`; the page then uses them directly for a day and sends an anonymous `model_load_failed` event. Each transcription is a result tied to its file: the file stays in memory, so it can be transcribed again with another model or language, and earlier results of the visit are listed under "Earlier". "Edit text" turns the transcript into a small subtitle editor: the words of each line can be changed while Whisper's times stay, and .txt/.srt use the edited text. A player under the file card follows the text (Whisper's segments): click a line to play it, the current line is highlighted, and video files get the transcript as a WebVTT subtitle track.

## SEO maintenance

- `python3 scripts/seo_sync.py` rewrites the FAQPage JSON-LD on every page from the FAQ that is visible on that page, and refreshes `<lastmod>` in `sitemap.xml` from git. Run it after editing a FAQ or a page (needs `beautifulsoup4`).
- CI (`.github/workflows/seo-check.yml`) runs `scripts/seo_sync.py --check` and fails if the markup and the visible FAQ drift apart.
- `python3 scripts/build_zh.py` rebuilds the Chinese tool pages (all tools except the converter, which is maintained by hand) from the English ones with the translation tables in the script, and keeps hreflang, the 中文/EN switch and the Chinese navigation in step. It stops if an English string it translates has changed, and runs `scripts/seo_sync.py` at the end.
- `python3 scripts/nav.py` writes the navigation of every page, English and Chinese: the bar with the main tools and the "Tools" menu with all of them (on phones only the logo, the language switch and the menu are left). `build_zh.py` and `build_landing.py` run it; CI runs `nav.py --check`. To add a tool to the menu, add it to `TOOLS` there.
- `python3 scripts/build_landing.py` rebuilds the format pages (`/mp4-to-mp3/`, `/video-to-mp3/`, `/mp3-to-wav/`, `/wav-to-mp3/` and their `/zh/` versions) from the converter pages: same code, own copy and FAQ, output format preselected via `<body data-default-format>`. Run it after changing a converter page; it also refreshes the "Popular conversions" links on the converters and runs `seo_sync.py`.
- Social preview images live in `og/` (1200×630, one per tool).

## Deployment

The site is static HTML — deploy to GitHub Pages:

```bash
git add .
git commit -m "Update audiotools.dev"
git push origin main
```

GitHub Pages serves from the `main` branch. The `CNAME` file points to `audiotools.dev`.

## Open Source Projects

This site is the hub for the audio tools ecosystem:

| Project | Language | Description |
|---------|----------|-------------|
| [go-audio-converter](https://github.com/formeo/go-audio-converter) | Go | Pure Go audio converter — no FFmpeg, custom FLAC encoder |
| [voice-to-text](https://github.com/formeo/voice-to-text) | Python | Bulk voice transcription — Whisper, faster-whisper, OpenAI, Groq |
| [music_recognition](https://github.com/formeo/music_recognition) | Python | Bulk music identification via Shazam + auto ID3 tagging |
| [audiobook-cleaner](https://github.com/formeo/Audiobook-Cleaner) | Python | AI noise removal — MDX-Net, VR, Roformer models |

## Tech Stack

- **Frontend**: Vanilla HTML/CSS/JS (no frameworks, fast loading)
- **Audio Processing**: Web Audio API, Mediabunny, Transformers.js (Whisper)
- **Hosting**: GitHub Pages
- **SEO**: JSON-LD structured data, Open Graph, semantic HTML

## License

MIT — [Roman Gordienko](https://github.com/formeo)
