# Source separation runtime (Vocal Remover)

Used by `/vocal-remover/separate-worker.js`. Everything here runs in the browser.

| File | What | Licence |
|---|---|---|
| `neural.js` + chunks | [`@audio/neural-separate`](https://github.com/audiojs/neural) 0.7.0 and `@audio/neural-runtime` 0.2.0 (with `fourier-transform`, `@audio/resample-sinc`), bundled with esbuild; the `onnxruntime-web` 1.31.1 JS for the wasm and WebGPU backends is in the `ort.*` chunks | MIT (see `NOTICE-neural-separate` and the licence comments at the end of each file) |
| `ort-wasm-simd-threaded.wasm`, `.mjs` | ONNX Runtime Web, CPU (WebAssembly) backend | MIT |
| `ort-wasm-simd-threaded.asyncify.wasm`, `.mjs` | ONNX Runtime Web, WebGPU backend | MIT |
| `scnet.int8.onnx` | SCNet, the separation model (13.2 MB). Weights: `scnet_checkpoint_musdb18.ckpt` from the release v.1.0.6 of [ZFTurbo/Music-Source-Separation-Training](https://github.com/ZFTurbo/Music-Source-Separation-Training) (MIT), trained on MUSDB18-HQ. Built with the package's own `scripts/export-scnet.py --model scnet --verify` (ONNX within 2e-6 of PyTorch) and `scripts/compact.py --model scnet` (int8 weights, the costliest 16 in float16, predicted 40 dB from float32). SHA-256 `3f049a0e4ce3c08264a6212a50445ba77f02a517cd4c6dc86cbe1ca130176d67`, checked by the worker before use | MIT |

`ort.webgl.*` and `roformer-*` are chunks the bundle can import but the Vocal Remover never loads (other backends and models).

The model is served from this site rather than Hugging Face so that it loads where Hugging Face is blocked and no third
party sees the request. audiojs publishes its own compact build of the same checkpoint (`audiojs/scnet` on Hugging Face,
12.9 MB) with the same scripts; the bytes differ because the calibration step chose a few different layers to keep in
float16 on this machine.

## Rebuild

```sh
npm i @audio/neural-separate@0.7.0 @audio/neural-runtime@0.2.0 onnxruntime-web@1.31.1 esbuild
printf "export { default as separate } from '@audio/neural-separate'\nexport { load, fetchModel } from '@audio/neural-runtime'\n" > entry.js
npx esbuild entry.js --bundle --format=esm --splitting --outdir=out --minify --platform=browser --target=es2022 \
  --legal-comments=eof --chunk-names=[name]-[hash] --entry-names=neural "--external:node:*"
cp out/*.js node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded{,.asyncify}.{wasm,mjs} vendor/neural/
```

`node:*` imports stay external: they are only reached in Node, never in a browser.
