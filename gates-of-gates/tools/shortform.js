// Short (conventional) form of a lambda term, its parser, and de Bruijn form for α-equality.
const NAMES = { A: 'apple', B: 'banana' };
const nm = v => NAMES[v] || v;
function db(n, env = []) {
  if (n.t === 'var') { const k = env.indexOf(n.v); return k < 0 ? nm(n.v) : String(k + 1); }
  if (n.t === 'lam') return 'λ' + db(n.body, [n.v, ...env]);
  return '(' + db(n.f, env) + ' ' + db(n.x, env) + ')';
}
function short(n, ctx = 'top') {
  if (n.t === 'var') return nm(n.v);
  if (n.t === 'lam') {
    let vs = n.v, b = n.body; while (b.t === 'lam') { vs += b.v; b = b.body; }
    const s = 'λ' + vs + '.' + short(b, 'top');
    return ctx === 'top' ? s : '(' + s + ')';
  }
  const s = short(n.f, 'fun') + ' ' + short(n.x, 'arg');
  return ctx === 'arg' ? '(' + s + ')' : s;
}
function parseShort(src) {
  const toks = src.match(/λ[a-z]+\.|\(|\)|[a-z]+/g); let i = 0;
  const WORDS = { apple: 'A', banana: 'B' };
  function term() {
    if (toks[i] && toks[i][0] === 'λ') {
      const vs = toks[i++].slice(1, -1).split(''); let body = term();
      for (const v of vs.reverse()) body = { t: 'lam', v, body };
      return body;
    }
    let f = atom();
    while (i < toks.length && toks[i] !== ')') { const x = toks[i][0] === 'λ' ? term() : atom(); f = { t: 'app', f, x }; }
    return f;
  }
  function atom() {
    const k = toks[i++];
    if (k === '(') { const t = term(); if (toks[i++] !== ')') throw 'expected ) in ' + src; return t; }
    return { t: 'var', v: WORDS[k] || k };
  }
  const t = term(); if (i !== toks.length) throw 'left over in ' + src; return t;
}
// short form, checked: it must parse back to the same term
function shortChecked(n) {
  const s = short(n);
  if (db(parseShort(s)) !== db(n)) throw 'short form does not read back: ' + s;
  return s;
}
module.exports = { db, short, parseShort, shortChecked };
