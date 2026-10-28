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
import os
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
PARKEN_ADDRESS = "Parkgata 3B, 6003 Ålesund"
AAFK_TEAMS = [("https://www.aafk.no/terminliste", "Aalesund"),
              ("https://www.aafk.no/lag/aalesund-fk-kvinner-senior-a/terminliste", "AaFK Kvinner")]
AAFK_VENUE = "Color Line Stadion"
DAMP = "https://www.dampsentralen.no"
DAMP_VENUE = "Dampsentralen"
OCONNORS = "https://oconnors.no/alesund"
OCONNORS_VENUE = "O'Connor's"
OCONNORS_ADDRESS = "Brunholmgata 10, 6004 Ålesund"
FABRIKKEN = "https://www.fabrikkenkulturscene.no"
FABRIKKEN_VENUE = "Fabrikken Kulturscene"
VITI = "https://www.vitimusea.no"
# Viti har museer i flere kommuner. Bare de i Ålesund er med: (navn hos Viti) -> (navn på siden, adresse)
VITI_MUSEUMS = {"Jugendstilsenteret og KUBE": ("Jugendstilsenteret og KUBE", "Apotekergata 16, Ålesund"),
                "Sunnmøre museum": ("Sunnmøre museum", "Museumsvegen 12, 6015 Ålesund")}
MONTHS = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
UA = {"User-Agent": "Mozilla/5.0 (skjer-i-alesund; +https://github.com)", "Accept-Language": "nb-NO,nb;q=0.9"}

ALESUND_VENUES = ("Løvenvold", "Terminalen", "Venterommet")
VENUE_NAMES = {"Terminalen": "Terminalen Byscene"}
# Kurs, medlemskap og ungdomsforestillinger som ikke hører hjemme i kalenderen
SKIP = re.compile(r"medlemsskap|gruppe, høst|day pass|cowork|festivalpass|SPIRE|foredrag|påmelding|^FUND$", re.I)
# Steder rundt Ålesund: Tikkio-arrangementer som siles bort, men nevner et av dem eller mangler sted, gir varsel
NEAR_ALESUND = re.compile(r"Ålesund|Aalesund|Spjelkavik|Moa\b|Borgund|Vigra|Giske|Hessa|Valderøy|Ellingsøy|Nørvasundet|Volsdalen", re.I)
UNSURE = []  # (url, tekst) fra siste fetch_tikkio()
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
    t = re.sub(r"^(ekstrashow!|ekstrakonsert!|få bill!|utsolgt!)\s*", "", t, flags=re.I)
    t = re.sub(r"\s*//.*$", "", t)                      # « // Terminalen Byscene»
    t = re.sub(r"\s*/\s*\d{1,2}\.\d{1,2}\s*$", "", t)   # « / 5.11»
    t = re.sub(r"\s*\|\s*Support:.*$", "", t, flags=re.I)
    return t.strip(" |-")


def norm_key(title):
    return slug(re.sub(r"\b(premiere|gr\.\s*\d)\b", "", title, flags=re.I))


def clean_address(street, venue):
    # Tikkio har iblant bare stedsnavnet i adressefeltet; uten husnummer er det ikke en adresse
    a = re.sub(r",\s*(Norge|Norway)\s*$", "", (street or "").strip())
    return a if re.search(r"\d", a) and a != venue else ""


def fetch_tikkio():
    page = get(LISTING)
    spelling = {}  # Tikkio staver samme sted ulikt («kyrkje»/«Kyrkje»); første skrivemåte vinner
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
            # Bynavnet mangler av og til (Dampsentralen), men gateadressen sier «6003 Ålesund»
            in_alesund = city == "Ålesund" or "Ålesund" in (addr.get("streetAddress") or "")
            name = html.unescape(it.get("name") or "").strip()
            start = datetime.datetime.fromisoformat(it["startDate"]).astimezone(TZ)
            offer = it.get("offers") or {}
            offer = offer[0] if isinstance(offer, list) else offer
            url = offer.get("url") or ""
            if not (in_alesund or any(v in venue for v in ALESUND_VENUES)):
                where = " ".join([venue, city, addr.get("streetAddress") or ""]).strip()
                if start.date() >= today and not SKIP.search(name) and (
                        NEAR_ALESUND.search(where) or not (city or addr.get("streetAddress"))):
                    UNSURE.append((url, f"{name} ({where or 'ingen sted'}, {start.date().isoformat()})"))
                continue
            if SKIP.search(name):
                continue
            if start.date() < today:
                continue
            venue = spelling.setdefault(venue.casefold(), VENUE_NAMES.get(venue, venue))
            raw.append({"name": name, "venue": venue, "start": start,
                        "address": clean_address(addr.get("streetAddress"), venue),
                        "url": url, **tikkio_event(url, "SoldOut" in json.dumps(offer.get("availability")))})
    return raw


