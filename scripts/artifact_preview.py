"""Lager en forhåndsvisning av nettsiden som kan publiseres som Claude-artefakt.

Artefakter pakker siden inn i sitt eget <html>/<head>/<body>, så skriptet tar
bort de taggene fra index.html og legger forhåndsvisningen i preview/ sammen med
en kopi av programmet. Den ekte siden er fortsatt GitHub Pages.

Kjør: python3 scripts/artifact_preview.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "preview"

page = (ROOT / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
# Tagger artefakten likevel setter selv, og deling/ikon som bare gir mening på den ekte siden
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="icon"[^>]*>\s*', "", page)
page = page.replace("<title>Skjer i Ålesund</title>",
                    '<title>Skjer i Ålesund</title>\n<meta name="claude:viewport-fit-sides" content="cover">', 1)

OUT.mkdir(exist_ok=True)
(OUT / "data").mkdir(exist_ok=True)
(OUT / "index.html").write_text(page)
shutil.copy(ROOT / "data" / "events.json", OUT / "data" / "events.json")
print("Skrev", OUT / "index.html")
