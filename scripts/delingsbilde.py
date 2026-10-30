"""Delingsbilde per arrangement (1200 × 630), forhåndsvisningen når en arrangementsside deles på Messenger, Facebook, SMS osv.

Design 5 «vinterutgave» fra docs/delingsbilde-AE-forslag.html: mørk himmel, måne, snøfall (30. okt – feb, ellers uten snø), kategori, stor tittel,
dato og sted, status/pris og jugendgavler med snø på takene foran Aksla nederst. Byen tegnes av en enkel generator
med fast frø, samme som i mockupen, så alle bildene får samme by.

Brukes av pages.py: render(e, fil). Skrifter som i helgebildet (FONT_DIR), pluss JetBrainsMono.ttf for kategorien.
Bildet tegnes i dobbel størrelse og skaleres ned, så kantene blir myke.
"""
import datetime
import hashlib

from helgepost import fit, font, no_emoji
import pages

W, H = 1200, 630
S = 2  # tegnes i dobbel størrelse
LOGO = pages.ROOT / "scripts" / "delelogo.png"

# Kategorifargene fra kveldstemaet (tema-kveld.css)
CAT_COLOR = {"konsert": "#5ab7bf", "standup": "#f08a4b", "show": "#ab93e6", "barn": "#6cc98a", "klubb": "#ec78ab",
             "happening": "#d9b84a", "quiz": "#b497e0", "julebord": "#ef7a7f", "sport": "#7aa7e6"}
CAT_NAME = {"konsert": "Konsert", "standup": "Standup", "show": "Show", "barn": "Barn og familie", "klubb": "Klubb",
            "happening": "Happening", "quiz": "Quiz", "julebord": "Julebord", "sport": "Sport"}
FG, GOLD, SEA, SNOW = "#e8f1ef", "#f7c873", "#5ab7bf", "#f4f7f6"
PILL = {"sold": ("#ff8a6b", "#1a0b07"), "few": ("#ffb547", "#2a1a02"), "free": ("#7ee0a1", "#0b2a17"), "price": ("#0a171b", "#ffffff")}
LEFT, TOP, TEXT_RIGHT = 72, 60, 270
PILL_TOP, PILL_RIGHT = 196, 72
TEXT_BOTTOM = 410  # under dette står byen


def hexrgb(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def rng(seed):
    """Samme tilfeldige tall som generatoren i mockupen (Park–Miller)."""
    def r():
        nonlocal seed
        seed = seed * 16807 % 2147483647
        return seed / 2147483647
    return r


def bez(p0, p1, p2, p3=None, n=24):
    """Punkter langs en kvadratisk (tre punkter) eller kubisk (fire punkter) Bézierkurve."""
    out = []
    for i in range(1, n + 1):
        t = i / n
        if p3 is None:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        else:
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]
        out.append((x, y))
    return out


def skyline(dr, layer, oy, h=210, seed=3, w=W):
    """Aksla, gavler med snø, lys i vinduene og bølgen. oy er toppen av byen i bildet (i vanlig størrelse)."""
    from PIL import ImageDraw
    r = rng(seed)
    P = lambda pts: [(x * S, (y + oy) * S) for x, y in pts]
    hill = [(w * .18, h)] + bez((w * .18, h), (w * .3, h * .25), (w * .42, h * .02), (w * .55, h * .05)) \
        + bez((w * .55, h * .05), (w * .68, h * .08), (w * .8, h * .3), (w * .95, h))
    dr.polygon(P(hill), fill="#1a3540")
    dr.rectangle(P([(w * .545, h * .02), (w * .565, h * .08)]), fill="#1a3540")
    win = ImageDraw.Draw(layer)
    caps = []
    x = -10
    while x < w:
        bw, top, kind = 46 + r() * 64, h * (.38 + r() * .34), r()
        spire = None
        if kind < .45:
            peak = top - 26 - r() * 34
            shape = [(x, h), (x, top), (x + bw / 2, peak), (x + bw, top), (x + bw, h)]
            caps.append([(x - 2, top + 2), (x + bw / 2, peak - 2), (x + bw + 2, top + 2)])
            if r() < .35:
                spire = [(x + bw / 2 - 2, peak), (x + bw / 2 - 2, peak - 18), (x + bw / 2 + 2, peak - 18), (x + bw / 2 + 2, peak)]
        elif kind < .7:
            s = 12 + r() * 6
            shape = [(x, h), (x, top), (x, top - s), (x + bw * .2, top - s), (x + bw * .2, top - 2 * s), (x + bw * .8, top - 2 * s),
                     (x + bw * .8, top - s), (x + bw, top - s), (x + bw, h)]
            caps.append([(x + bw * .2, top - 2 * s), (x + bw * .8, top - 2 * s)])
        elif kind < .85:
            t = top - 60 - r() * 30
            shape = [(x, h), (x, top), (x + bw * .35, top), (x + bw * .35, t + 22), (x + bw * .5, t), (x + bw * .65, t + 22),
                     (x + bw * .65, top), (x + bw, top), (x + bw, h)]
            caps.append([(x + bw * .33, t + 23), (x + bw * .5, t - 1), (x + bw * .67, t + 23)])
        else:
            arc = bez((x, top), (x + bw / 2, top - 46), (x + bw, top))
            shape = [(x, h), (x, top)] + arc + [(x + bw, h)]
            caps.append([(x, top)] + arc)
        dr.polygon(P(shape), fill="#06110f")
        if spire:
            dr.polygon(P(spire), fill="#06110f")
        wy = top + 16
        while wy < h - 30:
            wx = x + 10
            while wx < x + bw - 16:
                if r() < .22:
                    win.rounded_rectangle(P([(round(wx), round(wy)), (round(wx) + 9, round(wy) + 13)]), radius=3, fill=hexrgb(GOLD, 230))
                wx += 22
            wy += 30
        x += bw + (6 if r() < .25 else 0)
    return caps