def tikkio_event(url, sold=False):
    """Billettypene og statusen fra én Tikkio-side. Oversikten sier alltid «InStock»; bare merket på
    selve siden («Utsolgt» / «Få billetter igjen», over bildet) sier om det er utsolgt eller nesten."""
    page = ""
    if url:
        try:
            page = get(url)
            time.sleep(0.5)
        except Exception as e:  # en enkelt side som feiler skal ikke stoppe hele kjøringen
            print("feil:", url, e, file=sys.stderr)
    badge = re.search(r'whitespace-nowrap">\s*(Utsolgt|Få billetter igjen)\s*<', page)
    return {"tickets": tikkio_tickets(page), "soldOut": sold or bool(badge and badge.group(1) == "Utsolgt"),
            "few": bool(badge and badge.group(1) == "Få billetter igjen")}


def tikkio_tickets(page):
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
    """Leser ett arrangement fra Parken. Returnerer (tittel, [(start, status)], pris-tuple), der status er
    «sold», «few» («Få billetter igjen») eller tom."""
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S | re.I)
    title = clean_title(re.sub(r"<[^>]+>", " ", h1.group(1))) if h1 else ""
    title = re.sub(r"\s+", " ", title).strip()
    text = page_text(page)
    # Hovedinnholdet kommer først; kutt før «andre arrangementer» så vi ikke leser naboene
    text = re.split(r"\n(?:Se også|Andre arrangementer|Du vil kanskje også like|Relaterte arrangementer)\n", text)[0]

    shows = []
    status = {"Utsolgt": "sold", "Få billetter igjen": "few"}
    for m in re.finditer(r"\b(\d{1,2})\.(\d{1,2})\s*-\s*kl\.\s*(\d{1,2})[:.](\d{2})(?:\s*-\s*\d{1,2}[:.]\d{2})?\s*(Utsolgt|Få billetter igjen)?", text):
        d, mo, hh, mm = (int(x) for x in m.group(1, 2, 3, 4))
        try:
            start = datetime.datetime(guess_year(d, mo, today), mo, d, hh, mm, tzinfo=TZ)
        except ValueError:
            continue
        if all(s != start for s, _ in shows):
            shows.append((start, status.get(m.group(5), "")))
    if not shows:
        m = re.search(r"\b(\d{1,2})\.\s*(" + "|".join(MONTHS) + r")[a-zæøå]*\.?\s*(\d{4})(?:\s*kl\.\s*(\d{1,2})[:.](\d{2}))?", text, re.I)
        if m:
            d, mo, y = int(m.group(1)), MONTHS.index(m.group(2).lower()) + 1, int(m.group(3))
            hh, mm = (int(m.group(4)), int(m.group(5))) if m.group(4) else (0, 0)
            try:
                start = datetime.datetime(y, mo, d, hh, mm, tzinfo=TZ)
                shows.append((start, ""))
            except ValueError:
                pass
    # Merket over bildet gjelder hele arrangementet; bruk det når det bare er én forestilling uten egen status
    hero = re.search(r'class="sale-status sale-status-\d">\s*<p>\s*([^<]*?)\s*</p>', page)
    if len(shows) == 1 and not shows[0][1] and hero:
        shows[0] = (shows[0][0], status.get(hero.group(1), ""))

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
        genre = parken_genre(page)
        if not title or not shows or SKIP.search(title):
            continue
        for start, st in shows:
            if start.date() < today:
                continue
            raw.append({"name": title, "venue": PARKEN_VENUE, "address": PARKEN_ADDRESS, "start": start, "url": url,
                        "tickets": [], "price": price, "soldOut": st == "sold", "few": st == "few", "src": "parken", "genre": genre, "group": "parken-" + pid,
                        "noTime": start.hour == 0 and start.minute == 0})  # dato uten klokkeslett
    print(f"Parken: {len(urls)} lenker, {len(raw)} forestillinger", file=sys.stderr)
    return raw


