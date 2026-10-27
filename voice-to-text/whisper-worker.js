// On-device speech recognition with Whisper (Transformers.js, ONNX Runtime on WebGPU or WebAssembly).
// Audio arrives as 16 kHz mono Float32Array and never leaves the browser;
// only the model weights are downloaded (once, then cached by the browser).
//
// in:  { audio, model: { id, device, dtype }, language }
// out: { type: 'progress', loaded }           model download, bytes so far
//      { type: 'transcribing', chunks }       model ready; the audio is split into `chunks` parts
//      { type: 'partial', text, chunk }       text recognized so far in part `chunk` (0-based), as it is generated
//      { type: 'chunk', done }                parts finished so far
//      { type: 'done', text } | { type: 'error', message }
import { pipeline, WhisperTextStreamer } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1';

const CHUNK_S = 30, STRIDE_S = 5, RATE = 16000;   // the pipeline cuts 30 s windows that overlap by 5 s on each side
let asr = null;
let loadedKey = null;

const chunkCount = (samples) => {
    const window = CHUNK_S * RATE, jump = (CHUNK_S - 2 * STRIDE_S) * RATE;
    return samples <= window ? 1 : 1 + Math.ceil((samples - window) / jump);
};

self.onmessage = async ({ data: { audio, model, language } }) => {
    try {
        const key = model.id + '|' + model.device;
        if (loadedKey !== key) {
            const loadedPerFile = {};  // max bytes per file: some files are read twice (2nd time from cache)
            asr = await pipeline('automatic-speech-recognition', model.id, {
                dtype: model.dtype,
                device: model.device,
                progress_callback: (p) => {
                    if (p.status !== 'progress') return;
                    loadedPerFile[p.file] = Math.max(loadedPerFile[p.file] || 0, p.loaded);
                    const loaded = Object.values(loadedPerFile).reduce((s, n) => s + n, 0);
                    self.postMessage({ type: 'progress', loaded });
                },
            });
            loadedKey = key;
        }
        const chunks = chunkCount(audio.length);
        self.postMessage({ type: 'transcribing', chunks });
        let chunk = 0, text = '';
        const streamer = new WhisperTextStreamer(asr.tokenizer, {
            skip_prompt: true,
            callback_function: (piece) => { text += piece; self.postMessage({ type: 'partial', text, chunk }); },
            on_finalize: () => { chunk++; text = ''; self.postMessage({ type: 'chunk', done: chunk }); },
        });
        const out = await asr(audio, { language, task: 'transcribe', chunk_length_s: CHUNK_S, stride_length_s: STRIDE_S, streamer });
        self.postMessage({ type: 'done', text: out.text });
    } catch (e) {
        self.postMessage({ type: 'error', message: e.message || String(e) });
    }
};
