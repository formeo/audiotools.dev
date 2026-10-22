// Several files at once: a list with per-file status and download, plus "download all" as a ZIP.
// Used by the Converter and the Compressor. Everything stays in the browser.
const ZH = document.documentElement.lang.startsWith('zh');
const T = (en, zh) => (ZH ? zh : en);

export const fmtSize = (b) => (b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB');
export const fmtTime = (s) => Math.floor(s / 60) + ':' + String(Math.floor(s % 60)).padStart(2, '0');

export class BatchList {
    constructor(container, files) {
        this.el = container;
        this.items = Array.from(files, (file) => ({ file, blob: null, name: null }));
        this.el.innerHTML = '';
        this.el.hidden = false;
        this.rows = this.items.map(({ file }) => {
            const row = document.createElement('li');
            row.className = 'batch-row';
            row.innerHTML = '<span class="batch-name"></span><span class="batch-meta"></span><span class="batch-status">—</span><span class="batch-bar"></span>';
            row.querySelector('.batch-name').textContent = file.name;
            row.querySelector('.batch-name').title = file.name;
            row.querySelector('.batch-meta').textContent = fmtSize(file.size);
            this.el.appendChild(row);
            return row;
        });
    }
    // Back to "waiting" before running again (e.g. with another format)
    restart() {
        this.items.forEach((it) => { it.blob = null; it.name = null; });
        this.rows.forEach((row) => {
            const a = row.querySelector('a'); if (a) URL.revokeObjectURL(a.href);
            row.classList.remove('active', 'done', 'failed');
            row.querySelector('.batch-status').textContent = '—';
            row.querySelector('.batch-bar').style.width = '0';
        });
    }
    get totalBytes() { return this.items.reduce((s, it) => s + it.file.size, 0); }
    meta(i, text) { this.rows[i].querySelector('.batch-meta').textContent = text; }
    progress(i, p) {
        const row = this.rows[i];
        row.classList.add('active');
        row.querySelector('.batch-status').textContent = Math.round(p * 100) + '%';
        row.querySelector('.batch-bar').style.width = Math.round(p * 100) + '%';
    }
    done(i, blob, name) {
        Object.assign(this.items[i], { blob, name });
        const row = this.rows[i];
        row.classList.remove('active');
        row.classList.add('done');
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = name;
        a.textContent = fmtSize(blob.size);
        a.title = T('Download ', '下载 ') + name;
        row.querySelector('.batch-status').replaceChildren(a);
    }
    fail(i, message) {
        const row = this.rows[i];
        row.classList.remove('active');
        row.classList.add('failed');
        row.querySelector('.batch-status').textContent = T('Failed', '失败');
        row.querySelector('.batch-status').title = message;
    }
    get results() { return this.items.filter((it) => it.blob); }
    async downloadZip(zipName) {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(await zip(this.results.map((it) => ({ name: it.name, blob: it.blob }))));
        a.download = zipName;
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 30000);
    }
    clear() {
        this.rows.forEach((r) => { const a = r.querySelector('a'); if (a) URL.revokeObjectURL(a.href); });
        this.el.innerHTML = '';
        this.el.hidden = true;
    }
}

// Minimal ZIP writer, entries stored without compression (audio is already compressed). UTF-8 names.
const CRC = new Uint32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
function crc32(bytes) { let c = 0xFFFFFFFF; for (let i = 0; i < bytes.length; i++) c = CRC[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }

export async function zip(entries) {
    const enc = new TextEncoder();
    const d = new Date();
    const dosTime = (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1);
    const dosDate = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
    const used = new Set(), parts = [], central = [];
    let offset = 0;
    for (const { name, blob } of entries) {
        let unique = name;
        for (let n = 2; used.has(unique); n++) unique = name.replace(/(\.[^.]*)?$/, ` (${n})$1`);
        used.add(unique);
        const fname = enc.encode(unique), data = new Uint8Array(await blob.arrayBuffer()), crc = crc32(data);
        const header = (sig, size) => { const v = new DataView(new ArrayBuffer(size)); v.setUint32(0, sig, true); return v; };
        const local = header(0x04034b50, 30);
        [[4, 20], [6, 0x0800], [8, 0], [10, dosTime], [12, dosDate], [26, fname.length], [28, 0]].forEach(([o, v]) => local.setUint16(o, v, true));
        [[14, crc], [18, data.length], [22, data.length]].forEach(([o, v]) => local.setUint32(o, v, true));
        parts.push(local, fname, data);
        const cen = header(0x02014b50, 46);
        [[4, 20], [6, 20], [8, 0x0800], [10, 0], [12, dosTime], [14, dosDate], [28, fname.length], [30, 0], [32, 0], [34, 0], [36, 0]].forEach(([o, v]) => cen.setUint16(o, v, true));
        [[16, crc], [20, data.length], [24, data.length], [38, 0], [42, offset]].forEach(([o, v]) => cen.setUint32(o, v, true));
        central.push(cen, fname);
        offset += 30 + fname.length + data.length;
    }
    const size = central.reduce((s, p) => s + p.byteLength, 0);
    const end = new DataView(new ArrayBuffer(22));
    end.setUint32(0, 0x06054b50, true);
    end.setUint16(8, entries.length, true); end.setUint16(10, entries.length, true);
    end.setUint32(12, size, true); end.setUint32(16, offset, true);
    return new Blob([...parts, ...central, end], { type: 'application/zip' });
}
