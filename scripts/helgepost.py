"""Ukentlig helgepost: ferdig tekst til Facebook og Instagram, og et helgebilde i Instagram-format.

Teksten lages av .github/workflows/helgepost.yml hver torsdag og legges i et issue, så eieren
får den på e-post og kan lime den inn. Bildet lages av scripts/pages.py ved hver publisering
(denne-helgen/helgen.png, og helgen-2.png osv. når alt ikke får plass på ett). Alt kommer fra data/events.json, samme utvalg som siden «Denne helgen».

Kjør: python3 scripts/helgepost.py [fil]   (skriver issue-teksten til filen, ellers til skjermen)
Skrifter: legg BricolageGrotesque.ttf og Figtree.ttf i mappen FONT_DIR peker på, ellers brukes DejaVu.
"""
import datetime
import json
import re
import os
import sys
from pathlib import Path

import pages

W, H = 1080, 1350  # Instagram stående
EMOJI = {"konsert": "🎵", "standup": "😂", "show": "🎭", "barn": "🧸", "klubb": "🪩", "happening": "✨", "quiz": "🧠", "julebord": "🎄", "sport": "⚽"}
PLURAL = {"konsert": ("konsert", "konserter"), "standup": ("standup", "standup"), "show": ("show", "show"),
          "barn": ("for barn og familie", "for barn og familie"), "klubb": ("klubbkveld", "klubbkvelder"),
          "happening": ("happening", "happenings"), "quiz": ("quizkveld", "quizkvelder"), "julebord": ("julebord", "julebord"), "sport": ("AaFK-kamp", "AaFK-kamper")}
TEXT_MAX = 40  # flere enn dette blir for langt for et Facebook-innlegg


def line(e):
    extra = " (utsolgt)" if e.get("soldOut") else " (usikker dato, sjekk hos arrangør)" if e.get("uncertain") else ""
    price = pages.price_text(e)
    return f"{EMOJI.get(e['cat'], '✨')} {e['time'] + ' ' if e.get('time') else ''}{e['title']}, {e['venue']}" + (
        f" ({price})" if price not in ("Utsolgt", "Pris hos arrangør") else "") + extra


def summary(evs):
    counts = {}
    for e in evs:
        counts[e["cat"]] = counts.get(e["cat"], 0) + 1
    parts = [f"{n} {PLURAL.get(c, ('arrangement', 'arrangementer'))[n > 1]}" for c, n in sorted(counts.items(), key=lambda x: -x[1])]
    return ", ".join(parts[:-1]) + " og " + parts[-1] if len(parts) > 1 else parts[0]


def facebook_text(evs, start, sun):
    url = pages.BASE + "denne-helgen/"
    span = pages.range_text(start, sun)
    if not evs:
        return f"Vi har ikke funnet noe som skjer i Ålesund i helgen ({span}) ennå. Følg med på {url}"
    out = [f"Dette skjer i Ålesund i helgen, {span}:"]
    day = None
    for e in evs[:TEXT_MAX]:
        if e["date"] != day:
            day = e["date"]
            out += ["", pages.WD[datetime.date.fromisoformat(day).weekday()].upper()]
        out.append(line(e))
    if len(evs) > TEXT_MAX:
        out += ["", f"… og {len(evs) - TEXT_MAX} til."]
    kino = kino_line(start, sun)
    if kino:
        out += ["", kino]
    out += ["", "Priser, billettlenker og kart:", url]
    return "\n".join(out)


def kino_line(start, sun, limit=3):
    """«🎬 På kino i helgen: A, B, C og N til». Tom hvis vi ikke har kinoprogram for helgen."""
    f = pages.ROOT / "data" / "kino.json"
    if not f.exists():
        return ""
    days = {(start + datetime.timedelta(days=i)).isoformat() for i in range((sun - start).days + 1)}
    films = [x for x in json.loads(f.read_text()).get("films", []) if any(s["start"][:10] in days for s in x["shows"])]
    films.sort(key=lambda x: (-sum(s["start"][:10] in days for s in x["shows"]), x["title"].lower()))  # flest visninger først
    titles = [x["title"] for x in films]
    if not titles:
        return ""
    if len(titles) > limit:
        shown, more = ", ".join(titles[:limit]), f" og {len(titles) - limit} til"
    else:
        shown, more = (", ".join(titles[:-1]) + " og " + titles[-1]) if len(titles) > 1 else titles[0], ""
    return f"🎬 På kino i helgen: {shown}{more}. Program: {pages.BASE}kino/"