def fetch_dampsentralen():
    """Kalenderen til Dampsentralen (Squarespace; ?format=json gir kommende arrangementer). Når beskrivelsen lenker til et
    Tikkio-arrangement, hentes billettprisene derfra. Ellers vises «Pris hos arrangør». Gir None hvis siden ikke kunne leses."""
    today = datetime.datetime.now(TZ).date()
    try:
        data = json.loads(get(DAMP + "/kalender?format=json"))
    except Exception as e:
        warn(f"Klarte ikke å hente kalenderen til Dampsentralen: {e}")
        return None
    items = data.get("upcoming")
    if not isinstance(items, list):
        warn("Fant ikke «upcoming» i kalenderen til Dampsentralen. Sjekk om dampsentralen.no har endret siden.")
        return None
    raw = []
    for it in items:
        if not it.get("startDate") or not it.get("title"):
            continue
        start = datetime.datetime.fromtimestamp(it["startDate"] / 1000, TZ).replace(second=0, microsecond=0)
        if start.date() < today:
            continue
        name = re.sub(r"^[^\wÆØÅæøå]+|[^\wÆØÅæøå.!?]+$", "", html.unescape(it["title"]).strip())
        text = (it.get("excerpt") or "") + (it.get("body") or "")
        ticket = re.search(r'https://tikkio\.com/events/\d+[^"\'<\s]*', text)
        url = ticket.group(0) if ticket else DAMP + (it.get("fullUrl") or "/kalender")
        raw.append({"name": name, "venue": DAMP_VENUE, "start": start, "address": "", "url": url,
                    **(tikkio_event(url) if ticket else {"tickets": [], "soldOut": False})})
    print(f"Dampsentralen: {len(raw)} arrangementer", file=sys.stderr)
    return raw


def fetch_oconnors():
    """Programmet til O'Connor's Irish Pub (oconnors.no/alesund/hva-skjer/). Hvert arrangement har en egen side med dato, tid og pris.
    Sportsvisninger er ikke egne arrangementer hos dem og er ikke med. Gir None hvis siden ikke kunne leses."""
    today = datetime.datetime.now(TZ).date()
    try:
        listing = get(OCONNORS + "/hva-skjer/")
    except Exception as e:
        warn(f"Klarte ikke å hente programmet til O'Connor's: {e}")
        return None
    links = list(dict.fromkeys(re.findall(r'href="(https://oconnors\.no/alesund/event/[^"]+)"', listing)))
    if not links and "resthon-events-query" not in listing:
        warn("Fant ikke arrangementlista hos O'Connor's. Sjekk om oconnors.no har endret siden.")
        return None
    raw = []
    for url in links:
        try:
            page = get(url)
            time.sleep(0.5)
        except Exception as e:
            print("feil:", url, e, file=sys.stderr)
            continue
        text = lambda label: (m.group(1).strip() if (m := re.search(rf'<p class="label">{label}</p>\s*<p class="value">([^<]*)</p>', page)) else "")
        name = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
        day = re.search(r"(\d{1,2})\.\s*([a-zæøå]{3})", text("Dato").lower())
        hm = re.search(r"(\d{1,2}):(\d{2})", html.unescape(text("Tid")))
        if not (name and day and day.group(2) in MONTHS):
            print("Hopper over arrangement hos O'Connor's (uventet side):", url, file=sys.stderr)
            continue
        month = MONTHS.index(day.group(2)) + 1
        year = today.year + (1 if month < today.month - 1 else 0)
        start = datetime.datetime(year, month, int(day.group(1)), int(hm.group(1)) if hm else 0, int(hm.group(2)) if hm else 0, tzinfo=TZ)
        if start.date() < today:
            continue
        price = re.search(r"(\d+)", text("Pris"))
        body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(page)))
        title = re.sub(r"<[^>]+>", "", html.unescape(name.group(1))).strip().replace("’", "'")
        title = re.sub(r"\s+(hos\s+)?O'Connor's( Ålesund)?\s*$", "", title).strip(" !") or title  # stedet står allerede ved siden av
        raw.append({"name": title, "venue": OCONNORS_VENUE, "address": OCONNORS_ADDRESS,
                    "start": start, "url": url, "tickets": [], "soldOut": False, "noTime": not hm,
                    "group": "oconnors-" + start.date().isoformat() + "-" + slug(name.group(1))[:30],  # hver kveld har egen side og egen lenke
                    "price": (f"{price.group(1)} kr", int(price.group(1)), "") if price else None,
                    "gratis": bool(re.search(r"gratis å være med", listing, re.I))})
    print(f"O'Connor's: {len(raw)} arrangementer", file=sys.stderr)
    return raw


FAB_DATE = re.compile(r"\d{1,2}\.\s*(januar|februar|mars|april|mai|juni|juli|august|september|oktober|november|desember)|^(mandag|tirsdag|onsdag|torsdag|fredag|lørdag|søndag)\b", re.I)


def fabrikken_title(name):
    """«AUTUMN NIGHTS // Nordvest Big Band med solister // Lørdag 31. oktober» -> «AUTUMN NIGHTS – Nordvest Big Band med solister».
    Delene med ukedag eller dato tas bort (datoen står ved siden av), resten beholdes."""
    parts = [re.sub(r"\s+20\d\d$", "", p.strip()) for p in re.split(r"\s+/{1,2}\s+", html.unescape(name).strip())]
    return " – ".join(p for p in parts if p and not FAB_DATE.search(p)) or parts[0]


