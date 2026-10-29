"""Forhåndsvisning av to menyforslag på mobil: «Fast» (menyen skjules aldri) og «Kompakt» (bare søk, Mine og Filter-knapp).

Bygger på preview/ fra scripts/artifact_preview.py (kjør den først). Skriver preview/meny/ med en velger nederst («Nå | Fast | Kompakt»).
Kjør: python3 scripts/artifact_preview.py && python3 docs/meny-forslag/forhandsvisning.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC, OUT = ROOT / "preview", ROOT / "preview" / "meny"
page = (SRC / "index.html").read_text()
extra = (Path(__file__).parent / "overlay.html").read_text()
assert "</body>" in page or True
page = page.rstrip() + "\n" + extra
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "index.html").write_text(page)
shutil.copy(SRC / "data" / "events.json", OUT / "data" / "events.json")
print("Skrev", OUT)
