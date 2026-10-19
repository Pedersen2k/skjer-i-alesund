"""Bygger data/events.json for Skjer i Ålesund.

Henter Ålesund-arrangementer og billettpriser fra Tikkio, slår sammen
gjentatte forestillinger, og legger til manuelle arrangementer fra
data/manual.json. Overstyringer (kategori, tittel, tid, notat) ligger i
data/overrides.json, med normalisert tittel som nøkkel.

Kjør: python3 scripts/sync.py
"""
import datetime
import html
import json
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TZ = ZoneInfo("Europe/Oslo")
LISTING = "https://tikkio.com/locations/151197-alesund"
UA = {"User-Agent": "Mozilla/5.0 (skjer-i-alesund; +https://github.com)"}

ALESUND_VENUES = ("Løvenvold", "Terminalen", "Venterommet")
VENUE_NAMES = {"Terminalen": "Terminalen Byscene"}
# Kurs, medlemskap og ungdomsforestillinger som ikke hører hjemme i kalenderen
SKIP = re.compile(r"medlemsskap|gruppe, høst|day pass|cowork|festivalpass|SPIRE|foredrag|påmelding|^FUND$", re.I)
# Billettyper som ikke er reelle priser
NOISE = re.compile(r"ledsager|rullestol|gjest|faktura|flyttet|uttak|copy|gratisbillett", re.I)
REGULAR = re.compile(r"ordin|^billett$|^standard|^voksen|^kinobillett|^parkett", re.I)
MONTHS = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def slug(text):
    t = unicodedata.normalize("NFKD", text.lower().replace("ø", "o").replace("æ", "ae").replace("å", "a"))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def clean_title(name):
    t = html.unescape(name).strip()
    t = re.sub(r"^(ekstrashow!|ekstrakonsert!|få bill!)\s*", "", t, flags=re.I)
    t = re.sub(r"\s*//.*$", "", t)                      # « // Terminalen Byscene»
    t = re.sub(r"\s*/\s*\d{1,2}\.\d{1,2}\s*$", "", t)   # « / 5.11»
    t = re.sub(r"\s*\|\s*Support:.*$", "", t, flags=re.I)
    return t.strip(" |-")


def norm_key(title):
    return slug(re.sub(r"\b(premiere|gr\.\s*\d)\b", "", title, flags=re.I))


def fetch_tikkio():
    page = get(LISTING)
    today = datetime.datetime.now(TZ).date()
    raw = []
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', page, re.S):
        items = json.loads(m.group(1)).get("itemListElement")
        if not items:
            continue
        for it in (items.values() if isinstance(items, dict) else items):
            it = it.get("item", it)
            loc = it.get("location") or {}
            addr = loc.get("address") if isinstance(loc.get("address"), dict) else {}
            venue = (loc.get("name") or "").strip()
            city = (addr.get("addressLocality") or "").strip()
            if not (city == "Ålesund" or any(v in venue for v in ALESUND_VENUES)):
                continue
            name = html.unescape(it.get("name") or "").strip()
            if SKIP.search(name):
                continue
            start = datetime.datetime.fromisoformat(it["startDate"]).astimezone(TZ)
            if start.date() < today:
                continue
            offer = it.get("offers") or {}
            offer = offer[0] if isinstance(offer, list) else offer
            url = offer.get("url") or ""
            raw.append({"name": name, "venue": VENUE_NAMES.get(venue, venue), "start": start,
                        "url": url, "tickets": fetch_tickets(url),
                        "soldOut": "SoldOut" in json.dumps(offer.get("availability"))})
    return raw


def fetch_tickets(url):
    if not url:
        return []
    try:
        page = get(url)
        time.sleep(0.5)
    except Exception as e:  # en enkelt side som feiler skal ikke stoppe hele kjøringen
        print("feil:", url, e, file=sys.stderr)
        return []
    tickets = []
    pat = r'"item_name":"((?:[^"\\]|\\.)*)","item_brand":"[^"]*","item_category":\d+,"affiliation":"(?:[^"\\]|\\.)*","price":"([\d.]+)"'
    for t in re.finditer(pat, page):
        pair = (json.loads('"' + t.group(1) + '"').strip(" /|"), float(t.group(2)))
        if pair not in tickets:
            tickets.append(pair)
    return tickets


