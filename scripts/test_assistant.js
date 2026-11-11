#!/usr/bin/env node
// Focused assistant tests. Pass the JSON produced by --export-cases for the full holdout report.
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

function element(id) {
    const el = {
        id, children: [], textContent: '', value: '', files: [], listeners: {},
        className: '', _innerHTML: '',
        get innerHTML() { return this._innerHTML; },
        set innerHTML(value) { this._innerHTML = value; if (value === '') this.children = []; },
        addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); },
        appendChild(child) { this.children.push(child); return child; },
        querySelector(selector) {
            if (selector === 'b') return this.bold ||= element('b');
            if (selector === 'span') return this.span ||= element('span');
            return null;
        },
        click() {},
    };
    return el;
}

function boot(classify, lang = 'en') {
    const ids = ['assistant', 'assistantText', 'assistantFile', 'assistantResults'];
    const elements = Object.fromEntries(ids.map((id) => [id, element(id)]));
    const scripts = [];
    const events = [];
    const document = {
        documentElement: { lang },
        head: element('head'),
        getElementById: (id) => elements[id] || null,
        createElement: (tag) => element(tag),
    };
    document.head.appendChild = (script) => {
        scripts.push(script.src);
        setImmediate(() => {
            if (classify) {
                context.window.assistantClassify = classify;
                script.onload();
            } else script.onerror();
        });
    };
    const window = {};
    const context = {
        console, document, window, location: { pathname: '/', hash: '' },
        history: {}, sessionStorage: {}, setTimeout, clearTimeout, setInterval, clearInterval,
        gtag: (name, params) => events.push({ name, params }),
    };
    context.globalThis = context;
    vm.createContext(context);
    let source = fs.readFileSync(require.resolve('../assistant.js'), 'utf8');
    source = source.replace(/\}\)\(\);\s*$/, `globalThis.testAssistant = {
        TOOLS, AUDIO_DOMAIN, parseSettings, suggestByText, semanticSuggest,
        setVersion: (v) => { queryVersion = v; },
    };})();`);
    vm.runInContext(source, context);
    return { context, elements, scripts, events, api: context.testAssistant };
}

function ruleTools(api, query) {
    const q = query.toLowerCase();
    const found = api.parseSettings(q);
    const weight = (k) => k.length * (/[\u4e00-\u9fff]/.test(k) ? 3 : 1);
    return Object.entries(api.TOOLS).map(([tool, t]) => [tool,
        t.kw.filter((k) => q.includes(k)).reduce((sum, k) => sum + weight(k), 0) + (found[tool] ? 1000 : 0)])
        .filter(([, score]) => score > 0).sort((a, b) => b[1] - a[1]).map(([tool]) => tool);
}

function gate(ranked) {
    const [best, second] = ranked;
    return best.tool !== 'unsupported' && best.probability >= 0.80 && best.probability - second.probability >= 0.15 ? best.tool : null;
}

