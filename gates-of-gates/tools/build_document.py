#!/usr/bin/env python3
"""Build docs/gates-of-gates-document.html: one self-contained document with everything in gates-of-gates/.
It is written straight into docs/, the folder GitHub Pages serves; there is no other copy.
lambda16.txt and the 1995 poster photo are also copied into docs/ so the public site can serve them.

The README is converted with md2html.py (from the lasermade-tools repository), then:
  * every image is embedded as a data: URI,
  * the interactive Gates of Gates page and The 506 Programs page are embedded, each in its own
    frame (their styles would clash if merged), stored in the file and loaded without any network,
  * lambda16.txt and the two CSV files are added as appendices,
  * links to the separate files are pointed at sections of this document.
Nothing is loaded from the network: Google Fonts links are removed and the pages fall back to system fonts.

usage: python3 tools/build_document.py PATH/TO/md2html.py      (run from the gates-of-gates folder)
"""
import base64, html, pathlib, re, shutil, subprocess, sys, tempfile

if len(sys.argv) < 2:
    sys.exit(__doc__)
MD2HTML = pathlib.Path(sys.argv[1])
ROOT = pathlib.Path(__file__).resolve().parent.parent            # gates-of-gates/
REPO = ROOT.parent                                                # Logic Research/
OUT = REPO / 'docs' / 'gates-of-gates-document.html'

with tempfile.TemporaryDirectory() as tmp:
    conv = pathlib.Path(tmp) / 'readme.html'
    subprocess.run([sys.executable, str(MD2HTML), str(ROOT / 'README.md'), str(conv)], check=True, capture_output=True)
    doc = conv.read_text()

# ---- images: embed as data: URIs ----
def embed_img(m):
    path = ROOT / m.group(1)
    data = base64.b64encode(path.read_bytes()).decode()
    return f'src="data:image/jpeg;base64,{data}"'
doc, n_img = re.subn(r'src="(images/[^"]+\.jpg)"', embed_img, doc)
if n_img == 0 or 'src="images/' in doc:
    sys.exit('an image was not embedded')

# ---- links to separate files become links inside this document ----
LINKS = {
    'https://gernreich.github.io/Logic-Research/gates-of-gates.html': '#interactive-grid',
    'https://gernreich.github.io/Logic-Research/programs-506.html': '#all-506-programs',
    'https://gernreich.github.io/Logic-Research/lambda16.txt': '#appendix-lambda16',
    'https://gernreich.github.io/Logic-Research/gates-of-gates-document.html': '#gates-of-gates-16--16--16',       # the README's pointer to this document: its own top
    '../python/boolean16.py': 'https://github.com/Gernreich/Logic-Research/blob/main/python/boolean16.py',
}
for old, new in LINKS.items():
    if f'href="{old}"' not in doc:
        sys.exit(f'link not found in the converted README: {old}')
    doc = doc.replace(f'href="{old}"', f'href="{new}"')

# ---- the two interactive pages, stored as base64 and loaded into frames ----
RESIZE = """<script>
(() => { const post = () => parent.postMessage({ gogFrame: '%s', h: document.documentElement.scrollHeight }, '*');
  new ResizeObserver(post).observe(document.body); addEventListener('load', post); post(); })();
</script>"""
def page(src, frame_id):
    body = (ROOT / src).read_text()
    body = re.sub(r'<link[^>]+fonts\.(googleapis|gstatic)\.com[^>]*>\n?', '', body)   # no network
    if 'googleapis' in body or 'gstatic' in body:
        sys.exit(f'{src} still refers to Google Fonts')
    body = body.replace('</body>', (RESIZE % frame_id) + '\n</body>', 1)
    if (RESIZE % frame_id) not in body:
        sys.exit(f'{src}: no </body> to add the resize script to')
    return base64.b64encode(body.encode('utf-8')).decode()

grid64 = page('page/gates-of-gates.html', 'grid')
progs64 = page('page/programs-506.html', 'progs')

# ---- appendices ----
lambda16 = (REPO / 'lambda16.txt').read_text()
def download(name, mime):
    data = base64.b64encode((ROOT / 'data' / name).read_bytes()).decode()
    return f'<a download="{name}" href="data:{mime};base64,{data}">{name}</a>'

