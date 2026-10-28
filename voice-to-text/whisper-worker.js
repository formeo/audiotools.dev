// On-device speech recognition with Whisper (Transformers.js, ONNX Runtime on WebGPU or WebAssembly).
// Audio arrives as 16 kHz mono Float32Array and never leaves the browser;
// only the model weights are downloaded (once, then cached by the browser).
//
// in:  { audio, model: { id, device, dtype }, language, source }
//      language null: Whisper detects it. source 'site': the library and the model come from AudioTools.dev itself
//      (/vendor/transformers/, /models/), for networks where Hugging Face or jsDelivr can't be reached (China);
//      otherwise from jsDelivr and Hugging Face.
// out: { type: 'progress', loaded }           model download, bytes so far
//      { type: 'transcribing', chunks }       model ready; the audio is split into `chunks` parts
//      { type: 'partial', text, chunk }       text recognized so far in part `chunk` (0-based), as it is generated
//      { type: 'chunk', done }                parts finished so far
//      { type: 'done', text, chunks }         chunks: [{ timestamp: [start, end], text }]
//      { type: 'error', message, loading, network }   loading: the model never loaded; network: a download failed or stalled
const CDN = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1';
const STALL_MS = 30000;   // a download that sends nothing for this long counts as failed (a blocked site often just hangs)
const CHUNK_S = 30, STRIDE_S = 5, RATE = 16000;   // the pipeline cuts 30 s windows that overlap by 5 s on each side
let T = null;   // the Transformers.js module
let asr = null;
let loadedKey = null;
let networkFailed = false;

// Downloads from other sites give up when they stall, so a blocked Hugging Face fails in seconds instead of hanging.
const realFetch = self.fetch.bind(self);
self.fetch = async (url, opts = {}) => {
    if (new URL(String(url), self.location.href).origin === self.location.origin) return realFetch(url, opts);
    const ctl = new AbortController();
    let timer;
    const arm = () => { clearTimeout(timer); timer = setTimeout(() => ctl.abort(), STALL_MS); };
    arm();
    let res;
    try {
        res = await realFetch(url, { ...opts, signal: ctl.signal });
    } catch (e) {
        clearTimeout(timer); networkFailed = true; throw e;
    }
    if (!res.ok && res.status !== 404) networkFailed = true;   // 404: an optional file that this model doesn't have
    if (!res.body) { clearTimeout(timer); return res; }
    const reader = res.body.getReader();
    const body = new ReadableStream({
        async pull(c) {
            arm();
            try {
                const { done, value } = await reader.read();
                if (done) { clearTimeout(timer); c.close(); } else c.enqueue(value);
            } catch (e) { clearTimeout(timer); networkFailed = true; c.error(e); }
        },
        cancel(reason) { clearTimeout(timer); return reader.cancel(reason); },
    });
    return new Response(body, { status: res.status, statusText: res.statusText, headers: res.headers });
};

async function library(source) {
    if (T) return T;
    if (source === 'site') {
        T = await import('/vendor/transformers/transformers.min.js');
        T.env.backends.onnx.wasm.wasmPaths = new URL('/vendor/transformers/', self.location.href).href;
        T.env.remoteHost = new URL('/models/', self.location.href).href;
        T.env.remotePathTemplate = '{model}/';
    } else {
        let timer;
        try {
            T = await Promise.race([import(CDN), new Promise((_, no) => { timer = setTimeout(() => no(new Error('jsDelivr timed out')), STALL_MS); })]);
        } catch (e) {
            networkFailed = true; throw e;
        } finally { clearTimeout(timer); }
    }
    return T;
}

const chunkCount = (samples) => {
    const window = CHUNK_S * RATE, jump = (CHUNK_S - 2 * STRIDE_S) * RATE;
    return samples <= window ? 1 : 1 + Math.ceil((samples - window) / jump);
};

self.onmessage = async ({ data: { audio, model, language, source } }) => {
    let loading = true;
    try {
        const { pipeline, WhisperTextStreamer } = await library(source);
        const key = model.id + '|' + model.device;
        if (loadedKey !== key) {
            if (asr) {   // another model: let the previous one go first, so two never sit in memory together
                const old = asr;
                asr = null; loadedKey = null;
                await old.dispose().catch(() => {});
            }
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
        loading = false;
        const chunks = chunkCount(audio.length);
        self.postMessage({ type: 'transcribing', chunks });
        let chunk = 0, text = '';
        const streamer = new WhisperTextStreamer(asr.tokenizer, {
            skip_prompt: true,
            callback_function: (piece) => { text += piece; self.postMessage({ type: 'partial', text, chunk }); },
            on_finalize: () => { chunk++; text = ''; self.postMessage({ type: 'chunk', done: chunk }); },
        });
        const out = await asr(audio, { ...(language && { language }), task: 'transcribe', return_timestamps: true, chunk_length_s: CHUNK_S, stride_length_s: STRIDE_S, streamer });
        self.postMessage({ type: 'done', text: out.text, chunks: out.chunks || [] });
    } catch (e) {
        self.postMessage({ type: 'error', message: e.message || String(e), loading, network: loading && networkFailed });
        networkFailed = false;
    }
};
