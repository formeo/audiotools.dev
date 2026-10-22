// "Drop a file or say what you need" helper (home pages), "continue with this file" (tool pages),
// and the hand-off of the file (and settings like "compress to 10 MB") to the next tool page.
// Everything stays in the browser: the file is analyzed with Web Audio and passed to the tool
// through IndexedDB, which is cleared as soon as the tool picks it up.
(function () {
    const ZH = document.documentElement.lang.startsWith('zh');
    const T = (en, zh) => (ZH ? zh : en);
    const track = (name, params) => { if (typeof gtag === 'function') gtag('event', name, params); };

    // ---------- settings in plain words (EN / RU / ZH): "compress to 10 MB", "keep the first 30 s", "1.5x faster" ----------
    const num = (v) => parseFloat(v.replace(',', '.'));
    const has = (q, words) => words.some((w) => q.includes(w));
    const N = '(\\d+(?:[.,]\\d+)?)';
    const TIME = '(\\d+:\\d{1,2}(?:[.,]\\d+)?|\\d+(?:[.,]\\d+)?)\\s*(min|мин|分钟|分|s|sec|с|сек|秒)?';
    const sec = (v, unit) => (v.includes(':') ? +v.split(':')[0] * 60 + num(v.split(':')[1]) : num(v) * (/^(min|мин|分)/.test(unit || '') ? 60 : 1));
    const clock = (t) => Math.floor(t / 60) + ':' + String(Math.round(t % 60)).padStart(2, '0');
    const FMT = { mp3: 'mp3', m4a: 'm4a', aac: 'm4a', wav: 'wav', flac: 'flac' };

    // → { tool: settings } for every setting found in the request
    function parseSettings(q) {
        q = q.toLowerCase();
        const out = {};
        let m;
        const louder = has(q, ['louder', 'boost', 'volume', 'amplif', 'громч', 'громк', 'усил', '大声', '音量', '放大', '增强']);
        const faster = has(q, ['faster', 'speed up', 'быстр', 'ускор', '快', '加速']);
        const slower = has(q, ['slower', 'slow down', 'медлен', 'замедл', '慢', '减速']);
        const times = q.match(new RegExp(N + '\\s*(x|х|×|раза?|倍)(?![a-zа-я])'));
        const pct = q.match(/(\d+)\s*%/);
        // size or bitrate → compressor (or converter, if a target format is named)
        if ((m = q.match(new RegExp(N + '\\s*(mb|мб|мегабайт|兆)')))) out['audio-compressor'] = { targetMB: num(m[1]) };
        const kb = q.match(/(\d{2,3})\s*(kbps|kb\/s|кбит|кбпс|k)(?![a-zа-я])/);
        const to = q.match(/(?:\bto\b|\binto\b|(?:^|\s)в\s|转成|转为|转换为|转换成|转)\s*(mp3|m4a|aac|wav|flac)/);
        if (to) out.converter = { format: FMT[to[1]], ...(kb && { bitrate: +kb[1] }) };
        else if (kb) out['audio-compressor'] = { ...out['audio-compressor'], bitrate: +kb[1] };
        // volume
        if (has(q, ['normaliz', 'нормализ', '标准化'])) out['volume-booster'] = { normalize: true };
        else if (louder) {
            let gain = null;
            if ((m = q.match(/\+?(\d+(?:[.,]\d+)?)\s*(db|дб|分贝)/))) gain = 100 * Math.pow(10, num(m[1]) / 20);
            else if (pct) gain = +pct[1] > 100 ? +pct[1] : 100 + +pct[1];
            else if (times) gain = 100 * num(times[1]);
            if (gain) out['volume-booster'] = { gain: Math.min(500, Math.round(gain / 5) * 5) };
        }
        // speed
        if (!louder && times && (faster || slower || has(q, ['speed', 'скорост', '速度', '倍速']))) {
            const v = num(times[1]);
            out['audio-speed-changer'] = { speed: slower && v > 1 ? 1 / v : v };
        } else if (!louder && pct && (faster || slower)) out['audio-speed-changer'] = { speed: faster ? 1 + pct[1] / 100 : 1 - pct[1] / 100 };
        // trim
        const remove = has(q, ['remove', 'delete', 'cut off', 'drop', 'убер', 'убра', 'удал', 'отрез', 'отреж', 'обрез', 'обреж', '去掉', '删除', '删掉', '剪掉']);
        if ((m = q.match(new RegExp('(?:from|от|(?:^|\\s)с|从)\\s*' + TIME + '\\s*(?:to|до|по|-|–|到|至)\\s*' + TIME)))) out['audio-trimmer'] = { start: sec(m[1], m[2]), end: sec(m[3], m[4] || m[2]) };
        else if ((m = q.match(new RegExp('(?:first|перв\\S*|前)\\s*' + TIME)))) out['audio-trimmer'] = remove ? { start: sec(m[1], m[2]) } : { start: 0, end: sec(m[1], m[2]) };
        else if ((m = q.match(new RegExp('(?:last|последн\\S*|最后|后)\\s*' + TIME)))) out['audio-trimmer'] = remove ? { cutEnd: sec(m[1], m[2]) } : { fromEnd: sec(m[1], m[2]) };
        return out;
    }

    // [start, end] in seconds for a trim setting on a recording of `d` seconds
    function trimRange(t, d) {
        if (t.fromEnd != null) return [Math.max(0, d - t.fromEnd), d];
        if (t.cutEnd != null) return [0, Math.max(0, d - t.cutEnd)];
        return [Math.min(t.start || 0, d), Math.min(t.end != null ? t.end : d, d)];
    }
    const RATES = [64, 128, 192, 256, 320];
    const bitrateFor = (mb, d) => mb * 8 * 1048576 / d / 1000 * 0.97;   // kbps that fits `mb` (3% for headers)
    const pickRate = (kbps, options = RATES) => options.filter((r) => r <= kbps).pop() || options[0];

    // Short description of a setting, concrete when the recording length is known
    function describe(tool, st, d) {
        if (tool === 'audio-compressor') {
            if (st.targetMB && d) { const r = pickRate(bitrateFor(st.targetMB, d)); return T(`≤ ${st.targetMB} MB → MP3 at ${r} kbps (≈ ${(r * 1000 / 8 * d / 1048576).toFixed(1)} MB)`, `≤ ${st.targetMB} MB → MP3 ${r} kbps（约 ${(r * 1000 / 8 * d / 1048576).toFixed(1)} MB）`); }
            if (st.targetMB) return T(`Make it ${st.targetMB} MB or smaller`, `压缩到 ${st.targetMB} MB 以内`);
            return T(`MP3 at ${pickRate(st.bitrate)} kbps`, `MP3 ${pickRate(st.bitrate)} kbps`);
        }
        if (tool === 'converter') return T(`Convert to ${st.format.toUpperCase()}`, `转换为 ${st.format.toUpperCase()}`) + (st.bitrate ? ` · ${st.bitrate} kbps` : '');
        if (tool === 'volume-booster') return st.normalize ? T('Normalize the peak level', '将峰值标准化')
            : T(`Volume ${st.gain}% (${st.gain > 100 ? '+' : ''}${(20 * Math.log10(st.gain / 100)).toFixed(1)} dB)`, `音量 ${st.gain}%（${st.gain > 100 ? '+' : ''}${(20 * Math.log10(st.gain / 100)).toFixed(1)} dB）`);
        if (tool === 'audio-speed-changer') return T(`Speed ×${+st.speed.toFixed(2)}, pitch stays put`, `${+st.speed.toFixed(2)} 倍速，音调不变`);
        if (tool === 'audio-trimmer') {
            if (d) { const [a, b] = trimRange(st, d); return T(`Keep ${clock(a)}–${clock(b)}`, `保留 ${clock(a)}–${clock(b)}`); }
            if (st.fromEnd != null) return T(`Keep the last ${clock(st.fromEnd)}`, `保留最后 ${clock(st.fromEnd)}`);
            if (st.cutEnd != null) return T(`Remove the last ${clock(st.cutEnd)}`, `去掉最后 ${clock(st.cutEnd)}`);
            if (st.end == null) return T(`Remove the first ${clock(st.start)}`, `去掉前 ${clock(st.start)}`);
            return T(`Keep ${clock(st.start)}–${clock(st.end)}`, `保留 ${clock(st.start)}–${clock(st.end)}`);
        }
        return '';
    }

    // Tool pages: put the settings into the tool's own controls once it has loaded a file.
    // `buffer` is the decoded file each of these tools keeps in a top-level variable.
    const decoded = () => (typeof buffer !== 'undefined' && buffer) || null; // eslint-disable-line no-undef
    const shown = (id) => { const el = document.getElementById(id); return el && !el.classList.contains('hidden'); };
    function setControl(id, value, event) { const el = document.getElementById(id); el.value = value; el.dispatchEvent(new Event(event, { bubbles: true })); }
    const APPLY = {
        'converter': { ready: () => document.querySelector('#convertSection.show') && /Hz/.test(document.getElementById('fileMeta').textContent),
            run: (st) => {
                if (st.format) document.querySelector(`.format-chip[data-fmt="${st.format}"]`).click();
                if (st.bitrate) setControl('mp3Bitrate', pickRate(st.bitrate, [128, 192, 256, 320]), 'change');
            } },
        'audio-compressor': { ready: () => shown('panel') && decoded(),
            run: (st) => setControl('bitrate', pickRate(st.bitrate || bitrateFor(st.targetMB, decoded().duration)), 'change') },
        'audio-trimmer': { ready: () => shown('editor') && decoded(),
            run: (st) => {
                const [a, b] = trimRange(st, decoded().duration);
                const f = (t) => Math.floor(t / 60) + ':' + (t % 60).toFixed(2).padStart(5, '0');
                setControl('startTime', f(a), 'change');
                setControl('endTime', f(b), 'change');
            } },
        'audio-speed-changer': { ready: () => shown('panel') && decoded(), run: (st) => setControl('speed', st.speed, 'input') },
        'volume-booster': { ready: () => shown('panel') && decoded(),
            run: (st) => {
                document.querySelector(`.mode-btn[data-mode="${st.normalize ? 'normalize' : 'boost'}"]`).click();
                if (!st.normalize) setControl('gain', st.gain, 'input');
            } },
    };
    // Controls a setting lands in; compared when the file is processed to see if the user kept it.
    const SNAPSHOT = { 'converter': ['#mp3Bitrate', '.format-chip.active'], 'audio-compressor': ['#bitrate'],
        'audio-trimmer': ['#startTime', '#endTime'], 'audio-speed-changer': ['#speed'], 'volume-booster': ['#gain', '.mode-btn.active'] };
    const snapshot = (tool) => SNAPSHOT[tool].map((sel) => { const el = document.querySelector(sel); return el ? el.dataset.fmt || el.dataset.mode || el.value : ''; }).join('|');
    function applyWhenReady(settings) {
        const tool = location.pathname.replace(/^\/zh/, '').replace(/\//g, '');
        const a = APPLY[tool], st = settings && settings[tool];
        if (!a || !st) return;
        const timer = setInterval(() => {
            if (!a.ready()) return;
            clearInterval(timer);
            a.run(st);
            const applied = snapshot(tool);
            document.addEventListener('at:processed', () => track('settings_kept', { tool, kept: snapshot(tool) === applied ? 'yes' : 'no' }), { once: true });
        }, 250);
    }

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
    // via: 'assistant' (home helper) or 'next' ("continue with this file"); reported with file_processed
    const putPending = (files, settings, via) => store('readwrite', (s) => s.put({ files, settings, via }, 'pending'));
    const takePending = () => store('readwrite', (s) => { const g = s.get('pending'); s.delete('pending'); return g; });

    // ---------- tool pages: "continue with this file" after a result ----------
    const ZH_PAGES = ['converter', 'volume-booster', 'text-to-speech', 'audio-joiner', 'audio-compressor'];   // tools with a Chinese page
    const NEXT = [['audio-compressor', 'Compress', '压缩'], ['audio-trimmer', 'Trim', '剪辑'], ['volume-booster', 'Boost volume', '增强音量'],
                  ['converter', 'Convert format', '转换格式'], ['audio-speed-changer', 'Change speed', '变速'], ['audio-joiner', 'Join with more', '合并']];
    window.offerNext = function (tool, anchor, file) {
        const old = document.getElementById('next-actions');
        if (old) old.remove();
        const el = document.createElement('div');
        el.id = 'next-actions';
        el.className = 'next-actions';
        el.append(T('Continue with this file:', '继续处理此文件：'));
        NEXT.filter(([t]) => t !== tool).slice(0, 3).forEach(([t, en, zh]) => {
            const a = document.createElement('a');
            a.href = (ZH && ZH_PAGES.includes(t) ? '/zh/' : '/') + t + '/';
            a.textContent = T(en, zh);
            a.addEventListener('click', async (e) => {
                e.preventDefault();
                track('next_pick', { from: tool, tool: t });
                await putPending([file], null, 'next');
                location.href = a.href + '#from-assistant';
            });
            el.appendChild(a);
        });
        anchor.after(el);
    };

    // ---------- tool pages: pick up a file sent from the home page or another tool ----------
    const assistant = document.getElementById('assistant');
    if (!assistant) {
        if (location.hash !== '#from-assistant') return;
        history.replaceState(null, '', location.pathname + location.search);
        takePending().then((pending) => {
            const input = document.getElementById('fileInput') || document.getElementById('whisperFile');
            if (!pending || !input) return;
            try { sessionStorage.setItem('at_via:' + location.pathname, pending.via || 'assistant'); } catch (e) { /* private mode */ }
            applyWhenReady(pending.settings);   // also works if the user picks the file here
            const files = pending.files;
            if (!files || !files.length) return;
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
        'audio-compressor': { url: ZH ? '/zh/audio-compressor/' : '/audio-compressor/', name: T('Audio Compressor', '音频压缩'),
            kw: ['compress', 'smaller', 'reduce', 'file size', 'shrink', 'bitrate', 'email', 'telegram', 'whatsapp',
                 'сжать', 'уменьш', 'размер', 'меньше', 'битрейт', '压缩', '变小', '缩小', '大小', '体积'] },
        'volume-booster': { url: ZH ? '/zh/volume-booster/' : '/volume-booster/', name: T('Volume Booster', '音量增强'),
            kw: ['quiet', 'louder', 'volume', 'boost', 'normalize', 'amplify', 'gain',
                 'тих', 'громк', 'громч', 'усил', 'нормализ', '音量', '声音太小', '太小声', '放大', '增强', '标准化'] },
        'audio-trimmer': { url: '/audio-trimmer/', name: T('Audio Trimmer', '音频剪辑'),
            kw: ['trim', 'cut', 'crop', 'shorten', 'ringtone', 'clip', 'remove the start', 'remove the end',
                 'обрез', 'обреж', 'вырез', 'отрез', 'отреж', 'рингтон', 'укорот', '剪辑', '裁剪', '剪切', '铃声', '截取'] },
        'audio-joiner': { url: ZH ? '/zh/audio-joiner/' : '/audio-joiner/', name: T('Audio Joiner', '音频合并'),
            kw: ['join', 'merge', 'combine', 'concatenate', 'several files', 'multiple files',
                 'склеить', 'склей', 'объедин', 'соедин', 'несколько', '合并', '拼接', '连接', '多个'] },
        'audio-speed-changer': { url: '/audio-speed-changer/', name: T('Speed Changer', '音频变速'),
            kw: ['speed', 'slow down', 'speed up', 'faster', 'slower', 'tempo',
                 'скорост', 'замедл', 'ускор', 'темп', '速度', '变速', '放慢', '加快', '加速', '减速'] },
        'voice-to-text': { url: '/voice-to-text/', name: T('Voice to Text', '语音转文字'),
            kw: ['transcri', 'to text', 'subtitle', 'speech to text', 'dictat', 'voice message', 'lecture', 'interview',
                 'расшифр', 'в текст', 'субтитр', 'голосов', 'лекци', 'диктов', '转文字', '转录', '字幕', '语音转', '听写'] },
        'text-to-speech': { url: ZH ? '/zh/text-to-speech/' : '/text-to-speech/', name: T('Text to Speech', '文字转语音'),
            kw: ['text to speech', 'read aloud', 'tts', 'voice over', 'narrat', 'speak',
                 'озвуч', 'вслух', 'синтез речи', 'прочитать', '朗读', '配音', '文字转语音', '语音合成'] },
    };

    const input = document.getElementById('assistantText');
    const fileInput = document.getElementById('assistantFile');
    const results = document.getElementById('assistantResults');
    let files = null;            // files dropped on the helper, handed to the picked tool
    let fileInfo = null;         // { duration, text, items } of the dropped file
    const used = {};
    let noMatchTimer;

    function render(items, method, message) {
        clearTimeout(noMatchTimer);
        results.innerHTML = '';
        if (message) {
            const p = document.createElement('p');
            p.className = 'assistant-msg';
            p.textContent = message;
            results.appendChild(p);
        }
        items.forEach(({ tool, why, settings }, i) => {
            const a = document.createElement('a');
            a.className = 'assistant-pick';
            a.href = TOOLS[tool].url;
            a.innerHTML = '<b></b><span></span>';
            a.querySelector('b').textContent = TOOLS[tool].name;
            a.querySelector('span').textContent = why;
            a.addEventListener('click', async (e) => {
                track('assistant_pick', { tool, method, rank: i + 1, with_settings: settings ? 'yes' : 'no' });
                if (!files && !settings) return;
                e.preventDefault();
                await putPending(files || [], settings ? { [tool]: settings } : null, 'assistant');
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
        const method = files ? 'file' : 'text';
        const message = fileInfo && fileInfo.text;
        const found = parseSettings(q);
        q = q.toLowerCase();
        const scored = Object.entries(TOOLS)
            .map(([tool, t]) => [tool, t.kw.filter((k) => q.includes(k)).reduce((s, k) => s + weight(k), 0) + (found[tool] ? 1000 : 0)])
            .filter(([, score]) => score > 0)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3);
        if (!scored.length) {
            render([], method, T('Not sure what you need — try other words, or pick a tool below.',
                                 '没太明白您的需求——换个说法试试，或直接在下方选择工具。'));
            // counted once per visit, after typing settles; the text itself is never sent
            noMatchTimer = setTimeout(() => { if (!used.nomatch) { used.nomatch = true; track('assistant_nomatch', { method }); } }, 1500);
            return;
        }
        render(scored.map(([tool]) => (found[tool]
            ? { tool, settings: found[tool], why: describe(tool, found[tool], fileInfo && fileInfo.duration) }
            : { tool, why: WHY[tool] })), method, message);
    }
    const WHY = {
        'converter': T('MP3, M4A, WAV or FLAC, also from video', '转换为 MP3、M4A、WAV 或 FLAC，也可从视频提取'),
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
        fileInfo = null;
        if (files.length > 1) {
            fileInfo = { text: '', items: [{ tool: 'audio-joiner', why: T(`${files.length} files → merge them into one`, `${files.length} 个文件 → 合并为一个`) },
                                            { tool: 'converter', why: T(`Convert all ${files.length} at once, download as ZIP`, `一次转换全部 ${files.length} 个，打包下载`) },
                                            { tool: 'audio-compressor', why: T(`Make all ${files.length} smaller at once`, `一次压缩全部 ${files.length} 个文件`) }] };
            render(fileInfo.items, 'file');
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
        out.push({ tool: 'converter', why: T(`${ext} → MP3, M4A, WAV or FLAC`, `${ext} → MP3、M4A、WAV 或 FLAC`) });
        out.push({ tool: 'audio-trimmer', why: T(`Cut a part of the ${len} recording`, `从 ${len} 的录音中剪出片段`) });
        out.push({ tool: 'audio-speed-changer', why: WHY['audio-speed-changer'] });
        fileInfo = { duration: buf.duration, text: `${f.name} · ${len} · ${mb.toFixed(1)} MB`, items: out.slice(0, 3) };
        const q = input.value.trim();
        if (q.length >= 2) return suggestByText(q);   // "compress to 10 MB" typed before the file was dropped
        render(fileInfo.items, 'file', fileInfo.text);
    }

    let timer;
    input.addEventListener('input', () => {
        clearTimeout(timer);
        const q = input.value.trim();
        timer = setTimeout(() => (q.length >= 2 ? suggestByText(q) : fileInfo ? render(fileInfo.items, 'file', fileInfo.text) : render([], 'text')), 250);
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
