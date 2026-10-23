"""Bygger data/kino.json: kinoprogrammet til ODEON Ålesund.

Kilden er Filmweb sin programside for ODEON Ålesund (odeonkino.no blokkerer roboter). Siden har
programmet som JSON i HTML-en, med plakat, aldersgrense, varighet og billettlenke rett til ODEON.
Kinoprogrammet holdes adskilt fra data/events.json, så det ikke fyller opp hovedlista.

Filmweb viser bare dagens program i HTML-en. Visninger for senere dager som vi har lagret fra før,
beholdes, og dagens program erstatter det som lå der for i dag.

Kjør: python3 scripts/kino.py
"""
import datetime
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "kino.json"
TZ = ZoneInfo("Europe/Oslo")
SOURCE = "https://www.filmweb.no/program/sted/%C3%A5lesund/odeon%20%C3%A5lesund"
CINEMA = "ODEON Ålesund"
UA = {"User-Agent": "Mozilla/5.0 (skjer-i-alesund; +https://github.com)", "Accept-Language": "nb-NO,nb;q=0.9"}
# Merker som er verdt å vise. 2D og «Norsk tekst» er standard og sier ingenting.
SHOW_TAGS = {"3D", "Norsk tale", "Utekstet", "Dolby Atmos", "Teksting for hørselshemmede"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def movies_in(page):
    """Filmene med visninger, fra JSON-en som ligger i HTML-en (med escapede anførselstegn)."""
    text = page.replace('\\"', '"').replace("\\\\", "\\")
    dec = json.JSONDecoder()
    found = {}
    for m in re.finditer(r'\{"__typename":"Movie"', text):
        try:
            obj, _ = dec.raw_decode(text[m.start():])
        except ValueError:
            continue
        if obj.get("shows"):
            found[obj["mainVersionId"]] = obj
    return list(found.values())


def poster(url):
    """Plakaten i 2:3-format; sanity.io beskjærer og skalerer selv. Tom hvis kilden mangler bilde."""
    if not url or "cdn.sanity.io" not in url:
        return url or ""
    base = url.split("?")[0]
    return base + "?auto=format&fit=crop&crop=focalpoint&w=360&h=540"


def age(rating):
    m = re.match(r"(\d+)\s*år", rating or "")
    if m:
        return int(m.group(1))
    return 0 if rating and rating.lower().startswith("tillatt") else None


def build(movies):
    films = []
    for m in movies:
        shows = []
        for s in m["shows"]:
            if s.get("theaterName") not in (None, CINEMA) and s.get("firmName") not in (None, CINEMA):
                continue
            start = s["showStart"]
            tags = [t["tag"] for t in s.get("versionTags", []) if t["tag"] in SHOW_TAGS]
            screen = re.sub(r"^ODEON\s+", "", s.get("screenName", ""))
            if "LUXE" in screen:
                tags.append("LUXE")
                screen = screen.replace(" LUXE", "")
            shows.append({"start": start, "screen": screen, "tags": tags, "url": s.get("ticketSaleUrl", ""),
                          "club": bool(s.get("isKinoklubb"))})
        if not shows:
            continue
        shows.sort(key=lambda s: s["start"])
        films.append({
            "id": m["mainVersionId"], "title": m["title"].strip(), "age": age(m.get("rating")),
            "minutes": m.get("lengthInMinutes") or None, "genres": m.get("genres") or [],
            "poster": poster(m.get("sanityImagePosterUrl") or m.get("externalImagePosterUrl")),
            "premiere": (m.get("premiere") or "")[:10], "shows": shows,
        })
    return films


def merge(old_films, new_films, today):
    """Dagens program (alle datoer vi fikk) erstatter det gamle for de datoene; senere dager fra før beholdes."""
    fetched_days = {s["start"][:10] for f in new_films for s in f["shows"]}
    by_id = {f["id"]: f for f in new_films}
    for f in old_films:
        keep = [s for s in f["shows"] if s["start"][:10] >= today and s["start"][:10] not in fetched_days]
        if not keep:
            continue
        if f["id"] in by_id:
            by_id[f["id"]]["shows"] = sorted(by_id[f["id"]]["shows"] + keep, key=lambda s: s["start"])
        else:
            by_id[f["id"]] = {**f, "shows": keep}
    films = sorted(by_id.values(), key=lambda f: f["title"].lower())
    return [f for f in films if f["shows"]]


def warn(msg):
    print("ADVARSEL:", msg, file=sys.stderr)
    path = os.environ.get("SYNC_WARNINGS")
    if path:
        with open(path, "a") as f:
            f.write(f"- {msg}\n")


def main():
    today = datetime.datetime.now(TZ).date().isoformat()
    old = json.loads(OUT.read_text()) if OUT.exists() else {"films": []}
    try:
        new = build(movies_in(get(SOURCE)))
    except Exception as err:  # kino skal aldri stoppe resten av oppdateringen
        warn(f"Kinoprogrammet fra Filmweb kunne ikke hentes ({err!r}). Siden beholder forrige versjon.")
        return
    if not new:
        warn("Fant ingen kinovisninger hos Filmweb. Har siden endret oppbygging? Kinosiden beholder forrige versjon.")
        return
    films = merge(old.get("films", []), new, today)
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    OUT.write_text(json.dumps({"meta": {"updatedAt": now, "cinema": CINEMA, "source": SOURCE}, "films": films},
                              ensure_ascii=False, indent=1) + "\n")
    shows = sum(len(f["shows"]) for f in films)
    print(f"{len(films)} filmer, {shows} visninger")


if __name__ == "__main__":
    main()
