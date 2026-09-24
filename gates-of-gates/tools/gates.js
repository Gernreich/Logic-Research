// Builds gates.html: for every gate G, a 16x16 grid of G(X, Y), where X and Y are gates.
// Each cell is the gate λp.λq. G (X p q) (Y p q). Its truth table is found by lambda reduction
// on all four inputs, and cross-checked with plain bitwise arithmetic on the truth tables.
const fs = require('fs');
const core = require('./core.js');
const path = require('path');
// lambda16.txt: set LAMBDA16, or it is found two folders up (Logic Research/gates-of-gates/tools -> Logic Research)
const L16 = process.env.LAMBDA16 || path.join(__dirname, '..', '..', 'lambda16.txt');

const rows = [];
for (const l of fs.readFileSync(L16, 'utf8').split('\n')) {
  const m = l.match(/^\s*(\d+)\s+([01])\s+([01])\s+([01])\s+([01])\s+(.*?)\s+(λ\S.*)$/);
  if (m) rows[+m[1]] = { idx: +m[1], bits: m[2] + m[3] + m[4] + m[5], name: m[6].trim(), term: m[7] };
}
if (rows.length !== 16 || rows.some(r => !r)) throw 'expected 16 gates from lambda16.txt';

const T = 'λx.(λy.x)', F = 'λx.(λy.y)';
const INPUTS = [[T, T], [T, F], [F, T], [F, F]];            // TT, TF, FT, FF: the bit order used everywhere
const db = (n, env = []) => n.t === 'var' ? (env.indexOf(n.v) < 0 ? n.v : String(env.indexOf(n.v) + 1))
  : n.t === 'lam' ? 'λ' + db(n.body, [n.v, ...env]) : '(' + db(n.f, env) + ' ' + db(n.x, env) + ')';
const TRUE_DB = db(core.parse('λa.(λb.a)')), FALSE_DB = db(core.parse('λa.(λb.b)'));
function normal(term) {
  let n = core.parse(term);
  for (let i = 0; i < 1000; i++) { const s = core.step(n); if (!s) return n; n = s.n; }
  throw 'no normal form: ' + term;
}
const bitOf = term => { const d = db(normal(term)); if (d === TRUE_DB) return '1'; if (d === FALSE_DB) return '0'; throw 'not a boolean: ' + d; };
const w = t => '(' + t + ')';
// α-rename a gate's variables so copies used inside another gate can't be captured
const rename = (t, map) => t.replace(/[pqab]/g, c => map[c]);
const RX = { p: 'u', q: 'v', a: 'c', b: 'd' }, RY = { p: 'm', q: 'n', a: 'e', b: 'h' };

// sanity: every gate's own truth table, by reduction, matches the file
for (const r of rows) {
  const b = INPUTS.map(([p, q]) => bitOf(`((${w(r.term)} ${w(p)}) ${w(q)})`)).join('');
  if (b !== r.bits) throw `${r.name}: reduced to ${b}, file says ${r.bits}`;
}

const byBits = Object.fromEntries(rows.map(r => [r.bits, r.idx]));
const grid = [];   // grid[g][y][x] = index of the resulting gate
let reductions = 0;
const t0 = Date.now();
for (const G of rows) {
  const panel = [];
  for (const Y of rows) {
    const line = [];
    for (const X of rows) {
      // lambda: G (X p q) (Y p q) for each of the four inputs
      const bits = INPUTS.map(([p, q]) => {
        reductions++;
        return bitOf(`((${w(G.term)} ((${w(rename(X.term, RX))} ${w(p)}) ${w(q)})) ((${w(rename(Y.term, RY))} ${w(p)}) ${w(q)}))`);
      }).join('');
      // cross-check: bitwise, row by row. G's bit for inputs (x, y) sits at position (x ? 0 : 2) + (y ? 0 : 1)
      const check = [0, 1, 2, 3].map(k => G.bits[(X.bits[k] === '1' ? 0 : 2) + (Y.bits[k] === '1' ? 0 : 1)]).join('');
      if (bits !== check) throw `mismatch at G=${G.idx} X=${X.idx} Y=${Y.idx}: lambda ${bits}, bitwise ${check}`;
      line.push(byBits[bits]);
    }
    panel.push(line);
  }
  grid.push(panel);
}
// the two claims in the request: FALSE's square is all FALSE, TRUE's square is all TRUE
if (!grid[0].flat().every(v => v === 0)) throw 'FALSE square is not all FALSE';
if (!grid[15].flat().every(v => v === 15)) throw 'TRUE square is not all TRUE';
// patterns the page describes, proved here
const all = (g, f) => grid[g].every((line, y) => line.every((v, x) => f(v, x, y)));
const claims = {
  'P copies X':            all(6, (v, x) => v === x),
  'Q copies Y':            all(3, (v, x, y) => v === y),
  'NOT P is 15 - X':       all(9, (v, x) => v === 15 - x),
  'NOT Q is 15 - Y':       all(12, (v, x, y) => v === 15 - y),
  'symmetric gates':       [0, 2, 5, 7, 8, 10, 13, 15].every(g => all(g, (v, x, y) => v === grid[g][x][y])),
  'AND diagonal is X':     all(2, (v, x, y) => x !== y || v === x),
  'XOR diagonal is FALSE': all(5, (v, x, y) => x !== y || v === 0),
  'complement squares':    grid.every((sq, g) => all(15 - g, (v, x, y) => v === 15 - sq[y][x])),
  // XOR and XNOR: Latin squares (every row and column holds all 16 gates once), with a constant diagonal
  'XOR, XNOR Latin squares': [5, 10].every(g => grid[g].every(r => new Set(r).size === 16) && [...Array(16).keys()].every(x => new Set(grid[g].map(r => r[x])).size === 16)),
  'XOR diagonal FALSE, XNOR diagonal TRUE': all(5, (v, x, y) => x !== y || v === 0) && all(10, (v, x, y) => x !== y || v === 15),
  // in truth-table order, quarter k of XOR is a checkerboard of squares 2^(3-k) wide
  'XOR quarters are checkerboards': (() => { const tt = []; rows.forEach(r => { tt[parseInt(r.bits, 2)] = r.idx; });
    return [0, 1, 2, 3].every(k => { const w = 8 >> k; for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++)
      if ((rows[grid[5][tt[y]][tt[x]]].bits[k] === '1') !== ((Math.floor(x / w) + Math.floor(y / w)) % 2 === 1)) return false; return true; }); })(),
  // the eight gates with one or three TRUE rows are AND with its inputs and/or output flipped: the triangle family
  'triangle family is AND reflected or inverted': (() => {
    // g is in the family if, for some flips a, b, c: g(p, q) = c XOR ((p XOR a) AND (q XOR b)) on all four rows
    const isAndLike = g => [0, 1].some(a => [0, 1].some(b => [0, 1].some(c =>
      [[1, 1], [1, 0], [0, 1], [0, 0]].every(([p, q], k) => (rows[g].bits[k] === '1') === (((c ^ ((p ^ a) & (q ^ b))) & 1) === 1)))));
    const family = [1, 2, 4, 7, 8, 11, 13, 14];
    // control: every other gate must fail the test, so the test is not vacuous
    return family.every(isAndLike) && [0, 3, 5, 6, 9, 10, 12, 15].every(g => !isAndLike(g));
  })(),
};
for (const [k, ok] of Object.entries(claims)) if (!ok) throw 'claim failed: ' + k;
console.log('all', Object.keys(claims).length, 'pattern claims hold');
console.log(`${reductions} reductions in ${((Date.now() - t0) / 1000).toFixed(1)}s, all 4096 cells match bitwise`);

