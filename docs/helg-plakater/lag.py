"""Fete helgeplakater til Instagram-karusell (1080 x 1350). Data fra data/events.json, samme utvalg som «Denne helgen».

Kjør: python3 docs/helg-plakater/lag.py [mappe] [YYYY-MM-DD]   (standard: denne mappa, i dag)
"""
import datetime, json, math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import pages

W, H = 1080, 1350
INK, CREAM = "#14121a", "#fff4dc"
YEL, PINK, BLUE, GREEN, ORANGE, PURPLE, RED = "#ffd93b", "#ff4f8b", "#2b4bff", "#19c98b", "#ff7a1a", "#8a4dff", "#ff3b30"
DAY_BG = {4: PINK, 5: YEL, 6: BLUE}  # fredag, lørdag, søndag
DAY_FG = {4: INK, 5: INK, 6: CREAM}
CAT = {"konsert": BLUE, "standup": ORANGE, "show": PURPLE, "barn": GREEN, "klubb": PINK, "happening": "#e0a800", "quiz": PURPLE, "julebord": RED, "sport": BLUE}
CAT_NAME = {"konsert": "KONSERT", "standup": "STANDUP", "show": "SHOW", "barn": "BARN", "klubb": "KLUBB", "happening": "HAPPENING", "quiz": "QUIZ", "julebord": "JULEBORD", "sport": "SPORT"}
DAYS = ["MANDAG", "TIRSDAG", "ONSDAG", "TORSDAG", "FREDAG", "LØRDAG", "SØNDAG"]
MONTHS = ["", "JANUAR", "FEBRUAR", "MARS", "APRIL", "MAI", "JUNI", "JULI", "AUGUST", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"]
FD = "/usr/share/fonts/opentype/inter/"


def F(size, w="Black"):
    return ImageFont.truetype(f"{FD}InterDisplay-{w}.otf", size)


def fit(d, text, w, max_size, min_size=24, weight="Black"):
    s = max_size
    while s > min_size and d.textlength(text, font=F(s, weight)) > w:
        s -= 2
    f = F(s, weight)
    if d.textlength(text, font=f) > w:  # korter ned
        while text and d.textlength(text + "…", font=f) > w:
            text = text[:-1]
        text = text.rstrip() + "…"
    return text, f


def shadow_text(d, xy, text, f, fill, shadow=INK, off=8, outline=0, anchor="la"):
    x, y = xy
    d.text((x + off, y + off), text, font=f, fill=shadow, anchor=anchor, stroke_width=outline, stroke_fill=shadow)
    d.text((x, y), text, font=f, fill=fill, anchor=anchor, stroke_width=outline, stroke_fill=INK)


def halftone(img, color, x0, y0, x1, y1, step=26, rmax=11, vertical=True):
    d = ImageDraw.Draw(img)
    for y in range(y0, y1, step):
        t = (y - y0) / max(1, y1 - y0)
        r = rmax * (1 - t if vertical else 1)
        if r < 1:
            continue
        for x in range(x0 + (step // 2 if ((y - y0) // step) % 2 else 0), x1, step):
            d.ellipse((x - r, y - r, x + r, y + r), fill=color)


def burst(size, color, spikes=18, inner=0.82):
    s = size * 2
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(spikes * 2):
        r = (size - 6) * (1 if i % 2 == 0 else inner)
        a = math.pi * i / spikes
        pts.append((size + r * math.cos(a), size + r * math.sin(a)))
    d.polygon([(x + 8, y + 8) for x, y in pts], fill=INK)
    d.polygon(pts, fill=color, outline=INK, width=6)
    return im


def paste_rot(img, layer, center, angle):
    r = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.paste(r, (int(center[0] - r.width / 2), int(center[1] - r.height / 2)), r)


def sticker_layer(text, angle, bg, fg=INK, size=48, pad=(30, 16), weight="Black"):
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    f = F(size, weight)
    tw = tmp.textlength(text, font=f)
    w, h = int(tw + pad[0] * 2), int(size * 1.0 + pad[1] * 2)
    im = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((12 + 8, 12 + 8, w + 8, h + 8), 16, fill=INK)
    d.rounded_rectangle((12, 12, w, h), 16, fill=bg, outline=INK, width=6)
    d.text((12 + w / 2, 12 + h / 2 - 3), text, font=f, fill=fg, anchor="mm")
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)


def sticker(img, text, center, angle, bg, fg=INK, size=48, pad=(30, 16), weight="Black"):
    r = sticker_layer(text, angle, bg, fg, size, pad, weight)
    img.paste(r, (int(center[0] - r.width / 2), int(center[1] - r.height / 2)), r)


def skyline(img, base=INK, window=YEL, seed=3):
    """Ålesund-aktig silhuett: smale jugendstil-gavler med spir."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    x = -20
    while x < W + 20:
        w = rnd.choice([70, 90, 110, 130])
        h = rnd.choice([44, 62, 80, 96])
        top = H - h
        d.rectangle((x, top, x + w, H), fill=base)
        kind = rnd.choice(["gable", "step", "tower", "flat"])
        if kind == "gable":
            d.polygon([(x - 4, top), (x + w / 2, top - w * 0.4), (x + w + 4, top)], fill=base)
        elif kind == "step":
            d.rectangle((x + w * 0.2, top - 16, x + w * 0.8, top), fill=base)
            d.rectangle((x + w * 0.35, top - 30, x + w * 0.65, top - 16), fill=base)
        elif kind == "tower":
            d.rectangle((x + w * 0.35, top - 40, x + w * 0.65, top), fill=base)
            d.polygon([(x + w * 0.3, top - 40), (x + w / 2, top - 66), (x + w * 0.7, top - 40)], fill=base)
        for wy in range(top + 18, H - 14, 36):
            for wx in range(int(x + 14), int(x + w - 14), 28):
                if rnd.random() < 0.55:
                    d.rectangle((wx, wy, wx + 11, wy + 16), fill=window)
        x += w + rnd.choice([0, 0, 6])


def footer(img, fg=INK):
    d = ImageDraw.Draw(img)
    d.text((W // 2, H - 176), "kaskjerda.no", font=F(40), fill=fg, anchor="mm")


def price_bits(e):
    p = pages.price_text(e)
    if p == "Utsolgt" or e.get("soldOut"):
        return "UTSOLGT", RED
    if p == "Gratis":
        return "GRATIS", GREEN
    if p == "Pris hos arrangør":
        return "", None
    return p, None


def card_layer(e, tilt, chip=None, x0=60, x1=W - 60, h=150):
    layer = Image.new("RGBA", (x1 - x0 + 40, h + 40), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((20 + 10, 20 + 10, x1 - x0 + 10, h + 10 + 10), 22, fill=INK)
    ld.rounded_rectangle((20, 20, x1 - x0, h + 10), 22, fill=CREAM, outline=INK, width=6)
    cw = x1 - x0
    ccol = CAT.get(e["cat"], BLUE)
    chip = chip or (e.get("time") or "").split(" og ")[0] or "HELE DAGEN"
    more = "+" + e["time"].split(" og ")[1] if " og " in (e.get("time") or "") and chip == e["time"].split(" og ")[0] else ""
    ld.rounded_rectangle((20 + 6, 20 + 6, 20 + 214, h + 4), 18, fill=ccol)
    cf = F(46 if len(chip) <= 5 else 30)
    ld.text((20 + 110, 20 + (h - 10) / 2 + 6 - (14 if more else 0)), chip, font=cf, fill=CREAM if ccol not in (YEL, "#e0a800") else INK, anchor="mm")
    if more:
        ld.text((20 + 110, 20 + (h - 10) / 2 + 40), more, font=F(26, "ExtraBold"), fill=CREAM, anchor="mm")
    tx = 20 + 238
    tw = cw - tx - 24 + 20
    title, tf = fit(ld, e["title"], tw, 46, 30)
    ld.text((tx, 20 + 26), title, font=tf, fill=INK)
    price, pcol = price_bits(e)
    meta = e["venue"].upper()
    mf = F(24, "ExtraBold")
    pw = 0
    if price:
        pf = F(26)
        pw = ld.textlength(price, font=pf) + 30
        bx = 20 + cw - 24 - pw
        ld.rounded_rectangle((bx, 20 + 88, bx + pw, 20 + 88 + 42), 12, fill=pcol or YEL, outline=INK, width=4)
        ld.text((bx + pw / 2, 20 + 88 + 22), price, font=pf, fill=CREAM if pcol else INK, anchor="mm")
        pw += 14
    meta, mf = fit(ld, meta, tw - pw, 24, 18, "ExtraBold")
    ld.text((tx, 20 + 98), meta, font=mf, fill="#4b4758")
    return layer.rotate(tilt, resample=Image.BICUBIC, expand=True), layer.size


def card(img, y, e, tilt, chip=None, x0=60, x1=W - 60, h=150):
    r, (lw, lh) = card_layer(e, tilt, chip, x0, x1, h)
    img.paste(r, (int(x0 - 20 + (lw - r.width) / 2), int(y - 20 + (lh - r.height) / 2)), r)


def interesting(evs):
    """Utvalg per plakat: bort med gjentatte generiske DJ-kvelder og konkurranser uten pris/tittelinfo."""
    skip = ("DJ hver", "hver lørdag", "hver helg", "hver fredag")
    return [e for e in evs if not any(s.lower() in e["title"].lower() for s in skip) and not e.get("uncertain")]


def cover(evs, start, sun):
    img = Image.new("RGB", (W, H), BLUE)
    halftone(img, "#4a66ff", 0, 0, W, 760, step=30, rmax=13)
    d = ImageDraw.Draw(img)
    # stripe-sol
    for i, c in enumerate([PINK, ORANGE, YEL]):
        d.ellipse((W - 520 + i * 36, 120 + i * 36, W - 40 - i * 36, 600 - i * 36), fill=c)
    paste_rot(img, burst(150, YEL), (200, 250), -10)
    d = ImageDraw.Draw(img)
    d.text((200, 232), "HER", font=F(52), fill=INK, anchor="mm")
    d.text((200, 282), "SKJER DET", font=F(34), fill=INK, anchor="mm")
    t = "HELGA"
    f = F(330)
    while d.textlength(t, font=f) > 960:
        f = F(f.size - 6)
    lay = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    shadow_text(ld, (W // 2, 210), t, f, YEL, off=16, outline=10, anchor="mm")
    paste_rot(img, lay, (W // 2, 560), -4)
    sticker(img, "I ÅLESUND", (W // 2 - 60, 780), 3, PINK, INK, 92, (44, 20))
    span = f"{start.day}.–{sun.day}. {MONTHS[sun.month]}"
    d = ImageDraw.Draw(img)
    st, sf = fit(d, span, 940, 100)
    shadow_text(d, (W // 2, 930), st, sf, CREAM, off=8, outline=4, anchor="mm")
    n = len(evs)
    paste_rot(img, burst(130, GREEN, 14), (870, 1075), 8)
    d = ImageDraw.Draw(img)
    d.text((870, 1055), str(n), font=F(100), fill=INK, anchor="mm")
    d.text((870, 1115), "TING Å GJØRE", font=F(26), fill=INK, anchor="mm")
    sticker(img, "SVEIP  →", (330, 1075), -3, CREAM, INK, 64, (40, 18))
    skyline(img)
    d = ImageDraw.Draw(img)
    return img


def day_slides(evs, day, bg, fg, page_no=0, per=4, extra_night=None):
    wd = day.weekday()
    items = [e for e in interesting([x for x in evs if x["date"] == day.isoformat()]) if e["cat"] != "klubb"]
    items.sort(key=lambda e: (e.get("time") or "00:00"))
    n_all = len([x for x in evs if x["date"] == day.isoformat()])
    night = [x for x in evs if x["date"] == day.isoformat() and x["cat"] == "klubb"]
    k = min(3, max(1, -(-len(items) // per)))
    size = max(1, -(-len(items) // k))
    pages_ = [items[i:i + size] for i in range(0, max(len(items), 1), size)][:3]
    shown = sum(len(p) for p in pages_)
    out = []
    for pi, chunk in enumerate(pages_):
        img = Image.new("RGB", (W, H), bg)
        halftone(img, "#00000026" if False else ("#ffffff55" if bg != YEL else "#ffffff88"), 0, 0, W, 400, step=28, rmax=12)
        d = ImageDraw.Draw(img)
        name = DAYS[wd]
        f = F(250)
        while d.textlength(name, font=f) > 940:
            f = F(f.size - 6)
        lay = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
        shadow_text(ImageDraw.Draw(lay), (W // 2, 150), name, f, CREAM if bg != BLUE else YEL, off=12, outline=8, anchor="mm")
        paste_rot(img, lay, (W // 2, 190), -2.5)
        sub = f"{day.day}. {MONTHS[day.month]}"
        sticker(img, sub, (300, 352), 2, CREAM, INK, 44, (30, 12))
        sticker(img, f"{n_all} ARRANGEMENT" + (f"  {pi + 1}/{len(pages_)}" if len(pages_) > 1 else ""), (770, 352), -2, YEL if bg != YEL else PINK, INK, 36, (26, 12))
        y = 430
        for i, e in enumerate(chunk):
            card(img, y, e, [-1.2, 0.9, -0.7, 1.1, -0.9][i % 5])
            y += 162
        if pi == len(pages_) - 1:
            lines = []
            if night:
                lines.append("NATTA: " + " · ".join(dict.fromkeys(x["venue"] for x in night)) + " (klubb)")
            rest = len([x for x in evs if x["date"] == day.isoformat()]) - shown - len(night)
            if rest > 0:
                lines.append(f"+ {rest} til på kaskjerda.no")
            for j, t in enumerate(lines[:2]):
                d = ImageDraw.Draw(img)
                tt, tf = fit(d, t, 940, 30, 20, "ExtraBold")
                sticker(img, tt, (W // 2, y + 24 + j * 62), (-1 if j == 0 else 1), INK, CREAM, 30, (26, 10)) if False else None
                d.text((W // 2, y + 14 + j * 40), tt, font=tf, fill=fg, anchor="mm")
        skyline(img, seed=wd + pi)
        footer(img, fg)
        out.append(img)
    return out


def free_slide(evs):
    free = [e for e in interesting(evs) if pages.price_text(e) == "Gratis"]
    if not free:
        return None
    img = Image.new("RGB", (W, H), GREEN)
    halftone(img, "#ffffff55", 0, 0, W, 420, step=28, rmax=12)
    d = ImageDraw.Draw(img)
    lay = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    f = F(300)
    while d.textlength("GRATIS", font=f) > 940:
        f = F(f.size - 6)
    shadow_text(ImageDraw.Draw(lay), (W // 2, 160), "GRATIS", f, YEL, off=14, outline=9, anchor="mm")
    paste_rot(img, lay, (W // 2, 200), 3)
    sticker(img, "ingen billett. bare dukk opp.", (W // 2, 410), -2, CREAM, INK, 36, (28, 12), "ExtraBold")
    y = 500
    for i, e in enumerate(free[:5]):
        e2 = dict(e)
        wd = pages.WD[datetime.date.fromisoformat(e["date"]).weekday()][:3].upper()
        card(img, y, e2, [-1.2, 1, -0.8, 1.1, -1][i % 5], chip=f"{wd} {(e.get('time') or '').split(' og ')[0]}".strip())
        y += 162
    skyline(img, seed=11)
    footer(img)
    return img


def outro():
    img = Image.new("RGB", (W, H), YEL)
    halftone(img, "#ffffff88", 0, 0, W, 700, step=30, rmax=13)
    d = ImageDraw.Draw(img)
    for t, y, a, c in [("FANT DU", 250, -3, INK), ("NOE Å", 440, 2, PINK), ("GJØRE?", 630, -2, BLUE)]:
        lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        shadow_text(ImageDraw.Draw(lay), (W // 2, 130), t, F(220), c if c != INK else INK, shadow=CREAM if c == INK else INK, off=12, outline=7, anchor="mm")
        paste_rot(img, lay, (W // 2, y), a)
    sticker(img, "kaskjerda.no", (W // 2, 850), -2, INK, YEL, 100, (50, 22))
    sticker(img, "ALT SOM SKJER. MED PRISER.", (W // 2, 990), 2, CREAM, INK, 40, (30, 14))
    paste_rot(img, burst(120, PINK, 14), (880, 1110), 10)
    d = ImageDraw.Draw(img)
    d.text((880, 1090), "LAGRE", font=F(40), fill=INK, anchor="mm")
    d.text((880, 1140), "& DEL", font=F(40), fill=INK, anchor="mm")
    skyline(img, seed=5, window=PINK)
    return img


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    today = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else datetime.date.today()
    data = json.loads((ROOT / "data" / "events.json").read_text())
    start, sun = pages.weekend_range(today)
    evs = pages.occurrences([e for e in data["events"] if e["date"] >= today.isoformat() and e["cat"] not in pages.SEPARATE], start, sun)
    slides = [cover(evs, start, sun)]
    for i in range((sun - start).days + 1):
        day = start + datetime.timedelta(days=i)
        if day.weekday() in DAY_BG:
            slides += day_slides(evs, day, DAY_BG[day.weekday()], DAY_FG[day.weekday()])
    fs = free_slide(evs)
    if fs:
        slides.append(fs)
    slides.append(outro())
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("plakat-*.png"):
        old.unlink()
    for i, s in enumerate(slides, 1):
        s.save(out / f"plakat-{i}.png")
    print(len(slides), "plakater i", out)


if __name__ == "__main__":
    main()
