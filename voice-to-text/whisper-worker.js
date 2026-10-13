// On-device speech recognition with Whisper (Transformers.js, ONNX Runtime WASM).
// Audio arrives as 16 kHz mono Float32Array and never leaves the browser;
// only the model weights are downloaded (once, then cached by the browser).
import { pipeline } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1';

let asr = null;
let loadedModel = null;

self.onmessage = async ({ data: { audio, model, language } }) => {
    try {
        if (loadedModel !== model) {
            const loadedPerFile = {};  // max bytes per file: some files are read twice (2nd time from cache)
            asr = await pipeline('automatic-speech-recognition', model, {
                dtype: 'q8',
                device: 'wasm',
                progress_callback: (p) => {
                    if (p.status !== 'progress') return;
                    loadedPerFile[p.file] = Math.max(loadedPerFile[p.file] || 0, p.loaded);
                    const loaded = Object.values(loadedPerFile).reduce((s, n) => s + n, 0);
                    self.postMessage({ type: 'progress', loaded });
                },
            });
            loadedModel = model;
        }
        self.postMessage({ type: 'transcribing' });
        const out = await asr(audio, { language, task: 'transcribe', chunk_length_s: 30, stride_length_s: 5 });
        self.postMessage({ type: 'done', text: out.text });
    } catch (e) {
        self.postMessage({ type: 'error', message: e.message || String(e) });
    }
};