def wrap(dr, text, f, width_at):
    """Bryter teksten i linjer; width_at(i) er bredden linje i kan ha."""
    words, lines, cur = text.split(), [], ""
    for wd in words:
        test = f"{cur} {wd}".strip()
        if cur and dr.textlength(test, font=f) > width_at(len(lines)):
            lines.append(cur)
            cur = wd
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def status(e):
    d = datetime.date.fromisoformat(e["date"])
    if e.get("soldOut"):
        return "sold", "Utsolgt"
    if e.get("few") and pages.few_ok(e, d):
        return "few", "Få billetter igjen"
    if e.get("priceMin") == 0:
        return "free", "Gratis"
    return "price", e.get("price") or "Pris hos arrangør"


def when_parts(e):
    d = datetime.date.fromisoformat(e["date"])
    parts = [(f"{pages.WD[d.weekday()].capitalize()} {d.day}. {pages.MO[d.month - 1]}", FG, 600)]
    if e.get("time"):
        parts += [(" · ", FG, 600), (f"kl. {e['time']}", GOLD, 700)]
    n = len(e.get("moreShows") or [])
    if n:
        parts.append((f" · + {n} {'dato' if n == 1 else 'datoer'}", FG, 600))
    return parts


def version(e):
    """Kort kode for innholdet i bildet, til ?v= i adressen, så Facebook m.fl. henter nytt bilde når noe endres."""
    key = "|".join(str(x) for x in (e["title"], e["date"], e.get("time"), e["venue"], e["cat"], status(e), len(e.get("moreShows") or []), winter(), "v1"))
    return hashlib.sha1(key.encode()).hexdigest()[:8]


def winter(today=None):
    """Snø fra 30. oktober til og med februar (eierens valg). Resten av året samme by uten snø, med gyllen måne."""
    d = today or datetime.datetime.now(pages.TZ).date()
    return d.month in (11, 12, 1, 2) or (d.month == 10 and d.day >= 30)


_BG = None


def background():
    """Himmel, måne, by og (om vinteren) snø. Lik for alle arrangementene, så den tegnes bare én gang."""
    global _BG
    if _BG is not None:
        return _BG.copy()
    snowy = winter()
    moon = "#f4f1e6" if snowy else GOLD
    from PIL import Image, ImageDraw, ImageFilter
    img = Image.new("RGBA", (W * S, H * S))
    dr = ImageDraw.Draw(img)
    # Himmel: #14303f øverst, #0b1a24 ved 70 %, #0a171b nederst
    top, mid, bot = hexrgb("#14303f"), hexrgb("#0b1a24"), hexrgb("#0a171b")
    for y in range(H * S):
        t = y / (H * S)
        a, b, k = (top, mid, t / .7) if t < .7 else (mid, bot, (t - .7) / .3)
        dr.line([(0, y), (W * S, y)], fill=tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3)))

    # Månen med glød
    glow = Image.new("RGBA", img.size)
    gd = ImageDraw.Draw(glow)
    cx, cy, rad = 1044 * S, 112 * S, 46 * S
    gd.ellipse((cx - rad * 1.6, cy - rad * 1.6, cx + rad * 1.6, cy + rad * 1.6), fill=hexrgb(moon, 90))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(45 * S)))
    dr.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=moon)

    # Byen nederst (lag for vinduer, så de kan være litt gjennomsiktige)
    oy = H - 210
    lights = Image.new("RGBA", img.size)
    caps = skyline(dr, lights, oy)
    img.alpha_composite(lights)
    dr = ImageDraw.Draw(img)
    for c in caps if snowy else []:
        dr.line([(x * S, (y + oy) * S) for x, y in c], fill=SNOW, width=7 * S, joint="curve")
    wave = [(0, H - 14)]
    for i in range(0, W, 120):
        wave += bez((i, H - 14), (i + 40, H - 26), (i + 80, H - 26), (i + 120, H - 14), n=16)
    dr.line([(x * S, y * S) for x, y in wave], fill=SEA, width=6 * S, joint="curve")

    # Snøfall
    snow = Image.new("RGBA", img.size)
    sd = ImageDraw.Draw(snow)
    r = rng(42)
    for _ in range(90 if snowy else 0):
        x, y, s, o = r() * W, r() * H, 1.5 + r() * 3, .25 + r() * .45
        sd.ellipse(((x - s) * S, (y - s) * S, (x + s) * S, (y + s) * S), fill=(255, 255, 255, round(o * 255)))
    img.alpha_composite(snow)
    _BG = img
    return img.copy()


