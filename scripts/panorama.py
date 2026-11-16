"""«Lørdagen i ett sveip»: en sømløs Instagram-karusell for lørdagen som kommer.

Ett langt panorama (1080 × 1350 per bilde) som deles i bilder: himmelen går fra ettermiddag til natt, en rute
med stopp går gjennom alle lørdagens arrangementer, og Ålesund-silhuetten fortsetter langs bunnen, så folk må
sveipe for å følge den. Om vinteren (30. okt – feb, som delingsbildet) faller det snø, takene har snø, nordlyset
står over nattehimmelen, og i julesesongen (1. nov – 6. jan) er ruta en lysslynge.

Bildene lages av scripts/pages.py ved hver publisering og ligger i denne-helgen/ (panorama-1.png …, og hele
stripa som panorama.jpg). Teksten lages av .github/workflows/panorama.yml torsdag kveld og legges i et issue,
så eieren får den på e-post. Alt kommer fra data/events.json. Ingenting finnes på.

Kjør: python3 scripts/panorama.py [fil]          (issue-teksten)
      python3 scripts/panorama.py --bilder mappe (bare bildene, for å se på dem lokalt)
"""
import datetime
import json
import math
import os
import sys
from pathlib import Path

import pages
import helgepost
from helgepost import font, no_emoji, fit
from delingsbilde import rng, bez, winter
from ukepost import ok

W1, H = 1080, 1350   # ett bilde
S = 2                # tegnes i dobbel størrelse og skaleres ned
MIN_EVENTS = 4       # færre enn dette: ingen post den uka
MAX_SLIDES = 10      # Instagram tar 10 bilder i en karusell
CARD_W = 440
HIGH, LOW = 240, 670           # toppen av kortene i øvre og nedre rad
GROUND = 64                    # bakken nederst, der bildetekstene står
ROUTE_Y, ROUTE_AMP = 1000, 22  # ruta (lysslyngen) går rett over byen
CITY_TOP, CITY_H = 1020, 330
# Plassering av kortene i hvert bilde: (x fra venstre kant, rad)
FIRST = [(60, LOW), (580, LOW)]
SLOTS = {1: [(320, LOW)], 2: [(60, HIGH), (580, LOW)], 3: [(60, HIGH), (340, LOW), (590, HIGH)]}
SKY = [(0, "#f6d3a2"), (.16, "#ee9f7c"), (.32, "#c56a7c"), (.48, "#6e3f78"), (.64, "#2d2b62"), (.82, "#141c45"), (1, "#0a1232")]
BULBS = ["#ff5d5d", "#ffd166", "#6cc98a", "#7ab8ff", "#ff9ac5"]
GOLD, CREAM, SNOW = "#ffd98a", "#fff3cf", "#f4f8fb"


def jul(today):
    return today.month in (11, 12) or (today.month == 1 and today.day <= 6)


