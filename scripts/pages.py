"""Lager statiske undersider for søkemotorer og deling, og legger hele nettstedet i _site/.

Forsiden (index.html) bygger programmet med JavaScript. Undersidene er ferdig HTML,
så Google finner dem på søk som «standup ålesund» eller «skjer i ålesund i helgen»,
og en delt lenke til et arrangement får egen tittel og beskrivelse i forhåndsvisningen.

Alt hentes fra data/events.json. Ingenting her finner på arrangementer eller priser.
Sidene lages på nytt ved hver publisering (også «i dag» og «denne helgen»), og _site/ er ikke i git.

Kjør: python3 scripts/pages.py && python3 -m http.server -d _site
"""
import datetime
import json
import re
import shutil
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
BASE = "https://pedersen2k.github.io/skjer-i-alesund/"
TZ = ZoneInfo("Europe/Oslo")
SITE = "Skjer i Ålesund"
# Scener med færre arrangementer enn dette får ikke egen side (tynne sider hjelper ikke i søk)
VENUE_MIN = 3

WD = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"]
MO = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"]

# Kategori → (adresse, overskrift, ingress)
CATS = {
    "konsert": ("konserter", "Konserter i Ålesund", "Konserter i Ålesund"),
    "standup": ("standup", "Standup i Ålesund", "Standup og humor i Ålesund"),
    "show": ("show", "Show og teater i Ålesund", "Show, revy og teater i Ålesund"),
    "barn": ("barn-og-familie", "Barn og familie i Ålesund", "Arrangementer for barn og familie i Ålesund"),
    "klubb": ("klubb", "Klubb og fest i Ålesund", "Klubbkvelder og fest i Ålesund"),
    "happening": ("happenings", "Happenings i Ålesund", "Happenings, marked og andre arrangementer i Ålesund"),
    "sport": ("aafk-hjemmekamper", "AaFK-hjemmekamper", "Aalesunds hjemmekamper på Color Line Stadion"),
}
CAT_LABEL = {"konsert": "Konsert", "standup": "Standup", "show": "Show", "barn": "Barn & familie", "klubb": "Klubb", "happening": "Happening", "sport": "Sport"}


def slug(s):
    s = s.lower().replace("æ", "ae").replace("ø", "o").replace("å", "a")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def day_text(d, year=False):
    return f"{WD[d.weekday()]} {d.day}. {MO[d.month - 1]}" + (f" {d.year}" if year else "")


def range_text(a, b):
    if a == b:
        return day_text(a)
    if a.month == b.month:
        return f"{a.day}.–{b.day}. {MO[a.month - 1]}"
    return f"{a.day}. {MO[a.month - 1]}–{b.day}. {MO[b.month - 1]}"


def price_text(e):
    if e.get("soldOut"):
        return "Utsolgt"
    if e.get("priceMin") == 0:
        return "Gratis"
    return e.get("price") or "Pris hos arrangør"


def map_url(e):
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{e['venue']}, {e.get('address') or 'Ålesund'}")


def safe_url(u):
    return u if (u or "").startswith("https://") else ""


def event_ld(e):
    """schema.org/Event med bare felt vi har fra kilden (samme som forsiden lager med JavaScript)."""
    o = {
        "@type": "Event",
        "name": e["title"],
        "startDate": e["date"] + (f"T{e['time']}" if re.fullmatch(r"\d{2}:\d{2}", e.get("time") or "") else ""),
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": {"@type": "Place", "name": e["venue"], "address": {"@type": "PostalAddress", "addressLocality": "Ålesund", "addressCountry": "NO"}},
        "url": BASE + f"arrangement/{e['id']}/",
        "image": BASE + "og-image.png",
    }
    if e.get("address"):
        o["location"]["address"]["streetAddress"] = e["address"]
    if e.get("note"):
        o["description"] = e["note"]
    if isinstance(e.get("priceMin"), (int, float)) and e["priceMin"] > 0 and safe_url(e.get("url")):
        o["offers"] = {"@type": "Offer", "url": e["url"], "price": str(e["priceMin"]), "priceCurrency": "NOK",
                       "availability": "https://schema.org/SoldOut" if e.get("soldOut") else "https://schema.org/InStock"}
    return o


