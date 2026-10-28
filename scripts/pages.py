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
BASE = "https://kaskjerda.no/"
TZ = ZoneInfo("Europe/Oslo")
SITE = "Skjer i Ålesund"
# Scener med færre arrangementer enn dette får ikke egen side (tynne sider hjelper ikke i søk)
VENUE_MIN = 3
# IndexNow: nøkkelen må ligge som <nøkkel>.txt på roten (se scripts/indexnow.py)
INDEXNOW_KEY = "7c1e5b0a9d3f4a62b8e0c4d71f2a9e65"
ROBOTS_META = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"
FRONT_TITLE = "Hva skjer i Ålesund? Konserter, standup og show | Skjer i Ålesund"
FRONT_DESC = "Hva skjer i Ålesund i dag og i helgen? Konserter, standup, show, barn og klubb med billettpriser. Oppdatert hver andre time. Ka skjer da?"
ICON_LINKS = ('<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">\n<link rel="icon" href="{up}favicon-48.png" type="image/png" sizes="48x48">\n'
              '<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">\n<link rel="manifest" href="{up}manifest.webmanifest">')
CAT_TEXT = {
    "konsert": "Konserter i Ålesund spenner fra symfoniorkester og kor til band, visesang og jazz. Oversikten henter dato, scene og billettpris fra arrangørenes egne billettsider, så du slipper å lete på flere steder.",
    "standup": "Standup og humor i Ålesund: turnerende komikere og lokale kvelder. Her ser du hvor og når det er show, og hva billettene koster.",
    "show": "Show, revy og teater i Ålesund. Se hva som går på scenene i byen, med datoer og billettpriser.",
    "barn": "Arrangementer for barn og familie i Ålesund, fra barneteater til familieforestillinger. Sjekk aldersanbefaling hos arrangøren.",
    "klubb": "Klubbkvelder og fest i Ålesund. Sjekk alltid aldersgrense og åpningstid hos arrangøren.",
    "happening": "Happenings, marked og andre arrangementer i Ålesund som ikke passer i de andre kategoriene, for eksempel festivaler og julemarked.",
    "quiz": "Pubquiz, musikkquiz, bingo og andre quizkvelder i Ålesund, samlet på ett sted. Datoer, klokkeslett og pris hentes fra arrangørenes egne sider.",
    "julebord": "Her er julebordene der også par, vennegjenger og små firma kan bestille plass: julebuffet, juletapas, dinnershow og julebord på fjorden. Dato og pris hentes fra hotellenes og scenenes egne sider; mangler prisen, står den hos arrangøren.",
    "sport": "Hjemmekamper for Aalesunds FK på Color Line Stadion, for både herrer og damer, med avspark og lenke til billetter.",
}
MONTH_PAGES = {}
JUL_NAV = False  # settes i main(): Jul i Ålesund vises i snarveiene fra 1. november

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
    "quiz": ("quiz", "Quiz i Ålesund", "Pubquiz og quizkvelder i Ålesund"),
    "julebord": ("julebord", "Julebord i Ålesund", "Julebord i Ålesund som alle kan bestille"),
    "sport": ("aafk-hjemmekamper", "AaFK-hjemmekamper", "Aalesunds hjemmekamper på Color Line Stadion"),
}
SEPARATE = {"julebord"}  # kategorier med bare egen side
CAT_LABEL = {"konsert": "Konsert", "standup": "Standup", "show": "Show", "barn": "Barn & familie", "klubb": "Klubb", "happening": "Happening", "quiz": "Quiz", "julebord": "Julebord", "sport": "Sport"}


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


# «Få billetter igjen» der kilden sier det (som few/fewHtml/showsHtml i index.html). Parken merker nesten alt,
# så deres merke vises bare de siste to ukene før forestillingen.
def few_ok(e, d):
    return e.get("statusSrc") != "parken" or (d - datetime.datetime.now(TZ).date()).days <= 14


def few_html(e):
    d = datetime.date.fromisoformat(e["date"])
    return '<span class="few">Få billetter igjen</span>' if e.get("few") and not e.get("soldOut") and not e.get("shows") and few_ok(e, d) else ""


def shows_html(e):
    today = datetime.datetime.now(TZ).date()
    rows = [(iso, st, datetime.date.fromisoformat(iso[:10])) for iso, st in e.get("shows") or []]
    rows = [r for r in rows if r[2] >= today]
    if len(rows) < 2:
        return ""
    one_day = len({r[2] for r in rows}) == 1
    out = []
    for iso, st, d in rows:
        t = iso[11:16]
        lab = escape(t if one_day else f"{d.day}. {MO[d.month - 1][:3]}" + (f" {t}" if t and t != e.get("time") else ""))
        if st == "sold":
            out.append(f'<span class="sold"><b>{lab}</b><small>utsolgt</small></span>')
        elif st == "few" and few_ok(e, d):
            out.append(f'<span class="fewt">{lab}<small>få igjen</small></span>')
        else:
            out.append(f"<span>{lab}</span>")
    return f'<div class="times">{"".join(out)}</div>'


def map_url(e):
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{e['venue']}, {e.get('address') or 'Ålesund'}")


def safe_url(u):
    return u if (u or "").startswith("https://") else ""


def event_ld(e):
    """schema.org/Event med bare felt vi har fra kilden (samme som forsiden lager med JavaScript)."""
    o = {
        "@type": "FoodEvent" if e.get("cat") == "julebord" else "Event",
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
    d = datetime.date.fromisoformat(e["date"])
    o["description"] = e.get("note") or f"{e['title']} på {e['venue']} i Ålesund {day_text(d, year=True)}" + (f" kl. {e['time']}." if e.get("time") else ".")
    if isinstance(e.get("priceMin"), (int, float)) and e["priceMin"] >= 0:
        o["offers"] = {"@type": "Offer", "url": safe_url(e.get("url")) or o["url"], "price": str(e["priceMin"]), "priceCurrency": "NOK",
                       "availability": "https://schema.org/SoldOut" if e.get("soldOut") else "https://schema.org/LimitedAvailability" if e.get("few") else "https://schema.org/InStock"}
        if e["priceMin"] == 0:
            o["isAccessibleForFree"] = True
    return o


def breadcrumb_ld(trail):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(trail, 1)]}


def facts_html(evs):
    """Kort, datadrevet tekst øverst på listesidene: unikt innhold for hver side, uten noe vi ikke har fra kildene."""
    if not evs:
        return ""
    n = len(evs)
    nxt = evs[0]
    d = datetime.date.fromisoformat(nxt["date"])
    parts = [f"{n} {'arrangement' if n == 1 else 'arrangementer'} i oversikten. Først ut er {nxt['title']} på {nxt['venue']} {day_text(d)}."]
    prices = [x["priceMin"] for x in evs if isinstance(x.get("priceMin"), (int, float)) and x["priceMin"] > 0]
    if prices:
        parts.append(f"Billettene starter på {min(prices)} kr.")
    top = {}
    for x in evs:
        top[x["venue"]] = top.get(x["venue"], 0) + 1
    if len(top) > 1:
        parts.append("Mest på " + ", ".join(f"{v} ({c})" for v, c in sorted(top.items(), key=lambda t: -t[1])[:3]) + ".")
    return f'<p class="facts">{escape(" ".join(parts))}</p>'


