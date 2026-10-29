"""Lager en forhåndsvisning av juledesign-forslagene som kan publiseres som Claude-artefakt (flere filer).

Bygger på forsiden i _site/ (kjør scripts/pages.py først), tar bort taggene artefakten setter selv (som
scripts/artifact_preview.py), tvinger julesesongen på og legger til en velger nederst. Forslaget velges med
#peis, #sno, #lys, #kofte, #pepperkake eller #advent i adressen. Skriver preview/jul/.

Kjør: python3 scripts/pages.py && python3 docs/jul-design/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "preview" / "jul"

GROUPS = [("Lunt og tradisjonelt", [("vinterkveld", "Vinterkveld"), ("juletre", "Juletre"), ("frost", "Frostrose")]),
          ("Enkelt og stilrent", [("hvit", "Hvit jul"), ("gran", "Granbånd"), ("rodtrad", "Rød tråd")]),
          ("Første runde", [("peis", "Peiskos"), ("sno", "Snøfall"), ("lys", "Julelys"), ("kofte", "Lusekofte"), ("pepperkake", "Pepperkakebyen"), ("advent", "Adventstid")])]
NISSE = [("meny", "Over menyen"), ("kort", "Over julekortet"), ("side", "Fra siden"), ("", "Ingen nisse")]

page = (ROOT / "_site" / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Juledesign for Skjer i Ålesund</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
# Julekortet vises ellers først fra 1. november
page = page.replace("const JULSEASON = (() => {", "const JULSEASON = true || (() => {", 1)
# Ingen besøkstelling fra forhåndsvisningen
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

options = '<option value="">Dagens design</option>' + "".join(
    f'<optgroup label="{g}">' + "".join(f'<option value="{n}">{label}</option>' for n, label in items) + "</optgroup>" for g, items in GROUPS)
nisse = "".join(f'<option value="{n}">{label}</option>' for n, label in NISSE)
picker = f"""
<link rel="stylesheet" href="jul-design.css">
<style>
.jdpick {{ position: fixed; z-index: 50; left: 0; right: 0; bottom: 0; padding: 10px max(12px, env(safe-area-inset-right, 0px)) calc(10px + env(safe-area-inset-bottom, 0px)) max(12px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; background: #000d; backdrop-filter: blur(10px); font: 600 13px/1 "Figtree", system-ui, sans-serif; color: #fff; }}
.jdpick label {{ display: flex; flex-direction: column; gap: 4px; font-size: 10.5px; letter-spacing: .08em; text-transform: uppercase; color: #fffa; flex: 1 1 150px; max-width: 260px; }}
.jdpick select {{ font: 600 15px/1.2 "Figtree", system-ui, sans-serif; letter-spacing: 0; text-transform: none; padding: 9px 10px; border-radius: 10px; border: 1px solid #fff5; background: #222; color: #fff; }}
.jdpick select:focus-visible {{ outline: 2px solid #ffd27a; outline-offset: 2px; }}
.jdpick .nav {{ display: flex; gap: 6px; align-self: end; }}
.jdpick .nav button {{ font: 700 18px/1 system-ui, sans-serif; width: 42px; height: 40px; border-radius: 10px; border: 1px solid #fff5; background: #222; color: #fff; cursor: pointer; }}
body {{ padding-bottom: 90px; }}
</style>
<nav class="jdpick" aria-label="Velg juledesign">
  <label for="jdsel">Juledesign<select id="jdsel">{options}</select></label>
  <label for="jdnisse">Nisse<select id="jdnisse">{nisse}</select></label>
  <div class="nav"><button type="button" id="jdprev" aria-label="Forrige design">‹</button><button type="button" id="jdnext" aria-label="Neste design">›</button></div>
</nav>
<script src="jul-design.js"></script>
<script>
(() => {{
  const sel = document.getElementById("jdsel"), ns = document.getElementById("jdnisse"), all = [...sel.options].map(o => o.value);
  const pick = () => {{ const n = location.hash.slice(1); const name = JULDESIGN.names.includes(n) ? n : "";
    sel.value = name; JULDESIGN.apply(name); JULDESIGN.nisse(ns.value); }};
  const go = v => {{ if (v) location.hash = v; else {{ history.replaceState(null, "", location.pathname + location.search); pick(); }} scrollTo(0, 0); }};
  sel.onchange = () => go(sel.value);
  ns.onchange = () => JULDESIGN.nisse(ns.value);
  const step = d => go(all[(all.indexOf(sel.value) + d + all.length) % all.length]);
  document.getElementById("jdprev").onclick = () => step(-1);
  document.getElementById("jdnext").onclick = () => step(1);
  addEventListener("hashchange", pick);
  // Forsiden bytter ut listen når programmet er hentet; vent på det før pynten legges på
  const start = () => setTimeout(() => {{ if (!location.hash) location.hash = "vinterkveld"; else pick(); }}, 50);
  document.readyState === "complete" ? start() : addEventListener("load", start);
}})();
</script>
"""
page = page.rstrip() + "\n" + picker

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "index.html").write_text(page)
for f in ("events.json",):  # kino.json er stor og trengs ikke for designet
    if (ROOT / "data" / f).exists():
        shutil.copy(ROOT / "data" / f, OUT / "data" / f)
shutil.copy(ROOT / "tema-kveld.css", OUT / "tema-kveld.css")
for f in ("jul-design.css", "jul-design.js"):
    shutil.copy(HERE / f, OUT / f)
print("Skrev", OUT)
