// Shared audio encoding on top of Mediabunny (vendored in /vendor/mediabunny, MPL-2.0).
// Pages map the bare specifier: <script type="importmap">{"imports":{"mediabunny":"/vendor/mediabunny/mediabunny.min.mjs"}}</script>
// Everything runs in the browser; encoders that the browser lacks (MP3, FLAC, sometimes AAC) are WebAssembly
// extensions loaded on first use.
import {
    Input, Output, Conversion, BlobSource, BufferTarget, ALL_FORMATS, AudioBufferSource, canEncodeAudio,
    Mp3OutputFormat, Mp4OutputFormat, WavOutputFormat, FlacOutputFormat,
} from 'mediabunny';

const V = '/vendor/mediabunny/';
const MP3_RATES = [8000, 11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000];
const AAC_RATES = [44100, 48000];

const FORMATS = {
    mp3: { codec: 'mp3', mime: 'audio/mpeg', make: () => new Mp3OutputFormat(), rates: MP3_RATES, maxCh: 2,
        register: () => import(V + 'mp3-encoder.min.mjs').then((m) => m.registerMp3Encoder()) },
    m4a: { codec: 'aac', mime: 'audio/mp4', make: () => new Mp4OutputFormat(), rates: AAC_RATES, maxCh: 2,
        register: () => import(V + 'aac-encoder.min.mjs').then((m) => m.registerAacEncoder()) },
    flac: { codec: 'flac', mime: 'audio/flac', make: () => new FlacOutputFormat(),
        register: () => import(V + 'flac-encoder.min.mjs').then((m) => m.registerFlacEncoder()) },
    wav: { codec: 'pcm-s16', mime: 'audio/wav', make: () => new WavOutputFormat() },
};

const registered = {};
function ensureEncoder(fmt) {
    const f = FORMATS[fmt];
    if (!f) throw new Error('Unknown format: ' + fmt);
    if (!f.register) return Promise.resolve();
    return (registered[fmt] ??= canEncodeAudio(f.codec).catch(() => false).then((ok) => ok || f.register()));
}

// Sample rate / channel count the target codec accepts, closest to the source.
function fit(fmt, sampleRate, channels) {
    const f = FORMATS[fmt];
    const rate = !f.rates || f.rates.includes(sampleRate) ? sampleRate
        : f.rates.reduce((a, b) => (Math.abs(b - sampleRate) < Math.abs(a - sampleRate) ? b : a));
    return { sampleRate: rate, numberOfChannels: Math.min(channels, f.maxCh || channels) };
}

const openInput = (file) => new Input({ source: new BlobSource(file), formats: ALL_FORMATS });

// Duration and audio parameters, read from the container without decoding the whole file.
export async function probe(file) {
    const input = openInput(file);
    const track = await input.getPrimaryAudioTrack();
    if (!track) throw new Error('No audio track in this file');
    return {
        duration: await input.computeDuration(),
        sampleRate: track.sampleRate,
        channels: track.numberOfChannels,
        hasVideo: !!(await input.getPrimaryVideoTrack()),
    };
}

// Audio or video file → audio file in `format` (mp3 | m4a | wav | flac). Streams; video is dropped.
// `sampleRate` (optional) resamples, e.g. for smaller files.
export async function convertFile(file, { format, bitrate, sampleRate, onProgress } = {}) {
    await ensureEncoder(format);
    const input = openInput(file);
    const track = await input.getPrimaryAudioTrack();
    if (!track) throw new Error('No audio track in this file');
    const output = new Output({ format: FORMATS[format].make(), target: new BufferTarget() });
    const conversion = await Conversion.init({
        input, output, tracks: 'primary',
        video: { discard: true },
        audio: { codec: FORMATS[format].codec, bitrate, forceTranscode: true, ...fit(format, sampleRate || track.sampleRate, track.numberOfChannels) },
    });
    if (!conversion.isValid) throw new Error(conversion.discardedTracks.map((t) => t.reason).join(', ') || 'Cannot convert this file');
    if (onProgress) conversion.onProgress = onProgress;
    await conversion.execute();
    return new Blob([output.target.buffer], { type: FORMATS[format].mime });
}

async function resample(buf, sampleRate, channels) {
    if (buf.sampleRate === sampleRate && buf.numberOfChannels === channels) return buf;
    const off = new OfflineAudioContext(channels, Math.ceil(buf.duration * sampleRate), sampleRate);
    const src = off.createBufferSource();
    src.buffer = buf; src.connect(off.destination); src.start();
    return off.startRendering();
}

// AudioBuffer (e.g. a trimmed or boosted result) → audio file in `format`.
export async function encodeBuffer(buffer, { format, bitrate } = {}) {
    await ensureEncoder(format);
    const { sampleRate, numberOfChannels } = fit(format, buffer.sampleRate, buffer.numberOfChannels);
    const buf = await resample(buffer, sampleRate, numberOfChannels);
    const output = new Output({ format: FORMATS[format].make(), target: new BufferTarget() });
    const source = new AudioBufferSource({ codec: FORMATS[format].codec, bitrate });
    output.addAudioTrack(source);
    await output.start();
    await source.add(buf);
    source.close();
    await output.finalize();
    return new Blob([output.target.buffer], { type: FORMATS[format].mime });
}
