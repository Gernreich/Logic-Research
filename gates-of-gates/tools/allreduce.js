const fs = require('fs');
const FILE = require('path').join(__dirname, '..', '..', 'lambda16.txt');
const rows = fs.readFileSync(FILE, 'utf8').split('\n')
  .map(l => l.match(/^\s*(\d+)\s+([01])\s+([01])\s+([01])\s+([01])\s+(.*?)\s+(λ\S.*)$/)).filter(Boolean)
  .map(m => ({idx: +m[1], bits: m[2]+m[3]+m[4]+m[5], name: m[6].trim(), term: m[7].trim()}));
if (rows.length !== 16) throw 'expected 16 rows, got ' + rows.length;

function parse(s) {
  let i = 0; const ws = () => { while (s[i] === ' ') i++; };
  function term() { ws();
    if (s[i] === 'λ') { const v = s[i+1]; if (s[i+2] !== '.') throw 'bad λ'; i += 3; return {t:'lam', v, body: term()}; }
    if (s[i] === '(') { i++; const f = term(); ws(); if (s[i] === ')') { i++; return f; }
      const x = term(); ws(); if (s[i] !== ')') throw 'expected ) at ' + i; i++; return {t:'app', f, x}; }
    return {t:'var', v: s[i++]}; }
  const r = term(); ws(); if (i !== s.length) throw 'trailing'; return r; }
const show = n => n.t === 'var' ? n.v
  : n.t === 'lam' ? 'λ' + n.v + '.' + (n.body.t === 'var' ? n.body.v : '(' + inner(n.body) + ')')
  : '(' + arg(n.f) + ' ' + arg(n.x) + ')';
const inner = n => n.t === 'app' ? show(n).slice(1, -1) : show(n);
const arg = n => n.t === 'lam' ? '(' + show(n) + ')' : show(n);
const free = (n, v) => n.t === 'var' ? n.v === v : n.t === 'lam' ? n.v !== v && free(n.body, v) : free(n.f, v) || free(n.x, v);
// all arguments substituted are closed or use only a,b which are never rebound inside x/y terms: no capture possible
const subst = (n, v, a) => n.t === 'var' ? (n.v === v ? a : n) : n.t === 'lam' ? (n.v === v ? n : {t:'lam', v: n.v, body: subst(n.body, v, a)}) : {t:'app', f: subst(n.f, v, a), x: subst(n.x, v, a)};
let note;
function step(n) {   // normal order: leftmost-outermost redex
  if (n.t === 'app' && n.f.t === 'lam') { note = [n.f.v, n.x, free(n.f.body, n.f.v)]; return subst(n.f.body, n.f.v, n.x); }
  if (n.t === 'app') { const f = step(n.f); if (f) return {t:'app', f, x: n.x}; const x = step(n.x); if (x) return {t:'app', f: n.f, x}; }
  if (n.t === 'lam') { const b = step(n.body); if (b) return {t:'lam', v: n.v, body: b}; }
  return null; }

const TRUE = 'λx.(λy.x)', FALSE = 'λx.(λy.y)';
const label = a => { const s = show(a); return s === TRUE ? 'TRUE' : s === FALSE ? 'FALSE' : s; };
const inputs = [['TRUE', TRUE], ['TRUE', FALSE], ['FALSE', TRUE], ['FALSE', FALSE]].map(([pn, p], k) =>
  [pn, p, k < 2 ? (k === 0 ? 'TRUE' : 'FALSE') : (k === 2 ? 'TRUE' : 'FALSE')]);
const qs = [TRUE, FALSE, TRUE, FALSE];

let out = [], bad = 0, totalSteps = 0;
out.push('', '', 'Beta reduction of all sixteen, on all four inputs', '==================================================', '',
  'TRUE = λx.(λy.x) and FALSE = λx.(λy.y) use x and y so they cannot clash with a and b.',
  'Normal order: the leftmost, outermost redex is reduced first.',
  'Each step says which variable was replaced and by what. "(thrown away)" means',
  'the bound variable did not appear in the body, so the argument vanishes unreduced.',
  'Every reduction ends at λa.(λb.a) = TRUE or λa.(λb.b) = FALSE.');
for (const r of rows) {
  out.push('', '', `--- ${r.idx}  ${r.name}   ${r.term}`);
  for (let k = 0; k < 4; k++) {
    const pn = k < 2 ? 'TRUE' : 'FALSE', qn = k % 2 === 0 ? 'TRUE' : 'FALSE';
    const p = pn === 'TRUE' ? TRUE : FALSE, q = qn === 'TRUE' ? TRUE : FALSE;
    let n = parse(`((${r.term} (${p})) (${q}))`), i = 0;
    const lines = [`  ${String(i).padStart(2)}  ${show(n)}`];
    let s;
    while ((s = step(n))) {
      n = s; i++;
      const [v, a, used] = note;
      lines.push(`  ${String(i).padStart(2)}  ${show(n)}`);
      lines.push(`        ${v} := ${label(a)}${used ? '' : '   (thrown away)'}`);
      if (i > 50) throw 'runaway';
    }
    const res = show(n), want = r.bits[k] === '1' ? 'λa.(λb.a)' : 'λa.(λb.b)';
    if (res !== want) bad++;
    totalSteps += i;
    out.push('', `  p = ${pn}, q = ${qn}  →  ${r.bits[k] === '1' ? 'TRUE' : 'FALSE'}`, ...lines);
  }
}
console.error(`${rows.length} gates, ${rows.length * 4} reductions, ${totalSteps} steps, ${bad} wrong results`);
if (bad) process.exit(1);
fs.writeFileSync('reductions.txt', out.join('\n') + '\n');
