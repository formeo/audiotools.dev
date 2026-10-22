// Shared download for tools that render an AudioBuffer: MP3 (default) or WAV.
// MP3 is encoded by /media.js (LAME in WebAssembly via Mediabunny).
(function () {
    // Download `buffer` as the format chosen in `select` (mp3 | wav). `wavBlob` is reused for WAV.
    window.downloadAudio = async function (buffer, wavBlob, select, baseName, button) {
        const mp3 = select.value === 'mp3';
        const label = button && button.textContent;
        if (button) { button.disabled = true; if (mp3) button.textContent = document.documentElement.lang.startsWith('zh') ? '正在编码 MP3…' : 'Encoding MP3…'; }
        try {
            const blob = mp3 ? await (await import('/media.js')).encodeBuffer(buffer, { format: 'mp3', bitrate: 192000 }) : wavBlob;
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