def ld_script(obj):
    # </ i JSON kan avslutte <script>-taggen for tidlig
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def page(path, title, description, body, ld=None, up=None, image=None, raw=False, head_extra="", body_class="", lang="nb"):
    """Hele HTML-dokumentet. path er relativ adresse, f.eks. «konserter/».
    up er veien tilbake til roten; 404-siden vises på vilkårlige adresser og bruker derfor full adresse.
    image er (adresse, bredde, høyde) for forhåndsvisningsbildet, ellers brukes logoen."""
    up = "../" * path.count("/") if up is None else up
    img, img_w, img_h = image or (BASE + "og-image.png", 1200, 630)
    url = BASE + path
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
{'<meta name="robots" content="noindex">' if path == "404.html" else f'<meta name="robots" content="{ROBOTS_META}">' + chr(10) + f'<link rel="canonical" href="{url}">'}
{ICON_LINKS.format(up=up)}
<meta property="og:type" content="website">
<meta property="og:locale" content="{"en_GB" if lang == "en" else "nb_NO"}">
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
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,800&family=Figtree:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap">
<link rel="stylesheet" href="{up}stil.css">
<script>try{{const q=new URLSearchParams(location.search).get("tema");if(q==="kveld"||q==="standard")localStorage.setItem("skjer-tema",q);if(q==="standard")localStorage.setItem("skjer-theme",'"light"');if(q){{const u=new URL(location.href);u.searchParams.delete("tema");history.replaceState(null,"",u)}}if(localStorage.getItem("skjer-tema")!=="standard"){{document.documentElement.dataset.tema="kveld";var m=document.querySelector('meta[name="theme-color"]');if(m)m.content="#0a171b";document.write('<link rel="stylesheet" href="{up}tema-kveld.css">')}}}}catch{{}}</script>
<script>try {{ const t = JSON.parse(localStorage.getItem("skjer-theme")); if (t === "light" || t === "dark") document.documentElement.dataset.theme = t; }} catch {{}}</script>
{ld_script(ld) if ld else ""}
{head_extra}
</head>
<body{f' class="{body_class}"' if body_class else ""}>
{body if raw else f'''<div class="wrap sub">
  <div class="topbar"><nav class="crumbs"><a href="{up}">← {SITE}: hele programmet</a></nav><div class="tsw" role="group" aria-label="Design"><button type="button" data-t="kveld"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>Mørkt</button><button type="button" data-t="standard"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>Lyst</button></div></div>
{body}
</div>'''}
<script>document.querySelectorAll(".tsw button").forEach(b=>{{b.setAttribute("aria-pressed",String((b.dataset.t==="kveld")===(document.documentElement.dataset.tema==="kveld")));b.onclick=()=>{{try{{localStorage.setItem("skjer-tema",b.dataset.t);if(b.dataset.t==="standard")localStorage.setItem("skjer-theme",'"light"')}}catch{{}}location.reload()}}}})</script>
<script>
// Besøksstatistikk med GoatCounter (uten informasjonskapsler), samme konto som forsiden
const gc = document.createElement("script"); gc.async = true; gc.src = "https://gc.zgo.at/count.js";
gc.dataset.goatcounter = "https://kaskjerda.goatcounter.com/count"; document.head.appendChild(gc);
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
        <div class="side"><span class="{price_cls}">{escape(price_text(e))}</span>{few_html(e)}</div>
        <div class="meta"><span class="tag">{CAT_LABEL[c]}</span>{f'<a class="venue" href="{up}{venue_path(e["venue"])}">' if venue_path(e["venue"]) else '<span>'}{escape(e['venue'])}{'</a>' if venue_path(e["venue"]) else '</span>'}{f'<span class="t">kl. {escape(e["time"])}</span>' if e.get("time") else ""}</div>
        {shows_html(e)}
        {f'<div class="note{" warn" if e.get("uncertain") else ""}">{escape(e["note"])}</div>' if e.get("note") else ""}
        {f'<div class="actions"><a class="link" href="{escape(u)}" target="_blank" rel="noopener">Billetter →</a></div>' if u else ""}
      </article>"""


def quiz_card(q, up):
    """Alle quizkvelder som ett kort i lista på forsiden (samme som quizHtml() i index.html)."""
    places = len({e["venue"] for e in q})
    prices = [e["priceMin"] for e in q if isinstance(e.get("priceMin"), (int, float)) and e["priceMin"] > 0]
    rows = ""
    for e in q[:3]:
        d = datetime.date.fromisoformat(e["date"])
        u = safe_url(e.get("url"))
        tag, attrs = ("a", f' href="{escape(u)}" target="_blank" rel="noopener"') if u else ("div", "")
        rows += f'<{tag}{attrs} class="qrow"><b>{d.day}. {MO[d.month - 1][:3]}</b><span>{escape(e["title"])} <small>{escape(e["venue"])}</small></span><small>{escape("Gratis" if e.get("priceMin") == 0 else e.get("price") or "")}</small></{tag}>'
    return f"""<article class="ev quizcard" style="--c:var(--c-quiz)">
        <h3><a class="title" href="{up}quiz/">Quiz i Ålesund</a></h3>
        <div class="side">{f'<span class="price">fra {min(prices)} kr</span>' if prices else ""}</div>
        <div class="meta"><span class="tag">Quiz</span><span>{places} {'sted' if places == 1 else 'steder'}</span><span class="t">{len(q)} {'kveld' if len(q) == 1 else 'kvelder'}</span></div>
        <div class="qrows">{rows}</div>
        <div class="actions"><a class="link" href="{up}quiz/">Alle quizkvelder →</a></div>
      </article>"""


def day_list(events, up, collapse_quiz=False):
    out, days = [], {}
    q = [e for e in events if e["cat"] == "quiz"] if collapse_quiz else []
    if len(q) < 2:
        q = []
    for e in events:
        if q and e["cat"] == "quiz" and e is not q[0]:
            continue
        days.setdefault(e["date"], []).append(e)
    for date, evs in days.items():
        d = datetime.date.fromisoformat(date)
        out.append(f"""<section class="day"><div class="date"><div class="wd">{WD[d.weekday()][:3]}</div><div class="num">{d.day}</div><div class="mo">{MO[d.month - 1][:3]}</div></div>
      <div class="events">{"".join(quiz_card(q, up) if q and e is q[0] else card(e, up) for e in evs)}</div></section>""")
    return "\n".join(out)


VENUE_PAGES = {}


def venue_path(v):
    return VENUE_PAGES.get(v)


def links_nav(up, current, extra):
    """Snarveier til de andre undersidene, så både folk og søkemotorer finner rundt."""
    items = [("i-dag/", "I dag"), ("i-morgen/", "I morgen"), ("denne-helgen/", "Denne helgen"), ("denne-uka/", "Neste 7 dager"), ("kino/", "Kino")] + [(p + "/", CAT_LABEL[k] if k != "sport" else "AaFK") for k, (p, _, _) in CATS.items() if k in extra]
    if JUL_NAV:
        items.insert(5, ("jul-i-alesund/", "Jul i Ålesund"))
    items += [(p, l) for l, p in MONTH_PAGES.items()]
    items += [(p, v) for v, p in VENUE_PAGES.items()]
    return '<nav class="more"><h2>Mer fra programmet</h2><div class="row">' + "".join(
        f'<a class="chip" href="{up}{p}"{" aria-current=\"page\"" if p == current else ""}>{escape(l)}</a>' for p, l in items) + "</div></nav>"


def listing(path, h1, lede, events, empty, cats_present, about="", lead=""):
    up = "../" * path.count("/")
    body = f"""  <header class="top">
    <h1>{escape(h1)}</h1>
    <p class="lede">{escape(lede)}</p>
    {f'<p class="lede">{escape(about)}</p>' if about else ""}
    {facts_html(events)}
  </header>
  {lead}
  <main>
{day_list(events, up) if events else f'<p class="empty">{escape(empty)}</p>'}
  </main>
  {links_nav(up, path, cats_present)}
  <footer><div>Programmet hentes automatisk flere ganger om dagen fra arrangørenes billettsider. Datoer og priser kan endres, så sjekk alltid hos arrangøren før du kjøper billett. <a href="{up}kontakt/">Kontakt og om siden</a></div></footer>"""
    return body


WEB3FORMS_KEY = "4fdbd7cb-a640-4982-a1f4-6fefbf772424"  # offentlig nøkkel: kan bare brukes til å sende til eieren


def kontakt_page():
    return f"""  <header class="top">
    <h1>Kontakt og om siden</h1>
    <p class="lede">Mangler det et arrangement, er noe feil, eller vil du bare si hei? Send en melding her.</p>
  </header>
  <main>
  <form id="kform" class="kform" action="https://api.web3forms.com/submit" method="post">
    <input type="hidden" name="access_key" value="{WEB3FORMS_KEY}">
    <input type="hidden" name="subject" value="Melding fra kaskjerda.no">
    <input type="hidden" name="from_name" value="kaskjerda.no">
    <input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off" style="display:none">
    <label>Hva gjelder det?
      <select name="Type" id="ktype">
        <option>Foreslå et arrangement</option>
        <option>Rapportere en feil</option>
        <option>Er du arrangør?</option>
        <option>Annet</option>
      </select></label>
    <div id="kevent">
      <label>Tittel på arrangementet <input name="Arrangement" maxlength="150"></label>
      <label>Dato og klokkeslett <input name="Dato" maxlength="100"></label>
      <label>Sted <input name="Sted" maxlength="100"></label>
      <label>Lenke til billetter eller mer info <input name="Lenke" type="url" placeholder="https://" maxlength="300"></label>
    </div>
    <label>Melding <textarea name="Melding" rows="5" maxlength="3000" required></textarea></label>
    <label>Navn (valgfritt) <input name="name" maxlength="100"></label>
    <label>E-post hvis du vil ha svar (valgfritt) <input name="email" type="email" maxlength="150"></label>
    <button class="btn" type="submit">Send</button>
    <p id="kstatus" class="small" role="status"></p>
  </form>
  <script>
  (function () {{
    const f = document.getElementById("kform"), st = document.getElementById("kstatus"), t = document.getElementById("ktype"), ev = document.getElementById("kevent");
    const sync = () => {{ ev.hidden = t.value !== "Foreslå et arrangement"; }};
    t.onchange = sync; sync();
    f.onsubmit = async e => {{
      e.preventDefault(); st.textContent = "Sender …";
      try {{
        const r = await fetch(f.action, {{ method: "POST", headers: {{ Accept: "application/json" }}, body: new FormData(f) }});
        const j = await r.json();
        if (!j.success) throw 0;
        f.reset(); sync(); st.textContent = "Takk! Meldingen er sendt.";
      }} catch {{ st.textContent = "Det gikk ikke å sende. Prøv igjen litt senere."; }}
    }};
  }})();
  </script>
  <section class="about">
    <h2>Om siden</h2>
    <p>Skjer i Ålesund samler konserter, standup, show, barnearrangementer, klubbkvelder og AaFK-hjemmekamper i Ålesund på ett sted, med billettpriser. Programmet hentes automatisk flere ganger om dagen fra Tikkio, Parken kulturhus, Dampsentralen, Fabrikken Kulturscene og AaFK, og enkelte arrangementer legges inn for hånd. Vi finner ikke på noe: alt kommer fra arrangørenes egne sider. Datoer og priser kan endres, så sjekk alltid hos arrangøren før du kjøper billett.</p>
    <p>Er du arrangør og mangler på siden? Send oss en lenke til arrangementet, så legger vi det inn.</p>
    <h2>Personvern</h2>
    <p>Skjemaet sender bare det du skriver til oss, via tjenesten Web3Forms, og vi bruker det kun til å svare deg eller rette opp i programmet. E-post og navn er valgfritt. Siden teller besøk med GoatCounter, som ikke bruker informasjonskapsler og ikke lagrer personopplysninger.</p>
  </section>
  </main>
  <footer><div>Programmet hentes automatisk flere ganger om dagen fra arrangørenes billettsider. Datoer og priser kan endres, så sjekk alltid hos arrangøren før du kjøper billett.</div></footer>"""


def quiz_week(evs, today):
    """Neste syv dager med en prikk der det er quiz."""
    cells = ""
    for i in range(7):
        d = today + datetime.timedelta(days=i)
        has = any(e["date"] == d.isoformat() or any(m[:10] == d.isoformat() for m in e.get("moreShows", [])) for e in evs)
        cells += f'<div{" class=\"q\"" if has else ""}>{WD[d.weekday()][:3]}<b>{d.day}</b>{"<i></i>" if has else ""}</div>'
    return f'<div class="qweek" aria-label="Neste syv dager, prikk der det er quiz">{cells}</div>'


def julemeny_html():
    """Julemeny på restaurant uten faste datoer (data/julebord.json), som en egen boks på julebord/. Bare tilbud med kildelenke."""
    f = ROOT / "data" / "julebord.json"
    items = json.loads(f.read_text()).get("julemeny", []) if f.exists() else []
    rows = "".join(f"""<li><a href="{escape(i['url'])}" target="_blank" rel="noopener"><b>{escape(i['name'])}</b></a> <span>{escape(i['venue'])}</span>
      <small>{escape(" · ".join(x for x in (i.get("period", ""), i.get("price") or "Pris hos arrangør") if x))}</small>{f"<p>{escape(i['note'])}</p>" if i.get("note") else ""}</li>""" for i in items)
    tips = '<p class="jbtips">Har du et julebord som alle kan bestille? <a href="../kontakt/">Tips oss</a>.</p>'
    return (f'<section class="julemeny"><h2>Julemeny på restaurant</h2><p>Hele førjulen, uten faste datoer: bestill bord direkte hos restauranten.</p><ul>{rows}</ul></section>' if rows else "") + tips


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

OSLO_TZ = """BEGIN:VTIMEZONE
TZID:Europe/Oslo
BEGIN:STANDARD
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
END:DAYLIGHT
END:VTIMEZONE"""


def ics_text(s):
    return re.sub(r"[\\;,]", lambda m: "\\" + m.group(0), str(s or "")).replace("\r", "").replace("\n", "\\n")


def ics_fold(line):
    """Maks 75 byte per linje (RFC 5545), brutt mellom tegn."""
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode()) > (75 if not out else 74):
            out.append(cur)
            cur = ch
        else:
            cur += ch
    out.append(cur)
    return "\r\n ".join(out)


def build_ics(name, events, today):
    """Abonnerbar kalenderfil med kommende arrangementer, én hendelse per dag og visning."""
    end = today + datetime.timedelta(days=366)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Skjer i Ålesund//NB", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{ics_text(name)}", "X-WR-TIMEZONE:Europe/Oslo", "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
             "X-PUBLISHED-TTL:PT12H", *OSLO_TZ.split("\n")]
    for e in events:
        for o in occurrences([e], today, end):
            d = o["date"].replace("-", "")
            for t in (o["time"].split(" og ") if o["time"] else [""]):
                if re.fullmatch(r"\d{1,2}:\d{2}", t):
                    hh, mm = map(int, t.split(":"))
                    s0 = datetime.datetime.strptime(o["date"], "%Y-%m-%d").replace(hour=hh, minute=mm)
                    times = [f"DTSTART;TZID=Europe/Oslo:{s0:%Y%m%dT%H%M%S}",
                             f"DTEND;TZID=Europe/Oslo:{s0 + datetime.timedelta(hours=2):%Y%m%dT%H%M%S}"]
                else:
                    nxt = datetime.date.fromisoformat(o["date"]) + datetime.timedelta(days=1)
                    times = [f"DTSTART;VALUE=DATE:{d}", f"DTEND;VALUE=DATE:{nxt:%Y%m%d}"]
                url = e.get("url") if str(e.get("url", "")).startswith("https://") else ""
                desc = "\n".join(x for x in [e.get("note"), e.get("price") and "Pris: " + e["price"], url] if x)
                lines += ["BEGIN:VEVENT", f"UID:{e['id']}-{o['date']}-{t.replace(':', '')}@skjer-i-alesund", f"DTSTAMP:{stamp}", *times,
                          f"SUMMARY:{ics_text(e['title'])}", f"LOCATION:{ics_text(e['venue'] + ', Ålesund')}",
                          f"DESCRIPTION:{ics_text(desc)}", *([f"URL:{url}"] if url else []), "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(ics_fold(l) for l in lines) + "\r\n"


# --- Jul i Ålesund (sesongside) ---
JUL_PREFIXES = ("jul", "advent", "nøtteknekk", "lucia", "romjul", "nisse", "tomte", "christmas")
JUL_NOT = {"juli", "julie", "julia", "julian", "julius"}


def jul_config():
    f = ROOT / "data" / "jul.json"
    return json.loads(f.read_text()) if f.exists() else {}


def is_jul(e, cfg):
    """Julearrangement: ord i tittel eller notat som begynner på jul/advent osv., eller satt for hånd i data/jul.json."""
    if e["id"] in cfg.get("exclude", []):
        return False
    if e["id"] in cfg.get("include", []):
        return True
    words = re.findall(r"[a-zæøå]+", f"{e['title']} {e.get('note') or ''}".lower())
    return any(w.startswith(JUL_PREFIXES) and w not in JUL_NOT for w in words)


# Julesider etter tema (adresse, overskrift, tekst, utvalg). Lages bare med minst JUL_THEME_MIN arrangementer, og hvert år med årstall i tittelen.
JUL_THEME_MIN = 3
JUL_THEMES = [
    ("julekonserter-i-alesund/", "Julekonserter i Ålesund", "Julekonserter og adventskonserter i Ålesund: kor, symfoniorkester, viser og turnerende artister i kirker, konsertsaler og på klubbscener. Datoer og billettpriser hentes fra arrangørenes egne sider.",
     lambda e, jul: jul and e["cat"] == "konsert"),
    ("jul-for-barn-i-alesund/", "Jul for barn og familie i Ålesund", "Juleverksted, familiedager, julekonserter og familiejulebord i Ålesund for store og små. Sjekk aldersanbefaling hos arrangøren.",
     lambda e, jul: jul and (e["cat"] == "barn" or bool(re.search(r"\bbarn|familie|nisse|juleverksted", f"{e['title']} {e.get('note') or ''}".lower())))),
    ("julemarked-i-alesund/", "Julemarked og juleverksted i Ålesund", "Julemarked, julemesser og juleverksted i Ålesund, med datoer og sted.",
     lambda e, jul: bool(re.search(r"julemarked|julemesse|juleverksted|julebasar", f"{e['title']} {e.get('note') or ''}".lower()))),
    ("romjul-og-nyttar-i-alesund/", "Romjul og nyttår i Ålesund", "Hva skjer i Ålesund i romjulen og på nyttårsaften? Konserter, dans og fest fra 2. juledag til nyttår, med datoer og billettpriser.",
     None),  # alt fra 26. desember til 1. januar, se jul_theme_events()
]


def jul_theme_events(events, today, cfg):
    """{adresse: (overskrift, tekst, arrangementer)} for temasidene som har nok arrangementer."""
    out = {}
    for path, h1, about, pick in JUL_THEMES:
        if pick is None:
            evs = occurrences([e for e in events if e["cat"] not in SEPARATE], datetime.date(today.year, 12, 26), datetime.date(today.year + 1, 1, 1))
        else:
            evs = [e for e in events if pick(e, is_jul(e, cfg))]
        if len(evs) >= JUL_THEME_MIN:
            out[path] = (h1, about, evs)
    return out


def jul_links(up, current, themes):
    """«Mer jul i Ålesund»: lenker mellom julesiden, julebordsiden og temasidene."""
    items = [("jul-i-alesund/", "Jul i Ålesund"), ("julebord/", "Julebord")] + [(p, h1.replace(" i Ålesund", "")) for p, (h1, _, _) in themes.items()]
    return '<nav class="more julx"><h2>Mer jul i Ålesund</h2><div class="row">' + "".join(
        f'<a class="chip" href="{up}{p}"{" aria-current=\"page\"" if p == current else ""}>{escape(l)}</a>' for p, l in items) + "</div></nav>"


def julebord_facts(evs, year):
    """Kort svar på «hva koster julebord i Ålesund?», regnet ut fra julebordene vi har."""
    prices = sorted(e["priceMin"] for e in evs if isinstance(e.get("priceMin"), (int, float)) and e["priceMin"] > 0)
    if not prices:
        return ""
    venues = len({e["venue"] for e in evs})
    return (f'<p class="lede jbfacts"><b>Hva koster julebord i Ålesund i {year}?</b> Julebordene vi har funnet koster fra {prices[0]} til {prices[-1]} kr per person, '
            f'fordelt på {venues} steder. Prisen står på hvert julebord; der den mangler, får du den hos hotellet eller restauranten.</p>')


def jul_card(e, up, more=()):
    """Ett kort per arrangement; flere forestillinger står som «Flere datoer» i stedet for egne kort."""
    c = e["cat"] if e["cat"] in CAT_LABEL else "happening"
    pm = e.get("priceMin")
    dates = [f"{int(x['date'][8:])}. {MO[int(x['date'][5:7]) - 1][:3]}" for x in more]
    more_html = (f'<div class="jmore">Flere datoer: {", ".join(dates[:4])}' + (f" og {len(dates) - 4} til" if len(dates) > 4 else "") + "</div>") if dates else ""
    return (f'<article class="jc" style="--c:var(--c-{c})" data-cat="{c}" data-min="{pm if isinstance(pm, (int, float)) else ""}">'
            f'<h3><a href="{up}arrangement/{e["id"]}/">{escape(e["title"])}</a></h3>'
            f'<div class="jm">{escape(e["venue"])}{" · kl. " + e["time"] if e.get("time") else ""}</div>'
            f'<div class="jp">{escape(price_text(e))}</div>{more_html}</article>')


def jul_page(events, today, themes=None):
    """jul-i-alesund/: liste med julearrangementene, med filter. Returnerer (html, antall) eller None uten arrangementer."""
    cfg = jul_config()
    year = today.year
    up = "../"
    jul_events = [e for e in events if is_jul(e, cfg) and e["cat"] not in SEPARATE]  # julebord har egen side, se jb_html
    occ = occurrences(jul_events, today, datetime.date(year, 12, 31))
    jb = [e for e in events if e["cat"] == "julebord"]
    jb_prices = [e["priceMin"] for e in jb if isinstance(e.get("priceMin"), (int, float)) and e["priceMin"] > 0]
    jb_html = (f'<a class="jul-jb" href="{up}julebord/">🎄 <b>{len(jb)} julebord i Ålesund</b>{f" fra {min(jb_prices)} kr" if jb_prices else ""}: hoteller, restauranter og dinnershow →</a>'
               if jb else "")
    if not occ:
        return None
    by_id = {}
    for e in occ:
        by_id.setdefault(e["id"], []).append(e)
    by_day = {}
    for shows in by_id.values():  # første dato for hvert arrangement, resten som «Flere datoer»
        by_day.setdefault(shows[0]["date"], []).append(shows)
    by_day = dict(sorted(by_day.items()))
    rows = ""
    for date, evs in by_day.items():
        d = datetime.date.fromisoformat(date)
        rows += (f'<div class="jrow" id="r-{date}" data-date="{date}"><div class="jdt"><small>{WD[d.weekday()][:3]}</small><b>{d.day}</b><small>{MO[d.month - 1][:3]}</small></div>'
                 f'<div class="jcards">{"".join(jul_card(shows[0], up, shows[1:]) for shows in evs)}</div></div>')
    cd = (datetime.date(year, 12, 24) - today).days
    cd_html = f'<div class="jcd"><b id="jul-days">{cd}</b><span>dager til<br>julaften</span></div>' if cd > 0 else ""
    garland = '<div class="jgar" aria-hidden="true"><i class="w"></i><i class="a"></i><i class="b"></i></div>'
    n_ev = len(by_id)
    body = f"""<div class="jul-hero"><div class="snow"></div><div class="snow2"></div>{garland}
  <a class="jul-back" href="{up}">← {SITE}</a>
  <small>Ålesund · julen {year}</small><h1>Jul i Ålesund</h1>
  <p>Julekonserter, juleshow, adventskonserter og julemarked i Ålesund, samlet på ett sted med datoer og billettpriser.</p>{cd_html}</div>
