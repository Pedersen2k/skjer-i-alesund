"""«Helga i ett sveip»: en sømløs Instagram-karusell for helga som kommer, fredag til søndag.

Ett langt panorama (1080 × 1350 per bilde) som deles i bilder. En rute med stopp går gjennom alle helgas
arrangementer i tidsrekkefølge, og himmelen følger klokka: kveld og natt, soloppgang mellom dagene, dag og ny
kveld. Ålesund-silhuetten fortsetter langs bunnen, og et skilt i byen viser hvor en ny dag begynner, så folk
må sveipe for å følge helga. Om vinteren (30. okt – feb, som delingsbildet) faller det snø, takene har snø og
nordlyset står over nattehimmelen; i julesesongen (1. nov – 6. jan) er ruta en lysslynge.

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
from ukepost import ok, n_dates

W1, H = 1080, 1350   # ett bilde
S = 2                # tegnes i dobbel størrelse og skaleres ned
MIN_EVENTS = 4       # færre enn dette: ingen post den uka
MAX_SLIDES = 10      # Instagram tar 10 bilder i en karusell
MAX_STOPS = 2 + 3 * (MAX_SLIDES - 1)
CARD_W = 440
HIGH, LOW = 240, 670           # toppen av kortene i øvre og nedre rad
GROUND = 64                    # bakken nederst, der bildetekstene står
ROUTE_Y, ROUTE_AMP = 1000, 22  # ruta (lysslyngen) går rett over byen
CITY_TOP, CITY_H = 1020, 330
SIGN_Y = 1150                  # dagsskiltet står i byen
# Plassering av kortene i hvert bilde: (x fra venstre kant, rad)
FIRST = [(60, LOW), (580, LOW)]
SLOTS = {1: [(320, LOW)], 2: [(60, HIGH), (580, LOW)], 3: [(60, HIGH), (340, LOW), (590, HIGH)]}
# Himmelens farge etter klokkeslett (timer), fra natt via soloppgang og dag til ny natt
SKY = [(0, "#0a1232"), (5, "#0a1232"), (7, "#3a2c5e"), (8, "#c56a7c"), (9, "#ee9f7c"), (10, "#f6d3a2"), (14, "#f6d3a2"),
       (15, "#ee9f7c"), (16, "#c56a7c"), (17, "#6e3f78"), (18.5, "#2d2b62"), (20.5, "#141c45"), (22, "#0a1232"), (24, "#0a1232")]
BULBS = ["#ff5d5d", "#ffd166", "#6cc98a", "#7ab8ff", "#ff9ac5"]
GOLD, CREAM, SNOW, CITY = "#ffd98a", "#fff3cf", "#f4f8fb", "#0b2a2f"
CAT_DOT = {"konsert": "#5ab7bf", "standup": "#f08a4b", "show": "#ab93e6", "barn": "#6cc98a", "klubb": "#ec78ab",
           "happening": "#d9b84a", "quiz": "#b497e0", "sport": "#7aa7e6"}
WD3 = ["MAN", "TIR", "ONS", "TOR", "FRE", "LØR", "SØN"]


def jul(today):
    return today.month in (11, 12) or (today.month == 1 and today.day <= 6)


def rgb(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def sky_color(hour):
    h = hour % 24
    for (h0, c0), (h1, c1) in zip(SKY, SKY[1:]):
        if h <= h1:
            return mix(rgb(c0), rgb(c1), (h - h0) / (h1 - h0))
    return rgb(SKY[-1][1])


def night(hour):
    """1 midt på natta, 0 midt på dagen."""
    h = hour % 24
    if 9 <= h <= 15:
        return 0.0
    if h >= 21 or h <= 5:
        return 1.0
    return (h - 15) / 6 if h > 15 else (9 - h) / 4


def route_y(x):
    return ROUTE_Y + ROUTE_AMP * math.sin(x / 1600 * math.pi * 2)


# --- Utvalg ---

def sold_that_day(e, day):
    """Med mer enn seks forestillinger står utsolgte datoer bare i notatet («Utsolgt: 20. nov, 21. nov»)."""
    note = e.get("note") or ""
    if "Utsolgt:" not in note:
        return False
    return f"{day.day}. {pages.MO[day.month - 1][:3]}" in note.split("Utsolgt:", 1)[1].split("Flere")[0]


def hour_of(e):
    t = (e.get("time") or "").split(" og ")[0]
    return int(t[:2]) + int(t[3:5]) / 60 if t else 11.0


def stops(events, start, end):
    evs, d = [], start
    while d <= end:
        evs += [{**e, "_day": (d - start).days} for e in pages.occurrences(events, d, d) if ok(e) and not sold_that_day(e, d)]
        d += datetime.timedelta(days=1)
    if len(evs) > MAX_STOPS:
        # For mange til ti bilder: gjentatte klubbkvelder og serier går ut først, så alle dagene er med
        keep = sorted(evs, key=lambda e: (n_dates(e) > 3, e["cat"] == "klubb", -e["_day"]))[:MAX_STOPS]
        evs = [e for e in evs if any(e is k for k in keep)]
    return sorted(evs, key=lambda e: (e["_day"], e.get("time") or "00:00"))


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
    return e["venue"], "" if price == "Pris hos arrangør" else price


class Timeline:
    """Klokka langs panoramaet: timer (fredag 0–24, lørdag 24–48 …) for hver x, lineært mellom stoppene.
    Mellom to dager går den gjennom natta og soloppgangen."""

    def __init__(self, xs, hours, total):
        pts = sorted(zip(xs, hours))
        self.pts = [(0, pts[0][1] - 2)] + pts + [(total, pts[-1][1] + 1.5)]

    def __call__(self, x):
        for (x0, h0), (x1, h1) in zip(self.pts, self.pts[1:]):
            if x <= x1:
                return h0 + (h1 - h0) * ((x - x0) / (x1 - x0) if x1 > x0 else 0)
        return self.pts[-1][1]


# --- Tegning ---

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


def inside(x, margin):
    """Flytter x så noe med denne halve bredden ikke havner over skjøten mellom to bilder."""
    k = int(x // W1)
    return min(max(x, k * W1 + margin), (k + 1) * W1 - margin)


def draw_sky(img, total, tl):
    """Én farge per kolonne etter klokka, glattet sideveis så natt, soloppgang og dag glir over i hverandre."""
    from PIL import Image, ImageDraw, ImageFilter
    strip = Image.new("RGB", (total, 1))
    strip.putdata([sky_color(tl(x))[:3] for x in range(total)])
    pad = 600
    wide = Image.new("RGB", (total + 2 * pad, 40))
    wide.paste(strip.resize((total, 40)), (pad, 0))
    wide.paste(strip.crop((0, 0, 1, 1)).resize((pad, 40)), (0, 0))
    wide.paste(strip.crop((total - 1, 0, total, 1)).resize((pad, 40)), (total + pad, 0))
    wide = wide.filter(ImageFilter.GaussianBlur(160))
    img.paste(wide.crop((pad, 20, pad + total, 21)).resize(img.size), (0, 0))
    dr = ImageDraw.Draw(img)
    shade = Image.new("RGBA", img.size)  # litt mørkere øverst, så teksten og stjernene står bedre
    sd = ImageDraw.Draw(shade)
    for y in range(0, 500 * S, 2):
        sd.line([(0, y), (total * S, y)], fill=(8, 10, 30, round(70 * (1 - y / (500 * S)))), width=2)
    img.alpha_composite(shade)


def draw_lights(img, total, tl, snowy):
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    # Sola der det er dag, månen midt i hver natt
    xs = list(range(0, total, 20))
    day = lambda x: 11.5 <= tl(x) % 24 <= 15
    suns = [x for x in xs if day(x) and (x < 40 or not day(x - 20)) and all(day(x + d) for d in range(0, 500, 20))]
    for x in suns:
        sx, sy = (900, 500) if x < W1 else (inside(x + 250, 140), 140)  # over kortene, eller ved tittelen på første bilde
        glow(img, sx, sy, 180, "#fff3cf", 70, 55)
        ImageDraw.Draw(img).ellipse(((sx - 80) * S, (sy - 80) * S, (sx + 80) * S, (sy + 80) * S), fill=rgb("#fff1c8"))
    run = []
    for x in xs + [total]:
        if x < total and night(tl(x)) > .9:
            run.append(x)
        elif run:
            if run[-1] - run[0] >= 300:
                mx, my = inside((run[0] + run[-1]) / 2, 150), 170
                glow(img, mx, my, 120, "#fff3cf", 50, 50)
                moon = Image.new("RGBA", img.size)
                md = ImageDraw.Draw(moon)
                md.ellipse(((mx - 82) * S, (my - 82) * S, (mx + 82) * S, (my + 82) * S), fill=rgb("#fff3cf"))
                md.ellipse(((mx - 36) * S, (my - 104) * S, (mx + 128) * S, (my + 60) * S), fill=(0, 0, 0, 0))
                img.alpha_composite(moon)
            run = []
    r = rng(7)
    stars = Image.new("RGBA", img.size)
    st = ImageDraw.Draw(stars)
    for _ in range(int(total / 5)):
        x, y = r() * total, r() * 680
        if r() < night(tl(x)) * .8:
            s = 1.5 + r() * 2.5
            st.ellipse(((x - s) * S, (y - s) * S, (x + s) * S, (y + s) * S), fill=(255, 247, 234, round(150 + r() * 105)))
    img.alpha_composite(stars)
    if snowy:  # nordlys, bare der det er natt
        aur = Image.new("RGBA", img.size)
        ad = ImageDraw.Draw(aur)
        for band, (col, a, y0, amp, wdt) in enumerate([("#5effb0", 170, 210, 70, 80), ("#3fd6c8", 130, 300, 90, 56), ("#a77bff", 90, 160, 50, 44)]):
            n = max(60, total // 16)
            pts = [((-100 + (total + 200) * i / (n - 1)) * S,
                    (y0 + amp * math.sin(i / 18 + band) + 30 * math.sin(i / 7 + band * 2)) * S) for i in range(n)]
            ad.line(pts, fill=rgb(col, a), width=wdt * S, joint="curve")
        aur = aur.filter(ImageFilter.GaussianBlur(28 * S))
        mask = Image.new("L", (total, 1))
        mask.putdata([round(255 * max(0, night(tl(x)) - .3) / .7) for x in range(total)])
        mask = mask.resize(aur.size)
        aur.putalpha(ImageChops.multiply(aur.getchannel("A"), mask))
        img.alpha_composite(aur)


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
            caps += [[(x + bw * .2, top - 2 * s), (x + bw * .8, top - 2 * s)], [(x - 2, top - s), (x + bw * .2, top - s)],
                     [(x + bw * .8, top - s), (x + bw + 2, top - s)]]
        elif kind < .8:
            t = top - 90 - r() * 50
            shape = [(x, h), (x, top), (x + bw * .35, top), (x + bw * .35, t + 34), (x + bw * .5, t), (x + bw * .65, t + 34),
                     (x + bw * .65, top), (x + bw, top), (x + bw, h)]
            caps.append([(x + bw * .33, t + 35), (x + bw * .5, t - 2), (x + bw * .67, t + 35)])
        else:
            arc = bez((x, top), (x + bw / 2, top - 70), (x + bw, top))
            shape = [(x, h), (x, top)] + arc + [(x + bw, h)]
            caps.append([(x, top - 2)] + arc)
        dr.polygon(P(shape), fill=rgb(CITY))
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
    dr.rectangle(P([(0, h - GROUND), (total, h)]), fill=rgb(SNOW if snowy else "#07161a"))
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


def draw_signs(img, signs):
    """Et skilt i byen der en ny dag begynner («LØRDAG 21. NOV»)."""
    from PIL import ImageDraw
    dr = ImageDraw.Draw(img)
    f = font("JetBrainsMono.ttf", 34 * S, weight=800)
    for x, text in signs:
        w = dr.textlength(text, font=f) / S + 48
        x = inside(x, w / 2 + 30)
        dr.rectangle(((x - 4) * S, (SIGN_Y + 30) * S, (x + 4) * S, (H - GROUND) * S), fill=rgb("#3a2a1a"))
        dr.rounded_rectangle(((x - w / 2) * S, (SIGN_Y - 34) * S, (x + w / 2) * S, (SIGN_Y + 34) * S), radius=14 * S,
                             fill=rgb(GOLD), outline=rgb("#3a2a1a"), width=4 * S)
        dr.text((x * S, SIGN_Y * S), text, font=f, fill=rgb(CITY), anchor="mm")


def draw_route(img, total, xmas, pins):
    """Ruta gjennom helga. I julesesongen en lysslynge med fargede pærer, ellers prikker."""
    from PIL import Image, ImageDraw, ImageFilter
    dr = ImageDraw.Draw(img)
    if xmas:
        dr.line([(x * S, route_y(x) * S) for x in range(0, total + 1, 8)], fill=rgb("#1b1d2a"), width=3 * S, joint="curve")
        halo = Image.new("RGBA", img.size)
        hd = ImageDraw.Draw(halo)
        bulbs = []
        for i, x in enumerate(range(20, total, 44)):
            y = route_y(x) + 10
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
            y = route_y(x)
            dr.ellipse(((x - 3) * S, (y - 3) * S, (x + 3) * S, (y + 3) * S), fill=rgb(CREAM, 240))
    for x, y0, y1 in pins:
        dr.line([(x * S, y0 * S), (x * S, y1 * S)], fill=rgb(CREAM, 230), width=4 * S)
        glow(img, x, y1, 26, GOLD, 160, 12)
        dr = ImageDraw.Draw(img)
        dr.ellipse(((x - 15) * S, (y1 - 15) * S, (x + 15) * S, (y1 + 15) * S), fill=rgb(CREAM), outline=rgb(CITY), width=5 * S)


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


def card(img, e, x, y, sky, low=False):
    """Ett stopp: dag og klokkeslett, tittel, sted og pris på et mørkt kort i himmelens farge. Gir bunnen av kortet."""
    from PIL import Image, ImageDraw
    f_t, f_d, f_m = font("JetBrainsMono.ttf", 46 * S, weight=700), font("JetBrainsMono.ttf", 26 * S, weight=800), font("Figtree.ttf", 32 * S, weight=500)
    probe = ImageDraw.Draw(img)
    inner = (CARD_W - 60) * S
    name = no_emoji(e["title"])
    # Tittelen er 50 px, men mindre når et langt ord ellers går utenfor kortet, eller et kort ord blir alene på en linje
    size = 50
    while True:
        f_h = font("BricolageGrotesque.ttf", size * S, weight=700, optical=48, width=100)
        words_fit = max(probe.textlength(w, font=f_h) for w in name.split() or [""]) <= inner
        lone = any(len(ln) <= 2 for ln in wrap(probe, name, f_h, inner)[:-1])
        if size <= 38 or (words_fit and not lone):
            break
        size -= 2
    title = wrap(probe, name, f_h, inner)
    venue, price = meta(e)
    venue = fit(probe, venue, f_m, inner)
    lh = size + 2
    hgt = 26 + 56 + 6 + lh * len(title) + 10 + 40 + (40 if price else 0) + 26
    if low:  # nedre rad: bunnen av kortet holder seg over lysslyngen
        y = min(y, route_y(x + CARD_W / 2) - 44 - hgt)
    base = mix(sky, rgb("#0a0e1e"), .72)
    layer = Image.new("RGBA", img.size)
    ImageDraw.Draw(layer).rounded_rectangle((x * S, y * S, (x + CARD_W) * S, (y + hgt) * S), radius=24 * S, fill=base[:3] + (222,))
    img.alpha_composite(layer)
    dr = ImageDraw.Draw(img)
    cx, cy = (x + 30) * S, (y + 26) * S
    day = WD3[datetime.date.fromisoformat(e["date"]).weekday()]
    dw = dr.textlength(day, font=f_d) + 24 * S
    dr.rounded_rectangle((cx, cy + 8 * S, cx + dw, cy + 50 * S), radius=10 * S, fill=rgb(GOLD))
    dr.text((cx + dw / 2, cy + 29 * S), day, font=f_d, fill=rgb(CITY), anchor="mm")
    tx = cx + dw + 16 * S
    lab = label(e)
    if dr.textlength(lab, font=f_t) > inner - (tx - cx) - 30 * S:
        lab = lab.split(" og ")[0] + " +"
    dr.text((tx, cy), lab, font=f_t, fill=rgb(GOLD))
    tw = dr.textlength(lab, font=f_t)
    dr.ellipse((tx + tw + 14 * S, cy + 20 * S, tx + tw + 30 * S, cy + 36 * S), fill=rgb(CAT_DOT.get(e["cat"], "#d9b84a")))
    cy += 62 * S
    for ln in title:
        dr.text((cx, cy), ln, font=f_h, fill=rgb("#fff7ea"))
        cy += lh * S
    dr.text((cx, cy + 10 * S), venue, font=f_m, fill=rgb("#efdcc8"))
    if price:
        dr.text((cx, cy + 50 * S), price, font=font("Figtree.ttf", 32 * S, weight=700), fill=rgb(GOLD))
    return y + hgt


def phase(e):
    h = hour_of(e)
    return "formiddag" if h < 12 else "ettermiddag" if h < 17 else "kveld" if h < 22 else "natt"


def render(evs, start, end, today, folder):
    """Lager panorama-1.png … og hele stripa som panorama.jpg i folder. Gir filnavnene tilbake."""
    from PIL import Image, ImageDraw
    places, n = layout(evs)
    total = W1 * n
    snowy, xmas = winter(today), jul(today)
    centers = [k * W1 + x + CARD_W / 2 for k, x, _ in places]
    tl = Timeline(centers, [e["_day"] * 24 + hour_of(e) for e in evs], total)
    img = Image.new("RGBA", (total * S, H * S))
    draw_sky(img, total, tl)
    draw_lights(img, total, tl, snowy)
    if snowy:
        draw_snowfall(img, total)

    # Kortene på et eget lag først, så pinnene kan gå fra kortet ned til ruta
    cards = Image.new("RGBA", img.size)
    pins = []
    for e, (k, x, row), c in zip(evs, places, centers):
        bottom = card(cards, e, k * W1 + x, row, sky_color(tl(c)), row == LOW)
        pins.append((c, bottom, route_y(c)))
    draw_city(img, total, snowy)
    signs = []
    for i, e in enumerate(evs):
        if i == 0 or e["_day"] != evs[i - 1]["_day"]:
            d = datetime.date.fromisoformat(e["date"])
            x = centers[i] if i == 0 else (centers[i - 1] + centers[i]) / 2
            signs.append((x, f"{pages.WD[d.weekday()].upper()} {d.day}. {pages.MO[d.month - 1][:3].upper()}"))
    draw_signs(img, signs)
    draw_route(img, total, xmas, pins)
    img.alpha_composite(cards)

    dr = ImageDraw.Draw(img)
    ink = rgb("#2a1408") if night(tl(500)) < .45 else rgb(CREAM)
    dr.text((70 * S, 80 * S), "KASKJERDA.NO", font=font("JetBrainsMono.ttf", 34 * S, weight=700), fill=ink)
    head, hs = "Helga i Ålesund", 150
    while hs > 90 and dr.textlength(head, font=font("BricolageGrotesque.ttf", hs * S, weight=800, optical=96, width=100)) > (W1 - 130) * S:
        hs -= 4  # overskriften må holde seg på første bilde
    dr.text((62 * S, (120 + (150 - hs) * .6) * S), head, font=font("BricolageGrotesque.ttf", hs * S, weight=800, optical=96, width=100), fill=ink)
    dr.text((70 * S, 290 * S), f"{pages.range_text(start, end)} · sveip deg gjennom helga →",
            font=font("BricolageGrotesque.ttf", 50 * S, weight=700, optical=48, width=100), fill=ink)
    f_l = font("BricolageGrotesque.ttf", 40 * S, weight=700, optical=40, width=100)
    labels = {0: "Sveip →"}
    for e, (k, x, row) in zip(evs, places):
        if k and k not in labels:
            d = datetime.date.fromisoformat(e["date"])
            labels[k] = f"{pages.WD[d.weekday()].capitalize()} {phase(e)}"
    for k in range(n):
        txt, lx = labels.get(k, ""), k * W1 + 70
        if k == n - 1:
            txt = "Hele helga på kaskjerda.no"
            lx = (k + 1) * W1 - 60 - dr.textlength(txt, font=f_l) / S
        if txt:
            dr.text((lx * S, (H - GROUND + 8) * S), txt, font=f_l, fill=rgb(CITY if snowy else GOLD))

    full = img.resize((total, H), Image.LANCZOS).convert("RGB")
    names = [f"panorama-{i}.png" for i in range(1, n + 1)]
    for i, name in enumerate(names):
        full.crop((i * W1, 0, (i + 1) * W1, H)).save(folder / name, optimize=True)
    full.resize((total // 2, H // 2), Image.LANCZOS).save(folder / "panorama.jpg", quality=86)
    return names


def plan(today):
    events = json.loads((pages.ROOT / "data" / "events.json").read_text())["events"]
    start, end = pages.weekend_range(today)
    return start, end, stops([e for e in events if e["cat"] not in pages.SEPARATE], start, end)


def render_all(today, folder):
    """Kalles fra pages.py ved hver publisering."""
    folder.mkdir(parents=True, exist_ok=True)
    for old in list(folder.glob("panorama-*.png")) + list(folder.glob("panorama.jpg")):
        old.unlink()
    start, end, evs = plan(today)
    return render(evs, start, end, today, folder) if len(evs) >= MIN_EVENTS else []


def caption(start, end, evs):
    lines = [f"Hele helga i Ålesund, {pages.range_text(start, end)} ✨", "Sveip deg gjennom helga, fra fredag til søndag:"]
    day = None
    for e in evs:
        if e["date"] != day:
            day = e["date"]
            d = datetime.date.fromisoformat(day)
            lines += ["", f"{pages.WD[d.weekday()].upper()} {d.day}. {pages.MO[d.month - 1].upper()}"]
        venue, price = meta(e)
        lines.append(f"▪️ {label(e)} {no_emoji(e['title'])}, {venue}" + (f" – {price.lower()}" if price else ""))
    return "\n".join(lines + ["", "🎟️ Alt med priser og billettlenker: kaskjerda.no (lenke i bio)",
                              "💾 Lagre innlegget og send det til den du skal ut med!", "",
                              " ".join(helgepost.hashtags(evs, start, end))])


def body(start, end, evs, names, v):
    imgs = "\n\n".join(f"![Helga i ett sveip, bilde {i}]({pages.BASE}denne-helgen/{n}?v={v})" for i, n in enumerate(names, 1))
    return f"""Her er «Helga i ett sveip» for {pages.range_text(start, end)}: {len(evs)} stopp fra fredag til søndag på {len(names)} bilder. Post den fredag formiddag.

