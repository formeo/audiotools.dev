// Vocal removal on the device: SCNet (MIT weights) through @audio/neural-separate on ONNX Runtime Web
// (vendored in /vendor/neural/). The song arrives as Float32Array channels and never leaves the browser;
// only the model file is downloaded (once, then kept in the browser's cache).
//
// in:  { channels: Float32Array[], sampleRate, device: 'webgpu' | 'wasm', model: { url, sha256 } }
// out: { type: 'download', loaded, total }          model file, bytes so far
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

self.onmessage = async ({ data: { channels, sampleRate, device, model } }) => {
    let stage = 'load';
    try {
        const b = await modelBytes(model);
        const { stems, residual } = await separate(channels, {
            sampleRate,
            model: 'scnet',
            targets: ['vocals'],
            step: 0.5,   // each sample heard in two segments, not four: half the time, about 0.1 dB less (package README)
            session: async () => {
                const s = await load(b, {
                    backend: device, wasmPaths: '/vendor/neural/',
                    threads: self.crossOriginIsolated ? Math.min(4, navigator.hardwareConcurrency || 1) : 1,   // see /coi-sw.js
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
