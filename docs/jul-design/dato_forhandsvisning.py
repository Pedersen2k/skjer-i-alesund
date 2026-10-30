"""Forhåndsvisning av forsiden slik den blir en bestemt dag (standard søndag 1. november kl. 12), som Claude-artefakt.

Både byggingen (scripts/pages.py, som bestemmer snarveier og forhåndsviste lister ut fra dagens dato) og klokka i
nettleseren later som det er den dagen, så temalasteren, julekortet, adventskransen og «I dag»/«I morgen» blir som da.
Ingenting blir live. Skriver preview/dato/ og bygger _site/ på nytt for den dagen (kjør scripts/pages.py etterpå).

Kjør: python3 docs/jul-design/dato_forhandsvisning.py [2026-11-01T12:00]
"""
import datetime
import re
import runpy
import shutil
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "dato"
WHEN = datetime.datetime.fromisoformat(sys.argv[1] if len(sys.argv) > 1 else "2026-11-01T12:00").replace(tzinfo=ZoneInfo("Europe/Oslo"))


class FakeDateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return WHEN.astimezone(tz) if tz else WHEN.replace(tzinfo=None)

    @classmethod
    def today(cls):
        return cls.now()


class FakeDate(datetime.date):
    @classmethod
    def today(cls):
        return WHEN.date()


datetime.datetime, datetime.date = FakeDateTime, FakeDate
sys.argv = [str(ROOT / "scripts" / "pages.py")]
sys.path.insert(0, str(ROOT / "scripts"))
runpy.run_path(str(ROOT / "scripts" / "pages.py"), run_name="__main__")

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
ms = int(WHEN.timestamp() * 1000)
clock = ("<script>(()=>{const O=Date,off=%d-O.now();class D extends O{constructor(...a){super(...(a.length?a:[O.now()+off]))}"
         "static now(){return O.now()+off}}window.Date=D})()</script>" % ms)
page = re.sub(r"<title>[^<]*</title>", lambda m: '<title>Forsiden ' + WHEN.strftime("%d.%m") + '</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + clock, page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)
WD = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"][WHEN.weekday()]
MO = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"][WHEN.month - 1]
page = page.rstrip() + f"""
<div style="position:fixed;z-index:70;left:50%;bottom:calc(10px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);padding:8px 14px;border-radius:999px;background:#000d;color:#fff;font:600 13px/1.2 Figtree,system-ui,sans-serif;white-space:nowrap">Slik ser forsiden ut {WD} {WHEN.day}. {MO} kl. {WHEN:%H:%M}</div>
"""

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "index.html").write_text(page)
for f in ("stil.css", "tema-kveld.css", "tema-jul.css"):
    if (SITE / f).exists():
        shutil.copy(SITE / f, OUT / f)
for f in ("events.json", "kino.json"):
    if (SITE / "data" / f).exists():
        shutil.copy(SITE / "data" / f, OUT / "data" / f)
print("Skrev", OUT)