<main class="jul-main">
  {jb_html}
  <section class="jlist"><div class="jhd"><h2>Alle julearrangementer</h2><div class="jchips" id="jchips">
    <button type="button" class="chip" data-c="konsert" aria-pressed="false">Konsert</button><button type="button" class="chip" data-c="standup,show" aria-pressed="false">Standup og show</button><button type="button" class="chip" data-c="happening" aria-pressed="false">Marked og verksted</button><button type="button" class="chip" data-p="350" aria-pressed="false">Under 350 kr</button></div></div>
  <div class="jcnt" id="jcnt">{n_ev} arrangementer</div>{rows}</section>
  <p class="jul-note">Programmet hentes automatisk fra arrangørenes billettsider og oppdateres flere ganger om dagen. Datoer og priser kan endres, så sjekk alltid hos arrangøren før du kjøper billett. Savner du et julearrangement? <a href="{up}kontakt/">Gi beskjed</a>.</p>
  {jul_links(up, "jul-i-alesund/", themes or {})}
  {links_nav(up, "jul-i-alesund/", {e["cat"] for e in events})}
</main>
<script>
(function () {{
  document.documentElement.classList.add("js");
  var cnt = document.getElementById("jcnt"), rows = [].slice.call(document.querySelectorAll(".jrow"));
  var cd = document.getElementById("jul-days");
  if (cd) {{ var t = new Date(), n = Math.ceil((new Date(t.getFullYear(), 11, 24) - new Date(t.getFullYear(), t.getMonth(), t.getDate())) / 864e5); if (n > 0) cd.textContent = n; }}
  var on = {{ c: null, p: null }};
  document.getElementById("jchips").addEventListener("click", function (e) {{
    var b = e.target.closest("button"); if (!b) return; var was = b.getAttribute("aria-pressed") === "true";
    [].forEach.call(this.querySelectorAll("button"), function (x) {{ if (x.dataset.c && b.dataset.c) x.setAttribute("aria-pressed", "false"); }});
    b.setAttribute("aria-pressed", String(!was));
    on.c = null; on.p = null;
    [].forEach.call(this.querySelectorAll("button[aria-pressed=true]"), function (x) {{ if (x.dataset.c) on.c = x.dataset.c.split(","); if (x.dataset.p) on.p = +x.dataset.p; }});
    var shown = 0;
    rows.forEach(function (r) {{
      var any = 0;
      [].forEach.call(r.querySelectorAll(".jc"), function (c) {{
        var ok = (!on.c || on.c.indexOf(c.dataset.cat) > -1) && (!on.p || (c.dataset.min !== "" && +c.dataset.min <= on.p));
        c.hidden = !ok; if (ok) any++;
      }});
      r.hidden = !any; shown += any;
    }});
    cnt.textContent = shown + " arrangementer";
  }});
}})();
</script>"""
    title = f"Jul i Ålesund {year}: julekonserter, juleshow og julemarked | {SITE}"
    desc = describe(occ, f"Jul i Ålesund {year}: julekonserter, juleshow og julemarked")
    ld = {"@context": "https://schema.org", "@graph": [breadcrumb_ld([(SITE, BASE), (f"Jul i Ålesund {year}", BASE + "jul-i-alesund/")])] + [event_ld(e) for e in occ]}
    head_extra = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,700;1,400;1,700&display=swap">'
    return page("jul-i-alesund/", title, desc, body, ld, raw=True, head_extra=head_extra, body_class="jul"), n_ev


def describe(events, what):
    n = len(events)
    if not n:
        return f"{what}. Oversikt med billettpriser, oppdatert flere ganger om dagen."
    uniq = list(dict.fromkeys(e["title"] for e in events))
    names = ", ".join(uniq[:3])
    return f"{n} {'arrangement' if n == 1 else 'arrangementer'}: {names}{' med flere' if len(uniq) > 3 else ''}. {what}, med billettpriser, oppdatert flere ganger om dagen."[:300]


def front_html(src, events, today, extra_links=()):
    """Forsiden bygger lista med JavaScript. Her legges de neste ukene også inn som vanlig HTML og JSON-LD,
    så søkemotorer og delingstjenester ser innholdet uten å kjøre scriptet. Scriptet bytter ut lista når programmet er hentet."""
    h = src
    def sub(pattern, repl, count=1):
        nonlocal h
        new, n = re.subn(pattern, lambda _: repl, h, count=count)
        assert n, pattern
        h = new
    sub(r"<title>[^<]*</title>", f"<title>{escape(FRONT_TITLE)}</title>")
    sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{escape(FRONT_DESC)}">')
    sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{escape(FRONT_TITLE)}">')
    sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{escape(FRONT_DESC)}">')
    sub(r'<link rel="icon" href="data:[^"]*">', ICON_LINKS.format(up=""))
    graph = [
        {"@type": "WebSite", "@id": BASE + "#website", "url": BASE, "name": SITE, "alternateName": ["Ka skjer da?", "kaskjerda.no"], "inLanguage": "nb-NO", "description": FRONT_DESC},
        {"@type": "Organization", "@id": BASE + "#org", "name": SITE, "url": BASE, "logo": {"@type": "ImageObject", "url": BASE + "icon-512.png", "width": 512, "height": 512}},
    ] + [event_ld(e) for e in occurrences(events, today, today + datetime.timedelta(days=30))]
    head_extra = (f'<meta name="robots" content="{ROBOTS_META}">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                  + ld_script({"@context": "https://schema.org", "@graph": graph}).replace('<script type="application/ld+json">', '<script type="application/ld+json" id="ld-front">', 1))
    sub(r"</head>", head_extra + "\n</head>")
    if extra_links:  # julesidene i snarveiene nederst, så Google finner dem fra forsiden
        sub(r'<a href="kontakt/">Kontakt</a></nav>', "".join(f'<a href="{p}">{escape(l)}</a> · ' for p, l in extra_links) + '<a href="kontakt/">Kontakt</a></nav>')
    soon = occurrences(events, today, today + datetime.timedelta(days=45))
    sub(r'<main id="list"></main>', f'<main id="list">\n{day_list(soon, "", collapse_quiz=True)}\n  </main>')
    return h


def main():
    data = json.loads((ROOT / "data" / "events.json").read_text())
    today = datetime.datetime.now(TZ).date()
    all_events = [e for e in data["events"] if e["date"] >= today.isoformat()]
    all_events.sort(key=lambda e: (e["date"], e.get("time") or "99"))
    # Julebord har egen side og er ikke med i lister, dager, måneder, scener eller helgeposten (som kino)
    events = [e for e in all_events if e["cat"] not in SEPARATE]
    updated = (data.get("meta", {}).get("updatedAt") or today.isoformat())[:10]

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    # Forsiden og det den trenger, kopiert som de er
    shutil.copy(ROOT / "og-image.png", OUT / "og-image.png")
    for f in ("favicon-48.png", "icon-192.png", "icon-512.png", "apple-touch-icon.png"):
        shutil.copy(ROOT / f, OUT / f)
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n")
    (OUT / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY)
    (OUT / "manifest.webmanifest").write_text(json.dumps({
        "name": SITE, "short_name": "Ka skjer da?", "description": FRONT_DESC, "lang": "nb", "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#eef3f2", "theme_color": "#c8432b",
        "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}]},
        ensure_ascii=False, indent=2))
    (OUT / "CNAME").write_text("kaskjerda.no\n")
    (OUT / "data").mkdir()
    shutil.copy(ROOT / "data" / "events.json", OUT / "data" / "events.json")
    if (ROOT / "data" / "kino.json").exists():
        shutil.copy(ROOT / "data" / "kino.json", OUT / "data" / "kino.json")
    cfg = jul_config()
    themes = jul_theme_events(all_events, today, cfg)
    has_jul = any(is_jul(e, cfg) for e in all_events)
    extra = ([("jul-i-alesund/", "Jul i Ålesund")] if has_jul else []) + ([("julebord/", "Julebord")] if any(e["cat"] == "julebord" for e in all_events) else []) \
        + [(p, h1.replace(" i Ålesund", "")) for p, (h1, _, _) in themes.items()]
    index = (ROOT / "index.html").read_text()
    (OUT / "index.html").write_text(front_html(index, events, today, extra))
    # Undersidene bruker samme stil og ikon som forsiden, hentet rett fra index.html
    css = re.search(r"<style>(.*?)</style>", index, re.S).group(1)
    (OUT / "stil.css").write_text(css + SUB_CSS)
    (OUT / "tema-kveld.css").write_text((ROOT / "tema-kveld.css").read_text())
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
    cats_present = {e["cat"] for e in all_events}
    pages = []  # (adresse, endret)
    global JUL_NAV
    JUL_NAV = (today.month, today.day) >= (11, 1) and today.month != 1
    MONTH_PAGES.clear()
    months = []
    y, m = today.year, today.month
    for _ in range(8):
        first = max(datetime.date(y, m, 1), today)
        last = (datetime.date(y + (m == 12), m % 12 + 1, 1) - datetime.timedelta(days=1))
        evs_m = occurrences(events, first, last)
        if len(evs_m) >= 6:
            months.append((y, m, evs_m))
            MONTH_PAGES[f"{MO[m - 1].capitalize()} {y}"] = f"maned/{MO[m - 1]}-{y}/"
        y, m = y + (m == 12), m % 12 + 1

    def listing_page(path, title, h1, lede, evs, empty, what, image=None, about="", lead=""):
        write(path, page(path, title, describe(evs, what), listing(path, h1, lede, evs, empty, cats_present, about, lead),
                         {"@context": "https://schema.org", "@graph": [breadcrumb_ld([(SITE, BASE), (h1, BASE + path)])] + [event_ld(e) for e in evs]}, image=image))
        pages.append((path, updated))

    # I dag
    tod = occurrences(events, today, today)
    listing_page("i-dag/", f"Hva skjer i Ålesund i dag? {day_text(today).capitalize()} | {SITE}", "Skjer i Ålesund i dag",
                 f"Konserter, standup, show og andre arrangementer i Ålesund {day_text(today)}.", tod,
                 "Vi har ingen arrangementer registrert i dag. Se hva som skjer i helgen eller i hele programmet.",
                 "Hva skjer i Ålesund i dag")

    tomorrow = today + datetime.timedelta(days=1)
    listing_page("i-morgen/", f"Hva skjer i Ålesund i morgen? {day_text(tomorrow).capitalize()} | {SITE}", "Skjer i Ålesund i morgen",
                 f"Konserter, standup, show og andre arrangementer i Ålesund {day_text(tomorrow)}.", occurrences(events, tomorrow, tomorrow),
                 "Vi har ingen arrangementer registrert i morgen. Se hva som skjer i helgen eller i hele programmet.", "Hva skjer i Ålesund i morgen")
    week7 = today + datetime.timedelta(days=6)
    listing_page("denne-uka/", f"Hva skjer i Ålesund de neste 7 dagene? {range_text(today, week7)} | {SITE}", "Skjer i Ålesund de neste 7 dagene",
                 f"Alt vi har funnet i Ålesund {range_text(today, week7)}: konserter, standup, show, barn og klubb, med billettpriser.", occurrences(events, today, week7),
                 "Vi har ingen arrangementer registrert de neste dagene ennå.", "Hva skjer i Ålesund de neste 7 dagene")
    for y, m, evs_m in months:
        mo = MO[m - 1]
        listing_page(f"maned/{mo}-{y}/", f"Hva skjer i Ålesund i {mo} {y}? Konserter, standup og show | {SITE}", f"Hva skjer i Ålesund i {mo} {y}",
                     f"Konserter, standup, show, barn og klubb i Ålesund i {mo} {y}, med datoer og billettpriser.", evs_m, "", f"Hva skjer i Ålesund i {mo} {y}")

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
        evs = [e for e in all_events if e["cat"] == k]
        if k == "julebord":
            listing_page(p + "/", f"Julebord i Ålesund {today.year}: alle julebord med pris og dato | {SITE}", f"Julebord i Ålesund {today.year}",
                         f"{len(evs)} julebord med dato og pris per person, og julemenyer på restaurant.",
                         evs, "Ingen julebord registrert akkurat nå. Julebordene for neste sesong kommer i oktober.", f"Julebord i Ålesund {today.year}",
                         about=CAT_TEXT[k], lead=julebord_facts(evs, today.year) + julemeny_html() + jul_links("../", p + "/", themes))
            continue
        listing_page(p + "/", f"{h1} – program og billettpriser | {SITE}", h1,
                     f"{what}: {len(evs)} kommende {'arrangement' if len(evs) == 1 else 'arrangementer'}, " + ("med avspark og billettlenker." if k == "sport" else "med datoer og billettpriser."),
                     evs, f"Ingen kommende arrangementer i denne kategorien akkurat nå. Se hele programmet.", what, about=CAT_TEXT.get(k, ""),
                     lead=quiz_week(evs, today) if k == "quiz" else julemeny_html() if k == "julebord" else "")

    for v, p in VENUE_PAGES.items():
        evs = [e for e in events if e["venue"] == v]
        listing_page(p, f"{v} – program og billetter | {SITE}", f"Program for {v}",
                     f"Kommende arrangementer på {v}{', ' + evs[0]['address'] if evs[0].get('address') else ', Ålesund'}, med datoer og billettpriser.",
                     evs, "", f"Program for {v} i Ålesund",
                     about=f"{v} er en av scenene i Ålesund. Oversikten viser kommende arrangementer med dato, klokkeslett og billettpris, hentet fra arrangørens egne sider.")

    for e in all_events:
        path = f"arrangement/{e['id']}/"
        write(path, event_page(e, all_events if e["cat"] in SEPARATE else events, path))
        pages.append((path, (e.get("addedAt") or updated)[:10]))

    # Kalenderabonnement: kalender/alle.ics og én per kategori
    (OUT / "kalender").mkdir()
    feeds = {"alle": ("Skjer i Ålesund", events)}
    for k, (p, h1, _) in CATS.items():
        feeds[p] = (f"Skjer i Ålesund: {h1}", [e for e in all_events if e["cat"] == k])
    for fname, (cal_name, evs) in feeds.items():
        (OUT / "kalender" / f"{fname}.ics").write_text(build_ics(cal_name, evs, today))

    for p, (h1, about, evs) in themes.items():
        year = today.year
        listing_page(p, f"{h1} {year}: datoer og billetter | {SITE}", f"{h1} {year}",
                     f"{len(evs)} {'arrangement' if len(evs) == 1 else 'arrangementer'} med datoer og billettpriser, oppdatert flere ganger om dagen.",
                     evs, "", f"{h1} {year}", about=about, lead=jul_links("../", p, themes))
    jp = jul_page(all_events, today, themes)
    if jp:
        write("jul-i-alesund/", jp[0])
        pages.append(("jul-i-alesund/", updated))
        print(f"Jul i Ålesund: {jp[1]} arrangementer", file=sys.stderr)

    # Kino ligger på egen side og er ikke med i lister, kategorier eller helgeposten på bildet
    kino_meta, kino_films = load_kino(today)
    write("kino/", page("kino/", f"Kinoprogram ODEON Ålesund: hva går på kino? | {SITE}", "Hva går på kino i Ålesund? Program, plakater og visningstider for ODEON Ålesund (Amfi Moa).",
                        kino_page(kino_films, kino_meta, today)))
    pages.append(("kino/", (kino_meta.get("updatedAt") or updated)[:10]))

    write("en/", en_page(events, today))
    pages.append(("en/", updated))

    write("kontakt/", page("kontakt/", f"Kontakt og om siden | {SITE}", "Kontakt Skjer i Ålesund: foreslå et arrangement, rapporter en feil eller si hei. Om siden og personvern.", kontakt_page()))
    pages.append(("kontakt/", updated[:10]))

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


# Engelsk side (en/) for turister, cruisegjester og andre som søker på engelsk. Titler står som hos arrangøren;
# datoer, kategorier, priser og forklaringer er på engelsk. Siden er statisk HTML for søkemotorer, og et lite
# script setter «Today & tonight» / «Tomorrow» og skjuler dager som er over, så den stemmer selv om den ikke er bygget i dag.
EN_LANG = "faq"  # Eieren valgte «faq» 27. okt. «Mostly in Norwegian» for standup og show: "card" (på kortet), "faq" (bare under Good to know), "none"
EN_DAYS = 14
EN_CAT = {"konsert": "Concert", "standup": "Comedy", "show": "Show & theatre", "barn": "Kids & family", "klubb": "Club night",
          "happening": "Culture & events", "quiz": "Quiz & bingo", "sport": "Football", "julebord": "Christmas party"}
EN_CATS = {"konsert": ("concert", "concerts"), "standup": ("comedy show", "comedy shows"), "show": ("show", "shows"), "barn": ("family event", "family events"),
           "klubb": ("club night", "club nights"), "happening": ("culture event", "culture events"), "quiz": ("quiz night", "quiz nights"), "sport": ("football match", "football matches")}
EN_NORWEGIAN = {"standup", "show"}
EN_WD = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
EN_MO = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
HREFLANG = (f'<link rel="alternate" hreflang="nb" href="{BASE}">\n<link rel="alternate" hreflang="en" href="{BASE}en/">\n'
            f'<link rel="alternate" hreflang="x-default" href="{BASE}">')


def en_day(d, weekday=True):
    return (f"{EN_WD[d.weekday()]} " if weekday else "") + f"{d.day} {EN_MO[d.month - 1]}"


def en_price(e):
    if e.get("soldOut"):
        return "Sold out"
    if e.get("priceMin") == 0:
        return "Free"
    if e.get("price"):
        return "NOK " + re.sub(r"\s*kr\b", "", e["price"]).strip()
    return ""


def en_row(e, lang_mark, day=None):
    u = safe_url(e.get("url"))
    c = e["cat"] if e["cat"] in EN_CAT else "happening"
    pr = en_price(e)
    d = datetime.date.fromisoformat(e["date"])
    few = e.get("few") and not e.get("soldOut") and few_ok(e, d)
    times = (e.get("time") or "").replace(" og ", " & ")
    title = f'<a href="{escape(u)}" target="_blank" rel="noopener">{escape(e["title"])}</a>' if u else escape(e["title"])
    no = '<span class="nob">Mostly in Norwegian</span>' if lang_mark == "card" and c in EN_NORWEGIAN else ""
    return f"""<div class="enrow" style="--c:var(--c-{c})"><b class="tm">{escape(day or times or "–").replace(" &amp; ", "<br>")}</b>
      <span><span class="tt">{title}</span><small>{EN_CAT[c]} · {escape(e["venue"])}{f" · {escape(times)}" if day and times else ""}</small>{no}</span>
      <span class="pr">{f'<em class="{"sold" if e.get("soldOut") else ""}">{escape(pr)}</em>' if pr else '<em class="unk">See organiser</em>'}{'<span class="few">Few tickets left</span>' if few else ""}</span></div>"""


def en_page(events, today, lang_mark=EN_LANG, path="en/"):
    end = today + datetime.timedelta(days=EN_DAYS - 1)
    occ = [e for e in occurrences(events, today, end)]
    days = {}
    for e in occ:
        days.setdefault(e["date"], []).append(e)
    n = len(occ)
    counts = {}
    for e in occ:
        counts[e["cat"]] = counts.get(e["cat"], 0) + 1
    parts = [f"{c} {EN_CATS[k][c != 1]}" for k, c in sorted(counts.items(), key=lambda t: -t[1]) if k in EN_CATS][:4]
    prices = [e["priceMin"] for e in occ if isinstance(e.get("priceMin"), (int, float)) and e["priceMin"] > 0]
    venues = {}
    for e in occ:
        venues[e["venue"]] = venues.get(e["venue"], 0) + 1
    top_venues = [v for v, _ in sorted(venues.items(), key=lambda t: -t[1])[:2]]
    facts = (f"{n} events in the next two weeks: {', '.join(parts[:-1])} and {parts[-1]}." if len(parts) > 1 else f"{n} events in the next two weeks.") \
        + (f" Tickets from NOK {min(prices)}." if prices else "") + (f" Most at {' and '.join(top_venues)}." if top_venues else "")
    title = "What's on in Ålesund this week: concerts, comedy & events"
    desc = f"{n} events in Ålesund, Norway in the next two weeks: concerts, comedy, family events and nightlife" \
        + (f" at {' and '.join(top_venues)}" if top_venues else "") + ". Ticket prices and links, updated every two hours."

    wk_start, wk_end = weekend_range(today)
    blocks = []
    for date, evs in days.items():
        d = datetime.date.fromisoformat(date)
        wk = ' data-weekend="1"' if wk_start <= d <= wk_end else ""
        blocks.append(f"""<section class="enday" data-date="{date}"{wk}><h2><span class="rel"></span>{en_day(d)}</h2>
      {"".join(en_row(e, lang_mark) for e in evs)}</section>""")
    daytime = [e for e in occurrences(events, today, today + datetime.timedelta(days=6)) if re.match(r"\d{2}:\d{2}", e.get("time") or "") and e["time"] < "17:00"]
    day_html = "".join(f'<div data-date="{e["date"]}">{en_row(e, lang_mark, day=f"{EN_WD[datetime.date.fromisoformat(e["date"]).weekday()][:3]} {datetime.date.fromisoformat(e["date"]).day}")}</div>' for e in daytime)

    faq = [("Where do I buy tickets?", "Each event links to the organiser's own ticket page (Tikkio, Parken, Billetto and others). The pages are mostly in Norwegian: look for «Kjøp billett» (buy ticket) or «Billetter» (tickets)."),
           ("What does «Few tickets left» mean?", "The ticket page says there are only a few tickets left («Få billetter igjen»). «Sold out» means the organiser has marked it as sold out («Utsolgt»).")]
    if lang_mark != "none":
        faq.insert(1, ("Are the events in English?", "Concerts need no translation. Comedy and theatre are mostly in Norwegian. Check the organiser's page if you are unsure."))
    faq += [("Is anything free?", "Some events are free. They are marked «Free». Others show the ordinary ticket price in Norwegian kroner (NOK)."),
            ("How up to date is this?", "The list is updated every two hours from the organisers' own pages. Dates and prices can change, so always check with the organiser before you buy."),
            ("Is there a cinema in Ålesund?", "Yes, ODEON Ålesund at Amfi Moa. The programme is under «Cinema» below (page in Norwegian).")]
    faq_html = "".join(f'<details{" open" if i == 0 else ""}><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for i, (q, a) in enumerate(faq))

    up = "../"
    body = f"""<div class="wrap sub en">
  <div class="topbar"><nav class="crumbs"><a href="{up}">Skjer i Ålesund</a></nav><div class="topr"><a class="langbtn" href="{up}" hreflang="nb" lang="nb" aria-label="Norsk" id="langbtn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/></svg><span class="ll">Norsk</span><span class="ls">NO</span></a><div class="tsw" role="group" aria-label="Theme"><button type="button" data-t="kveld" aria-label="Dark"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg><span class="tl">Dark</span></button><button type="button" data-t="standard" aria-label="Light"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg><span class="tl">Light</span></button></div></div></div>
  <header class="top">
    <h1>What's on in Ålesund</h1>
    <p class="lede">Concerts, comedy, family events and nightlife in Ålesund, Norway, with ticket prices. Updated every two hours from the organisers' own pages.</p>
    <p class="facts">{escape(facts)}</p>
    <nav class="jump"><a href="#days">This week</a><a href="#daytime">In town for the day?</a><a href="#faq">Good to know</a></nav>
  </header>
  <main id="days">
{chr(10).join(blocks) if blocks else '<p class="empty">No events listed for the next two weeks yet. Check back soon.</p>'}
  </main>
  {f'<section class="daytime" id="daytime"><h2>In town for the day?</h2><p>Daytime events in the next week (before 5 pm):</p>{day_html}</section>' if daytime else ""}
  <section class="faq" id="faq"><h2>Good to know</h2>{faq_html}</section>
  <nav class="more"><h2>More (pages in Norwegian)</h2><div class="row"><a class="chip" href="{up}kino/">Cinema</a><a class="chip" href="{up}jul-i-alesund/">Christmas in Ålesund</a><a class="chip" href="{up}julebord/">Christmas parties (julebord)</a><a class="chip" href="{up}denne-helgen/">This weekend</a><a class="chip" href="{up}">Full programme</a></div></nav>
  <footer><div>Dates and prices come from the organisers' own ticket pages and can change. Always check with the organiser before you buy. <a href="{up}kontakt/">Contact</a></div></footer>