def fetch_fabrikken():
    """Programmet til Fabrikken Kulturscene (fabrikkenkulturscene.no/program, Webflow). Lista har dato, tittel og billettlenke
    (Billetto); klokkeslett (konsert-/showstart) og eventuell pris står i fritekst på arrangementsiden. Uten pris på siden
    vises «Pris hos arrangør». Gir None hvis siden ikke kunne leses."""
    today = datetime.datetime.now(TZ).date()
    try:
        listing = get(FABRIKKEN + "/program")
    except Exception as e:
        warn(f"Klarte ikke å hente programmet til Fabrikken Kulturscene: {e}")
        return None
    items = listing.split('role="listitem"')[1:]
    if not items:
        warn("Fant ikke arrangementlista hos Fabrikken Kulturscene. Sjekk om fabrikkenkulturscene.no har endret siden.")
        return None
    raw, parsed = [], 0
    for it in items:
        link = re.search(r'href="(/program/[^"]+)"', it)
        day = re.search(r'card-date[^>]*>\s*<div>(\d{1,2})</div><div>\.</div><div>(\d{1,2})</div><div>\.</div><div>(\d{2})</div>', it)
        name = re.search(r"<h3[^>]*>(.*?)</h3>", it, re.S)
        if not (link and day and name):
            continue
        parsed += 1
        d = datetime.date(2000 + int(day.group(3)), int(day.group(2)), int(day.group(1)))
        if d < today:
            continue
        url = FABRIKKEN + link.group(1)
        try:
            page = get(url)
            time.sleep(0.5)
        except Exception as e:
            print("feil:", url, e, file=sys.stderr)
            continue
        body = page.split("Andre arrangement")[0]
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", "", body, flags=re.S))))
        # «konsertstart ca. 20.30», «showstart 19.00», «Julebuffet og dinnershow starter kl. 20.00», «Forestilling: 20.00»
        hm = re.search(r"(?:start|starter|forestilling)\s*:?\s*(?:ca\.?\s*|kl\.?\s*)*(\d{1,2})\s*[.:]\s*(\d{2})", text, re.I)
        doors = re.search(r"Dør\w*\s+(?:åpner|opnar)\s*:?\s*(?:kl\.?\s*)?(\d{1,2})\s*[.:]\s*(\d{2})", text, re.I)
        hm = hm or doors
        ticket = re.search(r'href="(https://billetto\.no/e/[^"]+)"', it)
        raw.append({"name": fabrikken_title(re.sub(r"<[^>]+>", "", name.group(1))), "venue": FABRIKKEN_VENUE, "address": "",
                    "start": datetime.datetime(d.year, d.month, d.day, int(hm.group(1)) if hm else 0, int(hm.group(2)) if hm else 0, tzinfo=TZ),
                    "url": ticket.group(1) if ticket else url, "tickets": [], "soldOut": False, "noTime": not hm,
                    # bare beløpet; resten av fritekstlinja er beskrivelse
                    "price": (price[0], price[1], "") if (price := viti_price(text)) else ("", None, ""),
                    "note": f"Dørene åpner {int(doors.group(1)):02d}.{doors.group(2)}." if doors and hm is not doors else ""})
    if not parsed:
        warn("Klarte ikke å lese arrangementene hos Fabrikken Kulturscene. Sjekk om fabrikkenkulturscene.no har endret siden.")
        return None
    print(f"Fabrikken Kulturscene: {len(raw)} arrangementer", file=sys.stderr)
    return raw


def viti_price(text):
    """Pris fra fritekstblokken til arrangementet («Pris: 60 kr», «Inngang: Vaksen kr 80» o.l.). Gir None hvis den ikke står der."""
    m = re.search(r"(?:Pris|Inngang)\s*:\s*([^\n]+)", text)
    if not m:
        return None
    line = re.sub(r"\s+", " ", m.group(1)).strip()
    num = re.search(r"(\d+)\s*(?:kr|,-)|kr\s*(\d+)|Vaks\w*\s*(\d+)", line)
    if not num:
        return ("Gratis", 0, "") if re.match(r"gratis", line, re.I) else None
    n = int(next(g for g in num.groups() if g))
    rest = re.sub(r"^(?:Vaks\w*\s*)?(?:kr\s*)?\d+\s*(?:kr|,-)?[.,\s]*", "", line).strip()
    return f"{n} kr", n, rest if len(rest) > 3 else ""


