# MPEG audio decoder (MP1 / MP2 / MP3)

Used by `/mpeg-ps.js` to decode the sound of MPEG program streams (.mpg, .mpeg, .vob), which browsers can't open.
MP2, the usual sound of these files, has no decoder in browsers.

| File | What | Licence |
|---|---|---|
| `mpg123-decoder.min.mjs` | [`mpg123-decoder`](https://github.com/eshaz/wasm-audio-decoders/tree/master/src/mpg123-decoder) 1.0.3 (with `@wasm-audio-decoders/common` 9.0.7), bundled as an ES module with esbuild; the WebAssembly build of [mpg123](https://www.mpg123.de/) is inlined | wrapper MIT; mpg123 LGPL-2.1 (unmodified, loaded as a separate file; source at mpg123.de) |

## Rebuild

```sh
npm i mpg123-decoder@1.0.3 esbuild
printf "export { MPEGDecoder } from 'mpg123-decoder'\n" > entry.js
npx esbuild entry.js --bundle --format=esm --platform=browser --minify --legal-comments=eof --outfile=vendor/mpg123/mpg123-decoder.min.mjs
```