def rgb(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def sky_at(t):
    for (t0, c0), (t1, c1) in zip(SKY, SKY[1:]):
        if t <= t1:
            return mix(rgb(c0), rgb(c1), (t - t0) / (t1 - t0))
    return rgb(SKY[-1][1])


def route_y(x, total):
    return ROUTE_Y + ROUTE_AMP * math.sin(x / total * math.pi * 2 * (total / 1600))


# --- Utvalg ---

def saturday(today):
    return pages.weekend_range(today)[1] - datetime.timedelta(days=1)


def sold_that_day(e, day):
    """Med mer enn seks forestillinger står utsolgte datoer bare i notatet («Utsolgt: 20. nov, 21. nov»)."""
    note = e.get("note") or ""
    if "Utsolgt:" not in note:
        return False
    listed = note.split("Utsolgt:", 1)[1].split("Flere")[0]
    return f"{day.day}. {pages.MO[day.month - 1][:3]}" in listed


def stops(events, day):
    evs = [e for e in pages.occurrences(events, day, day) if ok(e) and not sold_that_day(e, day)]
    return sorted(evs, key=lambda e: (e.get("time") or "00:00"))[:2 + 3 * (MAX_SLIDES - 1)]


def layout(evs):
    """Gir (bilde, x, rad) for hvert stopp, og antall bilder."""
    out, rest, k = [(0, x, r) for x, r in FIRST[:len(evs)]], evs[2:], 1
    while rest:
        m = len(rest[:3])
        out += [(k, x, r) for x, r in SLOTS[m]]
        rest, k = rest[3:], k + 1
    return out, max(k, 2)


def label(e):
    t = (e.get("time") or "").split(" og ")
    return " og ".join(t) if t[0] else "Hele dagen"


def meta(e):
    price = pages.price_text(e)
    price = "" if price == "Pris hos arrangør" else price
    return e["venue"], price


# --- Tegning ---

def draw_sky(img, total):
    from PIL import ImageDraw
    dr = ImageDraw.Draw(img)
    for x in range(0, total * S, 2):
        c = sky_at(x / (total * S))
        dr.line([(x, 0), (x, H * S)], fill=c, width=2)
    # Litt mørkere øverst, så teksten og stjernene står bedre
    from PIL import Image
    shade = Image.new("RGBA", img.size)
    sd = ImageDraw.Draw(shade)
    for y in range(0, 500 * S, 2):
        sd.line([(0, y), (total * S, y)], fill=(8, 10, 30, round(70 * (1 - y / (500 * S)))), width=2)
    img.alpha_composite(shade)


def glow(img, cx, cy, r, color, alpha, blur):
    from PIL import Image, ImageDraw, ImageFilter
    pad = int(r + blur * 3)
    layer = Image.new("RGBA", (pad * 2 * S, pad * 2 * S))
    ImageDraw.Draw(layer).ellipse(((pad - r) * S, (pad - r) * S, (pad + r) * S, (pad + r) * S), fill=rgb(color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur * S))
    dx, dy = int((cx - pad) * S), int((cy - pad) * S)
    sx, sy = max(0, -dx), max(0, -dy)  # alpha_composite tåler ikke negative koordinater
    layer = layer.crop((sx, sy, min(layer.width, img.width - dx), min(layer.height, img.height - dy)))
    img.alpha_composite(layer, (dx + sx, dy + sy))


def draw_lights(img, total, snowy):
    from PIL import Image, ImageDraw, ImageFilter
    dr = ImageDraw.Draw(img)
    # Lav vintersol på første bilde, solnedgangsglød mot slutten av dagen, måne på siste bilde
    sx, sy, sr = 900, 500, 80
    glow(img, sx, sy, 180, "#fff3cf", 70, 55)
    dr.ellipse(((sx - sr) * S, (sy - sr) * S, (sx + sr) * S, (sy + sr) * S), fill=rgb("#fff1c8"))
    glow(img, total * .42, 980, 320, "#ffae6b", 110, 120)
    r = rng(7)
    stars = Image.new("RGBA", img.size)
    st = ImageDraw.Draw(stars)
    for _ in range(int(total / 9)):
        x = total * (.5 + r() * .5)
        y = r() * 640
        if r() < (x / total - .45) * 1.8:
            s = 1.5 + r() * 2.5
            st.ellipse(((x - s) * S, (y - s) * S, (x + s) * S, (y + s) * S), fill=(255, 247, 234, round(150 + r() * 105)))
    img.alpha_composite(stars)
    if snowy:  # nordlys over nattehimmelen
        aur = Image.new("RGBA", img.size)
        ad = ImageDraw.Draw(aur)
        for band, (col, a, y0, amp, wdt) in enumerate([("#5effb0", 170, 210, 70, 80), ("#3fd6c8", 130, 300, 90, 56), ("#a77bff", 90, 160, 50, 44)]):
            pts = []
            x0 = total * .55
            for i in range(0, 260):
                x = x0 + (total - x0 + 200) * i / 259
                y = y0 + amp * math.sin(i / 18 + band) + 30 * math.sin(i / 7 + band * 2)
                pts.append((x * S, y * S))
            ad.line(pts, fill=rgb(col, a), width=wdt * S, joint="curve")
        aur = aur.filter(ImageFilter.GaussianBlur(28 * S))
        img.alpha_composite(aur)
    mx, my = total - 170, 170
    glow(img, mx, my, 120, "#fff3cf", 50, 50)
    moon = Image.new("RGBA", img.size)
    md = ImageDraw.Draw(moon)
    md.ellipse(((mx - 82) * S, (my - 82) * S, (mx + 82) * S, (my + 82) * S), fill=rgb("#fff3cf"))
    md.ellipse(((mx - 82 + 46) * S, (my - 82 - 22) * S, (mx + 82 + 46) * S, (my + 82 - 22) * S), fill=(0, 0, 0, 0))
    img.alpha_composite(moon)


def draw_city(img, total, snowy):
    """Jugendgavler, tårn og runde tak langs hele stripa, med lys i vinduene og snø på takene om vinteren."""
    from PIL import ImageDraw
    dr = ImageDraw.Draw(img)
    r = rng(47)
    oy, h = CITY_TOP, CITY_H
    P = lambda pts: [(x * S, (y + oy) * S) for x, y in pts]
    caps, wins = [], []
    x = -20
    while x < total + 20:
        bw, top, kind = 90 + r() * 120, h * (.3 + r() * .38), r()
        if kind < .4:
            peak = top - 40 - r() * 50
            shape = [(x, h), (x, top), (x + bw / 2, peak), (x + bw, top), (x + bw, h)]
            caps.append([(x - 3, top + 3), (x + bw / 2, peak - 3), (x + bw + 3, top + 3)])
        elif kind < .62:
            s = 18 + r() * 8
            shape = [(x, h), (x, top), (x, top - s), (x + bw * .2, top - s), (x + bw * .2, top - 2 * s), (x + bw * .8, top - 2 * s),
                     (x + bw * .8, top - s), (x + bw, top - s), (x + bw, h)]
            caps.append([(x + bw * .2, top - 2 * s), (x + bw * .8, top - 2 * s)])
            caps.append([(x - 2, top - s), (x + bw * .2, top - s)])
            caps.append([(x + bw * .8, top - s), (x + bw + 2, top - s)])
        elif kind < .8:
            t = top - 90 - r() * 50
            shape = [(x, h), (x, top), (x + bw * .35, top), (x + bw * .35, t + 34), (x + bw * .5, t), (x + bw * .65, t + 34),
                     (x + bw * .65, top), (x + bw, top), (x + bw, h)]
            caps.append([(x + bw * .33, t + 35), (x + bw * .5, t - 2), (x + bw * .67, t + 35)])
        else:
            arc = bez((x, top), (x + bw / 2, top - 70), (x + bw, top))
            shape = [(x, h), (x, top)] + arc + [(x + bw, h)]
            caps.append([(x, top - 2)] + arc)
        dr.polygon(P(shape), fill=rgb("#0b2a2f"))
        wy = top + 26
        while wy < h - GROUND - 40:
            wx = x + 18
            while wx < x + bw - 30:
                if r() < .3:
                    wins.append((wx, wy))
                wx += 38
            wy += 52
        x += bw + (10 if r() < .25 else 0)
    for wx, wy in wins:
        dr.rounded_rectangle(P([(wx, wy), (wx + 16, wy + 24)]), radius=4 * S, fill=rgb("#ffcf6e", 235))
    if snowy:
        for c in caps:
            dr.line(P(c), fill=rgb(SNOW), width=10 * S, joint="curve")
    # Bakken: snø om vinteren, ellers kai
    ground = SNOW if snowy else "#07161a"
    dr.rectangle(P([(0, h - GROUND), (total, h)]), fill=rgb(ground))
    if snowy:
        dr.rectangle(P([(0, h - GROUND), (total, h - GROUND + 6)]), fill=rgb("#c9d9e6"))


def draw_snowfall(img, total):
    from PIL import Image, ImageDraw
    snow = Image.new("RGBA", img.size)
    sd = ImageDraw.Draw(snow)
    r = rng(11)
    for _ in range(int(total / 6)):
        x, y, s, o = r() * total, r() * (H - 40), 2 + r() * 4.5, .35 + r() * .5
        sd.ellipse(((x - s) * S, (y - s) * S, (x + s) * S, (y + s) * S), fill=(255, 255, 255, round(o * 255)))
    img.alpha_composite(snow)


def draw_route(img, total, xmas, pins):
    """Ruta gjennom dagen. I julesesongen en lysslynge med fargede pærer, ellers prikker."""
    from PIL import Image, ImageDraw, ImageFilter
    dr = ImageDraw.Draw(img)
    pts = [(x * S, route_y(x, total) * S) for x in range(0, total + 1, 8)]
    if xmas:
        dr.line(pts, fill=rgb("#1b1d2a"), width=3 * S, joint="curve")
        halo = Image.new("RGBA", img.size)
        hd = ImageDraw.Draw(halo)
        bulbs = []
        for i, x in enumerate(range(20, total, 44)):
            y = route_y(x, total) + 10
            col = BULBS[i % len(BULBS)]
            bulbs.append((x, y, col))
            hd.ellipse(((x - 16) * S, (y - 16) * S, (x + 16) * S, (y + 16) * S), fill=rgb(col, 150))
        img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(10 * S)))
        dr = ImageDraw.Draw(img)
        for x, y, col in bulbs:
            dr.line([(x * S, (y - 12) * S), (x * S, (y - 6) * S)], fill=rgb("#1b1d2a"), width=4 * S)
            dr.ellipse(((x - 6) * S, (y - 7) * S, (x + 6) * S, (y + 9) * S), fill=rgb(col))
    else:
        for x in range(0, total, 24):
            y = route_y(x, total)
            dr.ellipse(((x - 3) * S, (y - 3) * S, (x + 3) * S, (y + 3) * S), fill=rgb(CREAM, 240))
    for x, y0, y1 in pins:
        dr.line([(x * S, y0 * S), (x * S, y1 * S)], fill=rgb(CREAM, 230), width=4 * S)
        glow(img, x, y1, 26, GOLD, 160, 12)
        dr = ImageDraw.Draw(img)
        dr.ellipse(((x - 15) * S, (y1 - 15) * S, (x + 15) * S, (y1 + 15) * S), fill=rgb(CREAM), outline=rgb("#0b2a2f"), width=5 * S)