def ld_script(obj):
    # </ i JSON kan avslutte <script>-taggen for tidlig
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def page(path, title, description, body, ld=None, up=None, image=None):
    """Hele HTML-dokumentet. path er relativ adresse, f.eks. «konserter/».
    up er veien tilbake til roten; 404-siden vises på vilkårlige adresser og bruker derfor full adresse.
    image er (adresse, bredde, høyde) for forhåndsvisningsbildet, ellers brukes logoen."""
    up = "../" * path.count("/") if up is None else up
    img, img_w, img_h = image or (BASE + "og-image.png", 1200, 630)
    url = BASE + path
    return f"""<!doctype html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
{'<meta name="robots" content="noindex">' if path == "404.html" else f'<link rel="canonical" href="{url}">'}
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:locale" content="nb_NO">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{escape(img)}">
<meta property="og:image:width" content="{img_w}">
<meta property="og:image:height" content="{img_h}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#eef3f2">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,800&family=Figtree:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap">
<link rel="stylesheet" href="{up}stil.css">
<script>try {{ const t = JSON.parse(localStorage.getItem("skjer-theme")); if (t === "light" || t === "dark") document.documentElement.dataset.theme = t; }} catch {{}}</script>
{ld_script(ld) if ld else ""}
</head>
<body>
<div class="wrap sub">
  <nav class="crumbs"><a href="{up}">← {SITE}: hele programmet</a></nav>
{body}
</div>
<script>
// Besøksstatistikk med GoatCounter (uten informasjonskapsler), samme konto som forsiden
const gc = document.createElement("script"); gc.async = true; gc.src = "https://gc.zgo.at/count.js";
gc.dataset.goatcounter = "https://skjer-i-alesund.goatcounter.com/count"; document.head.appendChild(gc);
</script>
</body>
</html>
"""


def card(e, up):
    """Ett arrangement i en liste. Tittelen lenker til arrangementets egen side."""
    c = e["cat"] if e["cat"] in CAT_LABEL else "happening"
    u = safe_url(e.get("url"))
    price_cls = "price sold" if e.get("soldOut") else "price" if (e.get("price") or e.get("priceMin") == 0) else "price unk"
    return f"""<article class="ev" style="--c:var(--c-{c})">
        <h3><a class="title" href="{up}arrangement/{e['id']}/">{escape(e['title'])}</a></h3>
        <div class="side"><span class="{price_cls}">{escape(price_text(e))}</span></div>
        <div class="meta"><span class="tag">{CAT_LABEL[c]}</span>{f'<a class="venue" href="{up}{venue_path(e["venue"])}">' if venue_path(e["venue"]) else '<span>'}{escape(e['venue'])}{'</a>' if venue_path(e["venue"]) else '</span>'}{f'<span class="t">kl. {escape(e["time"])}</span>' if e.get("time") else ""}</div>
        {f'<div class="note{" warn" if e.get("uncertain") else ""}">{escape(e["note"])}</div>' if e.get("note") else ""}
        {f'<div class="actions"><a class="link" href="{escape(u)}" target="_blank" rel="noopener">Billetter →</a></div>' if u else ""}
      </article>"""


def day_list(events, up):
    out, days = [], {}
    for e in events:
        days.setdefault(e["date"], []).append(e)
    for date, evs in days.items():
        d = datetime.date.fromisoformat(date)
        out.append(f"""<section class="day"><div class="date"><div class="wd">{WD[d.weekday()][:3]}</div><div class="num">{d.day}</div><div class="mo">{MO[d.month - 1][:3]}</div></div>
      <div class="events">{"".join(card(e, up) for e in evs)}</div></section>""")
    return "\n".join(out)


VENUE_PAGES = {}


def venue_path(v):
    return VENUE_PAGES.get(v)


