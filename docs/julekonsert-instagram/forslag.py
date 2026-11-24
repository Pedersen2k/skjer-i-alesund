"""Forslag til Instagram-poster om julekonsertene (24. nov 2026). Alt fra data/events.json; utsolgte er ikke med.

2 Plakaten «Alle julekonsertene» (innlegg 1080 × 1350 som folk lagrer): A Lineup, B Veggkalender, + listebilde.
3 «Snart utsolgt»-historie (1080 × 1920): A Billetten, B Nedtelling, C Avgangstavla.
4 Reel (1080 × 1920, mp4): A «Desember i ett sveip» (panoramaet), B Rask klipp (ett bilde per konsert).

Kjør: FONT_DIR=<skrifter> python3 docs/julekonsert-instagram/forslag.py <mappe for png> <mappe for mp4>
"""
import datetime
import json
import math
import os
import random
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import numpy as np
import pages
import ukepost as u
from helgepost import font
from ukepost import B, F, M, fit, no_emoji, logo, wrap
from PIL import Image, ImageDraw, ImageFilter

W = 1080
TODAY = datetime.date(2026, 11, 24)
# Startdato kan settes med JUL_FRA=ÅÅÅÅ-MM-DD (f.eks. dagen reelen legges ut)
FROM = datetime.date.fromisoformat(os.environ.get("JUL_FRA", "2026-11-28"))
TO = datetime.date(2026, 12, 31)
CFG = pages.jul_config()
MANUAL = {e["id"]: e for e in json.loads((pages.ROOT / "data" / "manual.json").read_text())}


def FR(size, w=700, italic=False):
    return font("FrauncesItalic.ttf" if italic else "Fraunces.ttf", size, weight=w, optical=min(144, size), soft=50, wonk=1 if italic else 0)


def concerts():
    events, _ = u.load()
    ok = [e for e in events if e["cat"] == "konsert" and u.ok(e) and pages.is_jul(e, CFG)
          and not MANUAL.get(e["id"], {}).get("soldOut")]
    out, d = [], FROM
    while d <= TO:
        out += sorted(pages.occurrences(ok, d, d), key=lambda e: e.get("time") or "")
        d += datetime.timedelta(days=1)
    return out


EV = concerts()

# Korte navn til plakaten (artist/kor der tittelen har det, ellers tittelen)
SHORT = {
    "Ålesund symfoniorkester – Adventskonsert": "Ålesund symfoniorkester",
    "Mannskoret Varde Julekonsert": "Mannskoret Varde",
    "Julekonsert med Sveinung Hølmebakk": "Sveinung Hølmebakk",
    "Den store julekonserten – Ålesund kulturskole": "Ålesund kulturskole",
    "Julekonsert med Velledalskoret og POSH trio": "Velledalskoret & POSH trio",
    "Juletonar med Sonja Alnes Trio": "Sonja Alnes Trio",
    "Klassisk Jul  – julefavorittar med tradisjonar": "Klassisk Jul",
    "Christmas With Nordic Tenors 2026": "Nordic Tenors",
    "Scala Brio Julenattine 2026": "Scala Brio",
    "Anita Valderhaug m/gjester – Julero": "Anita Valderhaug",
    "Romjulsdans med Steinar Engelbrektson og Sissel Lunde Sundby": "Romjulsdans",
    "Den store romjulsfesten – 2. juledag": "Romjulsfesten",
    "Adventskonsert med AaUM": "AaUM",
    "Julekonsert på låven i Tennfjord": "Låven i Tennfjord",
    "For vår Jord – julekonsert": "For vår Jord",
    "Julekonsert med allsang": "Allsang i Volsdalen",
}


def short(e):
    t = no_emoji(e["title"])
    if t in SHORT:
        return SHORT[t]
    if " – " in t:
        return t.split(" – ")[0]
    return t


def tm(e):
    m = re.search(r"\d{1,2}:\d{2}", e.get("time") or "")
    return m.group(0).zfill(5) if m else ""


def price(e):
    p = pages.price_text(e)
    return "" if p == "Pris hos arrangør" else p


def d_of(e):
    return datetime.date.fromisoformat(e["date"])


def dshort(d):
    return f"{d.day}.{d.month:02d}"


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def grad(w, h, stops, angle=0.0):
    y, x = np.mgrid[0:h, 0:w].astype(float)
    t = (y / h) * math.cos(angle) + (x / w) * math.sin(angle)
    t = (t - t.min()) / (t.max() - t.min())
    out = np.zeros((h, w, 3))
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (t >= p0) & (t <= p1)
        k = ((t - p0) / (p1 - p0))[..., None]
        out[m] = (np.array(hexc(c0)) * (1 - k) + np.array(hexc(c1)) * k)[m]
    return Image.fromarray(out.astype("uint8"))