def render(e, path):
    from PIL import Image, ImageDraw
    img = background()
    dr = ImageDraw.Draw(img)

    # Status eller pris øverst til høyre
    kind, label = status(e)
    f_pill = font("Figtree.ttf", 29 * S, weight=700)
    pw = dr.textlength(label, font=f_pill) + 48 * S
    px1 = W * S - PILL_RIGHT * S
    px0, py0, py1 = px1 - pw, PILL_TOP * S, (PILL_TOP + 58) * S
    bg, fg = PILL[kind]
    if kind == "price":
        dr.rounded_rectangle((px0, py0, px1, py1), radius=29 * S, fill=hexrgb(bg, 205), outline=hexrgb("#ffffff", 70), width=2 * S)
    else:
        dr.rounded_rectangle((px0, py0, px1, py1), radius=29 * S, fill=bg)
    dr.text(((px0 + px1) / 2, (py0 + py1) / 2), label, font=f_pill, fill=fg, anchor="mm")

    # Kategori, tittel, dato og sted
    c = e["cat"] if e["cat"] in CAT_COLOR else "happening"
    f_cat = font("JetBrainsMono.ttf", 25 * S, weight=700)
    x, y = LEFT * S, TOP * S
    for ch in CAT_NAME[c].upper():
        dr.text((x, y), ch, font=f_cat, fill=CAT_COLOR[c])
        x += dr.textlength(ch, font=f_cat) + 3.5 * S
    y += 45 * S

    title = no_emoji(e["title"])
    f_when = font("Figtree.ttf", 37 * S, weight=600)
    when_h = 2 * 45 * S
    full_w = (W - LEFT - TEXT_RIGHT) * S
    size = max(46, min(90, 90 - (len(title) - 16) * 1.5))
    while True:
        f_t = font("BricolageGrotesque.ttf", round(size * S), weight=800, optical=96, width=100)
        lh = size * .98 * S
        # Linjer som ligger på høyde med statusmerket får kortere bredde
        width_at = lambda i: min(full_w, px0 - 30 * S - LEFT * S) if y + (i + 1) * lh > py0 - 6 * S and y + i * lh < py1 + 6 * S else full_w
        lines = wrap(dr, title, f_t, width_at)
        k = 1.0
        while len(lines) > 1 and k > .55:  # smalere bredde så lenge antall linjer ikke øker
            test = wrap(dr, title, f_t, lambda i: width_at(i) * (k - .05))
            if len(test) != len(lines):
                break
            lines, k = test, k - .05
        if (len(lines) <= 3 and y + len(lines) * lh + 20 * S + when_h <= TEXT_BOTTOM * S) or size <= 46:
            break
        size -= 2
    if len(lines) > 3:
        lines = lines[:3]
        last = lines[2]
        while last and dr.textlength(last + "…", font=f_t) > width_at(2):
            last = last[:-1]
        lines[2] = last.rstrip(" ,–-") + "…"
    for i, ln in enumerate(lines):
        dr.text((LEFT * S, y + i * lh), ln, font=f_t, fill="#ffffff", anchor="la")
    y += len(lines) * lh + 20 * S

    x = LEFT * S
    for text, color, weight in when_parts(e):
        f = font("Figtree.ttf", 37 * S, weight=weight)
        dr.text((x, y), text, font=f, fill=color, anchor="la")
        x += dr.textlength(text, font=f)
    dr.text((LEFT * S, y + 45 * S), fit(dr, e["venue"], f_when, full_w), font=f_when, fill=FG, anchor="la")

    # Logo og adresse nederst til venstre
    logo = Image.open(LOGO).convert("RGBA").resize((42 * S, 46 * S), Image.LANCZOS)
    ly = (H - 38 - 46) * S
    img.alpha_composite(logo, (LEFT * S, ly))
    f_brand = font("Figtree.ttf", 26 * S, weight=700)
    dr.text(((LEFT + 42 + 14) * S, ly + 23 * S), "kaskjerda.no", font=f_brand, fill=FG, anchor="lm")

    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").resize((W, H), Image.LANCZOS).save(path, "JPEG", quality=86, optimize=True, progressive=True)
