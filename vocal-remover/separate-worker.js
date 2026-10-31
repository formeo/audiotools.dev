// Vocal removal on the device: SCNet or SCNet-large (MIT weights) through @audio/neural-separate on ONNX Runtime Web
// (vendored in /vendor/neural/), on the CPU; Mel-RoFormer (MIT, Kimberley Jensen's vocals model) on WebGPU, as an
// experiment. The song arrives as Float32Array channels and never leaves the browser; only the model file is
// downloaded (once, then kept in the browser's cache).
//
// in:  { channels: Float32Array[], sampleRate, model: { name, url, sha256, device }, threads }
//      name: the package's preset ('scnet', 'scnet-large', 'mel-roformer'); device 'wasm' (CPU) or 'webgpu'
// out: { type: 'download', loaded, total }          model file, bytes so far
//      { type: 'loading' }                          model ready, the session is being made
//      { type: 'part', done, total }                 segments finished (sent as each one starts: done = its index)
//      { type: 'done', vocals: Float32Array[], instrumental: Float32Array[] }
//      { type: 'error', message, stage: 'load' | 'run' }
import { separate, load, fetchModel } from '/vendor/neural/neural.js';

let bytes = null, bytesUrl = null;

async function modelBytes({ url, sha256 }) {
    if (bytesUrl === url) return bytes;
    const b = await fetchModel(new URL(url, self.location.href).href, {
        progress: ({ loaded, total }) => self.postMessage({ type: 'download', loaded, total }),
    });
    const hex = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', b)), (x) => x.toString(16).padStart(2, '0')).join('');
    if (hex !== sha256) {
        await caches.open('audio-neural').then((c) => c.delete(new URL(url, self.location.href).href)).catch(() => {});
        throw new Error('The model file did not download completely. Try again.');
    }
    bytes = b; bytesUrl = url;
    return b;
}

self.onmessage = async ({ data: { channels, sampleRate, model, threads } }) => {
    let stage = 'load';
    try {
        const b = await modelBytes(model);
        self.postMessage({ type: 'loading' });
        const gpu = model.device === 'webgpu';
        const { stems, residual } = await separate(channels, {
            sampleRate,
            model: model.name,
            targets: ['vocals'],
            // SCNet: each sample heard in two segments, not four: half the time, 0.07–0.17 dB less (package README)
            ...(model.name.startsWith('scnet') && { step: model.step || 0.5 }),
            session: async () => {
                const s = await load(b, gpu ? { backend: 'webgpu', wasmPaths: '/vendor/neural/' } : {
                    backend: 'wasm', wasmPaths: '/vendor/neural/',
                    threads: self.crossOriginIsolated ? threads || 1 : 1,   // chosen by the page (see /coi-sw.js)
                    sessionOptions: { enableCpuMemArena: false, enableMemPattern: false },
                });
                stage = 'run';
                return s;
            },
            progress: ({ chunk, totalChunks }) => self.postMessage({ type: 'part', done: chunk - 1, total: totalChunks }),
        });
        const vocals = stems.vocals, instrumental = residual;
        self.postMessage({ type: 'done', vocals, instrumental }, [...vocals, ...instrumental].map((c) => c.buffer));
    } catch (e) {
        self.postMessage({ type: 'error', message: e.message || String(e), stage });
    }
};