extra = f"""
<h2 id="interactive-grid">Interactive: Gates of Gates</h2>
<p>The full interactive page: six cell views, two axis orders, hover details and a table for any square. It runs inside this document.</p>
<iframe class="embed" id="frame-grid" title="Gates of Gates, interactive" loading="eager"></iframe>

<h2 id="all-506-programs">All 506 programs</h2>
<p>Every distinct normal form behind the 4,096 cells, as a Tromp diagram, in eight notations, and mapped back to the cells it comes from. The list scrolls inside its frame; use the controls at its top to pick a gate or hide notations.</p>
<iframe class="embed tall" id="frame-progs" title="The 506 Programs" loading="eager"></iframe>

<h2 id="appendix-lambda16">Appendix: lambda16.txt</h2>
<p>The sixteen functions as lambda terms, with every β-reduction, exactly as in the repository.</p>
<details class="appx"><summary>Show lambda16.txt ({len(lambda16.splitlines())} lines)</summary><pre>{html.escape(lambda16)}</pre></details>

<h2 id="appendix-data">Appendix: data</h2>
<p>The data behind every picture, as CSV. Truth-table columns start with an apostrophe so spreadsheets keep the leading zeros.</p>
<ul>
<li>{download('cells.csv', 'text/csv')}: all 4,096 cells, with G, X, Y, the result, and which of the 506 programs it reduces to</li>
<li>{download('programs.csv', 'text/csv')}: the 506 programs, with behaviour, number of cells, whether it is the lambda16.txt term, short form and an example cell</li>
</ul>

<style>
iframe.embed {{ display: block; width: 100%; height: 900px; border: 1px solid var(--line); border-radius: 8px; background: var(--card); }}
iframe.embed.tall {{ height: 85vh; min-height: 600px; }}
details.appx pre {{ max-height: 70vh; overflow: auto; font-size: 12px; line-height: 1.45; }}
main a {{ overflow-wrap: anywhere; }}   /* long URLs as link text must not widen the page on phones */
</style>
<script>
(() => {{
  const pages = {{ grid: '{grid64}', progs: '{progs64}' }};
  const decode = b => new TextDecoder().decode(Uint8Array.from(atob(b), c => c.charCodeAt(0)));
  for (const [id, b] of Object.entries(pages)) document.getElementById('frame-' + id).srcdoc = decode(b);
  addEventListener('message', e => {{
    const d = e.data; if (!d || !d.gogFrame) return;
    const f = document.getElementById('frame-' + d.gogFrame); if (f && !f.classList.contains('tall') && d.h > 100) f.style.height = (d.h + 4) + 'px';
  }});
}})();
</script>
"""
if doc.count('</main>') != 1:
    sys.exit('expected one </main> in the converted README')
doc = doc.replace('</main>', extra + '\n</main>', 1)

# ---- contents list: add the new sections ----
nav_add = ''.join(f'<a class="l2" href="#{i}">{t}</a>' for i, t in [
    ('interactive-grid', 'Interactive: Gates of Gates'), ('all-506-programs', 'All 506 programs'),
    ('appendix-lambda16', 'Appendix: lambda16.txt'), ('appendix-data', 'Appendix: data')])
doc, n_nav = re.subn(r'(<nav>.*?)(</nav>)', lambda m: m.group(1) + nav_add + m.group(2), doc, count=1, flags=re.S)
if n_nav != 1:
    sys.exit('contents list not found')

# ---- self-contained check: nothing may be fetched ----
fetches = re.findall(r'<(?:link|script|img|iframe)\b[^>]*\b(?:href|src)="(https?:)?//', doc)
if fetches or 'fonts.googleapis' in doc:
    sys.exit('the document still loads something from the network')

OUT.write_text(doc)
(REPO / 'docs' / 'lambda16.txt').write_text(lambda16)
shutil.copyfile(ROOT / 'images' / 'poster-1995.jpg', REPO / 'docs' / 'poster-1995.jpg')
print(f'wrote {OUT.name}: {len(doc) / 1e6:.1f} MB, {n_img} images, 2 interactive pages, lambda16.txt, 2 CSV files; copied lambda16.txt and poster-1995.jpg to docs/')
