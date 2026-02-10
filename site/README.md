# 🎵 AudioTools.dev

**Free open source audio processing ecosystem** — [audiotools.dev](https://audiotools.dev)

Privacy-first audio tools that run entirely in your browser. No uploads, no accounts, no tracking.

## Online Tools

| Tool | URL | Technology |
|------|-----|------------|
| **Audio Converter** | [/converter/](https://audiotools.dev/converter/) | Web Audio API + lamejs + Go WASM |
| **Voice to Text** | [/voice-to-text/](https://audiotools.dev/voice-to-text/) | Web Speech API |

## Architecture

```
audiotools.dev/
├── index.html              ← Main hub page
├── converter/
│   └── index.html          ← Audio converter (JS + optional WASM)
├── voice-to-text/
│   └── index.html          ← Speech-to-text transcription
├── wasm/
│   ├── main.go             ← Go WASM source (FLAC encoder)
│   ├── build-wasm.sh       ← Build script
│   ├── converter.wasm      ← Compiled WASM binary (build it!)
│   └── wasm_exec.js        ← Go WASM runtime (from Go installation)
├── sitemap.xml
├── robots.txt
├── CNAME
└── README.md
```

## How it works

### Audio Converter

The converter has two engines:

1. **JavaScript engine** (always available):
   - **Decoding**: Web Audio API (supports WAV, MP3, FLAC, OGG, AAC, M4A, WebM)
   - **WAV encoding**: Custom JS encoder (lossless)
   - **MP3 encoding**: [lamejs](https://github.com/nicktrandafil/lamern) (128–320 kbps)

2. **WASM engine** (optional, adds FLAC output):
   - Compiles [go-audio-converter](https://github.com/formeo/go-audio-converter) to WebAssembly
   - Enables **FLAC encoding** in the browser — a pure Go FLAC encoder running as WASM
   - The page auto-detects WASM availability and enables/disables FLAC accordingly

### Voice to Text

Uses the browser's built-in Web Speech Recognition API. No audio leaves the device.

## Building WASM (optional)

To enable FLAC encoding in the browser:

```bash
# 1. Clone go-audio-converter
git clone https://github.com/formeo/go-audio-converter.git
cd go-audio-converter

# 2. Copy WASM source
mkdir -p cmd/wasm
cp /path/to/audiotools.dev/wasm/main.go cmd/wasm/main.go

# 3. Build
GOOS=js GOARCH=wasm go build -o converter.wasm -ldflags="-s -w" ./cmd/wasm/

# 4. Copy Go's WASM runtime
cp "$(go env GOROOT)/misc/wasm/wasm_exec.js" .

# 5. Deploy to site
cp converter.wasm /path/to/audiotools.dev/wasm/
cp wasm_exec.js /path/to/audiotools.dev/wasm/
```

The converter page will auto-detect `wasm/converter.wasm` and show a "WASM engine active" badge with FLAC enabled.

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
- **Audio Processing**: Web Audio API, lamejs, Go WASM
- **Hosting**: GitHub Pages
- **SEO**: JSON-LD structured data, Open Graph, semantic HTML

## License

MIT — [Roman Gordienko](https://github.com/formeo)
