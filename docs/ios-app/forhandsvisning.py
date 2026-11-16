#!/usr/bin/env python3
"""Lager preview/ios-app/ (index.html, app.html, data.js) fra data/events.json.

Prototype av kaskjerda.no som iPhone-app (hjemskjerm-modus). Ikke publisert på siden.
Bruk: python3 docs/ios-app/forhandsvisning.py
"""
import datetime as dt
import json
import pathlib
import shutil
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "preview" / "ios-app"
OSLO = ZoneInfo("Europe/Oslo")
MO = ["jan.", "feb.", "mars", "apr.", "mai", "juni", "juli", "aug.", "sep.", "okt.", "nov.", "des."]
KEEP = ["id", "date", "time", "title", "venue", "address", "cat", "price", "priceMin", "soldOut", "few",
        "statusSrc", "note", "uncertain", "url", "moreShows", "shows"]


def main():
    data = json.loads((ROOT / "data" / "events.json").read_text(encoding="utf-8"))
    today = dt.datetime.now(OSLO).date()
    # Demo-klokke: førstkommende fredag kl. 19:40 (i dag hvis det er fredag eller lørdag)
    wd = today.weekday()
    demo = today if wd in (4, 5) else today + dt.timedelta(days=(4 - wd) % 7)
    events = []
    for e in data["events"]:
        last = max([e["date"]] + [s[:10] for s in e.get("moreShows", [])])
        if last < demo.isoformat():
            continue
        events.append({k: e[k] for k in KEEP if k in e and e[k] not in (None, "", False, [])} | {
            "price": e.get("price", ""), "priceMin": e.get("priceMin"), "note": e.get("note", "")})
    up = dt.datetime.fromisoformat(data["meta"]["updatedAt"].replace("Z", "+00:00")).astimezone(OSLO)
    payload = {
        "events": events,
        "updatedLabel": f"{up.day}. {MO[up.month - 1]} kl. {up:%H:%M}",
        "demoDate": demo.isoformat(),
        "demoMin": 19 * 60 + 40,
    }
    # Eksempel for «Arrangement»: noe med flere tider, ellers noe med notat, de neste ti dagene
    soon = [e for e in events if e["date"] <= (demo + dt.timedelta(days=10)).isoformat() and e["cat"] != "julebord"]
    pick = next((e for e in soon if e.get("shows")), None) or next((e for e in soon if e.get("note")), soon[0])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / "data.js").write_text("window.KASK = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    shutil.copy(SRC / "app.html", OUT / "app.html")
    wdname = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"][demo.weekday()]
    page = (SRC / "index.html").read_text(encoding="utf-8")
    page = page.replace("__DETAIL__", pick["id"]).replace(
        '<span id="demoClock">fredag kveld</span>', f"{wdname} {demo.day}. {MO[demo.month - 1]} kl. 19:40")
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"{OUT}: {len(events)} arrangementer, demo {demo} 19:40, eksempel {pick['id']}")


if __name__ == "__main__":
    main()