def links_nav(up, current, extra):
    """Snarveier til de andre undersidene, så både folk og søkemotorer finner rundt."""
    items = [("i-dag/", "I dag"), ("denne-helgen/", "Denne helgen"), ("kino/", "Kino")] + [(p + "/", CAT_LABEL[k] if k != "sport" else "AaFK") for k, (p, _, _) in CATS.items() if k in extra]
    items += [(p, v) for v, p in VENUE_PAGES.items()]
    return '<nav class="more"><h2>Mer fra programmet</h2><div class="row">' + "".join(
        f'<a class="chip" href="{up}{p}"{" aria-current=\"page\"" if p == current else ""}>{escape(l)}</a>' for p, l in items) + "</div></nav>"


def listing(path, h1, lede, events, empty, cats_present):
    up = "../" * path.count("/")
    body = f"""  <header class="top">
    <h1>{escape(h1)}</h1>
    <p class="lede">{escape(lede)}</p>
  </header>
  <main>
{day_list(events, up) if events else f'<p class="empty">{escape(empty)}</p>'}
  </main>
  {links_nav(up, path, cats_present)}
  <footer><div>Programmet hentes automatisk morgen og kveld fra arrangørenes billettsider. Datoer og priser kan endres, så sjekk alltid hos arrangøren før du kjøper billett.</div></footer>"""
    return body


def write(path, html):
    f = OUT / path / "index.html" if path.endswith("/") or not path else OUT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(html)


def weekend_range(today):
    """Fredag–søndag. Fra mandag til torsdag er det helgen som kommer."""
    wd = today.weekday()
    return today + datetime.timedelta(days=max(0, 4 - wd)), today + datetime.timedelta(days=6 - wd)


def occurrences(events, start, end):
    """Arrangementene som går mellom start og end, én gang per dag. Gjentatte forestillinger
    (moreShows) tas med selv om første dato er tidligere, med dato og klokkeslett for den dagen
    («15:00 og 19:00» når det er flere samme dag)."""
    out = []
    for e in events:
        days = {}
        for d, t in [(e["date"], e.get("time") or "")] + [(s[:10], s[11:16]) for s in e.get("moreShows", [])]:
            if start.isoformat() <= d <= end.isoformat():
                days.setdefault(d, [])
                if t and t not in days[d]:
                    days[d].append(t)
        out += [{**e, "date": d, "time": " og ".join(sorted(ts))} for d, ts in days.items()]
    return sorted(out, key=lambda e: (e["date"], e["time"] or "99"))


def describe(events, what):
    n = len(events)
    if not n:
        return f"{what}. Oversikt med billettpriser, oppdatert morgen og kveld."
    names = ", ".join(e["title"] for e in events[:3])
    return f"{n} {'arrangement' if n == 1 else 'arrangementer'}: {names}{' med flere' if n > 3 else ''}. {what}, med billettpriser, oppdatert morgen og kveld."[:300]


