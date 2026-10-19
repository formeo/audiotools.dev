// "Drop a file or say what you need" helper (home pages) + hand-off of that file to the tool page.
// Everything stays in the browser: the file is analyzed with Web Audio and passed to the tool
// through IndexedDB, which is cleared as soon as the tool picks it up.
(function () {
    const ZH = document.documentElement.lang.startsWith('zh');
    const T = (en, zh) => (ZH ? zh : en);
    const track = (name, params) => { if (typeof gtag === 'function') gtag('event', name, params); };

    // ---------- hand-off store (one pending entry) ----------
    function store(mode, fn) {
        return new Promise((resolve, reject) => {
            const open = indexedDB.open('audiotools', 1);
            open.onupgradeneeded = () => open.result.createObjectStore('handoff');
            open.onerror = () => reject(open.error);
            open.onsuccess = () => {
                const tx = open.result.transaction('handoff', mode);
                const result = fn(tx.objectStore('handoff'));
                tx.oncomplete = () => resolve(result && result.result);
                tx.onerror = () => reject(tx.error);
            };
        });
    }
    const putPending = (files) => store('readwrite', (s) => s.put(files, 'pending'));
    const takePending = () => store('readwrite', (s) => { const g = s.get('pending'); s.delete('pending'); return g; });

    // ---------- tool pages: pick up a file sent from the home page ----------
    const assistant = document.getElementById('assistant');
    if (!assistant) {
        if (location.hash !== '#from-assistant') return;
        history.replaceState(null, '', location.pathname + location.search);
        takePending().then((files) => {
            const input = document.getElementById('fileInput') || document.getElementById('whisperFile');
            if (!files || !files.length || !input) return;
            const dt = new DataTransfer();
            files.forEach((f) => dt.items.add(f));
            input.files = dt.files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        });
        return;
    }

    // ---------- home page: suggestions ----------
    const TOOLS = {
        'converter': { url: ZH ? '/zh/converter/' : '/converter/', name: T('Audio Converter', '音频转换器'),
            kw: ['convert', 'format', 'mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac', 'webm', 'mp4', 'video', 'extract audio',
                 'конверт', 'формат', 'преобраз', 'видео', '转换', '格式', '视频', '提取音频'] },
        'audio-compressor': { url: '/audio-compressor/', name: T('Audio Compressor', '音频压缩'),
            kw: ['compress', 'smaller', 'reduce', 'file size', 'shrink', 'bitrate', 'email', 'telegram', 'whatsapp',
                 'сжать', 'уменьш', 'размер', 'меньше', 'битрейт', '压缩', '变小', '缩小', '大小', '体积'] },
        'volume-booster': { url: '/volume-booster/', name: T('Volume Booster', '音量增强'),
            kw: ['quiet', 'louder', 'volume', 'boost', 'normalize', 'amplify', 'gain',
                 'тих', 'громк', 'громч', 'усил', 'нормализ', '音量', '声音太小', '太小声', '放大', '增强', '标准化'] },
        'audio-trimmer': { url: '/audio-trimmer/', name: T('Audio Trimmer', '音频剪辑'),
            kw: ['trim', 'cut', 'crop', 'shorten', 'ringtone', 'clip', 'remove the start', 'remove the end',
                 'обрез', 'вырез', 'отрез', 'рингтон', 'укорот', '剪辑', '裁剪', '剪切', '铃声', '截取'] },
        'audio-joiner': { url: '/audio-joiner/', name: T('Audio Joiner', '音频合并'),
            kw: ['join', 'merge', 'combine', 'concatenate', 'several files', 'multiple files',
                 'склеить', 'склей', 'объедин', 'соедин', 'несколько', '合并', '拼接', '连接', '多个'] },
        'audio-speed-changer': { url: '/audio-speed-changer/', name: T('Speed Changer', '音频变速'),
            kw: ['speed', 'slow down', 'speed up', 'faster', 'slower', 'tempo',
                 'скорост', 'замедл', 'ускор', 'темп', '速度', '变速', '放慢', '加快', '加速', '减速'] },
        'voice-to-text': { url: '/voice-to-text/', name: T('Voice to Text', '语音转文字'),
            kw: ['transcri', 'to text', 'subtitle', 'speech to text', 'dictat', 'voice message', 'lecture', 'interview',
                 'расшифр', 'в текст', 'субтитр', 'голосов', 'лекци', 'диктов', '转文字', '转录', '字幕', '语音转', '听写'] },
        'text-to-speech': { url: '/text-to-speech/', name: T('Text to Speech', '文字转语音'),
            kw: ['text to speech', 'read aloud', 'tts', 'voice over', 'narrat', 'speak',
                 'озвуч', 'вслух', 'синтез речи', 'прочитать', '朗读', '配音', '文字转语音', '语音合成'] },
    };

    const input = document.getElementById('assistantText');
    const fileInput = document.getElementById('assistantFile');
    const results = document.getElementById('assistantResults');
    let files = null;            // files dropped on the helper, handed to the picked tool
    const used = {};

    function render(items, method, message) {
        results.innerHTML = '';
        if (message) {
            const p = document.createElement('p');
            p.className = 'assistant-msg';
            p.textContent = message;
            results.appendChild(p);
        }
        items.forEach(({ tool, why }) => {
            const a = document.createElement('a');
            a.className = 'assistant-pick';
            a.href = TOOLS[tool].url;
            a.innerHTML = '<b></b><span></span>';
            a.querySelector('b').textContent = TOOLS[tool].name + ' →';
            a.querySelector('span').textContent = why;
            a.addEventListener('click', async (e) => {
                track('assistant_pick', { tool, method });
                if (method !== 'file') return;
                e.preventDefault();
                await putPending(files);
                location.href = a.href + '#from-assistant';
            });
            results.appendChild(a);
        });
        if (items.length && !used[method]) { used[method] = true; track('assistant_used', { method }); }
    }

    // --- text: keyword match, longer matches weigh more ("text to speech" beats "to text");
    // a Chinese character carries about a word, so it counts 3x (变小 beats mp3)
    const weight = (k) => k.length * (/[\u4e00-\u9fff]/.test(k) ? 3 : 1);
    function suggestByText(q) {
        q = q.toLowerCase();
        const scored = Object.entries(TOOLS)
            .map(([tool, t]) => [tool, t.kw.filter((k) => q.includes(k)).reduce((s, k) => s + weight(k), 0)])
            .filter(([, score]) => score > 0)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3);
        if (!scored.length) {
            render([], 'text', T('Not sure what you need — try other words, or pick a tool below.',
                                  '没太明白您的需求——换个说法试试，或直接在下方选择工具。'));
            return;
        }
        render(scored.map(([tool]) => ({ tool, why: WHY[tool] })), 'text');
    }
    const WHY = {
        'converter': T('Change the format: MP3, WAV, FLAC, OGG, M4A…', '转换格式：MP3、WAV、FLAC、OGG、M4A…'),
        'audio-compressor': T('Make the file smaller (MP3, choose the bitrate)', '减小文件体积（MP3，可选码率）'),
        'volume-booster': T('Make a quiet recording louder or normalize it', '提高音量或标准化'),
        'audio-trimmer': T('Cut out the part you need', '剪出需要的片段'),
        'audio-joiner': T('Merge several files into one', '将多个文件合并为一个'),
        'audio-speed-changer': T('Slow down or speed up without changing pitch', '变速不变调'),
        'voice-to-text': T('Turn speech into text — Private mode runs Whisper on your device', '语音转文字——隐私模式在本机运行 Whisper'),
        'text-to-speech': T('Read text aloud in 50+ languages', '用 50 多种语言朗读文字'),
    };

    // --- file: look at format, size, length and loudness, then suggest
    const fmtTime = (s) => Math.floor(s / 60) + ':' + String(Math.round(s % 60)).padStart(2, '0');
    async function suggestByFile(list) {
        files = Array.from(list);
        input.value = '';
        if (files.length > 1) {
            render([{ tool: 'audio-joiner', why: T(`${files.length} files → merge them into one`, `${files.length} 个文件 → 合并为一个`) },
                    { tool: 'converter', why: WHY.converter }], 'file');
            return;
        }
        const f = files[0];
        render([], 'file', T('Analyzing in your browser…', '正在浏览器中分析…'));
        let buf;
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            buf = await ctx.decodeAudioData(await f.arrayBuffer());
            ctx.close();
        } catch (e) {
            render([], 'file', T('Could not read this file as audio. Try another file.', '无法将此文件识别为音频，请换一个文件。'));
            return;
        }
        let peak = 0;
        for (let c = 0; c < buf.numberOfChannels; c++) {
            const d = buf.getChannelData(c);
            for (let i = 0; i < d.length; i++) { const v = Math.abs(d[i]); if (v > peak) peak = v; }
        }
        const peakDb = peak > 0 ? 20 * Math.log10(peak) : -Infinity;
        const mb = f.size / 1048576;
        const mp3mb = buf.duration * 128000 / 8 / 1048576;
        const ext = (f.name.split('.').pop() || '').toUpperCase();
        const len = fmtTime(buf.duration);
        const out = [];
        if (peakDb < -12) out.push({ tool: 'volume-booster', why: T(`Quiet recording (peak ${peakDb.toFixed(0)} dB) → make it louder`, `录音偏小声（峰值 ${peakDb.toFixed(0)} dB）→ 提高音量`) });
        if (mb > 5 && mp3mb < mb * 0.7) out.push({ tool: 'audio-compressor', why: T(`${mb.toFixed(1)} MB → about ${mp3mb.toFixed(1)} MB as MP3 (128 kbps)`, `${mb.toFixed(1)} MB → 转为 MP3 约 ${mp3mb.toFixed(1)} MB（128 kbps）`) });
        if (buf.duration >= 20) out.push({ tool: 'voice-to-text', why: T(`${len} long — if it's speech, turn it into text on your device`, `时长 ${len}——如果是语音，可在本机转为文字`) });
        out.push({ tool: 'converter', why: T(`${ext} → MP3, WAV or FLAC`, `${ext} → MP3、WAV 或 FLAC`) });
        out.push({ tool: 'audio-trimmer', why: T(`Cut a part of the ${len} recording`, `从 ${len} 的录音中剪出片段`) });
        out.push({ tool: 'audio-speed-changer', why: WHY['audio-speed-changer'] });
        render(out.slice(0, 3), 'file', `${f.name} · ${len} · ${mb.toFixed(1)} MB`);
    }

    let timer;
    input.addEventListener('input', () => {
        clearTimeout(timer);
        files = null;
        const q = input.value.trim();
        timer = setTimeout(() => (q.length >= 2 ? suggestByText(q) : render([], 'text')), 250);
    });
    fileInput.addEventListener('change', () => { if (fileInput.files.length) suggestByFile(fileInput.files); fileInput.value = ''; });
    assistant.addEventListener('dragover', (e) => { e.preventDefault(); assistant.classList.add('drag'); });
    assistant.addEventListener('dragleave', () => assistant.classList.remove('drag'));
    assistant.addEventListener('drop', (e) => {
        e.preventDefault();
        assistant.classList.remove('drag');
        if (e.dataTransfer.files.length) suggestByFile(e.dataTransfer.files);
    });
})();
