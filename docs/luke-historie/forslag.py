"""Forslag til «Luke X»: julevarianten av «I kveld»-historien, 1.–24. desember (1080 × 1920).

Dagens luke = kveldens julekonsert (helst konsert, helst «få billetter igjen», ellers dyrest/største).
Resten av kveldens julearrangementer står uskarpt under, og pila peker ned til lenkemerket
(kaskjerda.no/julekonserter-i-alesund/?ref=ig-luke). Er det ingen julekonsert, blir det et annet
julearrangement; er det ingenting, viser luka neste julekonsert. Alt kommer fra data/events.json.

Fire varianter: A Kalenderen, B Døra, C Lysslynga, D Julekortet.

Kjør: FONT_DIR=<mappe med Bricolage, Figtree, JetBrainsMono, Fraunces, FrauncesItalic> \
      python3 docs/luke-historie/forslag.py docs/luke-historie 2026-12-13 2026-12-09 2026-12-07
"""
import datetime
import math
import os
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import numpy as np
import pages
import ukepost as u
from helgepost import font
from ukepost import B, F, M, PAD, W, block, fit, no_emoji, logo, wrap
from PIL import Image, ImageDraw, ImageFilter

H = 1920
LINK = "kaskjerda.no/julekonserter-i-alesund/?ref=ig-luke"
CFG = pages.jul_config()
EVENTS, _ = u.load()


def FR(size, w=700, italic=False):
    return font("FrauncesItalic.ttf" if italic else "Fraunces.ttf", size, weight=w, optical=min(144, size), soft=50, wonk=1 if italic else 0)


def tm(e):
    m = re.search(r"\d{1,2}:\d{2}", e.get("time") or "")
    return m.group(0).zfill(5) if m else ""


def price(e):
    p = pages.price_text(e)
    return "pris hos arrangør" if p == "Pris hos arrangør" else p


def jul_on(day):
    return [e for e in pages.occurrences([e for e in EVENTS if u.ok(e) and pages.is_jul(e, CFG)], day, day)]


def plan(day):
    """(tips, resten, neste). Tips: julekonsert, ellers annet julearrangement fra kl. 15. Ingenting: neste julekonsert."""
    ev = jul_on(day)
    kons = [e for e in ev if e["cat"] == "konsert"]
    pool = kons or [e for e in ev if not tm(e) or tm(e) >= "15:00"]
    if pool:
        tip = min(pool, key=lambda e: (not e.get("few"), e.get("priceMin") is None, -(e.get("priceMin") or 0), tm(e)))
        rest = sorted((e for e in ev if e is not tip and (e["cat"] == "konsert" or tm(e) >= "15:00")), key=tm)
        return tip, rest, None
    for k in range(1, 30):
        d = day + datetime.timedelta(days=k)
        nk = [e for e in jul_on(d) if e["cat"] == "konsert"]
        if nk:
            return None, [], (d, min(nk, key=lambda e: (e.get("priceMin") is None, -(e.get("priceMin") or 0))))
    return None, [], None


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def grad(stops, angle=0.0):
    y, x = np.mgrid[0:H, 0:W].astype(float)
    t = (y / H) * math.cos(angle) + (x / W) * math.sin(angle)
    t = (t - t.min()) / (t.max() - t.min())
    out = np.zeros((H, W, 3))
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (t >= p0) & (t <= p1)
        k = ((t - p0) / (p1 - p0))[..., None]
        out[m] = (np.array(hexc(c0)) * (1 - k) + np.array(hexc(c1)) * k)[m]
    return Image.fromarray(out.astype("uint8"))


def blob(img, xy, r, color, blur=160, alpha=200):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse((xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r), fill=hexc(color) + (alpha,))
    img.paste(Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(blur))).convert("RGB"))