def price_info(tickets):
    real = [(n, p) for n, p in tickets if not NOISE.search(n)]
    paid = [(n, p) for n, p in real if p > 0]
    if not paid:
        return ("Gratis", 0, "") if real else ("", None, "")
    regular = [p for n, p in paid if REGULAR.search(n)]
    base = int(max(regular) if regular else max(p for _, p in paid))
    discounts = sorted({(int(p), n) for n, p in paid if p < base})[:2]
    note = ("Rabatt: " + ", ".join(f"{n} {p} kr" for p, n in discounts) + ".") if discounts else ""
    return f"{base} kr", base, note


def fmt_day(d):
    return f"{d.day}. {MONTHS[d.month - 1]}"


def build_tikkio(raw, overrides):
    groups = {}
    for r in raw:
        title = clean_title(r["name"])
        groups.setdefault((norm_key(title), r["venue"]), []).append({**r, "title": title})
    events = []
    for (key, venue), shows in groups.items():
        shows.sort(key=lambda s: s["start"])
        first = shows[0]
        o = overrides.get(key, {})
        price, price_min, disc = price_info(first["tickets"])
        notes = [o.get("note", "")]
        extra_days = sorted({s["start"].date() for s in shows[1:]} - {first["start"].date()})
        same_day = [s["start"].strftime("%H:%M") for s in shows[1:] if s["start"].date() == first["start"].date()]
        if same_day:
            notes.append("Også kl. " + " og ".join(same_day) + ".")
        if extra_days:
            listed = ", ".join(fmt_day(d) for d in extra_days[:5])
            notes.append(f"Flere forestillinger: {listed}" + (" m.fl." if len(extra_days) > 5 else "") + ".")
        if o.get("discountNote", True):
            notes.append(disc)
        events.append({
            "id": slug(key + "-" + venue),
            "date": first["start"].date().isoformat(),
            "time": o.get("time") or first["start"].strftime("%H:%M"),
            "title": o.get("title") or first["title"],
            "venue": venue,
            "cat": o.get("cat") or guess_cat(first["title"]),
            "price": price, "priceMin": price_min,
            "soldOut": all(s["soldOut"] for s in shows),
            "note": " ".join(n for n in notes if n),
            "uncertain": False,
            "url": first["url"],
        })
    return events


def guess_cat(title):
    t = title.lower()
    if re.search(r"standup|stand-up|komiker|humor", t):
        return "standup"
    if re.search(r"quiz|bingo|verksted|marked|festival|dans\b|romjulsdans|skifilm", t):
        return "happening"
    if re.search(r"klubb|halloween|husfest|\bdj\b|fest\b|party", t):
        return "klubb"
    if re.search(r"barn|familie", t):
        return "barn"
    return "konsert"


def main():
    overrides = json.loads((DATA / "overrides.json").read_text())
    manual = json.loads((DATA / "manual.json").read_text())
    old_path = DATA / "events.json"
    old = json.loads(old_path.read_text()) if old_path.exists() else {"events": [], "meta": {}}
    first_seen = {e["id"]: e.get("addedAt") for e in old["events"]}

    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    today = datetime.datetime.now(TZ).date().isoformat()
    events = build_tikkio(fetch_tikkio(), overrides)
    if not events:
        sys.exit("Fant ingen arrangementer på Tikkio – beholder forrige versjon.")
    events += [e for e in manual if e["date"] >= today]

    added = 0
    for e in events:
        e["addedAt"] = first_seen.get(e["id"]) or now
        added += e["id"] not in first_seen
    meta = {
        "updatedAt": now,
        "seededAt": old["meta"].get("seededAt") or now,
        "lastAdded": added if first_seen else 0,
    }
    events.sort(key=lambda e: (e["date"], e["time"] or "99"))
    old_path.write_text(json.dumps({"meta": meta, "events": events}, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(events)} arrangementer, {meta['lastAdded']} nye")


if __name__ == "__main__":
    main()
