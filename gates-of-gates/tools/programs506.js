// Builds programs506.html: every one of the 506 normal forms behind the 4,096 gates-of-gates cells,
// as a Tromp diagram and in eight notations. Every notation is checked before the page is written.
const fs = require('fs');
const core = require('./core.js');
const SF = require('./shortform.js');
const D = JSON.parse(fs.readFileSync(__dirname + '/gates-data.json', 'utf8'));
const { gates: G, nfs } = D;

// ---------- helpers on named trees ----------
const long = n => n.t === 'var' ? n.v : n.t === 'lam' ? 'λ' + n.v + '.' + (n.body.t === 'var' ? n.body.v : '(' + inner(n.body) + ')') : '(' + argL(n.f) + ' ' + argL(n.x) + ')';
const inner = n => n.t === 'app' ? long(n).slice(1, -1) : long(n);
const argL = n => n.t === 'lam' ? '(' + long(n) + ')' : long(n);
const free = (n, v) => n.t === 'var' ? n.v === v : n.t === 'lam' ? n.v !== v && free(n.body, v) : free(n.f, v) || free(n.x, v);

// de Bruijn (1 = nearest λ), and back
const deb = (n, env = []) => n.t === 'var' ? String(env.indexOf(n.v) + 1) : n.t === 'lam' ? 'λ' + deb(n.body, [n.v, ...env]) : '(' + deb(n.f, env) + ' ' + deb(n.x, env) + ')';
// binary lambda calculus: 00 = λ, 01 = application, n = 1…1 0 (n ones); and a decoder back to de Bruijn
const blc = (n, env = []) => n.t === 'var' ? '1'.repeat(env.indexOf(n.v) + 1) + '0' : n.t === 'lam' ? '00' + blc(n.body, [n.v, ...env]) : '01' + blc(n.f, env) + blc(n.x, env);
function blcDecode(bits) {
  let i = 0;
  const r = () => { if (bits[i] === '0') { i++; if (bits[i++] === '0') return 'λ' + r(); const f = r(), a = r(); return '(' + f + ' ' + a + ')'; }
    let k = 0; while (bits[i] === '1') { k++; i++; } i++; return String(k); };
  const t = r(); if (i !== bits.length) throw 'leftover bits'; return t;
}
// Polish and reverse Polish, with @ = apply and λx as a one-argument operator; parsers back
const pn = n => n.t === 'var' ? [n.v] : n.t === 'lam' ? ['λ' + n.v, ...pn(n.body)] : ['@', ...pn(n.f), ...pn(n.x)];
const rpn = n => n.t === 'var' ? [n.v] : n.t === 'lam' ? [...rpn(n.body), 'λ' + n.v] : [...rpn(n.f), ...rpn(n.x), '@'];
function fromPN(t) { let i = 0; const r = () => { const k = t[i++]; if (k === '@') { const f = r(), x = r(); return { t: 'app', f, x }; } if (k[0] === 'λ') return { t: 'lam', v: k.slice(1), body: r() }; return { t: 'var', v: k }; }; const x = r(); if (i !== t.length) throw 'PN left over'; return x; }
function fromRPN(t) { const s = []; for (const k of t) { if (k === '@') { const x = s.pop(), f = s.pop(); s.push({ t: 'app', f, x }); } else if (k[0] === 'λ') s.push({ t: 'lam', v: k.slice(1), body: s.pop() }); else s.push({ t: 'var', v: k }); } if (s.length !== 1) throw 'RPN stack'; return s[0]; }

// SKI by bracket abstraction, with the K and η shortcuts
const C = c => ({ t: 'var', v: c, comb: true });
function ski(n) {
  if (n.t === 'var') return n;
  if (n.t === 'app') return { t: 'app', f: ski(n.f), x: ski(n.x) };
  return abs(n.v, ski(n.body));
}
function abs(x, e) {                                  // e contains no λ; returns a combinator term for λx.e
  if (!free(e, x)) return { t: 'app', f: C('K'), x: e };
  if (e.t === 'var') return C('I');                   // e is x itself
  if (e.x.t === 'var' && e.x.v === x && !free(e.f, x)) return e.f;       // η: λx.(f x) = f
  return { t: 'app', f: { t: 'app', f: C('S'), x: abs(x, e.f) }, x: abs(x, e.x) };
}
const skiStr = (n, arg = false) => n.t === 'var' ? n.v : (s => arg ? '(' + s + ')' : s)(skiStr(n.f) + (n.x.t === 'var' ? '' : '') + skiStr(n.x, true));
const skiLambda = n => n.t === 'var' ? (n.comb ? { S: '(λx.(λy.(λz.((x z) (y z)))))', K: '(λx.(λy.x))', I: '(λx.x)' }[n.v] : n.v) : '(' + skiLambda(n.f) + ' ' + skiLambda(n.x) + ')';