### Slik ser hele panoramaet ut
![Hele panoramaet]({pages.BASE}denne-helgen/panorama.jpg?v={v})

### Bilder (Instagram-karusell, 1080 × 1350)
Trykk på hvert bilde og lagre det. Legg dem ut i denne rekkefølgen som én karusell, så henger bildene sammen når man sveiper.

{imgs}

### Bildetekst
```text
{caption(start, end, evs)}
```

Utvalget er laget automatisk (ikke julebord, utsolgte eller usikre arrangementer; blir det for mange til ti bilder, går gjentatte klubbkvelder ut først). Sjekk gjerne lista før du poster; programmet hentes automatisk og kan endre seg. Dette issuet lukkes når neste ukes panorama kommer.
"""


def main():
    today = datetime.datetime.now(pages.TZ).date()
    if len(sys.argv) > 2 and sys.argv[1] == "--bilder":
        print(render_all(today, Path(sys.argv[2])))
        return
    start, end, evs = plan(today)
    title = f"Helga i ett sveip: {pages.range_text(start, end)}"
    skip = len(evs) < MIN_EVENTS
    n = layout(evs)[1]
    text = "" if skip else body(start, end, evs, [f"panorama-{i}.png" for i in range(1, n + 1)], today.isoformat())
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text)
    else:
        print(title + "\n\n" + text)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"title={title}\nskip={'true' if skip else 'false'}\n")


if __name__ == "__main__":
    main()