CAT_TAGS = {"konsert": ["#konsert", "#livemusikk"], "standup": ["#standup", "#humor"], "show": ["#teater", "#show"],
            "barn": ["#barnogfamilie", "#familietid"], "klubb": ["#klubb", "#natteliv", "#utgang"], "happening": ["#happening", "#opplevelser"],
            "quiz": ["#quiz", "#pubquiz"], "sport": ["#aafk", "#fotball"], "julebord": ["#julebord"]}
BASE_TAGS = ["#ålesund", "#alesund", "#skjeriålesund", "#kaskjerda", "#sunnmøre", "#ålesundby", "#møreogromsdal", "#visitålesund",
             "#hvaskjer", "#hvaskjeriålesund", "#helgetips", "#helgen", "#helgeiålesund"]
TAG_MAX = 22


def hashtags(evs, start, sun):
    """Byen og regionen, så kategoriene som faktisk er med i helgen, og litt sesong. Aldri flere enn TAG_MAX."""
    tags = list(BASE_TAGS)
    text = " ".join(e["title"].lower() for e in evs)
    if "halloween" in text:
        tags += ["#halloween", "#halloweenfest"]
    if "julemarked" in text:
        tags.append("#julemarked")
    if sun.month in (11, 12) and "jul" in text:
        tags += ["#jul", "#førjul"]
    if any(e.get("priceMin") == 0 for e in evs):
        tags.append("#gratis")
    if kino_line(start, sun):
        tags.append("#kino")
    counts = {}
    for e in evs:
        counts[e["cat"]] = counts.get(e["cat"], 0) + 1
    for c, _ in sorted(counts.items(), key=lambda x: -x[1]):
        tags += CAT_TAGS.get(c, [])
    return list(dict.fromkeys(tags))[:TAG_MAX]


def highlights(evs, limit=4):
    """Ett høydepunkt per kategori (det første som ikke er utsolgt), de største kategoriene først."""
    counts, first = {}, {}
    for e in evs:
        counts[e["cat"]] = counts.get(e["cat"], 0) + 1
        if not e.get("soldOut") and not e.get("uncertain") and len(e.get("moreShows") or []) < 6 and e["cat"] not in first:  # faste serier («DJ hver helg») er ikke tips
            first[e["cat"]] = e
    picked = [first[c] for c, _ in sorted(counts.items(), key=lambda x: -x[1]) if c in first][:limit]
    out = []
    for e in sorted(picked, key=lambda e: (e["date"], e.get("time") or "")):
        if e:
            c = e["cat"]
            day = pages.WD[datetime.date.fromisoformat(e["date"]).weekday()].capitalize()
            price = pages.price_text(e)
            out.append(f"{EMOJI.get(c, '✨')} {day}{' ' + e['time'].split(' og ')[0] if e.get('time') else ''}: {e['title']}, {e['venue']}"
                       + (f" ({price})" if price not in ("Utsolgt", "Pris hos arrangør") else ""))
    return out


def instagram_text(evs, start, sun):
    span = pages.range_text(start, sun)
    if not evs:
        return (f"Helgen i Ålesund, {span} 🌊\n\nProgrammet fylles på fortløpende. Følg med!\n\n"
                "Hele oversikten finner du på kaskjerda.no (lenke i bio).\n\n" + " ".join(hashtags(evs, start, sun)))
    n = len(evs)
    hl = highlights(evs)
    return (f"Hva skjer i Ålesund denne helgen? 🌊\n{span}\n\n"
            f"{n} {'arrangement' if n == 1 else 'arrangementer'} å velge mellom: {summary(evs)}.\n\n"
            + ("Noen tips:\n" + "\n".join(hl) + "\n\n" if hl else "")
            + "🎟️ Alle arrangementene med priser, kart og billettlenker: kaskjerda.no (lenke i bio)\n"
            "💾 Lagre innlegget og send det til den du skal ut med!\n\n"
            + " ".join(hashtags(evs, start, sun)))


def issue_body(evs, start, sun, today):
    names = image_names(evs)
    imgs = "\n\n".join(f"![Helgen i Ålesund, bilde {i}]({pages.BASE}denne-helgen/{n}?v={today.isoformat()})" for i, n in enumerate(names, 1))
    many = f"Det er {len(names)} bilder. Legg dem ut sammen som karusell på Instagram. " if len(names) > 1 else ""
    return f"""Her er helgeposten. Kopier teksten og lim den inn i Facebook-grupper eller på Instagram.

### {"Bilder" if len(names) > 1 else "Bilde"} (Instagram, 1080 × 1350)
{many}Trykk på bildet og lagre det. Det første er også forhåndsvisningen når noen deler {pages.BASE}denne-helgen/

{imgs}

### Facebook
```text
{facebook_text(evs, start, sun)}
```

### Instagram (bildetekst)
```text
{instagram_text(evs, start, sun)}
```

Sjekk gjerne lista før du poster. Programmet hentes automatisk og kan endre seg. Dette issuet lukkes neste torsdag når en ny helgepost kommer.
"""