// JavaScript arrow form
const js = n => n.t === 'var' ? n.v : n.t === 'lam' ? n.v + ' => ' + js(n.body) : jsApp(n);
const jsApp = n => { const f = n.f.t === 'lam' ? '(' + js(n.f) + ')' : js(n.f); return f + '(' + js(n.x) + ')'; };

// behaviour check: apply to the four boolean pairs and two free names A, B; must give A or B per the truth table
const T = 'λx.(λy.x)', F = 'λx.(λy.y)';
const PAIRS = [[T, T], [T, F], [F, T], [F, F]];
function lamBits(term) {
  return PAIRS.map(([p, q]) => {
    let n = core.parse(`((((${'(' + term + ')'} (${p})) (${q})) A) B)`);   // term p q A B
    for (let i = 0; i < 5000; i++) { const s = core.step(n); if (!s) break; n = s.n; }
    const out = core.show(n); if (out !== 'A' && out !== 'B') throw 'not A or B: ' + out;
    return out === 'A' ? '1' : '0';
  }).join('');
}
const TRUEjs = x => y => x, FALSEjs = x => y => y;
function jsBits(src) {
  const f = eval('(' + src + ')');
  return [[TRUEjs, TRUEjs], [TRUEjs, FALSEjs], [FALSEjs, TRUEjs], [FALSEjs, FALSEjs]].map(([p, q]) => { const r = f(p)(q)('A')('B'); if (r !== 'A' && r !== 'B') throw 'js gave ' + r; return r === 'A' ? '1' : '0'; }).join('');
}

// ---------- build every program ----------
const progs = nfs.map((f, k) => {
  const n = SF.parseShort(f.short), bits = G[f.gate].bits, L = long(n);
  if (SF.shortChecked(n) !== f.short) throw 'short form mismatch #' + (k + 1);
  const d = deb(n), b = blc(n), p = pn(n), r = rpn(n), s = ski(n), jsrc = js(n);
  if (blcDecode(b) !== d) throw 'binary does not decode #' + (k + 1);
  if (deb(fromPN(p)) !== d || deb(fromRPN(r)) !== d) throw 'PN/RPN do not read back #' + (k + 1);
  if (lamBits(L) !== bits) throw 'lambda behaviour wrong #' + (k + 1);
  if (lamBits(skiLambda(s)) !== bits) throw 'SKI behaviour wrong #' + (k + 1);
  if (jsBits(jsrc) !== bits) throw 'JavaScript behaviour wrong #' + (k + 1);
  const { frames } = core.trace(L, 0);
  const svg = core.renderSvg(frames[0], null, { scale: 1, aria: `Tromp diagram of program ${k + 1}` });
  return { k, gate: f.gate, exact: f.exact, count: f.count, first: f.first, bits,
    short: f.short, long: L, deb: d, blc: b, pn: p.join(' '), rpn: r.join(' '), ski: skiStr(s), js: jsrc, svg };
});
console.log(progs.length, 'programs: short, long, de Bruijn, binary, PN, RPN read back; lambda, SKI and JavaScript all give the right truth table');

// ---------- page ----------
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const byGate = G.map(() => []);
for (const p of progs) byGate[p.gate].push(p);
for (const list of byGate) list.sort((a, b) => (b.exact - a.exact) || (b.count - a.count) || (a.short.length - b.short.length));
const NOTES = [
  ['short', 'Lambda, short form'], ['long', 'Lambda, fully bracketed'], ['deb', 'De Bruijn'], ['blc', 'Tromp binary'],
  ['pn', 'Polish (prefix)'], ['rpn', 'Reverse Polish'], ['ski', 'SKI combinators'], ['js', 'JavaScript'],
];
const card = p => { const [g, x, y] = p.first;
  return `<article class="prog${p.exact ? ' exact' : ''}" id="p${p.k + 1}">
  <header><b>#${p.k + 1}</b><span>${G[p.gate].name} · ${p.bits}</span><span>${p.count} cell${p.count === 1 ? '' : 's'}</span>${p.exact ? '<span class="badge">lambda16.txt</span>' : `<span class="eg">e.g. ${esc(G[g].short)}(${esc(G[x].short)}, ${esc(G[y].short)})</span>`}</header>
  <div class="body"><div class="draw">${p.svg}</div><dl>${NOTES.map(([key, label]) =>
    `<div class="n-${key}"><dt>${label}</dt><dd><code>${esc(key === 'blc' ? p.blc + '  (' + p.blc.length + ' bits)' : p[key])}</code></dd></div>`).join('')}</dl></div></article>`; };