</div>
<script>
// Dagene får «Today & tonight» / «Tomorrow», og dager som er over skjules (siden bygges bare når programmet endres)
(() => {{
  const p = n => String(n).padStart(2, "0"), now = new Date(), iso = d => `${{d.getFullYear()}}-${{p(d.getMonth() + 1)}}-${{p(d.getDate())}}`;
  const today = iso(now), tom = iso(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1));
  document.querySelectorAll("[data-date]").forEach(el => {{ if (el.dataset.date < today) el.remove(); }});
  let wk = false;
  document.querySelectorAll(".enday").forEach(s => {{
    const r = s.querySelector(".rel");
    if (s.dataset.date === today) {{ s.classList.add("today"); r.textContent = "Today & tonight · "; }}
    else if (s.dataset.date === tom) r.textContent = "Tomorrow · ";
    else if (s.dataset.weekend && !wk) {{ wk = true; s.insertAdjacentHTML("beforebegin", '<div class="wkd">This weekend</div>'); }}
  }});
  const dt = document.getElementById("daytime"); if (dt && !dt.querySelector("[data-date]")) dt.remove();
  document.getElementById("langbtn").addEventListener("click", () => {{ try {{ window.goatcounter.count({{ path: "språk/no", title: "språk/no", event: true }}); }} catch {{}} }});
}})();
</script>"""
    graph = [
        {"@type": "CollectionPage", "@id": BASE + path, "url": BASE + path, "name": title, "description": desc, "inLanguage": "en",
         "isPartOf": {"@id": BASE + "#website"}, "about": {"@type": "City", "name": "Ålesund", "address": {"@type": "PostalAddress", "addressCountry": "NO"}}},
        breadcrumb_ld([(SITE, BASE), ("What's on in Ålesund", BASE + path)]),
    ]
    return page(path, title, desc, body, {"@context": "https://schema.org", "@graph": graph}, raw=True, lang="en", head_extra=HREFLANG)


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
      <dt>Pris</dt><dd class="{'sold' if e.get('soldOut') else ''}">{escape(pt)} {few_html(e)}</dd>
      {f'<dt>Tider</dt><dd>{shows_html(e)}</dd>' if shows_html(e) else ""}
    </dl>
    {f'<p class="note{" warn" if e.get("uncertain") else ""}">{escape(e["note"])}</p>' if e.get("note") else ""}
    <div class="cta">{f'<a class="btn" href="{escape(u)}" target="_blank" rel="noopener">Billetter og info hos arrangør →</a>' if u else ""}{f'<a class="link" href="{up}julebord/">Alle julebord</a>' if e["cat"] in SEPARATE else f'<a class="link" href="{up}#ev-{e["id"]}">Se i hele programmet</a>'}</div>
    <p class="small">Datoer og priser kan endres. Sjekk alltid hos arrangøren før du kjøper billett.</p>
  </article>
  {f'<section class="also"><h2>Samme dag</h2><div class="events">{"".join(card(x, up) for x in same_day)}</div></section>' if same_day else ""}
  {f'<section class="also"><h2>Mer på {venue}</h2><div class="events">{"".join(card(x, up) for x in same_venue)}</div></section>' if same_venue else ""}
  </main>
  <nav class="more"><div class="row"><a class="chip" href="{up}{cat_path}">Flere: {CAT_LABEL[c]}</a><a class="chip" href="{up}denne-helgen/">Denne helgen</a><a class="chip" href="{up}">Hele programmet</a></div></nav>"""
    trail = [(SITE, BASE), (CATS.get(c, CATS["happening"])[1], BASE + cat_path), (e["title"], BASE + path)]
    return page(path, title, desc[:300], body, {"@context": "https://schema.org", "@graph": [breadcrumb_ld(trail), event_ld(e)]})


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
    counts = {d: [sum(1 for f in films if any(x["start"][:10] == d for x in f["shows"])),
                  sum(1 for f in films for x in f["shows"] if x["start"][:10] == d)] for d in days}
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
    <div class="kstrip" id="kdays"></div>
    <button type="button" class="kpick" id="kpick" aria-expanded="false" aria-controls="kpop"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/></svg><span>Velg dato</span></button>
    <div class="kpop" id="kpop" hidden></div>
  </div>
  <p class="ksum" id="ksum"></p>
  <script type="application/json" id="kinodata">{json.dumps(counts)}</script>
  <main id="films" class="kinofilms grid">
{sections if days else '<p class="empty">Vi har ikke kinoprogrammet akkurat nå. Se ODEON Ålesund sin egen side.</p>'}
  </main>
  <p class="empty" id="kinoempty" hidden>Ingen flere visninger denne dagen.</p>
  <p class="small kinosrc">Program og plakater via <a href="https://www.filmweb.no/program/sted/%C3%A5lesund/odeon%20%C3%A5lesund" target="_blank" rel="noopener">Filmweb</a>, bestilling hos <a href="https://www.odeonkino.no/alesund/kino/odeon-alesund/" target="_blank" rel="noopener">ODEON Ålesund</a>. Hentet {updated}. Sjekk alltid tidene hos kinoen.</p>
  <script>
{KINO_JS}
  </script>
  <footer><div>Kinoprogrammet er adskilt fra resten av programmet. Det oppdateres flere ganger om dagen.</div></footer>"""
    return body


KINO_JS = """
const osloNow = () => { const p = Object.fromEntries(new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Oslo", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date()).map(x => [x.type, x.value])); return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`; };
const now = osloNow(), today = now.slice(0, 10);
const addDay = d => { const x = new Date(d + "T12:00:00Z"); x.setUTCDate(x.getUTCDate() + 1); return x.toISOString().slice(0, 10); };
const counts = JSON.parse(document.getElementById("kinodata").textContent);
const allDays = Object.keys(counts).sort();
const WD = ["søn", "man", "tir", "ons", "tor", "fre", "lør"], WDL = ["søndag", "mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag"];
const MOS = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"];
const MO = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"];
const dt = s => new Date(s + "T12:00:00Z");
const isWe = s => [0, 6].includes(dt(s).getUTCDay());
const upcoming = allDays.filter(d => d >= today);
const horizon = (() => { const x = dt(today); x.setUTCDate(x.getUTCDate() + 7); return x.toISOString().slice(0, 10); })();
let stripDays = upcoming.filter(d => d < horizon);
if (!stripDays.length) stripDays = upcoming.slice(0, 7);
let sel = null, open = false, cal = null;
document.querySelectorAll(".t").forEach(t => { if (t.dataset.start < now) t.classList.add("past"); });
const nf = (n, one, many) => `${n} ${n === 1 ? one : many}`;
function tile(d, extra) {
  const x = dt(d), c = counts[d];
  return `<button type="button" class="ktile${isWe(d) ? " we" : ""}${c[1] < 5 ? " sparse" : ""}${d === today ? " today" : ""}${extra ? " extra" : ""}" data-day="${d}" aria-pressed="${d === sel}"><span class="wd">${d === today ? "I dag" : WD[x.getUTCDay()]}</span><span class="n">${x.getUTCDate()}</span><span class="mo">${MOS[x.getUTCMonth()]}</span><span class="c">${nf(c[0], "film", "filmer")}</span></button>`;
}
function calendar() {
  const [y, m] = cal, first = new Date(Date.UTC(y, m, 1, 12)), n = new Date(Date.UTC(y, m + 1, 0, 12)).getUTCDate(), off = (first.getUTCDay() + 6) % 7;
  const lo = upcoming[0] ? [+upcoming[0].slice(0, 4), +upcoming[0].slice(5, 7) - 1] : cal, last = allDays[allDays.length - 1];
  const hi = [+last.slice(0, 4), +last.slice(5, 7) - 1];
  const idx = ([a, b]) => a * 12 + b;
  let h = `<div class="khead"><button type="button" class="karrow" data-nav="-1" aria-label="Forrige måned"${idx(cal) <= idx(lo) ? " disabled" : ""}>‹</button><h2>${MO[m]} ${y}</h2><button type="button" class="karrow" data-nav="1" aria-label="Neste måned"${idx(cal) >= idx(hi) ? " disabled" : ""}>›</button></div><div class="k7">`;
  ["man", "tir", "ons", "tor", "fre", "lør", "søn"].forEach(w => { h += `<div class="kdow">${w}</div>`; });
  for (let i = 0; i < off; i++) h += "<div></div>";
  for (let d = 1; d <= n; d++) {
    const s = `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`, c = counts[s], ok = c && s >= today, dots = ok ? Math.min(3, Math.ceil(c[0] / 7)) : 0;
    h += `<button type="button" class="kday${ok ? " has" : " none"}${s === today ? " today" : ""}" data-pick="${s}" aria-pressed="${s === sel}"${ok ? "" : " disabled"}><span class="d">${d}</span><span class="dots">${"<i></i>".repeat(dots)}</span></button>`;
  }
  return h + "</div>";
}
function render() {
  let h = stripDays.map(d => tile(d)).join("");
  if (sel && !stripDays.includes(sel)) h += tile(sel, true);
  document.getElementById("kdays").innerHTML = h;
  document.querySelectorAll(".kinoday").forEach(s => { s.hidden = s.dataset.day !== sel; });
  let any = false;
  document.querySelectorAll(".kinoday:not([hidden]) .film").forEach(f => { f.classList.toggle("done", !f.querySelector(".t:not(.past)")); any = true; });
  document.getElementById("kinoempty").hidden = any;
  const c = counts[sel];
  const sum = document.getElementById("ksum");
  if (sum) sum.innerHTML = c ? `<b>${(WDL[dt(sel).getUTCDay()] + " " + dt(sel).getUTCDate() + ". " + MO[dt(sel).getUTCMonth()]).replace(/^./, x => x.toUpperCase())}</b> · ${nf(c[0], "film", "filmer")}, ${nf(c[1], "visning", "visninger")}` : "";
  const pop = document.getElementById("kpop");
  pop.hidden = !open;
  document.getElementById("kpick").setAttribute("aria-expanded", open);
  if (open) pop.innerHTML = calendar();
}
function choose(d) { sel = d; open = false; render(); try { history.replaceState(null, "", "#" + d); } catch {} }
document.getElementById("kdays").addEventListener("click", e => { const b = e.target.closest("[data-day]"); if (b) choose(b.dataset.day); });
document.getElementById("kpick").addEventListener("click", () => { open = !open; if (open) cal = [+(sel || today).slice(0, 4), +(sel || today).slice(5, 7) - 1]; render(); });
document.getElementById("kpop").addEventListener("click", e => {
  const nav = e.target.closest("[data-nav]");
  if (nav) { const i = cal[0] * 12 + cal[1] + +nav.dataset.nav; cal = [Math.floor(i / 12), i % 12]; render(); return; }
  const b = e.target.closest("[data-pick]"); if (b && !b.disabled) choose(b.dataset.pick);
});
// render() bytter ut panelet, så et trykk på pilene er allerede løsrevet fra DOM-en her og må ikke regnes som et trykk utenfor
document.addEventListener("click", e => { if (open && e.target.isConnected && !e.target.closest("#kpop, #kpick")) { open = false; render(); } });
document.addEventListener("keydown", e => { if (e.key === "Escape" && open) { open = false; render(); } });
const wanted = location.hash.slice(1);
sel = allDays.includes(wanted) && wanted >= today ? wanted : (upcoming[0] || allDays[0] || null);
render();
"""


SUB_CSS = """
/* Engelsk side (en/) */
.en .jump { display: flex; flex-wrap: wrap; gap: 6px 16px; margin-top: 10px; font: 600 14px var(--font-body); }
.en .jump a, .en .daytime a, .en .faq a { color: var(--sea); }
.en .enday { margin-top: 22px; }
.en .enday h2, .en .daytime h2, .en .faq h2 { font: 800 19px/1.2 var(--font-display); margin: 0 0 4px; padding-bottom: 6px; border-bottom: 1px solid var(--line); }
.en .enday.today { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 12px 14px; }
.en .enday.today h2 { border: 0; }
.en .rel { color: var(--accent); }
.en .wkd { margin: 30px 0 -8px; font: 800 13px var(--font-body); text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
.en .enrow { display: grid; grid-template-columns: 58px 1fr auto; gap: 10px; align-items: baseline; padding: 9px 0; border-top: 1px solid var(--line); }
.en .enday h2 + .enrow { border-top: 0; }
.en .enrow .tm { font: 600 13px var(--font-mono); color: var(--fg); }
.en .enrow .tt { font: 600 15.5px/1.3 var(--font-body); }
.en .enrow .tt a { color: inherit; text-decoration: none; }
.en .enrow .tt a:hover { text-decoration: underline; }
.en .enrow small { display: block; font-size: 13px; color: var(--muted); }
.en .enrow small::before { content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--c); margin-right: 6px; }
.en .nob { display: inline-block; margin-top: 4px; font: 600 11px/1 var(--font-body); color: var(--muted); border: 1px solid var(--line); border-radius: 4px; padding: 3px 6px; }
.en .enrow .pr { display: flex; flex-direction: column; align-items: end; gap: 5px; }
.en .enrow em { font: 600 13px var(--font-mono); font-style: normal; white-space: nowrap; }
.en .enrow em.sold { color: var(--accent); }
.en .enrow em.unk { font: 500 12px var(--font-body); color: var(--muted); }
.en .daytime { margin-top: 30px; border: 1px dashed var(--line); border-radius: 14px; padding: 12px 14px; }
.en .daytime p { margin: 0 0 4px; font-size: 14px; color: var(--muted); }
.en .faq { margin-top: 30px; }
.en .faq details { border-bottom: 1px solid var(--line); padding: 10px 0; }
.en .faq summary { font: 700 15px var(--font-body); cursor: pointer; }
.en .faq p { margin: 6px 0 0; color: var(--muted); font-size: 14.5px; max-width: 70ch; }
@media (max-width: 420px) { .en .enrow { grid-template-columns: 48px 1fr auto; gap: 8px; } }

/* Undersider (lages av scripts/pages.py) */
.sub .topbar { padding-bottom: 14px; }
.sub .crumbs { font: 500 13px/1.4 var(--font-body); }
.sub .crumbs a, .sub .venue, .sub a.title { color: inherit; }
.sub a.title { text-decoration: none; }
.sub a.title:hover { text-decoration: underline; }
.sub .facts { margin: 0 0 6px; font-size: 14px; color: var(--muted); }
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
.qweek { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin: 4px 0 18px; }
.qweek div { background: var(--surface); border: 1px solid var(--line); border-radius: 9px; text-align: center; padding: 7px 0; font: 600 11px var(--font-mono); color: var(--muted); }
.qweek b { display: block; font: 800 18px var(--font-display); color: var(--fg); }
.qweek .q { background: color-mix(in srgb, var(--c-quiz) 12%, var(--surface)); border-color: var(--c-quiz); color: var(--c-quiz); }
.qweek .q i { display: block; width: 6px; height: 6px; border-radius: 50%; background: var(--c-quiz); margin: 3px auto 0; }
.julemeny { margin: 0 0 18px; padding: 14px 16px; border: 1px solid var(--c-julebord); border-radius: 12px; background: color-mix(in srgb, var(--c-julebord) 7%, var(--surface)); }
.julemeny h2 { margin: 0 0 4px; font-size: 17px; }
.julemeny > p { margin: 0 0 8px; color: var(--muted); font-size: 14px; }
.julemeny ul { list-style: none; margin: 0; padding: 0; }
.julemeny li { padding: 8px 0; border-top: 1px solid var(--line); }
.julemeny li span { color: var(--muted); font-size: 14px; }
.julemeny li small { display: block; font: 600 13px var(--font-mono); color: var(--c-julebord); margin-top: 2px; }
.julemeny li p { margin: 4px 0 0; font-size: 14px; }
.jbtips { margin: 0 0 14px; font-size: 14px; color: var(--muted); }
.kform { display: grid; gap: 14px; max-width: 560px; }
.kform label { display: grid; gap: 6px; font: 600 14px/1.3 var(--font-body); }
.kform input, .kform select, .kform textarea { font: 400 16px/1.4 var(--font-body); padding: 10px 12px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); color: var(--fg); width: 100%; box-sizing: border-box; }
.kform #kevent { display: grid; gap: 14px; }
.kform #kevent[hidden] { display: none; }
.kform .btn { border: 0; cursor: pointer; justify-self: start; }
.about { max-width: 640px; margin-top: 32px; }
.about h2 { font: 700 18px/1.2 var(--font-display); margin: 22px 0 8px; }
.about p { font-size: 15px; line-height: 1.55; }
.detail .small { font-size: 12.5px; color: var(--muted); margin: 14px 0 0; }

/* Kino */
:root { --kino: #3d4f8f; --kino-soft: #e3e8f5; --kino-ink: #ffffff; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --kino: #8fa3e6; --kino-soft: #1c2748; --kino-ink: #0b1230; } }
:root[data-theme="dark"] { --kino: #8fa3e6; --kino-soft: #1c2748; --kino-ink: #0b1230; }
.kinobar { position: relative; display: flex; gap: 8px; align-items: flex-start; margin-bottom: 12px; min-width: 0; }
.kstrip { flex: 0 1 auto; min-width: 0; display: flex; gap: 6px; overflow-x: auto; padding: 2px 2px 8px; scroll-snap-type: x proximity; }
.ktile { flex: none; scroll-snap-align: start; width: 68px; border: 1px solid var(--line); background: var(--surface); color: var(--fg); border-radius: 12px; padding: 8px 0 7px; display: grid; justify-items: center; gap: 1px; cursor: pointer; font: inherit; }
.ktile .wd { font: 500 11px/1.3 var(--font-mono); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
.ktile .n { font: 800 24px/1.1 var(--font-display); }
.ktile .mo { font: 500 11px/1.3 var(--font-body); color: var(--muted); }
.ktile .c { font: 600 10px/1.3 var(--font-mono); margin-top: 3px; color: var(--kino); }
.ktile.we { background: var(--kino-soft); }
.ktile.sparse:not([aria-pressed="true"]) { opacity: .6; }
.ktile.today .wd { color: var(--accent); }
.ktile[aria-pressed="true"] { background: var(--kino); border-color: var(--kino); color: var(--kino-ink); }
.ktile[aria-pressed="true"] .wd, .ktile[aria-pressed="true"] .mo, .ktile[aria-pressed="true"] .c { color: var(--kino-ink); opacity: .9; }
.kpick { flex: none; width: 74px; display: grid; justify-items: center; gap: 3px; padding: 8px 12px; border-radius: 12px; border: 1px solid var(--kino); color: var(--kino); background: var(--surface); font: 600 12px/1.2 var(--font-body); cursor: pointer; }
.kpick svg { width: 22px; height: 22px; }
.kpick[aria-expanded="true"] { background: var(--kino-soft); }
.kpop { position: absolute; top: 100%; right: 0; z-index: 20; width: min(360px, 100%); border: 1px solid var(--line); border-radius: 12px; padding: 12px; background: var(--surface); box-shadow: 0 8px 24px rgb(0 0 0 / .12); display: grid; gap: 10px; }
.khead { display: flex; align-items: center; justify-content: space-between; }
.khead h2 { margin: 0; font: 800 18px/1.2 var(--font-display); text-transform: capitalize; }
.karrow { width: 34px; height: 34px; border-radius: 50%; border: 1px solid var(--line); background: var(--surface); color: var(--fg); font-size: 16px; cursor: pointer; }
.karrow:disabled { opacity: .35; cursor: default; }
.k7 { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px; }
.kdow { font: 500 11px/1.3 var(--font-mono); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); text-align: center; padding-bottom: 2px; }
.kday { aspect-ratio: 1; max-height: 48px; border-radius: 10px; border: 1px solid transparent; background: none; color: var(--fg); display: grid; place-items: center; align-content: center; gap: 2px; font: inherit; cursor: pointer; }
.kday .d { font: 600 15px/1 var(--font-body); }
.kday .dots { display: flex; gap: 2px; height: 5px; }
.kday .dots i { width: 5px; height: 5px; border-radius: 50%; background: var(--kino); }
.kday.has { background: var(--kino-soft); }
.kday.none { color: var(--muted); opacity: .45; cursor: default; }
.kday.today .d { color: var(--accent); font-weight: 800; }
.kday[aria-pressed="true"] { background: var(--kino); color: var(--kino-ink); }
.kday[aria-pressed="true"] .d { color: var(--kino-ink); }
.kday[aria-pressed="true"] .dots i { background: var(--kino-ink); }
.ksum { margin: 0 0 12px; padding-top: 10px; border-top: 1px solid var(--line); color: var(--muted); font-size: 14px; }
.ksum b { color: var(--fg); font: 700 17px var(--font-display); }
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

/* Jul i Ålesund (sesongside) */
body.jul { background: #f6efe0; color: #2a2a22; font-family: "Figtree", system-ui, sans-serif; font-size: 15px; }
.jul .jul-hero { position: relative; background: radial-gradient(120% 90% at 50% 0%, #1d5c47 0%, #0d3327 70%); color: #fff; padding: 58px 20px 40px; text-align: center; overflow: hidden; }
.jul .jgar { position: absolute; left: 0; right: 0; top: 0; height: 46px; pointer-events: none; }
.jul .jgar i { position: absolute; inset: 0; background-repeat: repeat-x; background-size: 160px 46px; }
.jul .jgar .w { background-image: url("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22160%22 height=%2246%22 viewBox=%220 0 160 46%22%3E%3Cpath d=%22M0 8 Q40 36 80 8 Q120 36 160 8%22 fill=%22none%22 stroke=%22%232a1d12%22 stroke-width=%222%22/%3E%3C/svg%3E"); }
.jul .jgar .a { background-image: url("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22160%22 height=%2246%22 viewBox=%220 0 160 46%22%3E%3Ccircle cx=%2220%22 cy=%2226%22 r=%2211%22 fill=%22%23d9372f%22 opacity=%22.25%22/%3E%3Ccircle cx=%2220%22 cy=%2226%22 r=%225%22 fill=%22%23d9372f%22/%3E%3Ccircle cx=%22100%22 cy=%2226%22 r=%2211%22 fill=%22%233f7fd0%22 opacity=%22.25%22/%3E%3Ccircle cx=%22100%22 cy=%2226%22 r=%225%22 fill=%22%233f7fd0%22/%3E%3C/svg%3E"); animation: jtw 2.6s ease-in-out infinite; }
.jul .jgar .b { background-image: url("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22160%22 height=%2246%22 viewBox=%220 0 160 46%22%3E%3Ccircle cx=%2260%22 cy=%2226%22 r=%2211%22 fill=%22%23e8b04a%22 opacity=%22.25%22/%3E%3Ccircle cx=%2260%22 cy=%2226%22 r=%225%22 fill=%22%23e8b04a%22/%3E%3Ccircle cx=%22140%22 cy=%2226%22 r=%2211%22 fill=%22%232f9e62%22 opacity=%22.25%22/%3E%3Ccircle cx=%22140%22 cy=%2226%22 r=%225%22 fill=%22%232f9e62%22/%3E%3C/svg%3E"); animation: jtw 2.6s ease-in-out -1.3s infinite; }
@keyframes jtw { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
.jul .snow, .jul .snow2 { position: absolute; inset: 0; pointer-events: none; background-image: radial-gradient(circle, #fff 1.6px, transparent 2.2px), radial-gradient(circle, #fffb 1.2px, transparent 1.8px), radial-gradient(circle, #fff9 2px, transparent 2.6px); background-size: 90px 90px, 140px 140px, 200px 200px; background-position: 0 0, 40px 60px, 90px 20px; animation: jfall 16s linear infinite; opacity: .8; }
.jul .snow2 { background-size: 70px 70px, 110px 110px, 170px 170px; animation-duration: 24s; opacity: .5; }
@keyframes jfall { to { background-position: 0 90px, 40px 200px, 90px 220px; } }
@media (prefers-reduced-motion: reduce) { .jul .snow, .jul .snow2, .jul .jgar .a, .jul .jgar .b { animation: none; } }
.jul .jul-hero > * { position: relative; }
.jul .jul-back { position: absolute; left: 14px; top: 52px; font: 600 12px/1 "Figtree", sans-serif; color: #e9e2cf; text-decoration: none; }
.jul .jul-hero small { display: block; font: 700 11px "Figtree", sans-serif; letter-spacing: .24em; text-transform: uppercase; color: #e8b04a; }
.jul .jul-hero h1 { margin: 10px 0 2px; font: italic 700 clamp(44px, 12vw, 70px)/.95 "Fraunces", Georgia, serif; text-shadow: 0 2px 12px #0006; color: #fff; }
.jul .jul-hero p { margin: 10px auto 0; max-width: 34ch; font: 400 16px/1.4 "Fraunces", Georgia, serif; color: #e9e2cf; }
.jul .jcd { display: inline-flex; align-items: center; gap: 12px; margin-top: 18px; padding: 8px 18px 8px 12px; border-radius: 99px; background: #ffffff14; border: 1px solid #e8b04a66; }
.jul .jcd b { font: 700 34px/1 "Fraunces", serif; color: #e8b04a; } .jul .jcd span { font: 600 13px/1.15 "Figtree", sans-serif; text-align: left; }
.jul .jul-main { max-width: 760px; margin: 0 auto; padding: 0 16px 40px; }
.jul .jul-main h2 { margin: 26px 0 2px; font: italic 700 28px/1.1 "Fraunces", Georgia, serif; color: #0d3327; }
.jul .jul-sub { margin: 2px 0 14px; font-size: 13px; color: #6b6455; }
.jul .jc { background: #fff; border: 1px solid #eadfc4; border-left: 5px solid var(--c); border-radius: 12px; padding: 10px 12px; margin-bottom: 8px; box-shadow: 0 2px 0 #0000000d; }
.jul .jc[hidden], .jul .jrow[hidden] { display: none; }
.jul .jc h3 { margin: 0; font: 700 16px/1.2 "Fraunces", Georgia, serif; } .jul .jc h3 a { color: #1d2a24; text-decoration: none; } .jul .jc h3 a:hover { text-decoration: underline; }
.jul .jmore { font-size: 12px; color: #6b6455; margin-top: 3px; }
.jul .jm { font-size: 12.5px; color: #6b6455; margin-top: 2px; } .jul .jp { font: 700 12.5px "Figtree", sans-serif; color: #b3262d; margin-top: 2px; }
.jul .jlist .jhd { position: sticky; top: 0; z-index: 5; background: #f6efe0; padding: 12px 0 10px; border-bottom: 1px solid #e6dab8; margin-top: 24px; }
.jul .jlist .jhd h2 { margin: 0 0 8px; }
.jul .jchips { display: flex; flex-wrap: wrap; gap: 7px; }
.jul .jchips .chip { font: 600 13px "Figtree", sans-serif; padding: 8px 13px; border-radius: 99px; border: 1.5px solid #cdbf98; background: #fffaf0; color: #2a2a22; cursor: pointer; }
.jul .jchips .chip[aria-pressed="true"] { background: #0d3327; color: #fff; border-color: #0d3327; }
.jul .jcnt { font: 500 11.5px ui-monospace, monospace; color: #6b6455; padding: 10px 0 0; }
.jul .jrow { display: grid; grid-template-columns: 54px 1fr; gap: 12px; padding: 12px 0; border-bottom: 1px dashed #d8cba5; }
.jul .jdt { text-align: center; background: #0d3327; color: #fff; border-radius: 12px; padding: 6px 0; height: max-content; box-shadow: 0 3px 0 #0003; }
.jul .jdt small { display: block; font: 700 10px "Figtree", sans-serif; letter-spacing: .12em; text-transform: uppercase; color: #e8b04a; } .jul .jdt b { display: block; font: 700 24px/1 "Fraunces", serif; }
.jul .jul-jb { display: block; margin: 18px 0 4px; padding: 13px 16px; border-radius: 14px; background: #b3262d; color: #fff; text-decoration: none; font-size: 15px; box-shadow: 0 4px 12px #0002; }
.jul .jul-jb:hover { filter: brightness(1.07); }
.jul .jul-note { margin: 22px 0 0; font-size: 12.5px; color: #6b6455; } .jul .jul-note a { color: #1b5a45; }
.jul .more { margin-top: 26px; } .jul .more h2 { font: italic 700 20px "Fraunces", serif; color: #0d3327; margin: 0 0 8px; }
.jul .more .chip { background: #fffaf0; color: #2a2a22; border: 1.5px solid #cdbf98; text-decoration: none; padding: 8px 13px; border-radius: 99px; font: 600 13px "Figtree", sans-serif; }
.jul .more .row { display: flex; flex-wrap: wrap; gap: 7px; }
"""


if __name__ == "__main__":
    main()