def glow(img, fn, color, radius=22, strength=2):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(lay), hexc(color) + (255,))
    g = lay.filter(ImageFilter.GaussianBlur(radius))
    base = img.convert("RGBA")
    for _ in range(strength):
        base = Image.alpha_composite(base, g)
    img.paste(Image.alpha_composite(base, lay).convert("RGB"))


def snow(img, seed, n=140, color=(255, 255, 255), top=0, bottom=H):
    rnd = random.Random(seed)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y, r = rnd.uniform(0, W), rnd.uniform(top, bottom), rnd.choice((2, 3, 3, 4, 5, 7))
        d.ellipse((x - r, y - r, x + r, y + r), fill=color + (rnd.randint(70, 190),))
    img.paste(Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(0.8))).convert("RGB"))


def star(dr, cx, cy, r, fill, points=5, inner=0.45):
    pts = []
    for i in range(points * 2):
        a = -math.pi / 2 + i * math.pi / points
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    dr.polygon(pts, fill=fill)


def date_line(day):
    return f"{pages.WD[day.weekday()].upper()} {day.day}. {pages.MO[day.month - 1].upper()}"


def short_date(d):
    return f"{pages.WD[d.weekday()]} {d.day}. {pages.MO[d.month - 1][:3]}."


def card(img, dr, top, day, tip, nxt, s):
    """Tipskortet. s: bg, ink, label, accent, title(size)->font, radius, outline. Gir nederste kant tilbake."""
    x0, x1 = s.get("x0", PAD), s.get("x1", W - PAD)
    x, inner = x0 + 44, x1 - x0 - 88
    if tip:
        label = "KVELDENS JULEKONSERT" if tip["cat"] == "konsert" else "KVELDENS JULETIPS"
        f, size, lines = block(dr, no_emoji(tip["title"]), s["title"], (88, 78, 68, 60), inner, 2)
        step = round(size * 1.06)
        h = 48 + 50 + len(lines) * step + 24 + 70 + 50 + 44
    else:
        label = f"LUKE {day.day}"
        f, size = s["title"](76), 76
        lines = ["Ingen julekonsert", "i kveld"]
        step = 82
        h = 48 + 50 + 2 * step + 30 + (150 if nxt else 0) + 44
    if s.get("shadow"):
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((x0 + 6, top + 22, x1 + 6, top + h + 22), radius=s["radius"], fill=(0, 0, 0, 120))
        img.paste(Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(24))).convert("RGB"))
        dr = ImageDraw.Draw(img)
    dr.rounded_rectangle((x0, top, x1, top + h), radius=s["radius"], fill=s["bg"], outline=s.get("outline"), width=s.get("ow", 0))
    y = top + 48
    dr.text((x, y), label, font=M(30), fill=s["label"])
    y += 58
    for l in lines:
        dr.text((x - 3, y), l, font=f, fill=s["ink"])
        y += step
    y += 24
    if tip:
        t0 = f"kl. {tm(tip)}" if tm(tip) else "hele dagen"
        dr.text((x, y), t0, font=M(50), fill=s["accent"])
        if tip.get("few"):
            t = "Få billetter igjen"
            bx = x + dr.textlength(t0, font=M(50)) + 28
            fw = dr.textlength(t, font=F(32, 800))
            dr.rounded_rectangle((bx, y + 2, bx + fw + 44, y + 56), radius=27, fill=s["accent"])
            dr.text((bx + 22, y + 29), t, font=F(32, 800), fill=s["bg"], anchor="lm")
        y += 70
        dr.text((x, y), fit(dr, f"{tip['venue']} · {price(tip)}", F(40, 650), inner), font=F(40, 650), fill=s["ink"])
    elif nxt:
        d, e = nxt
        dr.text((x, y), f"Neste luke: {short_date(d)}", font=M(36), fill=s["accent"])
        y += 56
        for l in wrap(dr, no_emoji(e["title"]), F(42, 750), inner)[:2]:
            dr.text((x, y), l, font=F(42, 750), fill=s["ink"])
            y += 50
    return top + h


