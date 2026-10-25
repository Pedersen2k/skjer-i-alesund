"""Gir søkemotorer som støtter IndexNow (Bing, Yandex m.fl.) beskjed om sidene som endrer seg hver dag.

Nøkkelen ligger som <nøkkel>.txt på roten av siden (lages av pages.py). Google bruker ikke IndexNow og
henter sitemap.xml selv. Feil her er ufarlige, så scriptet avslutter alltid uten feilkode.

Kjør: python3 scripts/indexnow.py
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pages

SKIP = ("arrangement/", "scene/")


def main():
    sitemap = (pages.OUT / "sitemap.xml").read_text()
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", sitemap) if not any(u.startswith(pages.BASE + s) for s in SKIP)]
    body = json.dumps({"host": "kaskjerda.no", "key": pages.INDEXNOW_KEY, "keyLocation": f"{pages.BASE}{pages.INDEXNOW_KEY}.txt", "urlList": urls[:200]}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"IndexNow: {len(urls)} adresser sendt, svar {r.status}")
    except Exception as err:
        print(f"IndexNow feilet (ufarlig): {err!r}")


if __name__ == "__main__":
    main()