async function unitTests() {
    const good = boot((q) => [
        { tool: 'vocal-remover', probability: 0.91 },
        { tool: 'slowed-reverb', probability: 0.03 },
        { tool: 'unsupported', probability: 0.02 },
    ]);
    assert.equal(good.scripts.length, 0, 'initial load must not fetch the model');
    assert.deepEqual(good.api.parseSettings('compress to 10 MB')['audio-compressor'], { targetMB: 10 });
    assert.equal(good.api.parseSettings('convert to flac').converter.format, 'flac');
    assert.equal(good.api.parseSettings('1.5x faster')['audio-speed-changer'].speed, 1.5);
    assert.deepEqual(good.api.parseSettings('keep the first 30 s')['audio-trimmer'], { start: 0, end: 30 });
    good.api.suggestByText('remove vocals for karaoke');
    assert.equal(good.scripts.length, 0, 'a rule match must not fetch the model');
    assert.ok(good.elements.assistantResults.children[0].span.textContent.includes('Start with Fast'));
    good.api.suggestByText('hello how are you');
    assert.equal(good.scripts.length, 0, 'unrelated chit-chat must not fetch the model');
    good.api.suggestByText('sing over this track without the performer');
    await new Promise((resolve) => setTimeout(resolve, 10));
    assert.equal(good.scripts[0], '/assistant-model.js');
    assert.equal(good.elements.assistantResults.children[1].bold.textContent, 'Vocal Remover');
    assert.ok(good.elements.assistantResults.children[1].span.textContent.includes('Cleaner'));
    assert.ok(good.events.every((e) => !JSON.stringify(e.params).includes('sing over')), 'raw query must not be tracked');

    const stale = boot((q) => [
        { tool: 'audio-compressor', probability: 0.95 },
        { tool: 'converter', probability: 0.02 },
        { tool: 'unsupported', probability: 0.01 },
    ]);
    stale.context.window.assistantClassify = null;
    stale.api.setVersion(1);
    const pending = stale.api.semanticSuggest('heavy song attachment', 'text', '', 1);
    stale.api.setVersion(2);
    stale.api.suggestByText('karaoke');
    await pending;
    assert.equal(stale.elements.assistantResults.children[0].bold.textContent, 'Vocal Remover', 'stale result must not overwrite a newer query');

    const failed = boot(null);
    failed.api.semanticSuggest('write down this interview', 'text', '', 0);
    await new Promise((resolve) => setTimeout(resolve, 10));
    assert.ok(failed.elements.assistantResults.children[0].textContent.includes('Not sure'), 'model failure must preserve rule-only no-match');

    const chinese = boot((q) => [
        { tool: 'vocal-remover', probability: 0.9 },
        { tool: 'converter', probability: 0.04 },
        { tool: 'unsupported', probability: 0.02 },
    ], 'zh-CN');
    chinese.api.suggestByText('去掉主唱');
    await new Promise((resolve) => setTimeout(resolve, 10));
    assert.ok(chinese.elements.assistantResults.children[1].span.textContent.includes('先用 Fast'));
}

function holdoutTests(path, api) {
    const modelContext = { atob, self: {} };
    vm.createContext(modelContext);
    vm.runInContext(fs.readFileSync(require.resolve('../assistant-model.js'), 'utf8'), modelContext);
    const classify = modelContext.self.assistantClassify;
    const cases = JSON.parse(fs.readFileSync(path, 'utf8')).test;
    let rulesResolved = 0, rulesCorrect = 0, semanticResolved = 0, semanticCorrect = 0;
    for (const [query, expected, lang] of cases) {
        const rules = ruleTools(api, query);
        if (rules.length) {
            rulesResolved++;
            rulesCorrect += rules[0] === expected;
            continue;
        }
        if (!api.AUDIO_DOMAIN.test(query)) continue;
        const picked = gate(classify(query));
        if (picked) {
            semanticResolved++;
            semanticCorrect += picked === expected;
            if (picked !== expected) console.log(`WRONG [${lang}] ${query} → ${picked}; expected ${expected}`);
        }
    }
    const precision = semanticCorrect / semanticResolved;
    console.log(`Rules: ${rulesCorrect}/${rulesResolved} correct; fallback: ${semanticCorrect}/${semanticResolved} accepted correct (${(precision * 100).toFixed(1)}%)`);
    assert.ok(semanticResolved >= 25, 'fallback should materially cover held-out no-match queries');
    assert.ok(precision >= 0.95, 'fallback precision must stay at least 95% on held-out cases');

    const negatives = [
        'hello how are you', 'what is the weather today', 'write a poem about autumn',
        'remove noise from microphone', 'who sang this song', 'make a playlist',
        'привет как дела', 'какая завтра погода', 'удали шум с микрофона',
        '今天天气怎么样', '去除麦克风噪声', '这首歌是谁唱的',
    ];
    for (const query of negatives) {
        if (ruleTools(api, query).length || !api.AUDIO_DOMAIN.test(query)) continue;  // this test targets only the model fallback
        assert.equal(gate(classify(query)), null, `unsupported query must not be routed: ${query}`);
    }
    console.log(`Negative fallback checks: ${negatives.length} passed`);
}

(async () => {
    await unitTests();
    console.log('Assistant unit checks passed');
    if (process.argv[2]) holdoutTests(process.argv[2], boot(() => []).api);
})().catch((error) => { console.error(error); process.exitCode = 1; });