// ---- the programs: each cell's own lambda term, reduced to normal form ----
const SF = require('./shortform.js');
const ap = (...ts) => ts.map(t => t.startsWith('λ') ? '(' + t + ')' : t).reduce((f, x) => '(' + f + ' ' + x + ')');
const cellTerm = (g, x, y) => 'λi.(λj.(λk.(λl.' + ap(rows[g].term, ap(rename(rows[x].term, RX), 'i', 'j'), ap(rename(rows[y].term, RY), 'i', 'j'), 'k', 'l') + ')))';
// rename the four outer binders i j k l back to p q a b, the names lambda16.txt uses
const back = { i: 'p', j: 'q', k: 'a', l: 'b' };
const renameTree = n => n.t === 'var' ? { t: 'var', v: back[n.v] || n.v } : n.t === 'lam' ? { t: 'lam', v: back[n.v] || n.v, body: renameTree(n.body) } : { t: 'app', f: renameTree(n.f), x: renameTree(n.x) };
const fileDbs = rows.map(r => SF.db(core.parse(r.term)));
const nfIndex = new Map(), nfs = [], nfGrid = [];
for (let g = 0; g < 16; g++) {
  const panel = [];
  for (let y = 0; y < 16; y++) {
    const line = [];
    for (let x = 0; x < 16; x++) {
      const n = renameTree(normal(cellTerm(g, x, y)));
      const d = SF.db(n);
      if (!nfIndex.has(d)) {
        const k = nfs.length; nfIndex.set(d, k);
        nfs.push({ short: SF.shortChecked(n), gate: grid[g][y][x], exact: fileDbs[grid[g][y][x]] === d, count: 0, first: [g, x, y] });
      }
      const k = nfIndex.get(d); nfs[k].count++;
      // a normal form must always behave like the gate the grid says
      if (nfs[k].gate !== grid[g][y][x]) throw 'one normal form, two behaviours';
      line.push(k);
    }
    panel.push(line);
  }
  nfGrid.push(panel);
}
const exactCells = nfGrid.flat(2).filter(k => nfs[k].exact).length;
if (nfs.length !== 506) throw 'expected 506 normal forms, got ' + nfs.length;
if (exactCells !== 2064) throw 'expected 2064 exact cells, got ' + exactCells;
for (let g = 0; g < 16; g++) if (nfs.filter(f => f.gate === g && f.exact).length !== 1) throw 'gate ' + g + ' should have its file term exactly once';
console.log(nfs.length, 'normal forms,', exactCells, 'cells reduce to exactly the lambda16.txt term; every short form reads back');

const SHORT = ['FALSE', 'q∧¬p', 'AND', 'Q', 'p∧¬q', 'XOR', 'P', 'OR', 'NOR', '¬P', 'XNOR', 'p→q', '¬Q', 'NAND', 'q→p', 'TRUE'];
const data = { gates: rows.map(r => ({ idx: r.idx, bits: r.bits, name: r.name, short: SHORT[r.idx], term: r.term })), grid, nfs, nfGrid };
const tpl = fs.readFileSync(__dirname + '/gates.template.html', 'utf8');
fs.writeFileSync(__dirname + '/gates.html', tpl.replace('/*DATA*/', 'const DATA = ' + JSON.stringify(data) + ';'));
fs.writeFileSync(__dirname + '/gates-data.json', JSON.stringify(data));
console.log('gates.html and gates-data.json written');
