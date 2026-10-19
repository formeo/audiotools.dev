// Shared download for tools that render an AudioBuffer: MP3 (default) or WAV.
// MP3 uses lamejs (loaded by the page), same encoder as the Converter and Compressor.
(function () {
    const MP3_RATES = [8000, 11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000];

    // lamejs only takes MPEG sample rates — resample anything else (e.g. 96 kHz) to 44.1 kHz.
    async function toMp3Rate(buf) {
        if (MP3_RATES.includes(buf.sampleRate)) return buf;
        const ch = Math.min(buf.numberOfChannels, 2);
        const off = new OfflineAudioContext(ch, Math.ceil(buf.duration * 44100), 44100);
        const src = off.createBufferSource();
        src.buffer = buf; src.connect(off.destination); src.start();
        return off.startRendering();
    }

    function encodeMP3(buf, kbps) {
        return new Promise((resolve, reject) => {
            if (typeof lamejs === 'undefined') { reject(new Error('MP3 encoder not loaded. Please reload the page.')); return; }
            const numCh = Math.min(buf.numberOfChannels, 2);
            const enc = new lamejs.Mp3Encoder(numCh, buf.sampleRate, kbps);
            const to16 = (a) => { const o = new Int16Array(a.length); for (let i = 0; i < a.length; i++) { const s = Math.max(-1, Math.min(1, a[i])); o[i] = s < 0 ? s * 0x8000 : s * 0x7FFF; } return o; };
            const left = to16(buf.getChannelData(0));
            const right = numCh > 1 ? to16(buf.getChannelData(1)) : null;
            const block = 1152, total = Math.ceil(left.length / block), out = [];
            let done = 0;
            (function chunk() {   // in slices so the page stays responsive
                const end = Math.min(done + 200, total);
                for (let i = done; i < end; i++) {
                    const s = i * block, l = left.subarray(s, s + block);
                    const mb = right ? enc.encodeBuffer(l, right.subarray(s, s + block)) : enc.encodeBuffer(l);
                    if (mb.length) out.push(mb);
                }
                done = end;
                if (done < total) return setTimeout(chunk, 0);
                const last = enc.flush(); if (last.length) out.push(last);
                resolve(new Blob(out, { type: 'audio/mpeg' }));
            })();
        });
    }

    // Download `buffer` as the format chosen in `select` (mp3 | wav). `wavBlob` is reused for WAV.
    window.downloadAudio = async function (buffer, wavBlob, select, baseName, button) {
        const mp3 = select.value === 'mp3';
        const label = button && button.textContent;
        if (button) { button.disabled = true; if (mp3) button.textContent = 'Encoding MP3…'; }
        try {
            const blob = mp3 ? await encodeMP3(await toMp3Rate(buffer), 192) : wavBlob;
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = baseName + (mp3 ? '.mp3' : '.wav');
            a.click();
            setTimeout(() => URL.revokeObjectURL(a.href), 10000);
        } catch (e) {
            alert(e.message);
        } finally {
            if (button) { button.disabled = false; button.textContent = label; }
        }
    };
})();
