const fs = require('fs');
const src = fs.readFileSync(require('path').join(__dirname, 'allreduce.js'), 'utf8');
eval(src.slice(src.indexOf('function parse'), src.indexOf('const TRUE')).replace(/^(const|let) /gm, 'var '));
const FREE = { A: 'apple', B: 'banana' };           // single-letter free variables, shown by name
const C = 30, R = 24;                                // grid: column width, row height (px)

// Tromp layout. Returns width/height in grid units, the output line (leftmost), and drawing parts.
let GAP = 0;   // extra columns before an argument block, room for bar labels
function lay(n, env, x0, y0) {
  if (n.t === 'var') {
    const bound = n.v in env, w = bound ? 1 : 2, x = x0 + 0.5;
    const top = bound ? env[n.v] : -0.6;
    return { w, h: 0, out: { x, y: y0, v: n.v }, parts: [{ k: 'line', v: n.v, x1: x, y1: top, x2: x, y2: y0 }],
             free: bound ? [] : [{ x, v: n.v }] };
  }
  if (n.t === 'lam') {
    const b = lay(n.body, { ...env, [n.v]: y0 }, x0, y0 + 1);
    const w = Math.max(1, b.w);
    return { w, h: b.h + 1, out: b.out, free: b.free,
             parts: [{ k: 'bar', v: n.v, x1: x0, x2: x0 + w, y: y0 }, ...b.parts] };
  }
  const M = lay(n.f, env, x0, y0), N = lay(n.x, env, x0 + M.w + GAP, y0);
  const yL = y0 + Math.max(M.h, N.h) + 1;
  return { w: M.w + GAP + N.w, h: yL - y0, out: { x: M.out.x, y: yL, v: M.out.v }, free: [...M.free, ...N.free],
    parts: [...M.parts, ...N.parts,
      { k: 'line', v: M.out.v, x1: M.out.x, y1: M.out.y, x2: M.out.x, y2: yL },
      { k: 'line', v: N.out.v, x1: N.out.x, y1: N.out.y, x2: N.out.x, y2: yL },
      { k: 'link', x1: M.out.x, x2: N.out.x, y: yL }] };
}

function svg(term, aria, opts = {}) {
  GAP = opts.gap || 0;
  const n = parse(term), L = lay(n, {}, 0, 0);
  const parts = [...L.parts, { k: 'line', v: L.out.v, x1: L.out.x, y1: L.out.y, x2: L.out.x, y2: L.out.y + 0.8 }];
  const hasFree = L.free.length > 0;
  const padL = opts.labels === false ? 12 : 34, padT = hasFree ? 30 : 10, padR = 12, padB = 8;
  const W = padL + L.w * C + padR, H = padT + (L.h + 0.8) * R + padB;
  const X = x => padL + x * C, Y = y => padT + y * R;
  const cls = v => FREE[v] ? 'free' : 'v-' + v;
  let out = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${aria}">`;
  for (const p of parts) {
    if (p.k === 'bar') {
      out += `<line class="bar ${cls(p.v)}" x1="${X(p.x1) + 7}" y1="${Y(p.y)}" x2="${X(p.x2) - 7}" y2="${Y(p.y)}"/>`;
      if (opts.labels !== false && (opts.labels !== 'left' || p.x1 === 0)) out += `<text class="lbl ${cls(p.v)}" x="${X(p.x1) - 4}" y="${Y(p.y) + 4}" text-anchor="end">λ${p.v}</text>`;
    } else if (p.k === 'link') {
      out += `<line class="link" x1="${X(p.x1)}" y1="${Y(p.y)}" x2="${X(p.x2)}" y2="${Y(p.y)}"/>`;
    } else if (p.y2 > p.y1) {
      out += `<line class="vl ${cls(p.v)}" x1="${X(p.x1)}" y1="${Y(p.y1)}" x2="${X(p.x2)}" y2="${Y(p.y2)}"/>`;
    }
  }
  for (const f of L.free) out += `<text class="lbl free" x="${X(f.x)}" y="${Y(-0.6) - 6}" text-anchor="middle">${FREE[f.v] || f.v}</text>`;
  const bottom = Math.max(...parts.filter(p => p.k === 'line').map(p => p.y2));
  svg.lastBottomLines = parts.filter(p => p.k === 'line' && p.y2 === bottom).length;
  svg.lastCounts = { bars: parts.filter(p => p.k === 'bar').length, links: parts.filter(p => p.k === 'link').length };
  return out + '</svg>';
}

function reduceSteps(term) {
  let n = parse(term); const steps = [show(n)]; let s;
  while ((s = step(n))) { n = s; steps.push(show(n)); }
  return steps;
}
function reduceWithNotes(term, max = Infinity) {
  let n = parse(term); const out = [{ term: show(n) }]; let t;
  while (out.length <= max && (t = step(n))) { n = t; const [v, a, used] = note; out.push({ term: show(n), v, arg: show(a), used }); }
  return out;
}
module.exports = { svg, reduceSteps, reduceWithNotes, show, parse, lay };
if (require.main === module) {
  console.log(reduceSteps('(((λx.(λy.x)) A) B)'));
  console.log(reduceSteps('(((λx.(λy.y)) A) B)'));
  console.log(svg('λx.(λy.x)', 'TRUE'));
}