def wrap(dr, text, f, width, max_lines=3):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        test = f"{cur} {wd}".strip()
        if cur and dr.textlength(test, font=f) > width:
            lines.append(cur)
            cur = wd
        else:
            cur = test
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = fit(dr, lines[-1] + " …", f, width)
    return lines


def card(img, e, x, y, total, low=False):
    """Ett stopp: klokkeslett, tittel og sted · pris på et mørkt kort i himmelens farge. Gir bunnen av kortet."""
    from PIL import Image, ImageDraw
    f_t, f_m = font("JetBrainsMono.ttf", 46 * S, weight=700), font("Figtree.ttf", 32 * S, weight=500)
    probe = ImageDraw.Draw(img)
    inner = (CARD_W - 60) * S
    # Tittelen er 50 px, men mindre når et langt ord («Lørdagsomvisning») ellers går utenfor kortet
    size = 50
    while True:
        f_h = font("BricolageGrotesque.ttf", size * S, weight=700, optical=48, width=100)
        words_fit = max(probe.textlength(w, font=f_h) for w in no_emoji(e["title"]).split() or [""]) <= inner
        lone = any(len(ln) <= 2 for ln in wrap(probe, no_emoji(e["title"]), f_h, inner)[:-1])  # ikke «i» alene på en linje
        if size <= 38 or (words_fit and not lone):
            break
        size -= 2
    title = wrap(probe, no_emoji(e["title"]), f_h, inner)
    venue, price = meta(e)
    venue = fit(probe, venue, f_m, inner)
    lh = size + 2
    hgt = 26 + 56 + 6 + lh * len(title) + 10 + 40 + (40 if price else 0) + 26
    if low:  # nedre rad: bunnen av kortet holder seg over lysslyngen
        y = min(y, route_y(x + CARD_W / 2, total) - 44 - hgt)
    base = mix(sky_at((x + CARD_W / 2) / total), rgb("#0a0e1e"), .72)
    layer = Image.new("RGBA", img.size)
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((x * S, y * S, (x + CARD_W) * S, (y + hgt) * S), radius=24 * S, fill=base[:3] + (222,))
    img.alpha_composite(layer)
    dr = ImageDraw.Draw(img)
    cx, cy = (x + 30) * S, (y + 26) * S
    dot = helgepost_color(e["cat"])
    dr.text((cx, cy), label(e), font=f_t, fill=rgb(GOLD))
    tw = dr.textlength(label(e), font=f_t)
    dr.ellipse((cx + tw + 16 * S, cy + 18 * S, cx + tw + 32 * S, cy + 34 * S), fill=rgb(dot))
    cy += 62 * S
    for ln in title:
        dr.text((cx, cy), ln, font=f_h, fill=rgb("#fff7ea"))
        cy += lh * S
    dr.text((cx, cy + 10 * S), venue, font=f_m, fill=rgb("#efdcc8"))
    if price:
        dr.text((cx, cy + 50 * S), price, font=font("Figtree.ttf", 32 * S, weight=700), fill=rgb(GOLD))
    return y + hgt


