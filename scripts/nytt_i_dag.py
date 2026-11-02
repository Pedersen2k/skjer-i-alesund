#!/usr/bin/env python3
"""Daglig oversikt over arrangementer som er lagt til det siste døgnet (for «Nytt i programmet»-issuet).

Bruk: python3 scripts/nytt_i_dag.py body.md
Skriver brødteksten til filen og setter `title` og `count` i $GITHUB_OUTPUT. Er ingenting nytt, settes count=0
og ingen fil skrives (workflowen lager da ikke noe issue). «Nytt» er arrangementer med addedAt siste 24 timer
(sync.py husker addedAt også når tittelen endres eller et arrangement forsvinner et øyeblikk)."""
import json, os, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
OSLO = ZoneInfo("Europe/Oslo")
SITE = "https://kaskjerda.no"
UKEDAG = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"]
MND = ["jan.", "feb.", "mars", "apr.", "mai", "juni", "juli", "aug.", "sep.", "okt.", "nov.", "des."]
MND_LANG = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"]
KATEGORIER = [("konsert", "Konserter"), ("standup", "Standup"), ("show", "Show"), ("barn", "Barn og familie"),
              ("klubb", "Klubb"), ("happening", "Happenings"), ("quiz", "Quiz"), ("sport", "Sport"),
              ("julebord", "Julebord")]


def kort_dato(e):
    d = datetime.fromisoformat(e["date"])
    s = f"{UKEDAG[d.weekday()][:3]}. {d.day}. {MND[d.month - 1]}"
    if e.get("time"):
        s += f" kl. {e['time']}"
    if e.get("moreShows"):
        s += f" (+{len(e['moreShows'])} til)"
    return s


def linje(e):
    deler = [kort_dato(e), e["venue"], e.get("price") or "pris ukjent"]
    if e.get("soldOut"):
        deler.append("utsolgt")
    if e.get("uncertain"):
        deler.append("usikker, se notat")
    side = f"{SITE}/arrangement/{e['id']}/"
    return f"- **{e['title']}**: {' · '.join(deler)} · [side]({side})" + (f" · [arrangør]({e['url']})" if e.get("url") else "")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "body.md"
    data = json.loads((ROOT / "data" / "events.json").read_text())
    nå = datetime.now(timezone.utc)
    grense = nå - timedelta(hours=24)
    nye = [e for e in data["events"]
           if e.get("addedAt") and datetime.fromisoformat(e["addedAt"].replace("Z", "+00:00")) > grense]
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"count={len(nye)}\n")
    if not nye:
        print("Ingenting nytt siste døgn.")
        return
    nå_oslo = nå.astimezone(OSLO)
    dag = f"{UKEDAG[nå_oslo.weekday()]} {nå_oslo.day}. {MND_LANG[nå_oslo.month - 1]}"
    tittel = f"Nytt i programmet: {dag} ({len(nye)})"
    if gh:
        with open(gh, "a") as f:
            f.write(f"title={tittel}\n")
    rader = [f"**{len(nye)} nye arrangement{'' if len(nye) == 1 else 'er'}** siste døgn. Sortert etter dato i hver gruppe.", ""]
    brukt = set()
    for kode, navn in KATEGORIER:
        gruppe = sorted((e for e in nye if e["cat"] == kode), key=lambda e: (e["date"], e.get("time") or ""))
        if not gruppe:
            continue
        brukt.update(e["id"] for e in gruppe)
        rader += [f"### {navn} ({len(gruppe)})", ""] + [linje(e) for e in gruppe] + [""]
    resten = [e for e in nye if e["id"] not in brukt]
    if resten:
        rader += [f"### Annet ({len(resten)})", ""] + [linje(e) for e in sorted(resten, key=lambda e: e["date"])] + [""]
    rader += ["Julebord vises bare på [julebord-siden](" + SITE + "/julebord/), ikke i hovedlista.",
              "Feil kategori, pris eller dato? Rett det i `data/overrides.json` eller `data/manual.json`.", ""]
    Path(out).write_text("\n".join(rader))
    print(tittel)


if __name__ == "__main__":
    main()