def rest_rows(img, top, rest, row_fill, pill_bg, pill_ink, word="til i kveld"):
    """Resten av kvelden uskarpt, med «+ N»-pille. Gir nederste kant tilbake."""
    if not rest:
        return top
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    n = min(2, len(rest))
    for i, e in enumerate(rest[:n]):
        yy = top + i * 110
        d.rounded_rectangle((PAD, yy, W - PAD, yy + 92), radius=28, fill=row_fill)
        d.text((PAD + 40, yy + 46), tm(e), font=M(42), fill=(255, 255, 255, 255), anchor="lm")
        d.text((PAD + 200, yy + 46), fit(d, no_emoji(e["title"]), F(42, 700), W - 2 * PAD - 240), font=F(42, 700),
               fill=(255, 255, 255, 255), anchor="lm")
    img.paste(Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(9))).convert("RGB"))
    dr = ImageDraw.Draw(img)
    label = f"+ {len(rest)} {word}"
    fl = B(58, 800)
    lw = dr.textlength(label, font=fl)
    cy = top + 55 * n - 10
    dr.rounded_rectangle(((W - lw) // 2 - 42, cy - 52, (W + lw) // 2 + 42, cy + 52), radius=52, fill=pill_bg)
    dr.text((W // 2, cy), label, font=fl, fill=pill_ink, anchor="mm")
    return top + 110 * n


def arrow(dr, y, col):
    cx = W // 2
    dr.line((cx, y, cx, y + 60), fill=col, width=8)
    dr.line((cx - 26, y + 36, cx, y + 64), fill=col, width=8)
    dr.line((cx + 26, y + 36, cx, y + 64), fill=col, width=8)


def sticker(dr, y, col):
    w = 560
    x = (W - w) // 2
    for i in range(x, x + w, 28):
        dr.line((i, y, min(i + 14, x + w), y), fill=col, width=3)
        dr.line((i, y + 110, min(i + 14, x + w), y + 110), fill=col, width=3)
    for j in range(y, y + 110, 28):
        dr.line((x, j, x, min(j + 14, y + 110)), fill=col, width=3)
        dr.line((x + w, j, x + w, min(j + 14, y + 110)), fill=col, width=3)
    dr.text((W // 2, y + 55), "lenkemerke her", font=F(30, 600), fill=col, anchor="mm")


def brand(img, dr, fg, right="", y=1700):
    im, mask = logo(64)
    img.paste(im, (PAD, y), mask)
    dr.text((PAD + 84, y + 32), "kaskjerda.no", font=B(34, 700), fill=fg, anchor="lm")
    if right:
        dr.text((W - PAD, y + 32), right, font=M(30), fill=fg, anchor="rm")


def finish(img, dr, end, col, fg):
    ay = min(1460, end + 24)
    arrow(dr, ay, col)
    sticker(dr, ay + 84, col)
    brand(img, dr, fg)


def to_jul(day):
    n = (datetime.date(day.year, 12, 24) - day).days
    return "julaften!" if n == 0 else f"{n} {'dag' if n == 1 else 'dager'} til jul"


# --- A Kalenderen: fløyelsrød og gull, alle 24 luker, dagens åpnet ---

def var_a(day):
    tip, rest, nxt = plan(day)
    img = grad([(0, "#7a1426"), (0.45, "#4a0a17"), (1, "#1e0409")], 0.25)
    blob(img, (900, 160), 300, "#e8b04a", 180, 90)
    dr = ImageDraw.Draw(img)
    gold = "#e8b04a"
    dr.text((PAD, 120), date_line(day), font=M(32), fill="#f3d9a4")
    dr.text((PAD - 6, 156), f"Luke {day.day}", font=FR(136, 700, True), fill="#ffffff")
    dr.text((W - PAD, 236), to_jul(day), font=FR(44, 500, True), fill="#f3d9a4", anchor="rm")
    # 6 × 4 luker
    gx, gy, cw, ch, gap = PAD, 340, 140, 76, 19
    order = [7, 19, 3, 22, 11, 15, 1, 24, 9, 17, 5, 13, 20, 2, 14, 8, 23, 6, 12, 18, 4, 21, 10, 16]
    for i, n in enumerate(order):
        cx, cy = gx + (i % 6) * (cw + gap), gy + (i // 6) * (ch + gap)
        box = (cx, cy, cx + cw, cy + ch)
        if n == day.day:
            glow(img, lambda d, c: d.rounded_rectangle(box, radius=16, fill=c), gold, 26, 2)
            dr = ImageDraw.Draw(img)
            dr.text((cx + cw // 2, cy + ch // 2 + 2), str(n), font=FR(56, 800), fill="#3a0812", anchor="mm")
        elif n < day.day:
            dr.rounded_rectangle(box, radius=16, outline="#a8743a", width=2, fill="#2a060d")
            star(dr, cx + cw // 2, cy + ch // 2, 18, "#a8743a")
        else:
            dr.rounded_rectangle(box, radius=16, fill="#5c0f1d", outline="#c9934a", width=2)
            dr.text((cx + cw // 2, cy + ch // 2 + 2), str(n), font=FR(46, 600), fill="#f3d9a4", anchor="mm")
    top = gy + 4 * ch + 3 * gap + 40
    s = dict(bg="#fbf3e4", ink="#2a0610", label="#a3162f", accent="#a3162f", title=lambda z: FR(z, 750), radius=34, shadow=True)
    end = card(img, dr, top, day, tip, nxt, s)
    dr = ImageDraw.Draw(img)
    end = rest_rows(img, end + 36, rest, (255, 220, 170, 60), gold, "#2a0610")
    dr = ImageDraw.Draw(img)
    finish(img, dr, end, "#f3d9a4", "#ffffff")
    return img


# --- B Døra: vinternatt, luka står åpen og lyser ---

def var_b(day):
    tip, rest, nxt = plan(day)
    img = grad([(0, "#0f2350"), (0.55, "#0a1534"), (1, "#050a1a")])
    snow(img, day.toordinal(), 170)
    dr = ImageDraw.Draw(img)
    rnd = random.Random(day.day)
    for _ in range(14):
        star(dr, rnd.uniform(40, W - 40), rnd.uniform(40, 230), rnd.choice((6, 8, 10)), "#ffe7a3")
    dr.text((W // 2, 140), date_line(day), font=M(32), fill="#cfe0ff", anchor="mm")
    dr.text((W // 2, 230), f"Hva skjuler seg bak luke {day.day}?", font=FR(58, 600, True), fill="#ffffff", anchor="mm")
    # Ramme og åpne dører
    fx0, fx1, fy0 = 170, 910, 360
    s = dict(bg="#fff4da", ink="#1b1406", label="#b0741a", accent="#b3122e", title=lambda z: FR(z, 750), radius=10,
             x0=fx0 + 26, x1=fx1 - 26)
    # Mål kortet først for å vite høyden på åpningen
    probe = Image.new("RGB", (W, H))
    fy1 = card(probe, ImageDraw.Draw(probe), fy0 + 30, day, tip, nxt, dict(s, bg="#000")) + 30
    glow(img, lambda d, c: d.rectangle((fx0, fy0, fx1, fy1), fill=c), "#ffcf6b", 50, 2)
    dr = ImageDraw.Draw(img)
    num = str(day.day)
    halves = (num[0], num[1]) if len(num) == 2 else (num, "")
    door = "#9e1b2f"
    sw = 140
    dr.polygon([(fx0, fy0), (fx0 - sw, fy0 - 50), (fx0 - sw, fy1 + 50), (fx0, fy1)], fill=door, outline="#e8b04a", width=4)
    dr.polygon([(fx1, fy0), (fx1 + sw, fy0 - 50), (fx1 + sw, fy1 + 50), (fx1, fy1)], fill=door, outline="#e8b04a", width=4)
    for (cx, t) in ((fx0 - sw // 2, halves[0]), (fx1 + sw // 2, halves[1])):
        if t:
            dr.text((cx, (fy0 + fy1) // 2), t, font=FR(110, 800), fill="#f3d9a4", anchor="mm")
    card(img, dr, fy0 + 30, day, tip, nxt, dict(s, bg="#fff4da"))
    dr = ImageDraw.Draw(img)
    dr.rectangle((fx0, fy0, fx1, fy1), outline="#e8b04a", width=6)
    end = rest_rows(img, fy1 + 84, rest, (160, 190, 255, 60), "#ffcf6b", "#1b1406")
    dr = ImageDraw.Draw(img)
    finish(img, dr, end, "#ffffff", "#ffffff")
    return img


# --- C Lysslynga: 24 lyspærer, én tennes for hver dag ---

def var_c(day):
    tip, rest, nxt = plan(day)
    img = grad([(0, "#0f3a2c"), (0.5, "#0a261d"), (1, "#04110c")], 0.2)
    blob(img, (180, 1200), 300, "#1f7a55", 200, 80)
    dr = ImageDraw.Draw(img)
    colors = ["#ff4d5e", "#ffd23f", "#3fd18a", "#4da3ff", "#ff7ad9", "#ff9f3f"]
    bulbs = []
    for row, (y0, sag) in enumerate(((110, 60), (270, 60))):
        pts = [(x, y0 + sag * math.sin(math.pi * x / W)) for x in range(-20, W + 21, 6)]
        dr.line(pts, fill="#203a30", width=5)
        for i in range(12):
            n = row * 12 + i + 1
            x = 70 + i * (W - 140) / 11
            bulbs.append((n, x, y0 + sag * math.sin(math.pi * x / W)))
    for n, x, y in bulbs:
        c = colors[(n - 1) % len(colors)]
        r = 22 if n != day.day else 34
        by = y + 14 + r
        if n <= day.day:
            glow(img, lambda d, cc: d.ellipse((x - r, by - r * 1.25, x + r, by + r * 1.25), fill=cc), c, 26 if n == day.day else 16, 3 if n == day.day else 1)
        dr = ImageDraw.Draw(img)
        if n > day.day:
            dr.ellipse((x - r, by - r * 1.25, x + r, by + r * 1.25), fill="#2b3f37")
        dr.rectangle((x - 10, y, x + 10, y + 18), fill="#1a1a1a")
        if n == day.day:
            dr.text((x, by), str(n), font=B(34, 800), fill="#0a171b", anchor="mm")
    dr = ImageDraw.Draw(img)
    dr.text((PAD, 450), f"{date_line(day)} · {to_jul(day).upper()}", font=M(30), fill="#a9e7c9")
    dr.text((PAD - 8, 480), f"Luke {day.day}", font=B(160, 800), fill="#ffffff")
    s = dict(bg="#ffffff", ink="#0a171b", label="#13805a", accent="#d8233c", title=lambda z: B(z, 800), radius=40)
    end = card(img, dr, 700, day, tip, nxt, s)
    dr = ImageDraw.Draw(img)
    end = rest_rows(img, end + 36, rest, (255, 255, 255, 60), "#ffd23f", "#0a171b")
    dr = ImageDraw.Draw(img)
    finish(img, dr, end, "#ffffff", "#ffffff")
    return img


# --- D Julekortet: krempapir, frimerke og poststempel ---

def var_d(day):
    tip, rest, nxt = plan(day)
    red, green, ink = "#b3122e", "#1f5b3f", "#2b1d12"
    img = Image.new("RGB", (W, H), "#f4ead8")
    rnd = random.Random(7)
    px = np.array(img).astype(int)
    px += np.random.default_rng(3).integers(-7, 7, (H, W, 1))
    img = Image.fromarray(px.clip(0, 255).astype("uint8"))
    dr = ImageDraw.Draw(img)
    dr.rectangle((30, 30, W - 30, H - 30), outline=red, width=8)
    dr.rectangle((48, 48, W - 48, H - 48), outline=green, width=3)
    # Frimerke
    sx, sy, sw, sh = W - PAD - 250, 110, 250, 300
    stamp = Image.new("RGBA", (sw + 40, sh + 40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sd.rectangle((20, 20, 20 + sw, 20 + sh), fill="#fffaf0")
    for k in range(20, 20 + sw + 1, 25):
        for yy in (20, 20 + sh):
            sd.ellipse((k - 8, yy - 8, k + 8, yy + 8), fill=(0, 0, 0, 0))
    for k in range(20, 20 + sh + 1, 25):
        for xx in (20, 20 + sw):
            sd.ellipse((xx - 8, k - 8, xx + 8, k + 8), fill=(0, 0, 0, 0))
    sd.rectangle((38, 38, 2 + sw, 2 + sh), fill=red)
    star(sd, 20 + sw // 2, 92, 26, "#f3d9a4")
    sd.text((20 + sw // 2, 200), str(day.day), font=FR(130, 800), fill="#ffffff", anchor="mm")
    sd.text((20 + sw // 2, 290), "LUKE", font=M(26), fill="#f3d9a4", anchor="mm")
    stamp = stamp.rotate(-5, resample=Image.BICUBIC, expand=True)
    img.paste(stamp, (sx - 30, sy - 30), stamp)
    dr = ImageDraw.Draw(img)
    # Poststempel
    ccx, ccy = sx - 110, sy + 260
    for r in (110, 96):
        dr.ellipse((ccx - r, ccy - r, ccx + r, ccy + r), outline=(43, 29, 18), width=4)
    dr.text((ccx, ccy - 34), "ÅLESUND", font=M(28), fill=ink, anchor="mm")
    dr.text((ccx, ccy + 10), f"{day.day:02d}.12.{day.year % 100}", font=M(30), fill=ink, anchor="mm")
    for k in range(4):
        yy = ccy - 30 + k * 22
        dr.line((ccx + 120, yy, ccx + 330, yy + 6 * math.sin(k)), fill=(43, 29, 18), width=4)
    dr.text((PAD + 10, 130), "God jul", font=FR(96, 700, True), fill=red)
    dr.text((PAD + 10, 245), "fra Ålesund", font=FR(66, 500, True), fill=green)
    dr.text((PAD + 14, 360), date_line(day), font=M(30), fill=ink)
    s = dict(bg="#fffaf0", ink=ink, label=green, accent=red, title=lambda z: FR(z, 750), radius=6, outline=ink, ow=3)
    end = card(img, dr, 500, day, tip, nxt, s)
    dr = ImageDraw.Draw(img)
    end = rest_rows(img, end + 36, rest, (43, 29, 18, 50), green, "#ffffff")
    dr = ImageDraw.Draw(img)
    finish(img, dr, end, red, ink)
    return img


VARIANTS = [("A Kalenderen", var_a), ("B Døra", var_b), ("C Lysslynga", var_c), ("D Julekortet", var_d)]


def sheet(day, out):
    sc, gap, head = 0.5, 36, 90
    w, h = int(W * sc), int(H * sc)
    s = Image.new("RGB", (len(VARIANTS) * (w + gap) + gap, h + head + gap), "#efe9df")
    d = ImageDraw.Draw(s)
    for i, (name, fn) in enumerate(VARIANTS):
        im = fn(day).resize((w, h), Image.LANCZOS)
        x = gap + i * (w + gap)
        s.paste(im, (x, head))
        d.text((x, head // 2), name, font=B(40, 800), fill="#2b1d12", anchor="lm")
    s.save(out, optimize=True)
    print(out)


if __name__ == "__main__":
    folder = Path(sys.argv[1])
    for a in sys.argv[2:]:
        day = datetime.date.fromisoformat(a)
        sheet(day, folder / f"luke-{day.day:02d}.png")