# --- Bildet ---

BG, FG, MUTED, LINE, ACCENT, SEA, SURFACE = "#eef3f2", "#10282f", "#5a7177", "#d3dfdd", "#c8432b", "#1f6f78", "#ffffff"
CAT_COLOR = {"konsert": "#1f6f78", "standup": "#b5531c", "show": "#6a4fa3", "barn": "#2f8a4c", "klubb": "#a83167", "happening": "#8a6d12", "quiz": "#7a4fb0", "julebord": "#b3262d", "sport": "#2b5fa8"}


def font(name, size, **axes):
    """Variabel skrift fra FONT_DIR med akser som weight=800, ellers DejaVu (finnes på GitHubs maskiner)."""
    from PIL import ImageFont
    path = Path(os.environ.get("FONT_DIR", "")) / name
    try:
        f = ImageFont.truetype(str(path), size)
        if axes:
            f.set_variation_by_axes([axes.get(a["name"].decode().split()[0].lower(), a["default"]) for a in f.get_variation_axes()])
        return f
    except (OSError, ValueError):
        bold = axes.get("weight", 400) >= 600
        try:
            return ImageFont.truetype(f"DejaVuSans{'-Bold' if bold else ''}.ttf", size)
        except OSError:
            return ImageFont.load_default(size)


def no_emoji(text):
    """Skriftene i bildet har ikke emoji; de ville blitt firkanter."""
    return re.sub(r"[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE0F\u200d]", "", text).strip()


def fit(draw, text, f, width):
    """Kort ned teksten med … så den får plass på én linje."""
    if draw.textlength(text, font=f) <= width:
        return text
    while text and draw.textlength(text + "…", font=f) > width:
        text = text[:-1]
    return text.rstrip(" ,–-") + "…"


# Oppsett: stort (to linjer per arrangement) når alt får plass, ellers kompakt (én linje).
# Får heller ikke det plass, fortsetter lista på helgen-2.png osv. (karusell på Instagram).
PAD = 80
BOTTOM = H - PAD - 34 - 30  # over streken og bunnteksten
LARGE = {"top": 372, "day": 54, "row": 100}
COMPACT = {"top": 336, "day": 50, "row": 54}
TIGHT = {"top": 300, "day": 42, "row": 46}  # tettest mulig, så helgen får plass på ett bilde
NEXT_TOP = 236  # på bilde 2 og utover er overskriften mindre


def height(items, m):
    return len({e["date"] for e in items}) * m["day"] + len(items) * m["row"]


def plan(evs):
    """Hvilket oppsett, og hvilke arrangementer som havner på hvert bilde."""
    for m in (LARGE, COMPACT, TIGHT):  # ett bilde om det går, helst med størst mulig skrift
        if height(evs, m) <= BOTTOM - m["top"]:
            return m, [evs]
    sheets, rest, top = [], list(evs), COMPACT["top"]
    while rest:
        n = 1
        while n < len(rest) and height(rest[:n + 1], COMPACT) <= BOTTOM - top:
            n += 1
        sheets.append(rest[:n])
        rest, top = rest[n:], NEXT_TOP
    k = len(sheets)
    if k > 1:  # fordel jevnt, så ikke siste bilde bare får ett arrangement
        target, sheets, cur = height(evs, COMPACT) / k, [], []
        for e in evs:
            if cur and len(sheets) < k - 1 and height(cur + [e], COMPACT) > target:
                sheets.append(cur)
                cur = []
            cur.append(e)
        sheets.append(cur)
    return COMPACT, sheets


def image_names(evs):
    return ["helgen.png"] + [f"helgen-{i}.png" for i in range(2, len(plan(evs)[1]) + 1)]


