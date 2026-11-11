"""Forsiden med de 18 logoforslagene (A–R) fra logoforslag.html, valgt med en meny nederst (#A … #R, #dagens).

Kjør: python3 scripts/pages.py && python3 docs/logo-forslag/forhandsvisning.py  (skriver preview/logo-forside/)
"""
import re, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT/"preview"/"logo-forside"
src = (Path(__file__).parent/"logoforslag.html").read_text()
logos_js = src[src.index("let uid = 0;"):src.index("const GROUPS")]
anim_css = "\n".join(l for l in src.splitlines() if l.startswith("@keyframes") or l.startswith(".an-"))
page = (ROOT/"_site"/"index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Forside med ny logo</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)
m = re.search(r'<svg class="logo".*?</svg>', page, flags=re.S); assert m
old = m.group(0)
page = page.replace(old, '<span class="logo newlogo" id="newlogo"></span>' + old.replace('<svg class="logo"', '<svg class="logo" id="oldlogo"'), 1)
style = '''<style>
.newlogo { width: clamp(52px, 12vw, 84px); display: block; }
.newlogo .mk { --ink: var(--fg); --a: var(--accent); --s: var(--sea); --g: var(--gold, #f7c873); --cut: var(--bg); --snow: #fff; width: 100%; height: auto; display: block; }
''' + anim_css + '''
@media (prefers-reduced-motion: reduce) { .newlogo .mk * { animation: none !important; } .newlogo .an-draw { stroke-dashoffset: 0; } }
.cmpbar { position: fixed; z-index: 50; left: 50%; transform: translateX(-50%); bottom: calc(12px + env(safe-area-inset-bottom, 0px)); display: flex; align-items: center; gap: 4px; padding: 4px; border-radius: 999px; background: rgba(10,23,27,.9); border: 1px solid rgba(255,255,255,.18); font: 600 13px/1 Figtree, system-ui, sans-serif; box-shadow: 0 6px 20px rgba(0,0,0,.3); max-width: calc(100vw - 24px); }
.cmpbar button, .cmpbar select { border: 0; background: none; color: #e8f1ef; padding: 9px 12px; border-radius: 999px; cursor: pointer; font: inherit; }
.cmpbar select { background: #fff; color: #0a171b; max-width: 58vw; appearance: auto; }
.cmpbar button:focus-visible, .cmpbar select:focus-visible { outline: 2px solid #f7c873; outline-offset: 2px; }
</style>'''
page = re.sub(r'(<meta name="claude:viewport-fit-sides"[^>]*>)', lambda mm: mm.group(1)+"\n"+style, page, count=1)
picker = '''<div class="cmpbar" role="group" aria-label="Velg logo"><button type="button" id="lgPrev" aria-label="Forrige logo">‹</button><select id="lgSel" aria-label="Logo"></select><button type="button" id="lgNext" aria-label="Neste logo">›</button></div>
<script>
''' + logos_js + '''
(function(){
  const box = document.getElementById("newlogo"), old = document.getElementById("oldlogo"), sel = document.getElementById("lgSel");
  const opts = LOGOS.map(l => [l.id, l.id + " · " + l.name]).concat([["dagens", "Dagens logo"]]);
  sel.innerHTML = opts.map(o => `<option value="${o[0]}">${o[1]}</option>`).join("");
  function show(id) {
    const l = LOGOS.find(x => x.id === id);
    if (!l) { id = "dagens"; }
    sel.value = id;
    if (id === "dagens") { box.style.display = "none"; old.style.display = ""; }
    else { box.innerHTML = l.svg(); box.setAttribute("aria-label", "Logo: " + l.name); box.style.display = ""; old.style.display = "none"; }
    try { history.replaceState(null, "", "#" + id); } catch (e) {}
  }
  const step = d => { const i = opts.findIndex(o => o[0] === sel.value); show(opts[(i + d + opts.length) % opts.length][0]); };
  sel.onchange = () => show(sel.value);
  document.getElementById("lgPrev").onclick = () => step(-1);
  document.getElementById("lgNext").onclick = () => step(1);
  window.addEventListener("hashchange", () => show(location.hash.slice(1)));
  show(location.hash.slice(1) || "A");
})();
</script>'''
page = page + "\n" + picker
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"data").mkdir(parents=True)
(OUT/"index.html").write_text(page)
shutil.copy(ROOT/"data"/"events.json", OUT/"data"/"events.json")
for f in ["tema-jul.css","tema-kveld.css"]: shutil.copy(ROOT/f, OUT/f)
shutil.copy(ROOT/"data"/"kino.json", OUT/"data"/"kino.json")
print("ok")