def main():
    data = json.loads((ROOT / "data" / "events.json").read_text())
    today = datetime.datetime.now(TZ).date()
    events = [e for e in data["events"] if e["date"] >= today.isoformat()]
    events.sort(key=lambda e: (e["date"], e.get("time") or "99"))
    updated = (data.get("meta", {}).get("updatedAt") or today.isoformat())[:10]

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    # Forsiden og det den trenger, kopiert som de er
    shutil.copy(ROOT / "index.html", OUT / "index.html")
    shutil.copy(ROOT / "og-image.png", OUT / "og-image.png")
    (OUT / "data").mkdir()
    shutil.copy(ROOT / "data" / "events.json", OUT / "data" / "events.json")
    if (ROOT / "data" / "kino.json").exists():
        shutil.copy(ROOT / "data" / "kino.json", OUT / "data" / "kino.json")
    index = (ROOT / "index.html").read_text()
    # Undersidene bruker samme stil og ikon som forsiden, hentet rett fra index.html
    css = re.search(r"<style>(.*?)</style>", index, re.S).group(1)
    (OUT / "stil.css").write_text(css + SUB_CSS)
    icon = re.search(r'<link rel="icon" href="data:image/svg\+xml,([^"]+)"', index)
    if icon:
        from urllib.parse import unquote
        (OUT / "favicon.svg").write_text(unquote(icon.group(1)))

    counts = {}
    for e in events:
        counts[e["venue"]] = counts.get(e["venue"], 0) + 1
    VENUE_PAGES.clear()
    for v, n in sorted(counts.items(), key=lambda x: -x[1]):
        if n >= VENUE_MIN:
            VENUE_PAGES[v] = f"scene/{slug(v)}/"
    cats_present = {e["cat"] for e in events}
    pages = []  # (adresse, endret)

    def listing_page(path, title, h1, lede, evs, empty, what, image=None):
        write(path, page(path, title, describe(evs, what), listing(path, h1, lede, evs, empty, cats_present),
                         {"@context": "https://schema.org", "@graph": [event_ld(e) for e in evs]} if evs else None, image=image))
        pages.append((path, updated))

    # I dag
    tod = occurrences(events, today, today)
    listing_page("i-dag/", f"Hva skjer i Ålesund i dag? {day_text(today).capitalize()} | {SITE}", "Skjer i Ålesund i dag",
                 f"Konserter, standup, show og andre arrangementer i Ålesund {day_text(today)}.", tod,
                 "Vi har ingen arrangementer registrert i dag. Se hva som skjer i helgen eller i hele programmet.",
                 "Hva skjer i Ålesund i dag")

    start, sun = weekend_range(today)
    weekend = occurrences(events, start, sun)
    span = range_text(start, sun)
    # Helgebildet (Instagram-format) blir også forhåndsvisningen når siden deles. Krever Pillow.
    image = None
    try:
        import helgepost
        (OUT / "denne-helgen").mkdir(parents=True, exist_ok=True)
        helgepost.render_image(weekend, start, sun, OUT / "denne-helgen")
        image = (f"{BASE}denne-helgen/helgen.png?v={today.isoformat()}", helgepost.W, helgepost.H)
    except Exception as err:  # bildet skal aldri stoppe publiseringen
        print(f"Lager ikke helgebilde ({err!r})", file=sys.stderr)
    listing_page("denne-helgen/", f"Hva skjer i Ålesund i helgen? {span} | {SITE}", "Skjer i Ålesund i helgen",
                 f"Alt vi har funnet i Ålesund {span}: konserter, standup, show, klubb og familie, med billettpriser.", weekend,
                 "Vi har ingen arrangementer registrert denne helgen ennå.", f"Hva skjer i Ålesund i helgen, {span}", image)

    for k, (p, h1, what) in CATS.items():
        # Lages også uten arrangementer, så lenkene fra forsiden aldri blir døde
        evs = [e for e in events if e["cat"] == k]
        listing_page(p + "/", f"{h1} – program og billettpriser | {SITE}", h1,
                     f"{what}: {len(evs)} kommende {'arrangement' if len(evs) == 1 else 'arrangementer'}, " + ("med avspark og billettlenker." if k == "sport" else "med datoer og billettpriser."),
                     evs, f"Ingen kommende arrangementer i denne kategorien akkurat nå. Se hele programmet.", what)

    for v, p in VENUE_PAGES.items():
        evs = [e for e in events if e["venue"] == v]
        listing_page(p, f"{v} – program og billetter | {SITE}", f"Program for {v}",
                     f"Kommende arrangementer på {v}{', ' + evs[0]['address'] if evs[0].get('address') else ', Ålesund'}, med datoer og billettpriser.",
                     evs, "", f"Program for {v} i Ålesund")

    for e in events:
        path = f"arrangement/{e['id']}/"
        write(path, event_page(e, events, path))
        pages.append((path, (e.get("addedAt") or updated)[:10]))

    # Kino ligger på egen side og er ikke med i lister, kategorier eller helgeposten på bildet
    kino_meta, kino_films = load_kino(today)
    write("kino/", page("kino/", f"Kinoprogram ODEON Ålesund: hva går på kino? | {SITE}", "Hva går på kino i Ålesund? Program, plakater og visningstider for ODEON Ålesund (Amfi Moa).",
                        kino_page(kino_films, kino_meta, today)))
    pages.append(("kino/", (kino_meta.get("updatedAt") or updated)[:10]))

    # Delte lenker til arrangementer som er over, havner her
    write("404.html", page("404.html", f"Fant ikke siden | {SITE}", "Arrangementet er over eller finnes ikke lenger.",
                           f"""  <header class="top"><h1>Fant ikke siden</h1>
    <p class="lede">Arrangementet er kanskje over, eller lenken er feil. Se hva som skjer i Ålesund nå:</p></header>
  <p><a class="link" href="{BASE}">Hele programmet →</a></p>
  {links_nav(BASE, "", cats_present)}""", up=BASE))

    urls = [("", updated)] + pages
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "".join(f"  <url><loc>{BASE}{p}</loc><lastmod>{m}</lastmod></url>\n" for p, m in urls) + "</urlset>\n")
    print(f"Skrev {len(urls)} sider til {OUT.relative_to(ROOT)}/", file=sys.stderr)


