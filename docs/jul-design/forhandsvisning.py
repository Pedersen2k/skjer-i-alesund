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

NAMES = [("", "Dagens"), ("peis", "Peiskos"), ("sno", "Snøfall"), ("lys", "Julelys"), ("kofte", "Lusekofte"),
         ("pepperkake", "Pepperkakebyen"), ("advent", "Adventstid")]

page = (ROOT / "_site" / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Juledesign for Skjer i Ålesund</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
# Julekortet vises ellers først fra 1. november
page = page.replace("const JULSEASON = (() => {", "const JULSEASON = true || (() => {", 1)
# Ingen besøkstelling fra forhåndsvisningen
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

buttons = "".join(f'<button type="button" data-jd="{n}">{label}</button>' for n, label in NAMES)
picker = f"""
<link rel="stylesheet" href="jul-design.css">
<style>
.jdpick {{ position: fixed; z-index: 50; left: 0; right: 0; bottom: 0; padding: 8px max(10px, env(safe-area-inset-right, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(10px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; background: #000c; backdrop-filter: blur(10px); font: 600 13px/1 "Figtree", system-ui, sans-serif; }}
.jdpick b {{ width: 100%; text-align: center; color: #fff9; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; }}
.jdpick button {{ font: inherit; padding: 8px 11px; border-radius: 99px; border: 1px solid #fff4; background: transparent; color: #fff; cursor: pointer; }}
.jdpick button[aria-pressed="true"] {{ background: #fff; color: #111; }}
.jdpick button:focus-visible {{ outline: 2px solid #ffd27a; outline-offset: 2px; }}
body {{ padding-bottom: 96px; }}
</style>
<nav class="jdpick" aria-label="Velg juledesign"><b>Juledesign · forslag</b>{buttons}</nav>
<script src="jul-design.js"></script>
<script>
(() => {{
  const pick = () => {{ const n = location.hash.slice(1); const name = JULDESIGN.names.includes(n) ? n : "";
    JULDESIGN.apply(name); document.querySelectorAll(".jdpick button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.jd === name))); }};
  document.querySelectorAll(".jdpick button").forEach(b => b.onclick = () => {{ location.hash = b.dataset.jd; if (!b.dataset.jd) pick(); scrollTo(0, 0); }});
  addEventListener("hashchange", pick);
  // Forsiden bytter ut listen når programmet er hentet; vent på det før pynten legges på
  const go = () => setTimeout(pick, 50);
  document.readyState === "complete" ? go() : addEventListener("load", go);
}})();
</script>
"""
page = page.rstrip() + "\n" + picker

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "index.html").write_text(page)
for f in ("events.json", "kino.json"):
    if (ROOT / "data" / f).exists():
        shutil.copy(ROOT / "data" / f, OUT / "data" / f)
shutil.copy(ROOT / "tema-kveld.css", OUT / "tema-kveld.css")
for f in ("jul-design.css", "jul-design.js"):
    shutil.copy(HERE / f, OUT / f)
print("Skrev", OUT)
