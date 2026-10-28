# Self-hosted models

Copies of model files served from audiotools.dev, for networks where Hugging Face can't be reached (mainland China
above all). Voice to Text downloads from Hugging Face first and switches to these only when that fails or stalls.

## Xenova/whisper-base

OpenAI Whisper Base (MIT license), converted to ONNX by Xenova for Transformers.js. Only the files Transformers.js 3.8.1
reads for `dtype: 'q8'` on WebAssembly are kept.

| File | Size | SHA-256 |
|---|---|---|
| onnx/encoder_model_quantized.onnx | 23,200,850 | 3e345e977b55620a37c0c2b2af0644e019afdfad562dcf71eb929bb7274285f9 |
| onnx/decoder_model_merged_quantized.onnx | 53,707,539 | a6beb6baabb66f00b6a686d828c95ffca6146d51900cbad0266cad38f64cf861 |
| config.json | | d1d347fdb422e6347c2f843a90d375aa67ea3f4b3e20d2c3075f9a9f6243685b |
| generation_config.json | | 3bba359e33fdd6dc1c10f71846a477d339b0242f462f70ea1dd73274caa38d05 |
| preprocessor_config.json | | a6a76d28c93edb273669eb9e0b0636a2bddbb1272c3261e47b7ca6dfdbac1b8d |
| tokenizer.json | | 27fc476bfe7f17299480be2273fc0608e4d5a99aba2ab5dec5374b4482d1a566 |
| tokenizer_config.json | | 2a4c4281cf9f51ac6ccc406fdc711a087afe6530f671fa7b80953edc498275ce |

The decoder's hash matches the Git LFS object of `onnx/decoder_model_merged_quantized.onnx` in
https://huggingface.co/Xenova/whisper-base. To refresh, download the same paths from that repository and compare.
