"""Forhåndsvisning av juletemaet (tema-jul.css) som Claude-artefakt, uten at noe blir live.

Bygger på forsiden i _site/ (kjør scripts/pages.py først). Artefakter sender ikke med ?tema=jul, så temaet slås på
direkte, og julekortet (med nissen) vises uansett dato. Skriver preview/jul-tema/.

Kjør: python3 scripts/pages.py && python3 docs/jul-design/tema_forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "preview" / "jul-tema"

page = (ROOT / "_site" / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Juletema for Skjer i Ålesund</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
loader = re.search(r'<script>try\{const q=new URLSearchParams\(location\.search\)\.get\("tema"\).*?</script>', page)
assert loader, "fant ikke temalasteren i index.html"
page = page.replace(loader.group(0), '<script>document.documentElement.dataset.tema="jul"</script>\n'
                    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,700;1,700&display=swap">\n'
                    '<link rel="stylesheet" href="tema-jul.css">', 1)
page = page.replace("const JULSEASON = (() => {", "const JULSEASON = true || (() => {", 1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "index.html").write_text(page)
shutil.copy(ROOT / "data" / "events.json", OUT / "data" / "events.json")
shutil.copy(ROOT / "tema-jul.css", OUT / "tema-jul.css")
print("Skrev", OUT)