def helgepost_color(cat):
    return {"konsert": "#5ab7bf", "standup": "#f08a4b", "show": "#ab93e6", "barn": "#6cc98a", "klubb": "#ec78ab",
            "happening": "#d9b84a", "quiz": "#b497e0", "sport": "#7aa7e6"}.get(cat, "#d9b84a")


def phase(e):
    h = int((e.get("time") or "12:00")[:2])
    return "Formiddag" if h < 12 else "Ettermiddag" if h < 17 else "Kveld" if h < 22 else "Natt"


def render(evs, day, today, folder):
    """Lager panorama-1.png … og hele stripa som panorama.jpg i folder. Gir filnavnene tilbake."""
    from PIL import Image, ImageDraw
    places, n = layout(evs)
    total = W1 * n
    snowy, xmas = winter(today), jul(today)
    img = Image.new("RGBA", (total * S, H * S))
    draw_sky(img, total)
    draw_lights(img, total, snowy)
    if snowy:
        draw_snowfall(img, total)

    # Kortene først på et eget lag for å finne høyden, så pinnene kan gå fra kortet ned til ruta
    cards = Image.new("RGBA", img.size)
    pins = []
    for e, (k, x, row) in zip(evs, places):
        X = k * W1 + x
        bottom = card(cards, e, X, row, total, row == LOW)
        pins.append((X + CARD_W / 2, bottom, route_y(X + CARD_W / 2, total)))
    draw_city(img, total, snowy)
    draw_route(img, total, xmas, pins)
    img.alpha_composite(cards)

    dr = ImageDraw.Draw(img)
    ink = rgb("#2a1408")
    dr.text((70 * S, 80 * S), "KASKJERDA.NO", font=font("JetBrainsMono.ttf", 34 * S, weight=700), fill=ink)
    head, hs = f"{pages.WD[day.weekday()].capitalize()} i Ålesund", 150
    while hs > 90 and dr.textlength(head, font=font("BricolageGrotesque.ttf", hs * S, weight=800, optical=96, width=100)) > (W1 - 130) * S:
        hs -= 4  # overskriften må holde seg på første bilde
    dr.text((62 * S, (120 + (150 - hs) * .6) * S), head, font=font("BricolageGrotesque.ttf", hs * S, weight=800, optical=96, width=100), fill=ink)
    dr.text((70 * S, 290 * S), f"{day.day}. {pages.MO[day.month - 1]} · sveip deg gjennom dagen →",
            font=font("BricolageGrotesque.ttf", 50 * S, weight=700, optical=48, width=100), fill=ink)
    f_l = font("BricolageGrotesque.ttf", 40 * S, weight=700, optical=40, width=100)
    labels = {0: "Sveip →"}
    for e, (k, x, row) in zip(evs, places):
        if k:
            labels[k] = phase(e)
    last = "Hele helga på kaskjerda.no"
    for k in range(n):
        txt = labels.get(k, "")
        lx = k * W1 + 70
        if k == n - 1:
            txt = last if k else txt
            lx = (k + 1) * W1 - 60 - dr.textlength(txt, font=f_l) / S
        if txt:
            dr.text((lx * S, (H - GROUND + 8) * S), txt, font=f_l, fill=rgb("#0b2a2f" if snowy else GOLD))

    full = img.resize((total, H), Image.LANCZOS).convert("RGB")
    names = [f"panorama-{i}.png" for i in range(1, n + 1)]
    for i, name in enumerate(names):
        full.crop((i * W1, 0, (i + 1) * W1, H)).save(folder / name, optimize=True)
    full.resize((total // 2, H // 2), Image.LANCZOS).save(folder / "panorama.jpg", quality=86)
    return names


def plan(today):
    events = json.loads((pages.ROOT / "data" / "events.json").read_text())["events"]
    day = saturday(today)
    return day, stops([e for e in events if e["cat"] not in pages.SEPARATE], day)


def render_all(today, folder):
    """Kalles fra pages.py ved hver publisering."""
    folder.mkdir(parents=True, exist_ok=True)
    for old in list(folder.glob("panorama-*.png")) + list(folder.glob("panorama.jpg")):
        old.unlink()
    day, evs = plan(today)
    return render(evs, day, today, folder) if len(evs) >= MIN_EVENTS else []


def caption(day, evs):
    lines = [f"Hele lørdagen i Ålesund, {day.day}. {pages.MO[day.month - 1]} ✨", "Sveip deg gjennom dagen, fra første til siste stopp:", ""]
    for e in evs:
        venue, price = meta(e)
        lines.append(f"▪️ {label(e)} {no_emoji(e['title'])}, {venue}" + (f" – {price.lower()}" if price else ""))
    sun = day + datetime.timedelta(days=1)
    return "\n".join(lines + ["", "🎟️ Hele helga med priser og billettlenker: kaskjerda.no (lenke i bio)",
                              "💾 Lagre innlegget og send det til den du skal ut med!", "",
                              " ".join(helgepost.hashtags(evs, day - datetime.timedelta(days=1), sun))])


def body(day, evs, names, v):
    imgs = "\n\n".join(f"![Lørdagen i ett sveip, bilde {i}]({pages.BASE}denne-helgen/{n}?v={v})" for i, n in enumerate(names, 1))
    return f"""Her er «Lørdagen i ett sveip» for {pages.WD[day.weekday()]} {day.day}. {pages.MO[day.month - 1]}: {len(evs)} stopp på {len(names)} bilder. Post den fredag eller lørdag morgen.

### Slik ser hele panoramaet ut
![Hele panoramaet]({pages.BASE}denne-helgen/panorama.jpg?v={v})

### Bilder (Instagram-karusell, 1080 × 1350)
Trykk på hvert bilde og lagre det. Legg dem ut i denne rekkefølgen som én karusell, så henger bildene sammen når man sveiper.

{imgs}

### Bildetekst
```text
{caption(day, evs)}
```

Utvalget er laget automatisk (ikke julebord, utsolgte eller usikre arrangementer). Sjekk gjerne lista før du poster; programmet hentes automatisk og kan endre seg. Dette issuet lukkes når neste ukes panorama kommer.
"""


def main():
    today = datetime.datetime.now(pages.TZ).date()
    if len(sys.argv) > 2 and sys.argv[1] == "--bilder":
        folder = Path(sys.argv[2])
        print(render_all(today, folder))
        return
    day, evs = plan(today)
    title = f"Lørdagen i ett sveip: {day.day}. {pages.MO[day.month - 1]}"
    skip = len(evs) < MIN_EVENTS
    n = layout(evs)[1]
    text = "" if skip else body(day, evs, [f"panorama-{i}.png" for i in range(1, n + 1)], today.isoformat())
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text)
    else:
        print(title + "\n\n" + text)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"title={title}\nskip={'true' if skip else 'false'}\n")


if __name__ == "__main__":
    main()
