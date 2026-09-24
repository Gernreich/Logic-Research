// Shared core: terms with stable ids, a normal-order reducer that tracks where every part goes,
// the Tromp layout, and renderers. Used by anim.js and tutorial.js.
const old = require('./tromp.js');   // reference reducer used to check every trace
// ---- terms with stable ids ----
let nid = 0;
function parse(s) {
  let i = 0; const ws = () => { while (s[i] === ' ') i++; };
  function term() { ws();
    if (s[i] === 'λ') { const v = s[i + 1]; if (s[i + 2] !== '.') throw 'bad λ'; i += 3; return { t: 'lam', v, id: 'n' + ++nid, body: term() }; }
    if (s[i] === '(') { i++; const f = term(); ws(); if (s[i] === ')') { i++; return f; }
      const x = term(); ws(); if (s[i] !== ')') throw 'expected ) at ' + i; i++; return { t: 'app', id: 'n' + ++nid, f, x }; }
    return { t: 'var', v: s[i++], id: 'n' + ++nid }; }
  const r = term(); ws(); if (i !== s.length) throw 'trailing'; return r;
}
const show = n => n.t === 'var' ? n.v
  : n.t === 'lam' ? 'λ' + n.v + '.' + (n.body.t === 'var' ? n.body.v : '(' + inner(n.body) + ')')
  : '(' + arg(n.f) + ' ' + arg(n.x) + ')';
const inner = n => n.t === 'app' ? show(n).slice(1, -1) : show(n);
const arg = n => n.t === 'lam' ? '(' + show(n) + ')' : show(n);
const NAMES = { A: 'apple', B: 'banana' };
function termHtml(n, paren = false, strip = false, hl = null) {
  const c = (kind, id) => !hl ? '' : kind === 'bar' && id === hl.lam ? ' class="hl-bar"' : kind === 'app' && id === hl.app ? ' class="hl-link"' : kind === 'v' && hl.occ.has(id) ? ' class="hl-occ"' : kind === 'n' && id === hl.arg ? ' class="hl-arg"' : '';
  if (n.t === 'var') return `<span data-n="${n.id}" data-v="${n.id}"${c('v', n.id) || c('n', n.id)}>${NAMES[n.v] || n.v}</span>`;
  if (n.t === 'lam') {
    const body = n.body.t === 'var' ? termHtml(n.body, false, false, hl)
      : n.body.t === 'app' ? `<span data-app="${n.body.id}"${c('app', n.body.id)}>(</span>${termHtml(n.body, false, true, hl)}<span data-app="${n.body.id}"${c('app', n.body.id)}>)</span>`
      : '(' + termHtml(n.body, false, false, hl) + ')';
    return `<span data-n="${n.id}"${c('n', n.id)}>${paren ? '(' : ''}<span data-bar="${n.id}"${c('bar', n.id)}>λ${n.v}.</span>${body}${paren ? ')' : ''}</span>`;
  }
  const a = m => termHtml(m, m.t === 'lam', false, hl);
  return `<span data-n="${n.id}"${c('n', n.id)}>${strip ? '' : `<span data-app="${n.id}"${c('app', n.id)}>(</span>`}${a(n.f)} ${a(n.x)}${strip ? '' : `<span data-app="${n.id}"${c('app', n.id)}>)</span>`}</span>`;
}
const freeIn = (n, v) => n.t === 'var' ? n.v === v : n.t === 'lam' ? n.v !== v && freeIn(n.body, v) : freeIn(n.f, v) || freeIn(n.x, v);
const freeVars = (n, b = new Set(), out = new Set()) => { if (n.t === 'var') { if (!b.has(n.v)) out.add(n.v); }
  else if (n.t === 'lam') freeVars(n.body, new Set([...b, n.v]), out); else { freeVars(n.f, b, out); freeVars(n.x, b, out); } return out; };
const ids = (n, out = []) => { out.push(n.id); if (n.t === 'lam') ids(n.body, out); if (n.t === 'app') { ids(n.f, out); ids(n.x, out); } return out; };
const copy = (n, suffix) => { const id = suffix ? n.id + '|' + suffix : n.id;
  return n.t === 'var' ? { ...n, id } : n.t === 'lam' ? { ...n, id, body: copy(n.body, suffix) } : { ...n, id, f: copy(n.f, suffix), x: copy(n.x, suffix) }; };
