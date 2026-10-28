// MPEG program streams (.mpg, .mpeg, .vob: old camcorders, TV recordings, VCD, DVD) in the browser.
// Neither Mediabunny nor the browser's own decoder opens this container, so the sound is taken out here: the packets
// of the first MPEG audio stream (MP1/MP2/MP3) are joined into a plain audio stream, then decoded, MP3 by the browser,
// MP1/MP2 by mpg123 in WebAssembly (/vendor/mpg123/). AC-3 sound (most DVDs) is not decoded yet.
// The file is read in pieces, so a long recording is never loaded whole; only its audio is kept.

const ZH = () => document.documentElement.lang.startsWith('zh');
const msg = (en, zh) => (ZH() ? zh : en);

// A program stream starts with a pack header: 00 00 01 BA
export async function isMpegPs(file) {
    const h = new Uint8Array(await file.slice(0, 4).arrayBuffer());
    return h.length === 4 && h[0] === 0 && h[1] === 0 && h[2] === 1 && h[3] === 0xBA;
}

// → { audio: Uint8Array of MPEG audio frames, hasAc3 }
export async function extractAudio(file, onProgress) {
    const CHUNK = 4 << 20;
    let buf = new Uint8Array(0), i = 0, filePos = 0;
    const need = async (n) => {   // bytes buf[i .. i + n) in memory; false at the end of the file
        while (buf.length - i < n) {
            if (filePos >= file.size) return false;
            const next = new Uint8Array(await file.slice(filePos, filePos + CHUNK).arrayBuffer());
            filePos += next.length;
            const rest = buf.subarray(i), joined = new Uint8Array(rest.length + next.length);
            joined.set(rest);
            joined.set(next, rest.length);
            buf = joined;
            i = 0;
            if (onProgress) onProgress(filePos / file.size);
        }
        return true;
    };
    const parts = [];
    let audioId = -1, hasAc3 = false, size = 0;
    while (await need(4)) {
        if (buf[i] !== 0 || buf[i + 1] !== 0 || buf[i + 2] !== 1) { i++; continue; }   // find the next start code
        const id = buf[i + 3];
        if (id === 0xBA) {   // pack header: MPEG-2 (14 bytes + stuffing) or MPEG-1 (12 bytes)
            if (!(await need(14))) break;
            i += (buf[i + 4] & 0xC0) === 0x40 ? 14 + (buf[i + 13] & 7) : 12;
            continue;
        }
        if (id < 0xBB) { i += id === 0xB9 ? 4 : 1; continue; }   // end code, or not a packet: keep looking
        if (!(await need(6))) break;
        const len = (buf[i + 4] << 8) | buf[i + 5];
        if (!(await need(6 + len))) break;
        if ((id >= 0xC0 && id <= 0xDF) || id === 0xBD) {   // MPEG audio, or private stream 1 (AC-3, LPCM, subtitles)
            const end = i + 6 + len;
            let h = i + 6;
            if ((buf[h] & 0xC0) === 0x80) h += 3 + buf[h + 2];   // MPEG-2 PES header
            else {                                             // MPEG-1 PES header
                while (h < end && buf[h] === 0xFF) h++;
                if ((buf[h] & 0xC0) === 0x40) h += 2;
                if ((buf[h] & 0xF0) === 0x20) h += 5;
                else if ((buf[h] & 0xF0) === 0x30) h += 10;
                else if (buf[h] === 0x0F) h += 1;
            }
            if (id === 0xBD) {
                if (h < end && buf[h] >= 0x80 && buf[h] <= 0x87) hasAc3 = true;
            } else if (h < end && (audioId < 0 || id === audioId)) {
                audioId = id;
                parts.push(buf.slice(h, end));
                size += end - h;
            }
        }
        i += 6 + len;
    }
    const audio = new Uint8Array(size);
    let o = 0;
    for (const p of parts) { audio.set(p, o); o += p.length; }
    return { audio, hasAc3 };
}

// MPEG audio layer of the first frame: 1, 2 or 3 (MP3); 0 if none is found
function layerOf(a) {
    for (let k = 0; k + 1 < a.length && k < 65536; k++) {
        if (a[k] === 0xFF && (a[k + 1] & 0xE0) === 0xE0) {
            const bits = (a[k + 1] >> 1) & 3;
            if (bits) return 4 - bits;
        }
    }
    return 0;
}

// The sound of an MPEG program stream → AudioBuffer
export async function decodeMpegPs(file, ctx, onProgress) {
    const { audio, hasAc3 } = await extractAudio(file, onProgress);
    if (!audio.length) {
        throw new Error(hasAc3
            ? msg("This MPEG file has AC-3 (Dolby Digital) sound, which the browser can't decode yet.", '此 MPEG 文件的声音是 AC-3（杜比数字）格式，浏览器暂时无法解码。')
            : msg('No audio track was found in this MPEG file.', '此 MPEG 文件中没有找到音轨。'));
    }
    if (layerOf(audio) === 3) {
        try { return await ctx.decodeAudioData(audio.slice().buffer); } catch (e) { /* mpg123 below */ }
    }
    const { MPEGDecoder } = await import('/vendor/mpg123/mpg123-decoder.min.mjs');
    const decoder = new MPEGDecoder();
    await decoder.ready;
    try {
        const pieces = [];
        let total = 0, rate = 0, channels = 0;
        const STEP = 1 << 20;
        for (let o = 0; o < audio.length; o += STEP) {   // a streaming decoder: frames cut between steps carry over
            const r = decoder.decode(audio.subarray(o, o + STEP));
            if (!r.samplesDecoded) continue;
            pieces.push(r.channelData.map((c) => c.slice(0, r.samplesDecoded)));
            total += r.samplesDecoded;
            rate = r.sampleRate;
            channels = Math.max(channels, r.channelData.length);
        }
        if (!total) throw new Error(msg('Could not decode the sound of this MPEG file.', '无法解码此 MPEG 文件的声音。'));
        const out = new AudioBuffer({ length: total, numberOfChannels: channels, sampleRate: rate });
        for (let c = 0; c < channels; c++) {
            const dst = out.getChannelData(c);
            let o = 0;
            for (const p of pieces) { dst.set(p[Math.min(c, p.length - 1)], o); o += p[0].length; }
        }
        return out;
    } finally {
        decoder.free();
    }
}