def fetch_viti():
    """Arrangementene til Viti (vitimusea.no/arrangement), bare de som er i Ålesund (Jugendstilsenteret og Sunnmøre museum).
    Sidene er Next.js og har strukturerte data (datoer, by, museum) i __next_f; prisen står i fritekst og leses der den finnes.
    Arrangementer som varer over flere dager (samleoppføringer som «Familiedager på museet») er ikke med.
    Gir None hvis siden ikke kunne leses."""
    today = datetime.datetime.now(TZ).date()
    try:
        listing = get(VITI + "/arrangement")
    except Exception as e:
        warn(f"Klarte ikke å hente arrangementene til Viti: {e}")
        return None
    slugs = list(dict.fromkeys(re.findall(r'href="/arrangement/([^"/]+)"', listing)))
    if not slugs:
        warn("Fant ikke arrangementlista hos Viti. Sjekk om vitimusea.no har endret siden.")
        return None
    raw, bad = [], 0
    for sl in slugs:
        url = f"{VITI}/arrangement/{sl}"
        try:
            page = get(url)
            time.sleep(0.5)
            flight = "".join(json.loads('"' + c + '"') for c in re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', page, re.S))
            name = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
            city = re.search(r'"selectCity":\{"cityName":"([^"]*)"', flight)
            museums = re.findall(r'"address":"[^"]*","mapLink":"[^"]*","name":"([^"]*)"', flight[flight.find('"selectCity"'):])
            dates = re.findall(r'"endDate":"([^"]+)","startDate":"([^"]+)"', flight)
            tour = flight.find('"tour":[')
            blocks = json.JSONDecoder().raw_decode(flight[tour + 7:])[0] if tour >= 0 else []
        except Exception as e:
            print("feil:", url, e, file=sys.stderr)
            bad += 1
            continue
        text = "\n".join("".join(c.get("text", "") for c in b.get("children", [])) for b in blocks if isinstance(b, dict))
        museum = next((m for m in museums if m in VITI_MUSEUMS), None)
        in_alesund = (city.group(1) == "Ålesund") if city and city.group(1) else bool(museum)  # tom by: gå etter museet
        if not (name and dates and museum and in_alesund):
            continue
        venue, address = VITI_MUSEUMS[museum]
        price = viti_price(text)
        cat = "barn" if re.search(r"familie|baby|barn", name.group(1), re.I) else "happening"
        for end, start in dates:
            st = datetime.datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(TZ)
            en = datetime.datetime.fromisoformat(end.replace("Z", "+00:00")).astimezone(TZ)
            if st.date() < today or en.date() != st.date():
                continue
            raw.append({"name": html.unescape(name.group(1)).strip(), "venue": venue, "address": address, "start": st, "url": url,
                        "tickets": [], "soldOut": False, "cat": cat, "group": "viti-" + sl.strip("-"), "price": price})
    if bad == len(slugs):
        warn("Klarte ikke å lese noen av arrangementsidene hos Viti. Sjekk om vitimusea.no har endret siden.")
        return None
    print(f"Viti: {len(raw)} arrangementer i Ålesund", file=sys.stderr)
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


def fetch_aafk():
    """Hjemmekamper fra terminlistene til AaFK (herrer og kvinner). Billettprisene ligger i TicketCo og hentes ikke."""
    today = datetime.datetime.now(TZ).date()
    events = []
    for url, team in AAFK_TEAMS:
        try:
            page = get(url)
        except Exception as e:
            warn(f"Klarte ikke å hente terminlisten til AaFK ({url}): {e}")
            continue
        rows = re.findall(r'<tr class="[^"]*schedule__match">(.*?)</tr>', page, re.S)
        if not rows:  # ingen hjemmekamper er greit utenom sesongen, men en tom liste betyr at siden er endret
            warn(f"Fant ingen kamper i terminlisten til AaFK ({url}). Sjekk om aafk.no har endret siden.")
        for row in rows:
            m = re.search(r'item--teams">(.*?)</td>', row, re.S)
            d = re.search(r"<span>(\d{2})\.(\d{2})\.<span[^>]*>(\d{4})</span></span>\s*<span class=\"schedule__time\">\s*(\d{2}:\d{2})", row)
            if not m or not d or AAFK_VENUE not in row:
                continue
            teams = [t.strip() for t in re.sub(r"<[^>]+>", " ", m.group(1)).split(" - ")]
            if len(teams) != 2 or not teams[0].startswith(team):  # bare hjemmekamper
                continue
            day = datetime.date(int(d.group(3)), int(d.group(2)), int(d.group(1)))
            if day < today:
                continue
            link = re.search(r'ticket__button" href="([^"]+)"', row)
            lg = re.search(r'item--league[^>]*>(.*?)</td>', row, re.S)
            league = ""
            if lg:
                alt = re.search(r'alt="([^"]+)"', lg.group(1))
                league = html.unescape(alt.group(1) if alt else re.sub(r"<[^>]+>", " ", lg.group(1)))
                league = re.sub(r"\s*(-\s*)?\d{4}.*$", "", " ".join(league.split()))
            opponent = html.unescape(teams[1])
            events.append({
                "id": slug(f"aafk-{day.isoformat()}-{team}-{opponent}"),
                "date": day.isoformat(), "time": d.group(4),
                "title": f"{html.unescape(teams[0])} – {opponent}",
                "home": html.unescape(teams[0]), "away": opponent, "league": league,
                "venue": AAFK_VENUE, "address": "",
                "cat": "sport", "price": "", "priceMin": None, "soldOut": False,
                "note": "Fotball. Pris og billetter hos AaFK (TicketCo).",
                "uncertain": False,
                "url": html.unescape(link.group(1)) if link else url,
            })
    print(f"AaFK: {len(events)} hjemmekamper", file=sys.stderr)
    return events


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
        notes = [o.get("note", ""), first.get("note", "")]
        # Status per forestilling. Med 2–6 forestillinger og minst én status vises tidene som knapper med status på kortet
        # (i stedet for «Også kl.», «Utsolgt:» og «Flere forestillinger» i notatet)
        status = ["sold" if s["soldOut"] else "few" if s.get("few") else "" for s in shows]
        live = [x for x in status if x != "sold"]
        few = bool(live) and all(x == "few" for x in live)
        chips = 2 <= len(shows) <= 6 and any(status)
        extra_days = sorted({s["start"].date() for s in shows[1:]} - {first["start"].date()})
        same_day = [s["start"].strftime("%H:%M") for s in shows[1:] if s["start"].date() == first["start"].date()]
        if same_day and not chips:
            notes.append("Også kl. " + " og ".join(same_day) + ".")
        sold = [s for s in shows if s["soldOut"]]
        if sold and len(sold) < len(shows) and not chips:
            when = [s["start"].strftime("%H:%M") if s["start"].date() == first["start"].date() else fmt_day(s["start"].date()) for s in sold]
            notes.append("Utsolgt: " + ", ".join(dict.fromkeys(when)) + ".")
        if extra_days and not chips:
            listed = ", ".join(fmt_day(d) for d in extra_days[:5])
            notes.append(f"Flere forestillinger: {listed}" + (" m.fl." if len(extra_days) > 5 else "."))
        if o.get("discountNote", True):
            notes.append(disc)
        explicit = o.get("cat") or first.get("cat")
        rule = None if explicit else cat_rule(first["title"])
        cat = explicit or rule or "konsert"
        chk = None
        if not explicit:
            want = genre_cats(first.get("genre", ""))
            if want and cat not in want:
                chk = f"Parken oppgir «{first['genre']}», men kategorien er {cat}"
            elif rule is None and not want:
                chk = f"ingen regel traff tittelen, gjettet {cat}"
        events.append({
            "id": slug(key + "-" + venue),
            # «date» i en overstyring retter en feil dato hos kilden, men bare så lenge kilden fortsatt har «fromDate»
            "date": (o["date"] if o.get("date") and first["start"].date().isoformat() == o.get("fromDate", first["start"].date().isoformat()) else first["start"].date().isoformat()),
            "time": o.get("time") or ("" if first.get("noTime") else first["start"].strftime("%H:%M")),
            "title": o.get("title") or first["title"],
            "venue": venue,
            "address": first.get("address", ""),
            "cat": cat,
            **({"_chk": chk} if chk else {}),
            "price": price, "priceMin": price_min,
            "soldOut": all(s["soldOut"] for s in shows),
            **({"few": True} if few else {}),
            **({"shows": [[s["start"].strftime("%Y-%m-%d" if s.get("noTime") else "%Y-%m-%dT%H:%M"), x] for s, x in zip(shows, status)]} if chips else {}),
            # Parken merker nesten alt med «Få billetter igjen»; siden viser det derfor bare de siste to ukene
            **({"statusSrc": "parken"} if first.get("src") == "parken" and (few or chips) else {}),
            "note": " ".join(n for n in notes if n),
            "uncertain": bool(o.get("uncertain", False)),
            "url": first["url"],
            # Senere forestillinger, så helgelister o.l. finner dem selv om første dato er tidligere
            **({"moreShows": [s["start"].strftime("%Y-%m-%d" if s.get("noTime") else "%Y-%m-%dT%H:%M") for s in shows[1:]]} if len(shows) > 1 else {}),
        })
    return events


def cat_rule(title):
    """Kategori ut fra ord i tittelen, eller None når ingen regel treffer (da gjettes «konsert» og eieren varsles)."""
    t = title.lower()
    if re.search(r"julebord|julebuffet|julegilde", t):
        return "julebord"
    if re.search(r"standup|stand-up|stand up|komiker|humor|komedie|comedy", t):
        return "standup"
    if re.search(r"quiz|bingo", t):
        return "quiz"
    if re.search(r"verksted|marked|festival|dans\b|romjulsdans|skifilm", t):
        return "happening"
    if re.search(r"klubb|halloween|husfest|\bdj\b|fest\b|party", t):
        return "klubb"
    if re.search(r"barn|familie", t):
        return "barn"
    return None


def guess_cat(title):
    return cat_rule(title) or "konsert"


# Sjangeren Parken oppgir på arrangementssiden (fbq_content_category). Den er bare et hint: den er ikke alltid riktig
# (f.eks. «Komedie» på en konsert), så den setter ikke kategorien, men gir et varsel når kategorien ikke stemmer.
GENRE_CAT = {"humor": "standup", "komedie": "standup", "foredrag": "happening", "barn": "barn", "teater": "show", "dans": "show",
             "konsert": "konsert", "musikk": "konsert", "klassisk": "konsert", "folkemusikk": "konsert", "julekonsert": "konsert"}


def genre_cats(genre):
    return {GENRE_CAT[g.strip().lower()] for g in genre.split(",") if g.strip().lower() in GENRE_CAT}


def parken_genre(page):
    m = re.search(r'fbq_content_category" content="([^"]*)"', page)
    return html.unescape(m.group(1)).strip() if m else ""


def roll_forward(e):
    """Et manuelt arrangement med flere datoer (moreShows) flyttes til neste dato når den første har vært, så det ikke forsvinner."""
    today = datetime.datetime.now(TZ).date().isoformat()
    later = [m for m in e.get("moreShows", []) if m[:10] >= today]
    if e["date"] >= today or not later:
        return e
    nxt, rest = later[0], later[1:]
    e = {**e, "date": nxt[:10], "time": nxt[11:16] if len(nxt) > 10 else e.get("time", "")}
    if rest:
        e["moreShows"] = rest
    else:
        e.pop("moreShows", None)
    return e


def warn(msg):
    """Problemer som ikke stopper publiseringen, men som eieren bør vite om.
    I GitHub Actions skrives de til filen i SYNC_WARNINGS, og workflowen lager et issue."""
    print("ADVARSEL:", msg, file=sys.stderr)
    path = os.environ.get("SYNC_WARNINGS")
    if path:
        with open(path, "a") as f:
            f.write(f"- {msg}\n")


def main():
    overrides = json.loads((DATA / "overrides.json").read_text())
    manual = json.loads((DATA / "manual.json").read_text())
    old_path = DATA / "events.json"
    old = json.loads(old_path.read_text()) if old_path.exists() else {"events": [], "meta": {}}
    first_seen = {e["id"]: e.get("addedAt") for e in old["events"]}
    # Endres tittelen (og dermed id-en), kjenner vi arrangementet igjen på lenke og dato, så det ikke ser nytt ut
    seen_url = {(e["url"], e["date"]): e.get("addedAt") for e in old["events"] if e.get("url")}

    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    today = datetime.datetime.now(TZ).date().isoformat()
    events = build_events(fetch_tikkio(), overrides)
    if not events:
        sys.exit("Fant ingen arrangementer på Tikkio – beholder forrige versjon.")
    parken = build_events(fetch_parken(), overrides)
    if not parken:
        warn("Fikk ingen arrangementer fra Parken kulturhus. Siden viser reserven i data/manual.json, som kan være utdatert.")
    aafk = fetch_aafk()
    events += aafk
    damp_raw = fetch_dampsentralen()
    if damp_raw is None:  # siden svarte ikke: behold det vi hadde fra forrige gang
        damp = [e for e in old["events"] if e["venue"] == DAMP_VENUE and e["date"] >= today]
    else:
        damp = build_events(damp_raw, overrides)
    oc_raw = fetch_oconnors()
    if oc_raw is None:  # siden svarte ikke: behold det vi hadde fra forrige gang
        oconnors = [e for e in old["events"] if e["venue"] == OCONNORS_VENUE and e["date"] >= today]
    else:
        oconnors = build_events(oc_raw, overrides)
        for e in oconnors:
            if e["priceMin"] and any(r.get("gratis") for r in oc_raw) and "quiz" in e["title"].lower():
                e["uncertain"] = True
                e["note"] = (e["note"] + " " if e["note"] else "") + f"Oversikten deres sier kl. 20 og gratis, men arrangementssiden sier kl. {e['time']} og {e['price']}. Sjekk hos O'Connor's."
    viti_raw = fetch_viti()
    if viti_raw is None:  # siden svarte ikke: behold det vi hadde fra forrige gang
        viti = [e for e in old["events"] if e["venue"] in {v for v, _ in VITI_MUSEUMS.values()} and e["date"] >= today]
    else:
        viti = build_events(viti_raw, overrides)
    fab_raw = fetch_fabrikken()
    if fab_raw is None:  # siden svarte ikke: behold det vi hadde fra forrige gang
        fabrikken = [e for e in old["events"] if e["venue"] == FABRIKKEN_VENUE and e["date"] >= today]
    else:
        fabrikken = build_events(fab_raw, overrides)
    # Samme arrangement kan ligge både på Tikkio og hos Parken; Tikkio har billettprisene
    seen = {(e["date"], norm_key(e["title"])) for e in events}
    events += [e for e in parken if (e["date"], norm_key(e["title"])) not in seen]
    events += [e for e in damp if (e["date"], norm_key(e["title"])) not in seen]
    events += [e for e in oconnors if (e["date"], norm_key(e["title"])) not in seen]
    events += [e for e in viti if (e["date"], norm_key(e["title"])) not in seen]
    events += [e for e in fabrikken if (e["date"], norm_key(e["title"])) not in seen]
    # Manuelle Parken-arrangementer er reserve når Parken-siden (eller én av undersidene) ikke svarer
    parken_ids = {e["id"] for e in parken}
    events += [e for e in map(roll_forward, manual) if e["date"] >= today and e["id"] not in parken_ids]

    # Ikke alle Tikkio-arrangementer har adresse; bruk den fra et annet arrangement på samme scene
    known = {e["venue"]: e["address"] for e in events if e.get("address")}
    for e in events:
        e["address"] = e.get("address") or known.get(e["venue"], "")

    seeded_at = old["meta"].get("seededAt") or now
    # Første gang en ny kilde gir treff, regnes alt derfra som startprogram og ikke som NYTT
    sources = set(old["meta"].get("sources", ["tikkio"]))
    fresh_source = {e["id"] for e in parken} if parken and "parken" not in sources else set()
    if aafk and "aafk" not in sources:
        fresh_source |= {e["id"] for e in aafk}
    if damp and "dampsentralen" not in sources:
        fresh_source |= {e["id"] for e in damp}
    if oconnors and "oconnors" not in sources:
        fresh_source |= {e["id"] for e in oconnors}
    if viti and "viti" not in sources:
        fresh_source |= {e["id"] for e in viti}
    if fabrikken and "fabrikken" not in sources:
        fresh_source |= {e["id"] for e in fabrikken}
    if fabrikken:
        sources.add("fabrikken")
    if viti:
        sources.add("viti")
    if oconnors:
        sources.add("oconnors")
    if damp:
        sources.add("dampsentralen")
    if parken:
        sources.add("parken")
    if aafk:
        sources.add("aafk")
    added = 0
    check = []
    for e in events:
        known = first_seen.get(e["id"]) or seen_url.get((e["url"], e["date"]))
        is_new = not known and e["id"] not in first_seen and e["id"] not in fresh_source and not e.get("addedAt")
        e["addedAt"] = known or e.get("addedAt") or (now if is_new else seeded_at)
        added += is_new
        why = e.pop("_chk", None)
        if why and is_new and first_seen:
            check.append(f"{e['title']} ({e['venue']}, {e['date']}): {why}")
    if check:
        warn("Sjekk kategorien på nye arrangementer (rett den i data/overrides.json hvis den er feil): " + "; ".join(check))
    # Tikkio-arrangementer vi siler bort, men som kan være i Ålesund: varsle én gang per lenke
    checked = set(old["meta"].get("tikkioChecked", []))
    unsure = [(u, t) for u, t in UNSURE if u not in checked]
    if unsure and "tikkioChecked" in old["meta"]:
        warn("Tikkio har arrangementer som ikke er tatt med, men som kan være i Ålesund (legg inn sted i ALESUND_VENUES i sync.py eller i manual.json hvis de skal med): "
             + "; ".join(f"{t} {u}" for u, t in unsure))
    meta = {
        "tikkioChecked": sorted(checked | {u for u, _ in UNSURE}),
        "updatedAt": now,
        "seededAt": seeded_at,
        "lastAdded": added if first_seen else 0,
        "sources": sorted(sources),
    }
    events.sort(key=lambda e: (e["date"], e["time"] or "99"))
    # Et kraftig fall i antall arrangementer tyder på at en kilde har endret seg og ikke leses riktig lenger
    before = sum(e["date"] >= today for e in old["events"])
    if before >= 20 and len(events) < before * 0.6:
        warn(f"Antall arrangementer falt fra {before} til {len(events)}. Sjekk om Tikkio eller Parken har endret sidene sine.")
    old_path.write_text(json.dumps({"meta": meta, "events": events}, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(events)} arrangementer, {meta['lastAdded']} nye")


if __name__ == "__main__":
    main()
