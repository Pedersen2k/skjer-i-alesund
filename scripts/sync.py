"""Bygger data/events.json for Skjer i Ålesund.

Henter Ålesund-arrangementer og billettpriser fra Tikkio og programmet til
Parken kulturhus, slår sammen gjentatte forestillinger, og legger til
manuelle arrangementer fra data/manual.json. Overstyringer (kategori, tittel,
tid, notat) ligger i data/overrides.json, med normalisert tittel som nøkkel
(eller «parken-<id>» for et bestemt Parken-arrangement).

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
PARKEN = "https://www.parkenkulturhus.no"
PARKEN_VENUE = "Parken kulturhus"
UA = {"User-Agent": "Mozilla/5.0 (skjer-i-alesund; +https://github.com)", "Accept-Language": "nb-NO,nb;q=0.9"}

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


def page_text(page):
    """HTML til ren tekst med én linje per element, så regexene ikke avhenger av markup."""
    page = re.sub(r"<(script|style|noscript)\b.*?</\1>", " ", page, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "\n", page)).replace("\xa0", " ")
    return "\n".join(line for line in (re.sub(r"\s+", " ", l).strip() for l in text.split("\n")) if line)


def guess_year(day, month, today):
    # Datoer uten år («07.11»): velg neste gang datoen kommer, med litt slakk bakover
    year = today.year
    if datetime.date(year, month, day) < today - datetime.timedelta(days=60):
        year += 1
    return year


def parse_parken(page, today):
    """Leser ett arrangement fra Parken. Returnerer (tittel, [(start, utsolgt)], pris-tuple)."""
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S | re.I)
    title = clean_title(re.sub(r"<[^>]+>", " ", h1.group(1))) if h1 else ""
    title = re.sub(r"\s+", " ", title).strip()
    text = page_text(page)
    # Hovedinnholdet kommer først; kutt før «andre arrangementer» så vi ikke leser naboene
    text = re.split(r"\n(?:Se også|Andre arrangementer|Du vil kanskje også like|Relaterte arrangementer)\n", text)[0]

    shows = []
    for m in re.finditer(r"\b(\d{1,2})\.(\d{1,2})\s*-\s*kl\.\s*(\d{1,2})[:.](\d{2})(?:\s*-\s*\d{1,2}[:.]\d{2})?\s*(Utsolgt)?", text):
        d, mo, hh, mm = (int(x) for x in m.group(1, 2, 3, 4))
        try:
            start = datetime.datetime(guess_year(d, mo, today), mo, d, hh, mm, tzinfo=TZ)
        except ValueError:
            continue
        if all(s != start for s, _ in shows):
            shows.append((start, bool(m.group(5))))
    if not shows:
        m = re.search(r"\b(\d{1,2})\.\s*(" + "|".join(MONTHS) + r")[a-zæøå]*\.?\s*(\d{4})(?:\s*kl\.\s*(\d{1,2})[:.](\d{2}))?", text, re.I)
        if m:
            d, mo, y = int(m.group(1)), MONTHS.index(m.group(2).lower()) + 1, int(m.group(3))
            hh, mm = (int(m.group(4)), int(m.group(5))) if m.group(4) else (0, 0)
            try:
                start = datetime.datetime(y, mo, d, hh, mm, tzinfo=TZ)
                shows.append((start, False))
            except ValueError:
                pass

    price = None
    m = re.search(r"Pris:\s*(?:\n\s*)?(?:fra\s*)?(\d[\d .]*?)\s*kr(?:\s*til\s*(\d[\d .]*?)\s*kr)?", text, re.I)
    if m:
        lo = int(re.sub(r"\D", "", m.group(1)))
        hi = int(re.sub(r"\D", "", m.group(2))) if m.group(2) else None
        price = (f"{lo}–{hi} kr" if hi and hi != lo else f"{lo} kr", lo, "")
    elif re.search(r"Pris:\s*(?:\n\s*)?Gratis", text, re.I):
        price = ("Gratis", 0, "")
    return title, shows, price


def fetch_parken():
    try:
        listing = get(PARKEN + "/program/")
    except Exception as e:
        print("Parken: klarte ikke å hente programmet:", e, file=sys.stderr)
        return []
    today = datetime.datetime.now(TZ).date()
    urls = []
    for m in re.finditer(r'href="((?:https://www\.parkenkulturhus\.no)?/program/(\d+)-[^"/?#]+/?)"', listing):
        url = m.group(1) if m.group(1).startswith("http") else PARKEN + m.group(1)
        if all(u != url for u, _ in urls):
            urls.append((url, m.group(2)))
    raw = []
    for url, pid in urls:
        try:
            page = get(url)
            time.sleep(0.5)
        except Exception as e:  # en enkelt side som feiler skal ikke stoppe hele kjøringen
            print("feil:", url, e, file=sys.stderr)
            continue
        title, shows, price = parse_parken(page, today)
        if not title or not shows or SKIP.search(title):
            continue
        for start, sold in shows:
            if start.date() < today:
                continue
            raw.append({"name": title, "venue": PARKEN_VENUE, "start": start, "url": url,
                        "tickets": [], "price": price, "soldOut": sold, "group": "parken-" + pid,
                        "noTime": start.hour == 0 and start.minute == 0})  # dato uten klokkeslett
    print(f"Parken: {len(urls)} lenker, {len(raw)} forestillinger", file=sys.stderr)
    return raw


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


def build_events(raw, overrides):
    groups = {}
    for r in raw:
        title = clean_title(r["name"])
        groups.setdefault((r.get("group") or norm_key(title), r["venue"]), []).append({**r, "title": title})
    events = []
    for (key, venue), shows in groups.items():
        shows.sort(key=lambda s: s["start"])
        first = shows[0]
        title_key = norm_key(first["title"])
        o = overrides.get(key) or overrides.get(title_key, {})
        price, price_min, disc = first.get("price") or price_info(first["tickets"])
        notes = [o.get("note", "")]
        extra_days = sorted({s["start"].date() for s in shows[1:]} - {first["start"].date()})
        same_day = [s["start"].strftime("%H:%M") for s in shows[1:] if s["start"].date() == first["start"].date()]
        if same_day:
            notes.append("Også kl. " + " og ".join(same_day) + ".")
        sold = [s for s in shows if s["soldOut"]]
        if sold and len(sold) < len(shows):
            when = [s["start"].strftime("%H:%M") if s["start"].date() == first["start"].date() else fmt_day(s["start"].date()) for s in sold]
            notes.append("Utsolgt: " + ", ".join(when) + ".")
        if extra_days:
            listed = ", ".join(fmt_day(d) for d in extra_days[:5])
            notes.append(f"Flere forestillinger: {listed}" + (" m.fl." if len(extra_days) > 5 else "."))
        if o.get("discountNote", True):
            notes.append(disc)
        events.append({
            "id": slug(key + "-" + venue),
            "date": first["start"].date().isoformat(),
            "time": o.get("time") or ("" if first.get("noTime") else first["start"].strftime("%H:%M")),
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
    events = build_events(fetch_tikkio(), overrides)
    if not events:
        sys.exit("Fant ingen arrangementer på Tikkio – beholder forrige versjon.")
    parken = build_events(fetch_parken(), overrides)
    # Samme arrangement kan ligge både på Tikkio og hos Parken; Tikkio har billettprisene
    seen = {(e["date"], norm_key(e["title"])) for e in events}
    events += [e for e in parken if (e["date"], norm_key(e["title"])) not in seen]
    # Manuelle Parken-arrangementer er reserve når Parken-siden (eller én av undersidene) ikke svarer
    parken_ids = {e["id"] for e in parken}
    events += [e for e in manual if e["date"] >= today and e["id"] not in parken_ids]

    seeded_at = old["meta"].get("seededAt") or now
    # Første gang en ny kilde gir treff, regnes alt derfra som startprogram og ikke som NYTT
    sources = set(old["meta"].get("sources", ["tikkio"]))
    fresh_source = {e["id"] for e in parken} if parken and "parken" not in sources else set()
    if parken:
        sources.add("parken")
    added = 0
    for e in events:
        is_new = e["id"] not in first_seen and e["id"] not in fresh_source and not e.get("addedAt")
        e["addedAt"] = first_seen.get(e["id"]) or e.get("addedAt") or (now if is_new else seeded_at)
        added += is_new
    meta = {
        "updatedAt": now,
        "seededAt": seeded_at,
        "lastAdded": added if first_seen else 0,
        "sources": sorted(sources),
    }
    events.sort(key=lambda e: (e["date"], e["time"] or "99"))
    old_path.write_text(json.dumps({"meta": meta, "events": events}, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(events)} arrangementer, {meta['lastAdded']} nye")


if __name__ == "__main__":
    main()