def event_page(e, events, path):
    up = "../../"
    d = datetime.date.fromisoformat(e["date"])
    c = e["cat"] if e["cat"] in CAT_LABEL else "happening"
    u = safe_url(e.get("url"))
    when = day_text(d, year=True) + (f" kl. {e['time']}" if e.get("time") else "")
    title = f"{e['title']} – {e['venue']}, {d.day}. {MO[d.month - 1]} | {SITE}"
    pt = price_text(e)
    desc = f"{e['title']} på {e['venue']} i Ålesund {when}. " + (
        f"Billett: {pt}. " if pt != "Pris hos arrangør" else "") + (e.get("note") or "")
    venue = escape(e["venue"])
    venue_html = f'<a href="{up}{venue_path(e["venue"])}">{venue}</a>' if venue_path(e["venue"]) else venue
    same_venue = [x for x in events if x["venue"] == e["venue"] and x["id"] != e["id"]][:5]
    same_day = [x for x in events if x["date"] == e["date"] and x["id"] != e["id"]][:5]
    cat_path = CATS.get(c, CATS["happening"])[0] + "/"
    body = f"""  <main>
  <article class="detail" style="--c:var(--c-{c})">
    <div class="tag">{CAT_LABEL[c]}{f' · {escape(e["league"])}' if e.get("league") else ""}</div>
    <h1>{escape(e['title'])}</h1>
    <dl>
      <dt>Når</dt><dd>{escape(when[0].upper() + when[1:])}</dd>
      <dt>Hvor</dt><dd>{venue_html}{f', {escape(e["address"])}' if e.get("address") else ", Ålesund"} · <a href="{escape(map_url(e))}" target="_blank" rel="noopener">Kart</a></dd>
      <dt>Pris</dt><dd class="{'sold' if e.get('soldOut') else ''}">{escape(pt)}</dd>
    </dl>
    {f'<p class="note{" warn" if e.get("uncertain") else ""}">{escape(e["note"])}</p>' if e.get("note") else ""}
    <div class="cta">{f'<a class="btn" href="{escape(u)}" target="_blank" rel="noopener">Billetter og info hos arrangør →</a>' if u else ""}<a class="link" href="{up}#ev-{e['id']}">Se i hele programmet</a></div>
    <p class="small">Datoer og priser kan endres. Sjekk alltid hos arrangøren før du kjøper billett.</p>
  </article>
  {f'<section class="also"><h2>Samme dag</h2><div class="events">{"".join(card(x, up) for x in same_day)}</div></section>' if same_day else ""}
  {f'<section class="also"><h2>Mer på {venue}</h2><div class="events">{"".join(card(x, up) for x in same_venue)}</div></section>' if same_venue else ""}
  </main>
  <nav class="more"><div class="row"><a class="chip" href="{up}{cat_path}">Flere: {CAT_LABEL[c]}</a><a class="chip" href="{up}denne-helgen/">Denne helgen</a><a class="chip" href="{up}">Hele programmet</a></div></nav>"""
    return page(path, title, desc[:300], body, {"@context": "https://schema.org", **event_ld(e)})


# Det undersidene trenger i tillegg til forsidens stil
# --- Kino (egen side, holdt utenfor hovedlista) ---

KINO_COLORS = ["#4a5d3a", "#7a3b3b", "#2d4a6b", "#2a6a72", "#a8561c", "#5b3a7a", "#8a4a68", "#3f6b4a", "#7a6420", "#44505e"]
WD_SHORT = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"]


