"""Ukentlig helgepost: ferdig tekst til Facebook og Instagram, og et helgebilde i Instagram-format.

Teksten lages av .github/workflows/helgepost.yml hver torsdag og legges i et issue, så eieren
får den på e-post og kan lime den inn. Bildet lages av scripts/pages.py ved hver publisering
(denne-helgen/helgen.png). Alt kommer fra data/events.json, samme utvalg som siden «Denne helgen».

Kjør: python3 scripts/helgepost.py [fil]   (skriver issue-teksten til filen, ellers til skjermen)
Skrifter: legg BricolageGrotesque.ttf og Figtree.ttf i mappen FONT_DIR peker på, ellers brukes DejaVu.
"""
import datetime
import json
import os
import sys
from pathlib import Path

import pages

W, H = 1080, 1350  # Instagram stående
EMOJI = {"konsert": "🎵", "standup": "😂", "show": "🎭", "barn": "🧸", "klubb": "🪩", "happening": "✨", "sport": "⚽"}
PLURAL = {"konsert": ("konsert", "konserter"), "standup": ("standup", "standup"), "show": ("show", "show"),
          "barn": ("for barn og familie", "for barn og familie"), "klubb": ("klubbkveld", "klubbkvelder"),
          "happening": ("happening", "happenings"), "sport": ("AaFK-kamp", "AaFK-kamper")}
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
    out += ["", "Priser, billettlenker og kart:", url]
    return "\n".join(out)


def instagram_text(evs, start, sun):
    span = pages.range_text(start, sun)
    what = f"{len(evs)} {'arrangement' if len(evs) == 1 else 'arrangementer'}: {summary(evs)}." if evs else "Programmet fylles på fortløpende."
    return (f"Helgen i Ålesund, {span} 🌊\n\n{what}\n\n"
            "Hele oversikten med priser og billettlenker finner du på Skjer i Ålesund (lenke i bio).\n\n"
            "#ålesund #skjeriålesund #sunnmøre #ålesundby #hvaskjer")


def issue_body(evs, start, sun, today):
    img = f"{pages.BASE}denne-helgen/helgen.png?v={today.isoformat()}"
    return f"""Her er helgeposten. Kopier teksten og lim den inn i Facebook-grupper eller på Instagram.

### Bilde (Instagram, 1080 × 1350)
Trykk på bildet og lagre det. Det er også forhåndsvisningen når noen deler {pages.BASE}denne-helgen/

![Helgen i Ålesund]({img})

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
CAT_COLOR = {"konsert": "#1f6f78", "standup": "#b5531c", "show": "#6a4fa3", "barn": "#2f8a4c", "klubb": "#a83167", "happening": "#8a6d12", "sport": "#2b5fa8"}


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


def fit(draw, text, f, width):
    """Kort ned teksten med … så den får plass på én linje."""
    if draw.textlength(text, font=f) <= width:
        return text
    while text and draw.textlength(text + "…", font=f) > width:
        text = text[:-1]
    return text.rstrip(" ,–-") + "…"


def pick(evs, rows):
    """Fordel plassene jevnt på dagene, så søndag ikke forsvinner når fredag er full."""
    days = {}
    for e in evs:
        days.setdefault(e["date"], []).append(e)
    take = {d: 0 for d in days}
    left = rows - len(days)  # hver dag bruker én rad til overskrift
    while left > 0 and any(take[d] < len(v) for d, v in days.items()):
        for d, v in days.items():
            if left > 0 and take[d] < len(v):
                take[d] += 1
                left -= 1
    return {d: v[:take[d]] for d, v in days.items() if take[d]}


def render_image(evs, start, sun, out):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    pad = 80
    inner = W - 2 * pad
    f_eyebrow = font("Figtree.ttf", 30, weight=600)
    f_h1 = font("BricolageGrotesque.ttf", 132, weight=800, optical=96, width=100)
    f_span = font("BricolageGrotesque.ttf", 56, weight=800, optical=48, width=100)
    f_day = font("Figtree.ttf", 26, weight=700)
    f_title = font("BricolageGrotesque.ttf", 38, weight=700, optical=24, width=100)
    f_meta = font("Figtree.ttf", 28, weight=500)
    f_foot = font("Figtree.ttf", 28, weight=600)

    y = pad
    dr.text((pad, y), "SKJER I ÅLESUND", font=f_eyebrow, fill=SEA)
    y += 52
    dr.text((pad - 4, y), "I helgen", font=f_h1, fill=FG)
    y += 140
    dr.text((pad, y), pages.range_text(start, sun), font=f_span, fill=ACCENT)
    y += 100

    foot_y = H - pad - 34
    day_h, row_h = 54, 100
    rows = max(1, (foot_y - 40 - y) // row_h)
    chosen = pick(evs, rows + 1)  # dagsoverskriftene er lavere enn radene, så det er plass til litt mer
    shown = 0
    for date, items in chosen.items():
        if y + day_h + row_h > foot_y - 30:
            break
        d = datetime.date.fromisoformat(date)
        dr.text((pad, y), f"{pages.WD[d.weekday()].upper()} {d.day}. {pages.MO[d.month - 1].upper()}", font=f_day, fill=ACCENT)
        y += day_h
        for e in items:
            if y + row_h > foot_y - 30:
                break
            dr.rounded_rectangle((pad, y, pad + 8, y + row_h - 22), radius=4, fill=CAT_COLOR.get(e["cat"], SEA))
            x = pad + 30
            dr.text((x, y - 2), fit(dr, e["title"], f_title, inner - 30), font=f_title, fill=FG)
            meta = " · ".join(p for p in [e.get("time") and f"kl. {e['time']}", e["venue"], pages.price_text(e) if pages.price_text(e) != "Pris hos arrangør" else ""] if p)
            dr.text((x, y + 46), fit(dr, meta, f_meta, inner - 30), font=f_meta, fill=MUTED)
            y += row_h
            shown += 1
        y += 6
    if not evs:
        dr.text((pad, y), "Programmet fylles på fortløpende.", font=f_meta, fill=MUTED)

    dr.line((pad, foot_y - 26, W - pad, foot_y - 26), fill=LINE, width=2)
    rest = len(evs) - shown
    dr.text((pad, foot_y), f"+ {rest} til i helgen" if rest > 0 else "Priser og billetter på nettsiden", font=f_foot, fill=FG)
    site = "pedersen2k.github.io/skjer-i-alesund"
    dr.text((W - pad - dr.textlength(site, font=f_foot), foot_y), site, font=f_foot, fill=SEA)
    img.save(out, optimize=True)


def main():
    data = json.loads((pages.ROOT / "data" / "events.json").read_text())
    today = datetime.datetime.now(pages.TZ).date()
    start, sun = pages.weekend_range(today)
    evs = pages.occurrences([e for e in data["events"] if e["date"] >= today.isoformat()], start, sun)
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