// substitute a for v. The first occurrence keeps a's ids (so it slides into place); later ones are suffixed copies.
function subst(n, v, a, st, bound = new Set()) {
  if (n.t === 'var') { if (n.v !== v) return n;
    for (const f of freeVars(a)) if (bound.has(f)) throw 'capture of ' + f;
    st.occ.push(n.id); return copy(a, st.count++ ? n.id : null); }
  if (n.t === 'lam') return n.v === v ? n : { ...n, body: subst(n.body, v, a, st, new Set([...bound, n.v])) };
  return { ...n, f: subst(n.f, v, a, st, bound), x: subst(n.x, v, a, st, bound) };
}
function step(n) {   // normal order
  if (n.t === 'app' && n.f.t === 'lam') {
    const st = { count: 0, occ: [] };
    const r = subst(n.f.body, n.f.v, n.x, st);
    return { n: r, info: { lam: n.f.id, app: n.id, v: n.f.v, argIds: ids(n.x), occ: st.occ, uses: st.count, arg: show(n.x) } };
  }
  if (n.t === 'app') { const f = step(n.f); if (f) return { n: { ...n, f: f.n }, info: f.info };
    const x = step(n.x); if (x) return { n: { ...n, x: x.n }, info: x.info }; }
  if (n.t === 'lam') { const b = step(n.body); if (b) return { n: { ...n, body: b.n }, info: b.info }; }
  return null;
}

// ---- Tromp layout with keys ----
const FREE = { A: 'apple', B: 'banana' };
const GAP = 0.8;   // room for bar labels between side-by-side blocks
function layout(n) {
  const lines = {}, bars = [], links = [], labels = [];
  function lay(n, env, x0, y0) {
    if (n.t === 'var') {
      const bound = n.v in env, w = bound ? 1 : 2, x = x0 + 0.5;
      lines[n.id] = { x, y1: bound ? env[n.v] : -0.6, y2: y0, cls: bound ? 'v-' + n.v : 'free' };
      if (!bound) labels.push({ key: 't' + n.id, x, text: FREE[n.v] || n.v });
      return { w, h: 0, out: n.id };
    }
    if (n.t === 'lam') {
      const b = lay(n.body, { ...env, [n.v]: y0 }, x0, y0 + 1), w = Math.max(1, b.w);
      bars.push({ key: n.id, x1: x0, x2: x0 + w, y: y0, cls: 'v-' + n.v });
      return { w, h: b.h + 1, out: b.out };
    }
    const M = lay(n.f, env, x0, y0), N = lay(n.x, env, x0 + M.w + GAP, y0), yL = y0 + Math.max(M.h, N.h) + 1;
    lines[M.out].y2 = yL; lines[N.out].y2 = yL;
    links.push({ key: n.id, x1: lines[M.out].x, x2: lines[N.out].x, y: yL });
    return { w: M.w + GAP + N.w, h: yL - y0, out: M.out };
  }
  const L = lay(n, {}, 0, 0);
  lines[L.out].y2 = L.h + 0.8;
  const bottom = Math.max(...Object.values(lines).map(l => l.y2));
  if (Object.values(lines).filter(l => l.y2 === bottom).length !== 1) throw 'not exactly one line at the bottom: ' + show(n);
  const r3 = v => Math.round(v * 1000) / 1000;
  const el = [
    ...bars.map(b => ({ k: b.key, t: 'bar', x1: b.x1, x2: b.x2, y1: b.y, y2: b.y, c: b.cls })),
    ...Object.entries(lines).map(([k, l]) => ({ k, t: 'vl', x1: l.x, x2: l.x, y1: l.y1, y2: l.y2, c: l.cls })),
    ...links.map(l => ({ k: l.key, t: 'link', x1: l.x1, x2: l.x2, y1: l.y, y2: l.y, c: '' })),
  ].map(e => ({ ...e, x1: r3(e.x1), x2: r3(e.x2), y1: r3(e.y1), y2: r3(e.y2) }));
  const html = termHtml(n);
  if (html.replace(/<[^>]+>/g, '') !== show(n).replace(/\bA\b/g, 'apple').replace(/\bB\b/g, 'banana')) throw 'term html differs: ' + show(n);
  return { w: L.w, h: L.h, el, labels, term: show(n), html, tree: n };
}


const T = 'λx.(λy.x)', F = 'λx.(λy.y)';
const named = s => s.replace(/\bA\b/g, 'apple').replace(/\bB\b/g, 'banana');
const argName = a => a === T ? 'TRUE' : a === F ? 'FALSE' : named(a);