def load_kino(today):
    """Filmene med bare de visningene som er i dag eller senere. Tom liste hvis data/kino.json mangler."""
    f = ROOT / "data" / "kino.json"
    if not f.exists():
        return {}, []
    data = json.loads(f.read_text())
    films = []
    for film in data.get("films", []):
        shows = [s for s in film["shows"] if s["start"][:10] >= today.isoformat()]
        if shows:
            films.append({**film, "shows": shows})
    return data.get("meta", {}), films


def kino_age(a):
    if a is None:
        return ""
    return f'<span class="age a{a}" title="{"Tillatt for alle" if a == 0 else f"Aldersgrense {a} år"}">{"A" if a == 0 else a}</span>'


def kino_film(f, day):
    shows = [s for s in f["shows"] if s["start"][:10] == day]
    if not shows:
        return ""
    color = KINO_COLORS[sum(map(ord, f["title"])) % len(KINO_COLORS)]
    img = (f'<img src="{escape(f["poster"])}" width="360" height="540" loading="lazy" alt="Plakat for {escape(f["title"], True)}" '
           f'onerror="this.remove()">') if f.get("poster") else ""
    facts = []
    if f.get("minutes"):
        facts.append(f'{f["minutes"] // 60}t {f["minutes"] % 60}m')
    if f.get("genres"):
        facts.append(" / ".join(f["genres"][:3]))
    times = ""
    for s in shows:
        tags = "".join(f"<small>{escape(t)}</small>" for t in s["tags"] if t != "LUXE")
        title = escape(f'{f["title"]} {s["start"][11:16]}, {s["screen"]}' + (" (LUXE)" if "LUXE" in s["tags"] else ""), True)
        times += (f'<a class="t" href="{escape(safe_url(s["url"]))}" target="_blank" rel="noopener noreferrer" '
                  f'data-start="{s["start"]}" title="{title}">{s["start"][11:16]}{tags}</a>')
    premiere = '<span class="newfilm">Ny</span>' if f.get("premiere") == day else ""
    return f"""    <article class="film">
      <div class="poster" style="--pc:{color}"><span>{escape(f["title"])}</span>{img}</div>
      <div class="info">
        <h2>{escape(f["title"])} {premiere}</h2>
        <div class="facts">{kino_age(f.get("age"))}<span>{escape(" · ".join(facts))}</span></div>
      </div>
      <div class="times">{times}</div>
    </article>
"""


def kino_page(films, meta, today):
    days = sorted({s["start"][:10] for f in films for s in f["shows"]})
    chips = "".join(
        f'<button type="button" class="chip" data-day="{d}" aria-pressed="false">'
        f'{WD_SHORT[datetime.date.fromisoformat(d).weekday()]} {datetime.date.fromisoformat(d).day}.</button>' for d in days)
    sections = ""
    for d in days:
        sections += f'  <section class="kinoday" data-day="{d}" hidden aria-label="Program {d}">\n'
        sections += "".join(kino_film(f, d) for f in films)
        sections += "  </section>\n"
    updated = (meta.get("updatedAt") or "")[:10]
    body = f"""  <header class="top">
    <h1>Kino i Ålesund</h1>
    <p class="lede">Hva som går på ODEON Ålesund (Amfi Moa).</p>
  </header>
  <div class="kinobar">
    <div class="row" id="kinodays">{chips}</div>
    <div class="row" id="kinoview" role="group" aria-label="Visning">
      <button type="button" class="chip" data-v="list" aria-pressed="true">Kort</button>
      <button type="button" class="chip" data-v="grid" aria-pressed="false">Plakater</button>
    </div>
  </div>
  <main id="films" class="kinofilms">
{sections if days else '<p class="empty">Vi har ikke kinoprogrammet akkurat nå. Se ODEON Ålesund sin egen side.</p>'}
  </main>
  <p class="empty" id="kinoempty" hidden>Ingen flere visninger denne dagen.</p>
  <p class="small kinosrc">Program og plakater via <a href="https://www.filmweb.no/program/sted/%C3%A5lesund/odeon%20%C3%A5lesund" target="_blank" rel="noopener">Filmweb</a>, bestilling hos <a href="https://www.odeonkino.no/alesund/kino/odeon-alesund/" target="_blank" rel="noopener">ODEON Ålesund</a>. Hentet {updated}. Sjekk alltid tidene hos kinoen.</p>
  <script>
{KINO_JS}
  </script>
  <footer><div>Kinoprogrammet er adskilt fra resten av programmet. Det oppdateres morgen og kveld.</div></footer>"""
    return body