const sections = byGate.map((list, gi) => `<section class="gate" id="g${gi}" data-gate="${gi}">
  <h2>${gi} ${esc(G[gi].name)} <span>${G[gi].bits} · ${list.length} program${list.length === 1 ? '' : 's'} · ${list.reduce((t, p) => t + p.count, 0)} cells</span></h2>
  ${list.map(card).join('\n')}
</section>`).join('\n');

const css = fs.readFileSync(__dirname + '/programs506.css', 'utf8');
const html = `<title>The 506 Programs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
${css}
</style>
<main class="wrap">
<header class="top">
  <h1>The 506 programs</h1>
  <p class="lede">Every cell of the 16 × 16 × 16 gates-of-gates grid is a lambda term, <code>λp.λq.λa.λb. G (X p q) (Y p q) a b</code>. Reducing all 4,096 of them gives <b>506 different normal forms</b>, each behaving like one of the 16 gates. Here is every one, as a Tromp diagram and in eight notations. Numbers #1–506 match the Gates of gates page.</p>
  <div class="how">
    <div><b>Short form</b> drops brackets by convention. <b>Fully bracketed</b> shows every application.</div>
    <div><b>De Bruijn</b> replaces names with “how many λs up”. <b>Tromp binary</b> writes that in bits: 00 = λ, 01 = apply, n ones and a zero = variable n.</div>
    <div><b>Polish</b> puts <code>@</code> (apply) and <code>λx</code> before their parts; <b>reverse Polish</b> puts them after.</div>
    <div><b>SKI</b> uses no variables at all: S, K and I combined. <b>JavaScript</b> is arrow functions, runnable as written.</div>
  </div>
  <div class="controls">
    <label for="gsel">Show <select id="gsel"><option value="all">all 16 gates</option>${G.map(g => `<option value="${g.idx}">${g.idx} ${esc(g.name)}</option>`).join('')}</select></label>
    <label for="onlyExact"><input type="checkbox" id="onlyExact"> only the lambda16.txt programs</label>
    <fieldset class="nots"><legend>Notations</legend>${NOTES.map(([key, label]) => `<label for="t-${key}"><input type="checkbox" id="t-${key}" data-n="${key}" checked> ${label}</label>`).join('')}</fieldset>
  </div>
  <nav class="jump" aria-label="Gates">${G.map(g => `<a href="#g${g.idx}">${g.idx} ${esc(g.short)} <span>${byGate[g.idx].length}</span></a>`).join('')}</nav>
</header>
${sections}
<p class="muted foot">Built from the verified gates-of-gates data. For every program, the short form, de Bruijn form, binary, Polish and reverse Polish forms were each read back and compared with the original term, and the lambda term, its SKI translation and its JavaScript version were each run on all four inputs and gave the gate's truth table. Tromp diagrams are drawn from the same terms.</p>
</main>
<script>
(() => {
  const $ = id => document.getElementById(id);
  const apply = () => {
    const g = $('gsel').value, ex = $('onlyExact').checked;
    document.querySelectorAll('section.gate').forEach(s => { s.hidden = g !== 'all' && s.dataset.gate !== g; });
    document.querySelectorAll('article.prog').forEach(a => { a.hidden = ex && !a.classList.contains('exact'); });
    document.querySelectorAll('.nots input').forEach(c => document.body.classList.toggle('hide-' + c.dataset.n, !c.checked));
  };
  $('gsel').addEventListener('change', apply); $('onlyExact').addEventListener('change', apply);
  document.querySelectorAll('.nots input').forEach(c => c.addEventListener('change', apply));
  apply();
})();
</script>`;
fs.writeFileSync(__dirname + '/programs506.html', html);
console.log('programs506.html', (html.length / 1e6).toFixed(2), 'MB,', (html.match(/<svg/g) || []).length, 'diagrams');