// Reduce up to max steps, checked against the reference reducer.
// frames[i] is the term after i steps; trans[i] says what step i+1 does.
function trace(term, max = 50) {
  nid = 0;
  let n = parse(term);
  const frames = [layout(n)], trans = [];
  for (let i = 0; i < max; i++) {
    const s = step(n); if (!s) break;
    n = s.n; frames.push(layout(n));
    const nameA = argName(s.info.arg), v = s.info.v;
    trans.push({ lam: s.info.lam, app: s.info.app, argIds: s.info.argIds, occ: s.info.occ, v, arg: s.info.arg, uses: s.info.uses,
      text: s.info.uses === 0 ? `λ${v} takes ${nameA}. Nothing hangs from λ${v}, so ${nameA} is dropped.`
        : s.info.uses === 1 ? `λ${v} takes ${nameA}. One line hangs from λ${v}, so ${nameA} slides into its place.`
        : `λ${v} takes ${nameA}. ${s.info.uses} lines hang from λ${v}, so ${nameA} is copied into each place.` });
  }
  const ref = old.reduceWithNotes(term, max).map(r => r.term);
  if (ref.length !== frames.length || ref.some((r, i) => r !== frames[i].term)) throw term + ' differs from the reference reducer';
  return { frames, trans };
}
const hlOf = tr => tr ? { lam: tr.lam, app: tr.app, occ: new Set(tr.occ), arg: tr.argIds[0], argAll: new Set(tr.argIds) } : null;
const highlightedHtml = (frame, tr) => termHtml(frame.tree, false, false, hlOf(tr));

// Static SVG of one frame, marking what the next step (tr) does. Same geometry as the animation page.
function renderSvg(frame, tr, { scale = 1.4, aria = '' } = {}) {
  const C = 30, R = 24, PADL = 34, PADR = 16, PADB = 10, pt = frame.labels.length ? 34 : 12;
  const hl = hlOf(tr);
  const W = PADL + frame.w * C + PADR, H = pt + (frame.h + 0.8) * R + PADB;
  const X = x => (PADL + x * C).toFixed(1), Y = y => (pt + y * R).toFixed(1);
  const order = { bar: 1, vl: 2, link: 3 };
  const els = [...frame.el].sort((a, b) => order[a.t] - order[b.t]);
  let s = `<svg viewBox="0 0 ${W.toFixed(1)} ${H.toFixed(1)}" width="${(W * scale).toFixed(0)}" height="${(H * scale).toFixed(0)}" role="img" aria-label="${aria}">`;
  if (hl) for (const e of els) if (hl.argAll.has(e.k))
    s += `<line class="halo" x1="${X(e.x1)}" y1="${Y(e.y1)}" x2="${X(e.x2)}" y2="${Y(e.y2)}"/>`;
  for (const e of els) {
    let cls = `${e.t} ${e.c}`.trim();
    if (hl) { if (e.k === hl.lam) cls += ' hl-bar'; else if (e.k === hl.app) cls += ' hl-link'; else if (hl.occ.has(e.k)) cls += ' hl-occ'; }
    const inset = e.t === 'bar' ? 7 : 0;
    s += `<line class="${cls}" x1="${(+X(e.x1) + inset).toFixed(1)}" y1="${Y(e.y1)}" x2="${(+X(e.x2) - inset).toFixed(1)}" y2="${Y(e.y2)}"/>`;
  }
  for (const e of els) if (e.t === 'bar')
    s += `<text class="lbl ${e.c}" x="${(+X(e.x1) - 2).toFixed(1)}" y="${(+Y(e.y1) + 4).toFixed(1)}" text-anchor="end">λ${e.c.slice(2)}</text>`;
  for (const lb of frame.labels)
    s += `<text class="lbl free" x="${X(lb.x)}" y="${(pt - 0.6 * R - 6).toFixed(1)}" text-anchor="middle">${lb.text}</text>`;
  return s + '</svg>';
}

// Colour each ( and its matching ) by nesting depth. Works on HTML: characters inside tags are skipped.
function paintBrackets(html) {
  let out = '', depth = 0, inTag = false;
  for (const ch of html) {
    if (ch === '<') inTag = true;
    if (!inTag && (ch === '(' || ch === ')')) {
      if (ch === ')') depth--;
      out += `<span class="br br${depth % 5}">${ch}</span>`;
      if (ch === '(') depth++;
    } else out += ch;
    if (ch === '>') inTag = false;
  }
  if (depth !== 0) throw 'unbalanced brackets in ' + html;
  return out;
}
module.exports = { paintBrackets, parse, show, step, layout, trace, termHtml, highlightedHtml, renderSvg, named, argName, T, F };