def snow(img, seed, n=140):
    rnd = random.Random(seed)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y, r = rnd.uniform(0, img.width), rnd.uniform(0, img.height), rnd.choice((2, 3, 3, 4, 5, 6))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rnd.randint(60, 180)))
    img.paste(Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(0.8))).convert("RGB"))


def star(dr, cx, cy, r, fill, points=5, inner=0.45):
    dr.polygon([(cx + (r if i % 2 == 0 else r * inner) * math.cos(-math.pi / 2 + i * math.pi / points),
                 cy + (r if i % 2 == 0 else r * inner) * math.sin(-math.pi / 2 + i * math.pi / points)) for i in range(points * 2)], fill=fill)


def brand(img, dr, x, y, fg, size=60):
    im, mask = logo(size)
    img.paste(im, (x, y), mask)
    dr.text((x + size + 18, y + size // 2), "kaskjerda.no", font=B(32, 700), fill=fg, anchor="lm")


def sticker(dr, cx, y, col, text="lenkemerke her", w=560):
    x = cx - w // 2
    for i in range(x, x + w, 28):
        dr.line((i, y, min(i + 14, x + w), y), fill=col, width=3)
        dr.line((i, y + 110, min(i + 14, x + w), y + 110), fill=col, width=3)
    for j in range(y, y + 110, 28):
        dr.line((x, j, x, min(j + 14, y + 110)), fill=col, width=3)
        dr.line((x + w, j, x + w, min(j + 14, y + 110)), fill=col, width=3)
    dr.text((cx, y + 55), text, font=F(30, 600), fill=col, anchor="mm")


# ───────────── 2 Plakaten ─────────────

BIG = ("Parken kulturhus", "Løvenvold Theater")


def poster_a():
    """Lineup: alle navnene som på en festivalplakat, i datorekkefølge. Store scener i stor skrift."""
    H = 1350
    img = grad(W, H, [(0, "#1a0f3d"), (0.5, "#2a0b2e"), (1, "#3d0a1c")], 0.3)
    snow(img, 3, 160)
    dr = ImageDraw.Draw(img)
    gold, cream = "#f2c46b", "#fff4dc"
    dr.text((W // 2, 82), "KASKJERDA.NO · LAGRE DENNE", font=M(28), fill=gold, anchor="mm")
    dr.text((W // 2, 190), "Julekonsertene", font=FR(124, 750, True), fill=cream, anchor="mm")
    dr.text((W // 2, 292), "ÅLESUND · 28. NOV – 26. DES 2026", font=B(40, 800), fill=gold, anchor="mm")
    # Flyt navnene i sentrerte linjer
    names, seen = [], set()
    for e in EV:
        n = short(e)
        if n not in seen:
            seen.add(n)
            names.append((n, e["venue"] in BIG))
    def flow(big_s, small_s, draw):
        y, maxw, sep, i = 360, W - 110, 30, 0
        while i < len(names):
            line, w = [], 0
            while i < len(names):
                n, big = names[i]
                f = B(big_s, 800) if big else F(small_s, 700)
                tw = dr.textlength(n, font=f)
                if line and w + sep + tw > maxw:
                    break
                line.append((n, f, tw, big))
                w += tw + (sep if len(line) > 1 else 0)
                i += 1
            x = (W - w) / 2
            lh = round((big_s if any(b for *_, b in line) else small_s) * 1.32)
            for k, (n, f, tw, big) in enumerate(line):
                if k:
                    if draw:
                        star(dr, x + sep / 2, y + lh / 2 - 2, 7, gold)
                    x += sep
                if draw:
                    dr.text((x, y + lh / 2), n, font=f, fill=cream if big else "#e9cfc0", anchor="lm")
                x += tw
            y += lh
        return y
    big_s, small_s = 54, 38
    while flow(big_s, small_s, False) > H - 190:
        big_s, small_s = big_s - 2, small_s - 1.5
    flow(big_s, small_s, True)
    dr.text((W // 2, H - 150), f"{len(EV)} julekonserter · datoer og priser på kaskjerda.no", font=F(34, 700), fill=gold, anchor="mm")
    dr.text((W // 2, H - 90), "Sveip for dag for dag  →", font=B(40, 800), fill=cream, anchor="mm")
    return img


def poster_b():
    """Veggkalender: desember som månedsark, navnene i rutene."""
    H = 1350
    img = Image.new("RGB", (W, H), "#f4ead8")
    dr = ImageDraw.Draw(img)
    red, green, ink = "#b3122e", "#1f5b3f", "#2b1d12"
    dr.rectangle((0, 0, W, 300), fill=red)
    snow(img, 5, 60)
    dr = ImageDraw.Draw(img)
    dr.text((56, 60), "JULEKONSERTER I ÅLESUND", font=M(30), fill="#f3d9a4")
    dr.text((50, 100), "Desember", font=FR(140, 750, True), fill="#ffffff")
    dr.text((W - 56, 130), "Lagre", font=B(44, 800), fill="#ffffff", anchor="ra")
    dr.text((W - 56, 185), "og heng på", font=F(30, 600), fill="#f3d9a4", anchor="ra")
    dr.text((W - 56, 222), "skjermen", font=F(30, 600), fill="#f3d9a4", anchor="ra")
    start = datetime.date(2026, 11, 23)
    x0, y0, gap = 36, 340, 6
    cw = (W - 2 * x0 - 6 * gap) / 7
    for k, wd in enumerate(["MAN", "TIR", "ONS", "TOR", "FRE", "LØR", "SØN"]):
        dr.text((x0 + k * (cw + gap) + 10, y0), wd, font=M(22), fill=green)
    y0 += 36
    rows = 5
    ch = (H - y0 - 80 - (rows - 1) * gap) / rows
    by_day = {}
    for e in EV:
        by_day.setdefault(e["date"], []).append(e)
    for r in range(rows):
        for c in range(7):
            d = start + datetime.timedelta(days=r * 7 + c)
            x, y = x0 + c * (cw + gap), y0 + r * (ch + gap)
            evs = by_day.get(d.isoformat(), [])
            jul = d.month == 12 and d.day == 24
            fill = "#fffaf0" if evs else ("#efe3cc" if not jul else red)
            dr.rounded_rectangle((x, y, x + cw, y + ch), radius=10, fill=fill, outline="#d9c7a8", width=1)
            dr.text((x + 10, y + 6), str(d.day), font=FR(30, 700), fill="#ffffff" if jul else (red if evs else "#a8977c"))
            if jul:
                star(dr, x + cw / 2, y + ch / 2 + 10, 26, "#f3d9a4")
            yy = y + 46
            for e in evs[:4]:
                for ln in wrap(dr, short(e), F(17, 750), cw - 16)[:2]:
                    if yy > y + ch - 20:
                        break
                    dr.text((x + 8, yy), ln, font=F(17, 750), fill=ink)
                    yy += 19
                yy += 5
    brand(img, dr, x0, H - 66, ink, 48)
    dr.text((W - x0, H - 42), "priser og billetter: kaskjerda.no", font=F(26, 650), fill=green, anchor="rm")
    return img


def poster_list(a, b, title):
    """Listebildet som følger etter forsiden i karusellen: én uke om gangen."""
    H = 1350
    img = grad(W, H, [(0, "#1a0f3d"), (1, "#3d0a1c")], 0.3)
    dr = ImageDraw.Draw(img)
    gold, cream = "#f2c46b", "#fff4dc"
    dr.text((72, 80), "JULEKONSERTENE I ÅLESUND", font=M(28), fill=gold)
    dr.text((66, 118), title, font=FR(96, 750, True), fill=cream)
    y = 270
    evs = [e for e in EV if a <= d_of(e) <= b]
    last = None
    for e in evs:
        d = d_of(e)
        if d != last:
            y += 14
            dr.text((72, y), f"{pages.WD[d.weekday()][:3].upper()} {d.day}.", font=M(30), fill=gold)
            last = d
        x = 260
        dr.text((x, y - 6), fit(dr, no_emoji(e["title"]), B(40, 800), W - x - 70), font=B(40, 800), fill=cream)
        meta = " · ".join(p for p in (tm(e), e["venue"], price(e)) if p)
        dr.text((x, y + 44), fit(dr, meta, F(28, 600), W - x - 70), font=F(28, 600), fill="#d9bfb4")
        if e.get("few"):
            tw = dr.textlength(meta, font=F(28, 600))
            if x + tw + 230 < W - 40:
                dr.rounded_rectangle((x + tw + 16, y + 44, x + tw + 216, y + 80), radius=18, fill="#e3344f")
                dr.text((x + tw + 116, y + 62), "få igjen", font=F(24, 800), fill="#ffffff", anchor="mm")
        y += 104
    brand(img, dr, 72, H - 110, cream)
    dr.text((W - 72, H - 80), "Sveip →", font=B(40, 800), fill=gold, anchor="rm")
    return img


# ───────────── 3 Snart utsolgt ─────────────

def few_list(today):
    return [e for e in EV if e.get("few") and d_of(e) > today]


def story_a(e, today):
    """Billetten med stempel."""
    H = 1920
    img = grad(W, H, [(0, "#2b0a3d"), (0.6, "#7a1033"), (1, "#c2272f")], 0.3)
    snow(img, 9, 120)
    dr = ImageDraw.Draw(img)
    dr.text((W // 2, 200), "Snart utsolgt", font=FR(118, 750, True), fill="#ffffff", anchor="mm")
    dr.text((W // 2, 300), "SIKRE DEG BILLETT FØR DET ER FOR SEINT", font=M(28), fill="#ffd9a0", anchor="mm")
    # Billett
    x0, x1, y0, y1 = 90, 990, 420, 1120
    tk = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tk)
    td.rounded_rectangle((x0, y0, x1, y1), radius=36, fill="#fff4dc")
    for cy in (y0 + 470,):
        td.ellipse((x0 - 34, cy - 34, x0 + 34, cy + 34), fill=(0, 0, 0, 0))
        td.ellipse((x1 - 34, cy - 34, x1 + 34, cy + 34), fill=(0, 0, 0, 0))
    for xx in range(x0 + 50, x1 - 40, 30):
        td.line((xx, y0 + 470, xx + 14, y0 + 470), fill="#c9b48f", width=4)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 140), mask=tk.getchannel("A"))
    img = Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(30)).transform(sh.size, Image.AFFINE, (1, 0, 0, 0, 1, -24)))
    img = Image.alpha_composite(img, tk).convert("RGB")
    dr = ImageDraw.Draw(img)
    d = d_of(e)
    ink, red = "#2a0610", "#b3122e"
    dr.text((x0 + 60, y0 + 56), "BILLETT · JULEKONSERT", font=M(28), fill=red)
    lines = wrap(dr, short(e), FR(96, 800), x1 - x0 - 120)
    yy = y0 + 110
    for ln in lines[:2]:
        dr.text((x0 + 56, yy), ln, font=FR(96, 800), fill=ink)
        yy += 104
    sub = no_emoji(e["title"]).split(" – ", 1)[1] if " – " in e["title"] and short(e) != e["title"] else ""
    if sub:
        dr.text((x0 + 60, yy + 6), fit(dr, sub, FR(46, 500, True), x1 - x0 - 120), font=FR(46, 500, True), fill="#6b2a3a")
    yb = y0 + 510
    for k, (lab, val) in enumerate((("DATO", f"{pages.WD[d.weekday()][:3]} {d.day}. {pages.MO[d.month - 1][:3]}"), ("KL.", tm(e)), ("PRIS", price(e)))):
        xx = x0 + 60 + k * 290
        dr.text((xx, yb), lab, font=M(24), fill="#9a7a5a")
        dr.text((xx, yb + 36), val, font=B(48, 800), fill=ink)
    dr.text((x0 + 60, yb + 112), e["venue"], font=F(36, 700), fill=ink)
    # Stempel
    st = Image.new("RGBA", (560, 200), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle((8, 8, 552, 192), radius=20, outline=(227, 52, 79, 235), width=10)
    sd.text((280, 100), "FÅ BILLETTER IGJEN", font=B(52, 800), fill=(227, 52, 79, 235), anchor="mm")
    st = st.rotate(14, resample=Image.BICUBIC, expand=True)
    img.paste(st, (470, 250 + 460 - 120), st)
    dr = ImageDraw.Draw(img)
    dr.text((W // 2, 1230), "Legg på nedtellingsmerke her ↓", font=F(32, 650), fill="#ffd9a0", anchor="mm")
    sticker(dr, W // 2, 1280, "#ffd9a0", "nedtelling til konserten", 640)
    sticker(dr, W // 2, 1440, "#ffffff")
    brand(img, dr, 72, 1700, "#ffffff")
    return img


def story_b(e, today):
    """Nedtelling: antall dager stort."""
    H = 1920
    img = grad(W, H, [(0, "#0d1b3e"), (1, "#050914")])
    snow(img, 11, 160)
    dr = ImageDraw.Draw(img)
    d = d_of(e)
    n = (d - today).days
    gold = "#ffcf6b"
    dr.text((W // 2, 230), "OM", font=B(60, 800), fill=gold, anchor="mm")
    num = Image.new("RGBA", (W, 600), (0, 0, 0, 0))
    ImageDraw.Draw(num).text((W // 2, 300), str(n), font=B(520, 800), fill=hexc(gold) + (255,), anchor="mm")
    glowl = num.filter(ImageFilter.GaussianBlur(40))
    base = img.convert("RGBA")
    base.alpha_composite(glowl, (0, 220))
    base.alpha_composite(num, (0, 220))
    img = base.convert("RGB")
    dr = ImageDraw.Draw(img)
    dr.text((W // 2, 860), "dager", font=FR(90, 600, True), fill="#ffffff", anchor="mm")
    lines = wrap(dr, short(e), B(92, 800), W - 160)
    y = 990
    for ln in lines[:2]:
        dr.text((W // 2, y), ln, font=B(92, 800), fill="#ffffff", anchor="mm")
        y += 100
    dr.text((W // 2, y + 10), f"{pages.WD[d.weekday()]} {d.day}. {pages.MO[d.month - 1]} · {tm(e)} · {e['venue']}", font=F(36, 650), fill="#c9d6ff", anchor="mm")
    t = f"Få billetter igjen · {price(e)}"
    tw = dr.textlength(t, font=F(40, 800))
    dr.rounded_rectangle((W // 2 - tw / 2 - 40, y + 70, W // 2 + tw / 2 + 40, y + 150), radius=40, fill="#e3344f")
    dr.text((W // 2, y + 110), t, font=F(40, 800), fill="#ffffff", anchor="mm")
    cx = W // 2
    ay = y + 200
    for a, b in (((cx, ay), (cx, ay + 60)), ((cx - 26, ay + 36), (cx, ay + 64)), ((cx + 26, ay + 36), (cx, ay + 64))):
        dr.line((*a, *b), fill="#ffffff", width=8)
    sticker(dr, W // 2, ay + 90, "#ffffff")
    brand(img, dr, 72, 1700, "#ffffff")
    return img


def story_c(today):
    """Avgangstavla: alle julekonsertene med «få igjen», gult på svart."""
    H = 1920
    img = Image.new("RGB", (W, H), "#0b0b0c")
    dr = ImageDraw.Draw(img)
    amber, dim = "#ffb21e", "#5a4310"
    dr.text((72, 170), "SISTE BILLETTER", font=M(72, 800), fill=amber)
    dr.text((72, 262), "Julekonserter som snart er utsolgt", font=F(38, 600), fill="#e8e2d0")
    for k, h in enumerate(("DATO", "KONSERT", "STATUS")):
        dr.text(((72, 250, 800)[k], 380), h, font=M(26), fill=dim)
    dr.line((72, 424, W - 72, 424), fill=dim, width=2)
    y = 450
    evs = few_list(today)
    for e in evs[:7]:
        dr.rectangle((60, y - 8, W - 60, y + 150), fill="#151516")
        dr.text((72, y + 8), dshort(d_of(e)), font=M(44, 800), fill=amber)
        lines = wrap(dr, short(e).upper(), M(36, 800), 520)
        yy = y + 8
        for ln in lines[:2]:
            dr.text((250, yy), ln, font=M(36, 800), fill=amber)
            yy += 46
        dr.text((250, yy + 6), fit(dr, f"{tm(e)} {e['venue']}", M(26, 600), 520), font=M(26, 600), fill="#b9913a")
        blink = "FÅ IGJEN"
        dr.rounded_rectangle((800, y + 10, 1010, y + 66), radius=8, fill="#e3344f")
        dr.text((905, y + 38), blink, font=M(30, 800), fill="#ffffff", anchor="mm")
        y += 172
    cx, ay = W // 2, min(y + 30, 1420)
    for a, b in (((cx, ay), (cx, ay + 60)), ((cx - 26, ay + 36), (cx, ay + 64)), ((cx + 26, ay + 36), (cx, ay + 64))):
        dr.line((*a, *b), fill=amber, width=8)
    sticker(dr, W // 2, ay + 90, amber)
    brand(img, dr, 72, 1700, "#e8e2d0")
    dr.text((W - 72, 1730), f"OPPDATERT {dshort(today)}", font=M(24), fill=dim, anchor="rm")
    return img


# ───────────── 4 Reels ─────────────

def ffmpeg(path, w, h, fps):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps),
                             "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium", "-movflags", "+faststart", str(path)],
                            stdin=subprocess.PIPE)


def strip():
    """Panoramaet fra «Helga i ett sveip», men for alle julekonsertene og alltid kveld."""
    import panorama as p
    p.S = 1
    evs = [{**e, "_day": (d_of(e) - FROM).days} for e in EV]
    places, n = p.layout(evs)
    total = p.W1 * n
    centers = [k * p.W1 + x + p.CARD_W / 2 for k, x, _ in places]
    tl = p.Timeline(centers, [19.5 + 2.5 * math.sin(i / 2) for i in range(len(evs))], total)
    img = Image.new("RGBA", (total, p.H))
    p.draw_sky(img, total, tl)
    p.draw_lights(img, total, tl, True)
    p.draw_snowfall(img, total)
    cards = Image.new("RGBA", img.size)
    pins = []
    for e, (k, x, row), c in zip(evs, places, centers):
        bottom = p.card(cards, e, k * p.W1 + x, row, p.sky_color(tl(c)), row == p.LOW)
        pins.append((c, bottom, p.route_y(c)))
    p.draw_city(img, total, True)
    signs = []
    for i, e in enumerate(evs):
        if i == 0 or e["_day"] != evs[i - 1]["_day"]:
            d = d_of(e)
            x = centers[i] if i == 0 else (centers[i - 1] + centers[i]) / 2
            signs.append((x, f"{pages.WD[d.weekday()].upper()} {d.day}. {pages.MO[d.month - 1][:3].upper()}"))
    p.draw_signs(img, signs)
    p.draw_route(img, total, True, pins)
    img.alpha_composite(cards)
    return img.convert("RGB"), centers, evs


def reel_a(out, stills):
    H = 1920
    st, centers, evs = strip()
    top = 330
    sky_top = st.getpixel((10, 2))
    # Hold 1,5 s på starten, sveip i jevnt tempo, hold 2 s på slutten
    fps, start_hold, end_hold, speed = 30, 45, 60, 420
    span = st.width - W
    frames = start_hold + int(span / speed * fps) + end_hold
    first = min(d_of(e) for e in evs)
    proc = ffmpeg(out, W, H, fps)
    shots = {0: "a-start", start_hold + int(span / speed * fps * 0.4): "a-midt", frames - 1: "a-slutt"}
    for f in range(frames):
        x = min(span, max(0, (f - start_hold) * speed / fps))
        img = Image.new("RGB", (W, H), sky_top)
        img.paste(st.crop((int(x), 0, int(x) + W, st.height)), (0, top))
        # Overgang fra overfeltet til himmelen
        dr = ImageDraw.Draw(img)
        dr.rectangle((0, top + st.height, W, H), fill="#081c20")
        cx = x + W / 2
        # Datoen i midten nå
        i = min(range(len(centers)), key=lambda k: abs(centers[k] - cx))
        d = d_of(evs[i])
        dr.text((60, 90), "ALLE JULEKONSERTENE I ÅLESUND", font=M(30), fill="#ffd98a")
        dr.text((54, 130), f"{d.day}. {pages.MO[d.month - 1]}", font=B(110, 800), fill="#ffffff")
        # Fremdrift gjennom desember
        prog = x / span
        dr.rounded_rectangle((60, 272, W - 60, 284), radius=6, fill="#2a3466")
        dr.rounded_rectangle((60, 272, 60 + (W - 120) * prog + 12, 284), radius=6, fill="#ffd98a")
        if f < start_hold:
            dr.text((W - 60, 196), "sveip med →", font=F(36, 700), fill="#ffd98a", anchor="rm")
        dr.text((W // 2, top + st.height + 80), "Datoer og priser: kaskjerda.no", font=B(44, 800), fill="#ffffff", anchor="mm")
        dr.text((W // 2, top + st.height + 140), "Lagre denne til du skal kjøpe billetter", font=F(32, 600), fill="#9fc9c4", anchor="mm")
        proc.stdin.write(img.tobytes())
        if f in shots:
            stills.append((shots[f], img.copy()))
    proc.stdin.close()
    proc.wait()


PAL = [("#e3344f", "#fff4dc"), ("#ffcf6b", "#2a0610"), ("#1f5b3f", "#fff4dc"), ("#2a2f8f", "#ffffff"), ("#fff4dc", "#b3122e")]


def clip_frame(e, k, total):
    H = 1920
    bg, fg = PAL[k % len(PAL)]
    img = Image.new("RGB", (W, H), bg)
    dr = ImageDraw.Draw(img)
    d = d_of(e)
    dr.text((72, 150), f"{k + 1}/{total}", font=M(34), fill=fg)
    dr.text((W - 72, 150), "JULEKONSERTENE", font=M(34), fill=fg, anchor="ra")
    dr.text((60, 300), str(d.day), font=B(420, 800), fill=fg)
    dr.text((72, 760), f"{pages.MO[d.month - 1].upper()} · {pages.WD[d.weekday()].upper()}", font=M(44, 800), fill=fg)
    y = 880
    for ln in wrap(dr, short(e), FR(110, 800), W - 144)[:3]:
        dr.text((66, y), ln, font=FR(110, 800), fill=fg)
        y += 118
    meta = " · ".join(p for p in (tm(e), e["venue"], price(e)) if p)
    dr.text((72, y + 30), fit(dr, meta, F(40, 650), W - 144), font=F(40, 650), fill=fg)
    if e.get("few"):
        dr.rounded_rectangle((72, y + 100, 420, y + 170), radius=35, fill=fg)
        dr.text((246, y + 135), "Få billetter igjen", font=F(34, 800), fill=bg, anchor="mm")
    dr.text((72, 1700), "kaskjerda.no", font=B(44, 800), fill=fg)
    return img


def reel_b(out, stills):
    H = 1920
    fps, hold = 30, 18  # 0,6 s per konsert, raskt som et taktslag
    proc = ffmpeg(out, W, H, fps)
    intro = Image.new("RGB", (W, H), "#2a0610")
    dr = ImageDraw.Draw(intro)
    dr.text((W // 2, 760), f"{len(EV)}", font=B(400, 800), fill="#ffcf6b", anchor="mm")
    dr.text((W // 2, 1010), "julekonserter", font=FR(110, 750, True), fill="#fff4dc", anchor="mm")
    dr.text((W // 2, 1130), "i Ålesund før og i jula", font=F(48, 650), fill="#fff4dc", anchor="mm")
    dr.text((W // 2, 1300), "Ta skjermbilde av din →", font=F(40, 700), fill="#ffcf6b", anchor="mm")
    for _ in range(45):
        proc.stdin.write(intro.tobytes())
    stills.append(("b-intro", intro))
    for k, e in enumerate(EV):
        fr = clip_frame(e, k, len(EV))
        if k in (5, 22):
            stills.append((f"b-{k}", fr))
        for _ in range(hold):
            proc.stdin.write(fr.tobytes())
    outro = Image.new("RGB", (W, H), "#2a0610")
    dr = ImageDraw.Draw(outro)
    dr.text((W // 2, 820), "Alle datoer og priser", font=FR(84, 700, True), fill="#fff4dc", anchor="mm")
    dr.text((W // 2, 940), "kaskjerda.no", font=B(110, 800), fill="#ffcf6b", anchor="mm")
    dr.text((W // 2, 1060), "lenke i bio", font=F(44, 650), fill="#fff4dc", anchor="mm")
    for _ in range(75):
        proc.stdin.write(outro.tobytes())
    stills.append(("b-slutt", outro))
    proc.stdin.close()
    proc.wait()



def day_frame(d, evs, k, total):
    """Ett bilde per dag: dato stort, alle kveldens julekonserter under."""
    H = 1920
    bg, fg = PAL[k % len(PAL)]
    img = Image.new("RGB", (W, H), bg)
    dr = ImageDraw.Draw(img)
    dr.text((72, 150), f"{k + 1}/{total}", font=M(34), fill=fg)
    dr.text((W - 72, 150), "JULEKONSERTENE", font=M(34), fill=fg, anchor="ra")
    dr.text((60, 260), str(d.day), font=B(360, 800), fill=fg)
    dr.text((72, 660), f"{pages.MO[d.month - 1].upper()} · {pages.WD[d.weekday()].upper()}", font=M(44, 800), fill=fg)
    n = len(evs)
    size = 96 if n == 1 else 76 if n == 2 else 60
    y = 780
    for e in evs:
        lines = wrap(dr, short(e), FR(size, 800), W - 144)[:2]
        for ln in lines:
            dr.text((66, y), ln, font=FR(size, 800), fill=fg)
            y += round(size * 1.08)
        meta = " · ".join(p for p in (tm(e), e["venue"], price(e)) if p)
        dr.text((72, y + 6), fit(dr, meta, F(36, 650), W - 144), font=F(36, 650), fill=fg)
        y += 56
        if e.get("few"):
            dr.rounded_rectangle((72, y, 380, y + 56), radius=28, fill=fg)
            dr.text((226, y + 28), "Få billetter igjen", font=F(30, 800), fill=bg, anchor="mm")
            y += 70
        y += 34 if n > 2 else 50
    dr.text((72, 1700), "kaskjerda.no", font=B(44, 800), fill=fg)
    return img


def reel_dag(out, stills):
    """Som reel B, men ett bilde per dag og lengre tid per bilde (0,9 s + 0,35 s per konsert)."""
    H = 1920
    fps = 30
    days = {}
    for e in EV:
        days.setdefault(d_of(e), []).append(e)
    proc = ffmpeg(out, W, H, fps)
    intro = Image.new("RGB", (W, H), "#2a0610")
    dr = ImageDraw.Draw(intro)
    dr.text((W // 2, 760), f"{len(EV)}", font=B(400, 800), fill="#ffcf6b", anchor="mm")
    dr.text((W // 2, 1010), "julekonserter", font=FR(110, 750, True), fill="#fff4dc", anchor="mm")
    dr.text((W // 2, 1130), "i Ålesund før og i jula", font=F(48, 650), fill="#fff4dc", anchor="mm")
    dr.text((W // 2, 1300), "Ta skjermbilde av din →", font=F(40, 700), fill="#ffcf6b", anchor="mm")
    for _ in range(45):
        proc.stdin.write(intro.tobytes())
    stills.append(("intro", intro))
    for k, (d, evs) in enumerate(sorted(days.items())):
        fr = day_frame(d, evs, k, len(days))
        if len(evs) >= 3 and len(stills) < 3 or k == 1:
            stills.append((f"{d.day}.{d.month}", fr))
        for _ in range(round(fps * (0.9 + 0.35 * len(evs)))):
            proc.stdin.write(fr.tobytes())
    outro = Image.new("RGB", (W, H), "#2a0610")
    dr = ImageDraw.Draw(outro)
    dr.text((W // 2, 820), "Alle datoer og priser", font=FR(84, 700, True), fill="#fff4dc", anchor="mm")
    dr.text((W // 2, 940), "kaskjerda.no", font=B(110, 800), fill="#ffcf6b", anchor="mm")
    dr.text((W // 2, 1060), "lenke i bio", font=F(44, 650), fill="#fff4dc", anchor="mm")
    for _ in range(75):
        proc.stdin.write(outro.tobytes())
    stills.append(("slutt", outro))
    proc.stdin.close()
    proc.wait()

def sheet(items, out, scale=0.5, head=90, gap=36):
    w = int(items[0][1].width * scale)
    h = max(int(im.height * scale) for _, im in items)
    s = Image.new("RGB", (len(items) * (w + gap) + gap, h + head + gap), "#efe9df")
    d = ImageDraw.Draw(s)
    for i, (name, im) in enumerate(items):
        x = gap + i * (w + gap)
        s.paste(im.resize((w, int(im.height * scale)), Image.LANCZOS), (x, head))
        d.text((x, head // 2), name, font=B(40, 800), fill="#2b1d12", anchor="lm")
    s.save(out, optimize=True)
    print(out)


if __name__ == "__main__":
    png, mp4 = Path(sys.argv[1]), Path(sys.argv[2])
    what = sys.argv[3] if len(sys.argv) > 3 else "alle"
    if what in ("alle", "plakat"):
        sheet([("A Lineup", poster_a()), ("B Veggkalender", poster_b()),
               ("Bilde 2: uka", poster_list(datetime.date(2026, 11, 28), datetime.date(2026, 12, 2), "28. nov – 2. des"))],
              png / "plakat.png", scale=0.6)
    if what in ("alle", "utsolgt"):
        day = datetime.date(2026, 12, 9)
        e = next(x for x in EV if x["title"].startswith("Adam Douglas"))
        sheet([("A Billetten", story_a(e, day)), ("B Nedtelling", story_b(e, day)), ("C Avgangstavla", story_c(day))],
              png / "snart-utsolgt.png")
    if what == "reel-b":
        stills = []
        reel_b(mp4 / f"reel-B-klipp-{FROM.isoformat()}.mp4", stills)
        sheet([(n.replace("b-", "B "), im) for n, im in stills], png / f"reel-B-{FROM.isoformat()}.png", 0.4)
    if what == "reel-dag":
        stills = []
        reel_dag(mp4 / f"reel-B-dag-{FROM.isoformat()}.mp4", stills)
        sheet(stills[:5], png / f"reel-B-dag-{FROM.isoformat()}.png", 0.4)
    if what in ("alle", "reel"):
        stills = []
        reel_a(mp4 / "reel-A-sveip.mp4", stills)
        reel_b(mp4 / "reel-B-klipp.mp4", stills)
        sheet([(n.replace("a-", "A ").replace("b-", "B "), im) for n, im in stills if n in ("a-start", "a-midt", "a-slutt")], png / "reel-A.png", 0.4)
        sheet([(n.replace("b-", "B "), im) for n, im in stills if n.startswith("b-")], png / "reel-B.png", 0.4)