KINO_JS = """
const osloNow = () => { const p = Object.fromEntries(new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Oslo", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date()).map(x => [x.type, x.value])); return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`; };
const now = osloNow(), today = now.slice(0, 10);
const addDay = d => { const x = new Date(d + "T12:00:00Z"); x.setUTCDate(x.getUTCDate() + 1); return x.toISOString().slice(0, 10); };
const chips = [...document.querySelectorAll("#kinodays .chip")];
chips.forEach(c => { if (c.dataset.day === today) c.textContent = "I dag"; else if (c.dataset.day === addDay(today)) c.textContent = "I morgen"; });
document.querySelectorAll(".t").forEach(t => { if (t.dataset.start < now) t.classList.add("past"); });
function pick(day) {
  chips.forEach(c => c.setAttribute("aria-pressed", c.dataset.day === day));
  let any = false;
  document.querySelectorAll(".kinoday").forEach(s => { s.hidden = s.dataset.day !== day; });
  document.querySelectorAll(".kinoday:not([hidden]) .film").forEach(f => {
    const live = f.querySelector(".t:not(.past)");
    f.classList.toggle("done", !live); any = true;
  });
  document.getElementById("kinoempty").hidden = any || chips.length === 0;
}
chips.forEach(c => c.addEventListener("click", () => { pick(c.dataset.day); try { history.replaceState(null, "", "#" + c.dataset.day); } catch {} }));
const wanted = location.hash.slice(1);
pick(chips.find(c => c.dataset.day === wanted) ? wanted : (chips.find(c => c.dataset.day >= today) || chips[0] || {}).dataset?.day);
const films = document.getElementById("films");
function view(v) { films.classList.toggle("grid", v === "grid"); document.querySelectorAll("#kinoview .chip").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === v)); try { localStorage.setItem("skjer-kinovisning", v); } catch {} }
document.querySelectorAll("#kinoview .chip").forEach(b => b.addEventListener("click", () => view(b.dataset.v)));
try { view(localStorage.getItem("skjer-kinovisning") === "grid" ? "grid" : "list"); } catch { view("list"); }
"""


