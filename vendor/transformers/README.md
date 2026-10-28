# Transformers.js 3.8.1

`transformers.min.js` (the build jsDelivr serves for `@huggingface/transformers@3.8.1`) and the ONNX Runtime Web
files it loads (`ort-wasm-simd-threaded.jsep.mjs`, `.wasm`), copied unchanged from the npm package.
Transformers.js: Apache-2.0 (see LICENSE). ONNX Runtime: MIT.

Used by `voice-to-text/whisper-worker.js` only when jsDelivr or Hugging Face can't be reached; normally the library
comes from jsDelivr.