def render_image(evs, start, sun, folder):
    """Lager helgen.png (og helgen-2.png osv. ved behov) i folder. Gir filnavnene tilbake."""
    from PIL import Image, ImageDraw
    m, sheets = plan(evs)
    names = image_names(evs)
    for old in folder.glob("helgen*.png"):
        old.unlink()
    inner = W - 2 * PAD
    big, tight = m is LARGE, m is TIGHT
    f_eyebrow = font("Figtree.ttf", 30, weight=600)
    f_h1 = font("BricolageGrotesque.ttf", 132 if big else 92 if tight else 112, weight=800, optical=96, width=100)
    f_h1_next = font("BricolageGrotesque.ttf", 72, weight=800, optical=72, width=100)
    f_span = font("BricolageGrotesque.ttf", 56 if big else 42 if tight else 48, weight=800, optical=48, width=100)
    f_day = font("Figtree.ttf", 26, weight=700)
    f_title = font("BricolageGrotesque.ttf", 38 if big else 28 if tight else 32, weight=700, optical=24, width=100)
    f_meta = font("Figtree.ttf", 28 if big else 23 if tight else 26, weight=500)
    f_foot = font("Figtree.ttf", 28, weight=600)
    span = pages.range_text(start, sun)

    for i, items in enumerate(sheets or [[]]):
        img = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(img)
        dr.text((PAD, PAD), "SKJER I ÅLESUND", font=f_eyebrow, fill=SEA)
        if i == 0:
            dr.text((PAD - 4, PAD + 52), "I helgen", font=f_h1, fill=FG)
            dr.text((PAD, PAD + (192 if big else 158 if tight else 170)), span, font=f_span, fill=ACCENT)
            y = m["top"]
        else:
            dr.text((PAD - 3, PAD + 50), f"I helgen, forts.", font=f_h1_next, fill=FG)
            y = NEXT_TOP
        day = None
        for e in items:
            if e["date"] != day:
                day = e["date"]
                d = datetime.date.fromisoformat(day)
                dr.text((PAD, y), f"{pages.WD[d.weekday()].upper()} {d.day}. {pages.MO[d.month - 1].upper()}", font=f_day, fill=ACCENT)
                y += m["day"]
            color = CAT_COLOR.get(e["cat"], SEA)
            x = PAD + 30
            if big:
                dr.rounded_rectangle((PAD, y, PAD + 8, y + m["row"] - 22), radius=4, fill=color)
                dr.text((x, y - 2), fit(dr, no_emoji(e["title"]), f_title, inner - 30), font=f_title, fill=FG)
                price = pages.price_text(e)
                meta = " · ".join(p for p in [e.get("time") and f"kl. {e['time']}", e["venue"], price if price != "Pris hos arrangør" else ""] if p)
                dr.text((x, y + 46), fit(dr, meta, f_meta, inner - 30), font=f_meta, fill=MUTED)
            else:
                # Én linje: klokkeslett, tittel og scene. Tittelen kortes ned før scenen.
                dr.rounded_rectangle((PAD, y + 4, PAD + 8, y + m["row"] - 14), radius=4, fill=color)
                t = (e.get("time") or "").split(" og ")[0]
                dr.text((x, y + 4), t, font=f_meta, fill=MUTED)
                x += 96
                venue = " · " + e["venue"]
                vw = min(dr.textlength(venue, font=f_meta), inner * 0.42)
                venue = fit(dr, venue, f_meta, vw)
                title = fit(dr, no_emoji(e["title"]), f_title, inner - (x - PAD) - vw)
                dr.text((x, y), title, font=f_title, fill=FG)
                dr.text((x + dr.textlength(title, font=f_title), y + 4), venue, font=f_meta, fill=MUTED)
            y += m["row"]
        if not evs:
            dr.text((PAD, y), "Programmet fylles på fortløpende.", font=f_meta, fill=MUTED)

        foot_y = H - PAD - 34
        dr.line((PAD, foot_y - 26, W - PAD, foot_y - 26), fill=LINE, width=2)
        dr.text((PAD, foot_y), f"{i + 1}/{len(sheets)}" if len(sheets) > 1 else "Priser og billetter på nettsiden", font=f_foot, fill=FG)
        site = "kaskjerda.no"
        dr.text((W - PAD - dr.textlength(site, font=f_foot), foot_y), site, font=f_foot, fill=SEA)
        img.save(folder / names[i], optimize=True)
    return names


def main():
    data = json.loads((pages.ROOT / "data" / "events.json").read_text())
    today = datetime.datetime.now(pages.TZ).date()
    start, sun = pages.weekend_range(today)
    evs = pages.occurrences([e for e in data["events"] if e["date"] >= today.isoformat() and e["cat"] not in pages.SEPARATE], start, sun)
    body = issue_body(evs, start, sun, today)
    title = f"Helgepost: {pages.range_text(start, sun)}"
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(body)
    else:
        print(title + "\n\n" + body)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"title={title}\n")


if __name__ == "__main__":
    main()