SUB_CSS = """
/* Undersider (lages av scripts/pages.py) */
.sub .crumbs { font: 500 13px/1.4 var(--font-body); padding-bottom: 14px; }
.sub .crumbs a, .sub .venue, .sub a.title { color: inherit; }
.sub a.title { text-decoration: none; }
.sub a.title:hover { text-decoration: underline; }
.sub h1 { font-size: clamp(32px, 7vw, 52px); }
.sub .ev { grid-template-columns: 1fr auto; }
.sub .ev .side { grid-row: 1; }
.sub .more, .sub .also { margin-top: 28px; }
.sub .more h2, .sub .also h2 { font: 700 18px/1.2 var(--font-display); margin: 0 0 10px; }
.sub .more .chip { text-decoration: none; }
.sub .more .chip[aria-current="page"] { background: var(--fg); color: var(--bg); border-color: var(--fg); }
.detail { background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--c); border-radius: 12px; padding: 18px 20px; }
.detail .tag { margin-bottom: 8px; }
.detail h1 { font-size: clamp(28px, 6vw, 44px); line-height: 1.05; margin-bottom: 16px; overflow-wrap: anywhere; }
.detail dl { display: grid; grid-template-columns: auto 1fr; gap: 6px 16px; margin: 0 0 12px; }
.detail dt { font: 500 12px/1.6 var(--font-mono); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
.detail dd { margin: 0; }
.detail dd a { color: var(--sea); }
.detail dd.sold { color: var(--accent); font-weight: 600; }
.detail .note { font-size: 14px; }
.detail .cta { display: flex; flex-wrap: wrap; gap: 10px 18px; align-items: center; margin-top: 14px; }
.btn { display: inline-block; font: 600 15px/1 var(--font-body); padding: 12px 16px; border-radius: 10px; background: var(--accent); color: var(--accent-ink); text-decoration: none; }
.btn:hover { filter: brightness(1.05); }
.detail .small { font-size: 12.5px; color: var(--muted); margin: 14px 0 0; }

/* Kino */
:root { --kino: #3d4f8f; --kino-soft: #e3e8f5; --kino-ink: #ffffff; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --kino: #8fa3e6; --kino-soft: #1c2748; --kino-ink: #0b1230; } }
:root[data-theme="dark"] { --kino: #8fa3e6; --kino-soft: #1c2748; --kino-ink: #0b1230; }
.kinobar { display: grid; gap: 10px; margin-bottom: 16px; }
.kinobar #kinodays { flex-wrap: nowrap; overflow-x: auto; padding-bottom: 2px; }
.kinobar .chip { flex: none; }
.kinobar .chip[aria-pressed="true"] { background: var(--kino); border-color: var(--kino); color: var(--kino-ink); }
.kinoday { display: grid; gap: 12px; }
.film { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 14px; display: grid; grid-template-columns: 72px minmax(0, 1fr); gap: 8px 14px; }
.film.done { opacity: .6; }
.poster { grid-row: span 1; width: 72px; aspect-ratio: 2 / 3; border-radius: 6px; background: var(--pc); position: relative; overflow: hidden; color: #fff; }
.poster span { position: absolute; inset: 0; padding: 6px; font: 700 11px/1.15 var(--font-display); display: flex; align-items: flex-end; overflow-wrap: break-word; hyphens: auto; }
.poster img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.film .info { min-width: 0; display: grid; gap: 6px; align-content: start; }
.film h2 { margin: 0; font: 700 19px/1.2 var(--font-display); overflow-wrap: anywhere; }
.film .facts { display: flex; flex-wrap: wrap; gap: 4px 10px; align-items: center; color: var(--muted); font-size: 13px; }
.age { display: inline-grid; place-items: center; min-width: 26px; height: 26px; padding: 0 5px; border-radius: 5px; font: 700 12px/1 var(--font-display); color: #fff; background: #2f8a4c; }
.age.a7, .age.a9 { background: #2b7fb8; } .age.a12 { background: #9a6d0f; } .age.a15 { background: #c8432b; } .age.a18 { background: #1a1a1a; }
.newfilm { font: 700 10px/1 var(--font-body); letter-spacing: .06em; text-transform: uppercase; padding: 3px 6px; border-radius: 4px; background: var(--kino); color: var(--kino-ink); vertical-align: middle; }
.film .times { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 6px; }
.film .t { font: 500 15px/1 var(--font-mono); font-variant-numeric: tabular-nums; padding: 8px 12px; border-radius: 8px; border: 1.5px solid var(--kino); color: var(--kino); text-decoration: none; display: inline-flex; gap: 6px; align-items: baseline; }
.film .t:hover { background: var(--kino); color: var(--kino-ink); }
.film .t small { font: 600 10px/1 var(--font-body); letter-spacing: .04em; text-transform: uppercase; opacity: .85; }
.film .t.past { text-decoration: line-through; border-color: var(--line); color: var(--muted); }
.kinosrc { margin-top: 18px; }
.kinofilms.grid .kinoday { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
.kinofilms.grid .film { grid-template-columns: 1fr; padding: 0; overflow: hidden; align-content: start; gap: 0; }
.kinofilms.grid .poster { width: 100%; border-radius: 0; }
.kinofilms.grid .poster span { font-size: 17px; padding: 12px; }
.kinofilms.grid .info { padding: 10px 12px 0; }
.kinofilms.grid .info h2 { font-size: 15px; }
.kinofilms.grid .times { padding: 10px 12px 12px; gap: 5px; }
.kinofilms.grid .t { padding: 6px 8px; font-size: 13px; }
@media (max-width: 400px) { .kinofilms.grid .kinoday { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
"""


if __name__ == "__main__":
    main()
