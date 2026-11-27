"""Engangsløsning: 1. søndag i advent (27.–29. nov 2026). Instagram-karusell (9 bilder, 1080 × 1350) og reel (1080 × 1920, mp4).

Alt kommer fra data/events.json og data/kino.json (samme utvalg og filter som ukepost.py). Tider, priser og steder hentes ut
fra arrangementene, ikke skrevet inn for hånd; finnes ikke et arrangement lenger, stopper skriptet i stedet for å gjette.

Kjør: FONT_DIR=<skrifter> python3 scripts/adventshelg.py <mappe> [--bilder|--reel]
Skrifter: BricolageGrotesque, Figtree, JetBrainsMono, Fraunces og FrauncesItalic (som i oppdater.yml, pluss Fraunces).
"""
import datetime
import json
import math
import random
import re
import struct
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pages
import ukepost as u
from helgepost import font
from ukepost import B, F, M, fit, logo, no_emoji, wrap
from PIL import Image, ImageDraw, ImageFilter

W, H, RH = 1080, 1350, 1920
FRI, SAT, SUN = (datetime.date(2026, 11, d) for d in (27, 28, 29))
DAYS = (FRI, SAT, SUN)
GOLD, CREAM, RED, GREEN = "#ffd98a", "#fff4dc", "#e3344f", "#2f8f5b"
PAD = 72

EVENTS, _ = u.load()
FILMS = json.loads((pages.ROOT / "data" / "kino.json").read_text())["films"]


def FR(size, w=700, italic=False):
    return font("FrauncesItalic.ttf" if italic else "Fraunces.ttf", size, weight=w, optical=min(144, size), wonk=1 if italic else 0)


# ───────────── Data ─────────────

def occ(day):
    return [e for e in pages.occurrences(EVENTS, day, day) if u.ok(e) or e.get("soldOut")]


def ev(day, key):
    """Arrangementet på dagen med key i tittelen. Stopper hvis det ikke finnes."""
    for e in occ(day):
        if key.lower() in e["title"].lower():
            return e
    raise SystemExit(f"Fant ikke «{key}» {day}: oppdater skriptet eller dataene")


def tid(e):
    return e.get("time") or ""


def pris(e):
    p = pages.price_text(e)
    return "" if p in ("Pris hos arrangør",) else p.replace(" kr", "\u00a0kr")


def film(key):
    for f in FILMS:
        if key.lower() in f["title"].lower():
            return f
    raise SystemExit(f"Fant ikke filmen «{key}»")


def film_tider(f, day):
    return [s["start"][11:16] for s in f["shows"] if s["start"][:10] == day.isoformat()]


def antall():
    """Antall ulike arrangementer fredag–søndag (ikke julebord, ikke utsolgte)."""
    ids = set()
    for d in DAYS:
        ids |= {e["id"] for e in occ(d) if e["cat"] != "julebord" and not e.get("soldOut")}
    return len(ids)


# ───────────── Tegning ─────────────

class Dr:
    """ImageDraw som blander halvgjennomsiktige farger (#rrggbbaa eller RGBA-tuppel) inn i et RGBA-bilde, ikke bare skriver dem over."""

    def __init__(self, img):
        self.img, self.d = img, ImageDraw.Draw(img)

    def __getattr__(self, name):
        attr = getattr(self.d, name)
        if name not in ("text", "rounded_rectangle", "line", "ellipse", "polygon", "rectangle"):
            return attr

        def call(*a, **kw):
            fill = kw.get("fill")
            alpha = (int(fill[7:], 16) if isinstance(fill, str) and len(fill) == 9 else fill[3] if isinstance(fill, tuple) and len(fill) == 4 else 255)
            if alpha >= 255:
                return attr(*a, **kw)
            if isinstance(fill, str):
                kw["fill"] = hexc(fill[:7]) + (alpha,)
            lay = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
            getattr(ImageDraw.Draw(lay), name)(*a, **kw)
            self.img.alpha_composite(lay)
        return call


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def grad(w, h, c0, c1, angle=0.0):
    y, x = np.mgrid[0:h, 0:w].astype(float)
    t = (y / h) * math.cos(angle) + (x / w) * math.sin(angle)
    t = ((t - t.min()) / (t.max() - t.min()))[..., None]
    return Image.fromarray((np.array(hexc(c0)) * (1 - t) + np.array(hexc(c1)) * t).astype("uint8"))


def snow_layer(w, h, seed, n=130, rmax=6):
    rnd = random.Random(seed)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.choice((2, 3, 3, 4, 5, rmax))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rnd.randint(70, 200)))
    return lay.filter(ImageFilter.GaussianBlur(0.8))


def stars(img, seed, n=70, ymax=None):
    rnd = random.Random(seed)
    d = Dr(img)
    for _ in range(n):
        x, y = rnd.uniform(0, img.width), rnd.uniform(0, ymax or img.height)
        r = rnd.choice((1, 1, 2, 2, 3))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 244, 220))


def glow(img, xy, r, color, alpha=150):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse((xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r), fill=(*hexc(color), alpha))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(r / 2.2)))


def skyline(img, base, seed, body="#071a1e", amp=1.0, ground=400):
    """Ålesund-silhuett med snø på takene og tente vinduer."""
    rnd = random.Random(seed)
    d = Dr(img)
    x = -20
    while x < img.width + 20:
        w = rnd.randint(70, 150)
        h = int(rnd.randint(110, 250) * amp)
        top = base - h
        d.rectangle((x, top, x + w, base + ground), fill=body)
        kind = rnd.choice(("flat", "pitch", "pitch", "tower"))
        if kind == "pitch":
            d.polygon([(x - 6, top + 4), (x + w / 2, top - w * 0.42), (x + w + 6, top + 4)], fill=body)
            d.line([(x - 6, top + 2), (x + w / 2, top - w * 0.42), (x + w + 6, top + 2)], fill="#eef6f8", width=6)
        elif kind == "tower":
            tw = w * 0.34
            cx = x + w / 2
            d.rectangle((cx - tw / 2, top - 80, cx + tw / 2, top), fill=body)
            d.polygon([(cx - tw / 2 - 5, top - 80), (cx, top - 80 - tw * 1.5), (cx + tw / 2 + 5, top - 80)], fill=body)
            d.line([(cx - tw / 2 - 5, top - 82), (cx, top - 82 - tw * 1.5)], fill="#eef6f8", width=5)
        else:
            d.rectangle((x - 4, top - 10, x + w + 4, top + 4), fill="#eef6f8")
        for wy in range(top + 26, base - 10, 44):
            for wx in range(int(x) + 16, int(x + w) - 22, 34):
                if rnd.random() < 0.55:
                    d.rectangle((wx, wy, wx + 14, wy + 20), fill="#ffc86b" if rnd.random() < 0.8 else "#ff9d4a")
        x += w + rnd.randint(-8, 6)
    d.rectangle((0, base + 1, img.width, base + ground), fill="#f3f8fa")


def garland(img, y, seed, sag=40, x0=-20, x1=None, size=11):
    rnd = random.Random(seed)
    d = Dr(img)
    x1 = x1 or img.width + 20
    pts = [(x, y + sag * math.sin(math.pi * (x - x0) / (x1 - x0) * 4) * 0.5 + sag * 0.5) for x in range(int(x0), int(x1), 8)]
    d.line(pts, fill="#0c1418", width=4)
    cols = ["#ff4d6d", "#ffd35c", "#5be0a3", "#6cb7ff", "#ffffff"]
    for i in range(0, len(pts), 5):
        x, yy = pts[i]
        c = rnd.choice(cols)
        glow(img, (x, yy + size), size * 2.4, c, 90)
        d.ellipse((x - size / 2, yy, x + size / 2, yy + size * 1.6), fill=c)


def candle(img, x, base, h, lit, phase=0.0, w=40, color="#d02a46"):
    d = Dr(img)
    d.rounded_rectangle((x - w / 2, base - h, x + w / 2, base), radius=6, fill=color)
    d.rectangle((x - w / 2, base - h, x - w / 2 + 9, base), fill="#9c1730")
    d.line((x, base - h, x, base - h - 14), fill="#2a1d10", width=4)
    if lit:
        fy = base - h - 18
        fl = 1 + 0.07 * math.sin(phase * 2.1) + 0.04 * math.sin(phase * 5.3)
        sway = 3 * math.sin(phase * 1.7)
        glow(img, (x, fy - 24), 150 * fl, "#ffb84d", 120)
        glow(img, (x, fy - 24), 70 * fl, "#fff0b0", 160)
        d = Dr(img)
        fh, fw = 58 * fl, 17
        d.polygon([(x + sway * 0.4, fy - fh), (x + fw, fy - fh * 0.32), (x + fw * 0.7, fy), (x - fw * 0.7, fy), (x - fw, fy - fh * 0.32)], fill="#ffc34a")
        d.polygon([(x + sway * 0.2, fy - fh * 0.62), (x + fw * 0.52, fy - fh * 0.2), (x, fy + 2), (x - fw * 0.52, fy - fh * 0.2)], fill="#fff6c8")


def wreath(img, cx, cy, rx, ry, lit=1, phase=0.0, candle_h=190):
    """Adventskrans med fire lys, `lit` av dem tent (fra venstre)."""
    d = Dr(img)
    rnd = random.Random(7)
    for k, (col, rr) in enumerate((("#13402b", 38), ("#1f6a46", 32), ("#2f8f5b", 24))):
        for i in range(120):
            a = i / 120 * 2 * math.pi
            x = cx + (rx + rnd.uniform(-10, 10)) * math.cos(a)
            y = cy + (ry + rnd.uniform(-6, 6)) * math.sin(a)
            d.ellipse((x - rr, y - rr * 0.8, x + rr, y + rr * 0.8), fill=col)
    for i in range(26):
        a = rnd.uniform(0, 2 * math.pi)
        x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill="#d62d4a")
        d.ellipse((x - 4, y - 5, x - 1, y - 2), fill="#ff9aa8")
    for i, f in enumerate((-0.8, -0.27, 0.27, 0.8)):
        x = cx + rx * f
        y = cy - ry * math.sqrt(1 - f * f) + 6
        candle(img, x, y, candle_h, i < lit, phase + i * 1.3)
    # sløyfe foran
    bx, by = cx, cy + ry + 6
    d = Dr(img)
    d.polygon([(bx, by), (bx - 70, by - 34), (bx - 70, by + 38)], fill="#c8243e")
    d.polygon([(bx, by), (bx + 70, by - 34), (bx + 70, by + 38)], fill="#c8243e")
    d.ellipse((bx - 18, by - 18, bx + 18, by + 18), fill="#e8465f")


def star5(d, cx, cy, r, fill, inner=0.45):
    d.polygon([(cx + (r if i % 2 == 0 else r * inner) * math.cos(-math.pi / 2 + i * math.pi / 5),
                cy + (r if i % 2 == 0 else r * inner) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)], fill=fill)


def wrap1(dr, text, f, width):
    """Som wrap, men bryter bare på vanlig mellomrom (ikke \u00a0, så «350 kr» holdes samlet)."""
    out, cur = [], ""
    for word in text.split(" "):
        t = f"{cur} {word}".strip()
        if cur and dr.textlength(t, font=f) > width:
            out.append(cur)
            cur = word
        else:
            cur = t
    return out + [cur] if cur else out


def lines(dr, x, y, text, f, fill, width, lh=1.08, max_lines=3, anchor="l"):
    """Bryter teksten og tegner den. Gir underkant."""
    allv = wrap1(dr, text, f, width)
    ls = allv[:max_lines]
    if len(allv) > max_lines:
        ls[-1] = fit(dr, " ".join(allv[max_lines - 1:]), f, width)
    for ln in ls:
        dr.text((x, y), ln, font=f, fill=fill, anchor=anchor + "a")
        y += int(f.size * lh)
    return y


def pill(dr, x, y, text, fg, bg, f=None, padx=26, h=62):
    f = f or F(32, 800)
    w = dr.textlength(text, font=f)
    dr.rounded_rectangle((x, y, x + w + padx * 2, y + h), radius=h // 2, fill=bg)
    dr.text((x + padx, y + h / 2 + 1), text, font=f, fill=fg, anchor="lm")
    return w + padx * 2


def dag(d):
    return pages.WD[d.weekday()][:3].upper()


# ───────────── Karusell ─────────────

TOTAL = 9
THEMES = {  # (bakgrunn topp, bunn, tekst, aksent)
    "natt": ("#0a1238", "#231a5c", CREAM, GOLD),
    "plomme": ("#2a0d3d", "#6a2155", CREAM, GOLD),
    "skog": ("#0b2b24", "#1c5a3f", CREAM, GOLD),
    "vin": ("#33091a", "#8a1d3a", CREAM, GOLD),
    "kino": ("#101a3a", "#1e3f6e", CREAM, "#ffcf6b"),
}


def slide(n, theme, kicker="1. ADVENT · 27.–29. NOV", last=False, flakes=True):
    top, bot, fg, ac = THEMES[theme]
    img = grad(W, H, top, bot, 0.25).convert("RGBA")
    stars(img, n, 55, 520)
    if flakes:
        img.alpha_composite(snow_layer(W, H, n * 3, 110))
    dr = Dr(img)
    dr.text((PAD, 74), kicker, font=M(28), fill=ac)
    if n:
        dr.text((W - PAD, 74), f"{n}/{TOTAL}", font=M(28), fill=ac, anchor="ra")
    y = 1318 - 68
    im, mask = logo(68)
    img.paste(im.convert("RGBA"), (PAD, y), mask)
    dr.text((PAD + 88, y + 34), "kaskjerda.no", font=B(34, 700), fill=fg, anchor="lm")
    if not last:
        dr.text((W - PAD, y + 34), "sveip →", font=F(34, 700), fill=ac, anchor="rm")
    return img, dr, fg, ac


def save(img, folder, name):
    img.convert("RGB").save(folder / name, optimize=True)


def cover(folder):
    img, dr, fg, ac = slide(1, "natt", kicker="ÅLESUND · 27.–29. NOVEMBER", flakes=False)
    glow(img, (W // 2, 880), 420, "#ffb347", 55)
    skyline(img, 1150, 4, amp=0.9, ground=70)
    garland(img, 1060, 3, 50)
    wreath(img, W // 2, 1030, 330, 88, lit=1, phase=0.6, candle_h=170)
    img.alpha_composite(snow_layer(W, H, 5, 120))
    dr = Dr(img)
    dr.text((PAD, 150), "JUL, BARN OG LYS", font=M(34, 800), fill=GOLD)
    for i, t in enumerate(("Første advent", "i Ålesund")):
        dr.text((PAD - 4, 210 + i * 160), t, font=FR(140, 800, True), fill=CREAM)
    dr.text((PAD, 560), "Alt som skjer fra fredag til søndag.", font=F(46, 650), fill=CREAM)
    t = f"{antall()} arrangementer"
    f = B(46, 800)
    w = dr.textlength(t, font=f)
    dr.rounded_rectangle((PAD, 640, PAD + w + 56, 716), radius=38, fill=GOLD)
    dr.text((PAD + 28, 679), t, font=f, fill="#2a0d3d", anchor="lm")
    save(img, folder, "1-forside.png")


def stop(img, dr, y, tm, title, sub, tag, ac, fg, last=False):
    """Ett punkt på tidslinja: klokkeslett til venstre, lysperle og tekst til høyre."""
    dr.text((PAD, y + 6), tm, font=M(50, 800), fill=ac)
    cx = 322
    if not last:
        dr.line((cx, y + 58, cx, y + 272), fill=(255, 217, 138, 120), width=4)
    glow(img, (cx, y + 36), 34, "#ffcf6b", 140)
    Dr(img).ellipse((cx - 14, y + 22, cx + 14, y + 50), fill="#ffd98a")
    x = 372
    f = B(60, 800)
    ls = wrap(dr, title, f, W - x - PAD)[:2]
    yy = y
    for ln in ls:
        dr.text((x, yy), ln, font=f, fill=fg)
        yy += 64
    yy = lines(dr, x, yy + 6, sub, F(34, 600), "#d9d4ee", W - x - PAD, lh=1.2, max_lines=3)
    if tag:
        pill(dr, x, yy + 8, tag, "#2a0d3d", ac, F(30, 800), 22, 52)


def rute(n, theme, folder, name, tittel, steg):
    img, dr, fg, ac = slide(n, theme)
    for i, t in enumerate(tittel):
        dr.text((PAD - 4, 130 + i * 118), t, font=FR(118, 800, True), fill=fg)
    y = 130 + len(tittel) * 118 + 40
    dr.text((PAD, y), "Forslag til dagen, alt fra programmet", font=F(34, 600), fill="#d9d4ee")
    y += 82
    for i, s in enumerate(steg):
        stop(img, dr, y + i * 262, *s, ac, fg, last=i == len(steg) - 1)
    save(img, folder, name)


def slide_lordag(folder):
    steinerskolen = ev(SAT, "Julemarked på Steinerskolen")
    putti = ev(SAT, "Putti Plutti")
    lys = ev(SAT, "Lysparken")
    steg = [
        ("11:00", "Julemarked på Steinerskolen", "Kafé, salgsboder og aktiviteter for store og små. Åpent til kl. 17.", None),
        (tid(putti).split(" og ")[0], "Putti Plutti Pott", f"Barneforestilling i Parken kulturhus, {pris(putti)}. Også kl. 16:00.", None),
        (tid(lys), "Lysparken tennes", "I Spjelkavika. Konsert kl. 17, lysene tennes 17:30 og fyrverkeri 17:45.", "GRATIS"),
    ]
    assert steinerskolen["time"] == "11:00"
    rute(2, "plomme", folder, "2-familielordag.png", ("Perfekt", "familielørdag"), steg)


def slide_sondag(folder):
    f = film("Julenissens verksted")
    peppe = ev(SUN, "Pepperkakeverksted")
    symf = ev(SUN, "Adventskonsert")
    steg = [
        (film_tider(f, SUN)[0], "Julenissens verksted", f"Tegnefilm på ODEON Ålesund, {f['minutes']} minutter og tillatt for alle.", None),
        (tid(peppe), "Pepperkakeverksted", "Med Racoon hos Sunnmørsposten. Dørene åpner 12:30." + (" Få plasser igjen." if peppe.get("few") else ""), "GRATIS"),
        (tid(symf), "Adventskonsert med barnekor", "Ålesund kirke, med barnekoret 123.klang. Gratis for barn i følge med voksen.", None),
    ]
    rute(3, "skog", folder, "3-familiesondag.png", ("Perfekt", "familiesøndag"), steg)


def card(img, dr, y, chip, chip_bg, title, sub, meta, fg, sub_col="#d9d4ee", fill="#ffffff1f"):
    """Kort med brikke, tittel og tekst. Høyden følger innholdet. Gir underkant."""
    inner = W - 2 * PAD - 72
    ft, fs = B(58, 800), F(33, 600)
    tl, sl = wrap(dr, title, ft, inner)[:2], wrap1(dr, sub, fs, inner)[:3]
    h = 98 + 62 * len(tl) + 4 + int(33 * 1.22) * len(sl) + 28
    dr.rounded_rectangle((PAD, y, W - PAD, y + h), radius=34, fill=fill)
    dr.rounded_rectangle((PAD + 24, y + 22, PAD + 24 + 150 + (60 if len(chip) > 8 else 0), y + 22 + 54), radius=27, fill=chip_bg)
    dr.text((PAD + 24 + (150 + (60 if len(chip) > 8 else 0)) / 2, y + 22 + 28), chip, font=M(27, 800), fill="#1b1030", anchor="mm")
    yy = y + 98
    for ln in tl:
        dr.text((PAD + 36, yy), ln, font=ft, fill=fg)
        yy += 62
    lines(dr, PAD + 36, yy + 4, sub, fs, sub_col, inner, lh=1.22, max_lines=3)
    if meta:
        dr.text((W - PAD - 28, y + 50), meta, font=B(40, 800), fill=GOLD, anchor="rm")
    return y + h


def slide_lys(folder):
    img, dr, fg, ac = slide(4, "natt")
    garland(img, 118, 9, 26, size=9)
    dr = Dr(img)
    dr.text((PAD - 4, 170), "Lys og marked", font=FR(118, 800, True), fill=fg)
    lys, devold = ev(SAT, "Lysparken"), ev(SAT, "Designernes julemarked")
    st = ev(SAT, "Julemarked på Steinerskolen")
    y = 360
    y = card(img, dr, y, "LØR " + tid(lys), GOLD, "Lysparken tennes", "Spjelkavika. Konsert kl. 17, lysene tennes 17:30 og fyrverkeri 17:45. Står hele desember.", "Gratis", fg) + 26
    y = card(img, dr, y, "LØR–SØN", "#9fe3c0", "Designernes julemarked", "Julegaver og håndverk fra lokale designere, på Devoldfabrikken i Langevåg. Lør 10–18, søn 12–17.", "", fg) + 26
    card(img, dr, y, "LØR " + tid(st), "#ffb3c1", "Julemarked på Steinerskolen", "Kafé, salgsboder og aktiviteter for store og små. Åpent til kl. 17.", "", fg)
    assert devold["title"].startswith("Designernes")
    save(img, folder, "4-lys-og-marked.png")


def slide_barn(folder):
    img, dr, fg, ac = slide(5, "vin")
    dr.text((PAD - 4, 130), "Mer for barna", font=FR(118, 800, True), fill=fg)
    putti, gard = ev(SAT, "Putti Plutti"), ev(SUN, "Jul på gården")
    f1, f2 = film("Julenissens verksted"), film("Jul med Astrid Lindgren")
    tider = {d: tid(ev(d, "Putti Plutti")) for d in DAYS}
    y = 320
    y = card(img, dr, y, "PARKEN", "#ffcf6b", "Putti Plutti Pott",
             f"Fre {tider[FRI]}, lør {tider[SAT]} og søn {tider[SUN]}. Barneforestilling i Parken kulturhus.", pris(putti), fg) + 26
    y = card(img, dr, y, "SØN " + tid(gard), "#9fe3c0", "Jul på gården med nissebesøk",
             "Borgund Dyreklubb. Nissen kommer på besøk til dyra og barna.", pris(gard), fg) + 26
    card(img, dr, y, "KINO", "#9cc6ff", "Julenissens verksted",
         f"Lør og søn fra kl. {film_tider(f1, SAT)[0]}, {f1['minutes']} min. Jul med Astrid Lindgren kl. {film_tider(f2, SAT)[0]} og {film_tider(f2, SAT)[1]}. Begge tillatt for alle.", "", fg)
    save(img, folder, "5-barna.png")
    assert "nisse" in gard["title"].lower()


def rad(img, dr, y, d, tm, title, sub, fg, ac, extra=None, h=150):
    dr.text((PAD, y + 4), dag(d), font=M(30, 800), fill=ac)
    dr.text((PAD, y + 44), tm.split(" og ")[0], font=M(44, 800), fill=fg)
    x = 250
    yy = y
    f = B(52, 800)
    for ln in wrap(dr, title, f, W - x - PAD)[:2]:
        dr.text((x, yy), ln, font=f, fill=fg)
        yy += 56
    yy = lines(dr, x, yy + 2, sub, F(34, 600), "#d9d4ee", W - x - PAD, lh=1.2, max_lines=3)
    if extra:
        pill(dr, x, yy + 8, extra, "#2a0d3d", ac, F(28, 800), 20, 48)
        yy += 60
    return yy


def slide_konserter(folder):
    img, dr, fg, ac = slide(6, "plomme")
    for i, t in enumerate(("Adventskonserter",)):
        dr.text((PAD - 4, 130), t, font=FR(104, 800, True), fill=fg)
    tf, vf = ev(SAT, "Julekonsert på låven"), ev(SAT, "For vår Jord")
    sy, va = ev(SUN, "Adventskonsert"), ev(SUN, "Mannskoret Varde")
    zi = ev(SUN, "Zimmermann")
    rows = [
        (SAT, tid(tf), "Julekonsert på låven i Tennfjord", f"Jazzsangerinne Gine Gaustad Anderssen og pianist Arne Torvik. {pris(tf)}.", "Også kl. 19:00"),
        (SAT, tid(vf), "For vår Jord, Borgund kirke", "Anita Skorgan, Karoline Krüger og Sara Skorgan Teigen.", None),
        (SUN, tid(sy), "Ålesund symfoniorkester", f"Ålesund kirke. Nøtteknekkeren og barnekor. {pris(sy)}.", "Få billetter igjen" if sy.get("few") else None),
        (SUN, tid(va), "Mannskoret Varde", f"Julekonsert i Borgund kirke. {pris(va)}.", None),
    ]
    y = 290
    for d, tm, t, s, x in rows:
        y = rad(img, dr, y, d, tm, t, s, fg, ac, x) + 40
    if zi.get("soldOut"):
        dr.rounded_rectangle((PAD, y + 4, W - PAD, y + 90), radius=24, fill="#ffffff18")
        dr.text((PAD + 28, y + 47), "Zimmermann på Løvenvold (søn) er utsolgt", font=F(32, 700), fill="#ffb3c1", anchor="lm")
    save(img, folder, "6-konserter.png")


def slide_kveld(folder):
    img, dr, fg, ac = slide(7, "natt")
    for i, t in enumerate(("For de voksne",)):
        dr.text((PAD - 4, 130), t, font=FR(104, 800, True), fill=fg)
    molja, lv = ev(FRI, "Jul på Molja"), ev(FRI, "Juleshow på Løvenvold")
    birk, zug = ev(FRI, "Birk Bream"), ev(SAT, "Good The Bad")
    liv, damp = ev(SAT, "DJ hver helg"), ev(SAT, "KLUBB DAMP")
    rows = [
        (FRI, tid(birk), "Birk Bream & Rumi Rafael", f"Venterommet i Terminalen. {pris(birk)}.", None),
        (FRI, tid(molja), "Jul på Molja", f"Juleshow med Fredrik Steen og Jorunn Torsheim. Fre og lør, {pris(molja)}. 15 år.", None),
        (FRI, tid(lv).split(" og ")[-1], "Juleshow på Løvenvold", f"Ørjan Liavåg, Are Kalvø og Marit Voldsæter. {pris(lv)}. Også lørdag.", "Mye er utsolgt: sjekk billett"),
        (SAT, tid(zug), "The Good The Bad and The Zugly", f"Terminalen Byscene. {pris(zug)}.", None),
        (SAT, tid(liv), "Dans: Liv & Røre og Klubb Damp", "DJ på Liv & Røre Moa og Klubb Damp på Dampsentralen.", None),
    ]
    y = 275
    for d, tm, t, s, x in rows:
        y = rad(img, dr, y, d, tm, t, s, fg, ac, x) + 30
    assert damp["time"] == "23:00"
    save(img, folder, "7-for-de-voksne.png")


def slide_snartborte(folder):
    img, dr, fg, ac = slide(8, "vin")
    for i, t in enumerate(("Ikke vent", "for lenge")):
        dr.text((PAD - 4, 130 + i * 118), t, font=FR(118, 800, True), fill=fg)
    sy, pe, zi = ev(SUN, "Adventskonsert"), ev(SUN, "Pepperkakeverksted"), ev(SUN, "Zimmermann")
    y = 420
    dr.text((PAD, y), "FÅ BILLETTER IGJEN", font=M(32, 800), fill=GOLD)
    y += 60
    for e, sub in ((sy, f"Søn {tid(sy)} · Ålesund kirke · {pris(sy)}"), (pe, f"Søn {tid(pe)} · Sunnmørsposten · gratis")):
        if not e.get("few"):
            continue
        dr.rounded_rectangle((PAD, y, W - PAD, y + 180), radius=34, fill="#ffffff22")
        dr.text((PAD + 36, y + 30), e["title"].split(" – ")[0].replace(" med Racoon", ""), font=B(52, 800), fill=fg)
        dr.text((PAD + 36, y + 106), sub, font=F(34, 600), fill="#ffd9de")
        y += 204
    y += 28
    dr.text((PAD, y), "UTSOLGT", font=M(32, 800), fill="#ff8aa0")
    y += 60
    if zi.get("soldOut"):
        dr.rounded_rectangle((PAD, y, W - PAD, y + 180), radius=34, fill="#ffffff12")
        dr.text((PAD + 36, y + 30), "Zimmermann – julekonsert", font=B(52, 800), fill="#ffffff90")
        dr.text((PAD + 36, y + 106), "Søn 18:00 og 20:30 · Løvenvold Theater", font=F(34, 600), fill="#ffd9de90")
        dr.line((PAD + 30, y + 58, PAD + 30 + 620, y + 58), fill="#ff8aa0", width=5)
        y += 204
    dr.text((PAD, y + 10), "Sjekk billettstatus på kaskjerda.no", font=F(36, 700), fill=CREAM)
    save(img, folder, "8-snart-utsolgt.png")


def slide_slutt(folder):
    img, dr, fg, ac = slide(9, "natt", kicker="1. ADVENT · 27.–29. NOV", last=True, flakes=False)
    glow(img, (W // 2, 400), 360, "#ffb347", 60)
    skyline(img, 1190, 11, amp=0.5, ground=40)
    wreath(img, W // 2, 480, 250, 66, lit=1, phase=2.0, candle_h=150)
    img.alpha_composite(snow_layer(W, H, 12, 120))
    dr = Dr(img)
    dr.text((W // 2, 590), "Lagre og send til", font=FR(96, 800, True), fill=CREAM, anchor="ma")
    dr.text((W // 2, 700), "dem du skal gå med", font=FR(96, 800, True), fill=CREAM, anchor="ma")
    dr.text((W // 2, 835), "Alle tider og priser: kaskjerda.no", font=B(46, 800), fill=GOLD, anchor="ma")
    dr.text((W // 2, 902), "Følg for hver helg i Ålesund", font=F(34, 600), fill="#d9d4ee", anchor="ma")
    save(img, folder, "9-lagre.png")


def carousel(folder):
    cover(folder)
    slide_lordag(folder)
    slide_sondag(folder)
    slide_lys(folder)
    slide_barn(folder)
    slide_konserter(folder)
    slide_kveld(folder)
    slide_snartborte(folder)
    slide_slutt(folder)


# ───────────── Reel ─────────────

FPS = 30
CLR = [("#2a0d3d", "#6a2155"), ("#0b2b24", "#1c5a3f"), ("#33091a", "#8a1d3a"), ("#101a3a", "#1e3f6e"), ("#3a1a05", "#a14a12"), ("#0a1238", "#231a5c"), ("#2a0d3d", "#6a2155")]


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def back(t):
    t = max(0.0, min(1.0, t))
    c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def glyph(img, kind, cx, cy, s, t):
    """Enkle tegnede symboler (s = størrelse)."""
    d = Dr(img)
    if kind == "fyrverkeri":
        rnd = random.Random(3)
        for k, (ox, oy, col) in enumerate(((0, 0, "#ffd35c"), (-0.9, 0.5, "#ff6f91"), (0.9, 0.45, "#6cd6ff"))):
            p = ease((t * 1.6 - k * 0.25))
            if p <= 0:
                continue
            for i in range(18):
                a = i / 18 * 2 * math.pi
                r1, r2 = s * 0.25 * p, s * (0.25 + 0.4 * p) * 0.9
                x1, y1 = cx + ox * s * 0.5 + r1 * math.cos(a), cy + oy * s * 0.5 + r1 * math.sin(a)
                x2, y2 = cx + ox * s * 0.5 + r2 * math.cos(a), cy + oy * s * 0.5 + r2 * math.sin(a)
                d.line((x1, y1, x2, y2), fill=col, width=8)
                d.ellipse((x2 - 7, y2 - 7, x2 + 7, y2 + 7), fill=col)
    elif kind == "pepperkake":
        col = "#c97a3c"
        d.ellipse((cx - s * .2, cy - s * .55, cx + s * .2, cy - s * .15), fill=col)
        d.rounded_rectangle((cx - s * .22, cy - s * .2, cx + s * .22, cy + s * .25), radius=40, fill=col)
        for sx in (-1, 1):
            d.line((cx + sx * s * .18, cy - s * .1, cx + sx * s * .48, cy - s * .3 - 20 * math.sin(t * 8)), fill=col, width=int(s * .16))
            d.line((cx + sx * s * .1, cy + s * .2, cx + sx * s * .3, cy + s * .6), fill=col, width=int(s * .17))
            d.ellipse((cx + sx * s * .48 - 13, cy - s * .3 - 20 * math.sin(t * 8) - 13, cx + sx * s * .48 + 13, cy - s * .3 - 20 * math.sin(t * 8) + 13), fill=col)
        for ex in (-1, 1):
            d.ellipse((cx + ex * s * .08 - 8, cy - s * .4 - 8, cx + ex * s * .08 + 8, cy - s * .4 + 8), fill="#fff4dc")
        d.arc((cx - s * .1, cy - s * .38, cx + s * .1, cy - s * .24), 20, 160, fill="#fff4dc", width=6)
        for k in range(3):
            d.ellipse((cx - 10, cy - s * .1 + k * s * .12 - 10, cx + 10, cy - s * .1 + k * s * .12 + 10), fill="#e3344f")
    elif kind == "nisse":
        d.polygon([(cx - s * .3, cy + s * .05), (cx + s * .3, cy + s * .05), (cx + s * .08 + 25 * math.sin(t * 6), cy - s * .6)], fill="#d62d4a")
        d.rounded_rectangle((cx - s * .36, cy + s * .02, cx + s * .36, cy + s * .16), radius=24, fill="#fff4dc")
        d.ellipse((cx + s * .08 + 25 * math.sin(t * 6) - 28, cy - s * .6 - 28, cx + s * .08 + 25 * math.sin(t * 6) + 28, cy - s * .6 + 28), fill="#fff4dc")
        d.ellipse((cx - s * .28, cy + s * .14, cx + s * .28, cy + s * .56), fill="#ffd9bf")
        d.pieslice((cx - s * .3, cy + s * .3, cx + s * .3, cy + s * .85), 0, 180, fill="#f4f4f4")
        d.ellipse((cx - 8, cy + s * .26 - 8, cx + 8, cy + s * .26 + 8), fill="#e0907a")
    elif kind == "kino":
        d.rounded_rectangle((cx - s * .55, cy - s * .35, cx + s * .55, cy + s * .35), radius=30, fill="#0a1238", outline="#9cc6ff", width=10)
        d.polygon([(cx - s * .12, cy - s * .18), (cx - s * .12, cy + s * .18), (cx + s * .2, cy)], fill="#ffd98a")
        for i in range(8):
            x = cx - s * .5 + i * s * .143
            d.rectangle((x, cy + s * .44, x + s * .07, cy + s * .5), fill="#9cc6ff")
    elif kind == "gardin":
        for sx in (-1, 1):
            op = 0.25 + 0.2 * ease(t * 2)
            pts = [(cx + sx * s * .6, cy - s * .5), (cx + sx * s * (.05 + (1 - ease(t * 2)) * .0), cy - s * .5), (cx + sx * s * (.18 + op * .0), cy + s * .5), (cx + sx * s * .6, cy + s * .5)]
            d.polygon(pts, fill="#c8243e")
            for k in range(1, 4):
                d.line((cx + sx * (s * .6 - k * s * .13), cy - s * .5, cx + sx * (s * .6 - k * s * .09), cy + s * .5), fill="#8c1327", width=6)
        d.rectangle((cx - s * .6, cy - s * .55, cx + s * .6, cy - s * .48), fill="#ffd98a")
        star5(d, cx, cy + s * .05, s * .22 * (0.9 + 0.1 * math.sin(t * 9)), "#ffd98a")
    elif kind == "noter":
        for k, ox in enumerate((-0.3, 0.3)):
            bob = 14 * math.sin(t * 7 + k * 2)
            x, y = cx + ox * s, cy + s * .3 + bob
            d.ellipse((x - 42, y - 30, x + 42, y + 30), fill="#ffd98a")
            d.rectangle((x + 30, y - s * .7, x + 42, y), fill="#ffd98a")
        d.polygon([(cx - 0.3 * s + 30, cy - s * .4), (cx + 0.3 * s + 42, cy - s * .4 - 34), (cx + 0.3 * s + 42, cy - s * .4 + 22), (cx - 0.3 * s + 30, cy - s * .4 + 56)], fill="#ffd98a")


SCALE = {"fyrverkeri": 0.62, "nisse": 0.72, "pepperkake": 0.8, "noter": 0.9}


def build_scenes():
    lys, putti = ev(SAT, "Lysparken"), ev(SAT, "Putti Plutti")
    peppe, gard = ev(SUN, "Pepperkakeverksted"), ev(SUN, "Jul på gården")
    f1 = film("Julenissens verksted")
    sy = ev(SUN, "Adventskonsert")
    return [
        (1.9, 0, "fyrverkeri", f"LØR {tid(lys)}", ["Lysparken", "tennes"], "Fyrverkeri 17:45 · Spjelkavika", "GRATIS"),
        (1.9, 1, "gardin", "FRE–SØN", ["Putti", "Plutti Pott"], "Barneforestilling i Parken", pris(putti)),
        (1.9, 2, "nisse", f"SØN {tid(gard)}", ["Nissebesøk", "på gården"], "Borgund Dyreklubb", pris(gard)),
        (1.9, 4, "pepperkake", f"SØN {tid(peppe)}", ["Pepperkake-", "verksted"], "Hos Sunnmørsposten · få plasser igjen" if peppe.get("few") else "Hos Sunnmørsposten", "GRATIS"),
        (1.9, 3, "kino", f"LØR + SØN {film_tider(f1, SAT)[0]}", ["Kino for", "de minste"], "Julenissens verksted · ODEON", None),
        (1.9, 5, "noter", f"SØN {tid(sy)}", ["Adventskonsert", "med barnekor"], "Ålesund kirke · barn gratis", None),
    ]


def reel_frames(folder, with_audio):
    scenes = build_scenes()
    intro, outro = 2.6, 3.0
    total = intro + sum(s[0] for s in scenes) + outro
    n = int(total * FPS)
    bgs = [grad(W, RH, a, b, 0.2).convert("RGBA") for a, b in CLR]
    flakes = [snow_layer(W, RH, 21, 120, 7), snow_layer(W, RH, 22, 70, 9)]
    sky = grad(W, RH, "#0a1238", "#231a5c", 0.2).convert("RGBA")
    stars(sky, 5, 110, 800)
    city = Image.new("RGBA", (W, RH), (0, 0, 0, 0))
    skyline(city, 1480, 4, amp=1.0, ground=100)
    ImageDraw.Draw(city).rectangle((0, 1581, W, RH), fill="#0a1238")
    low = Image.new("RGBA", (W, RH), (0, 0, 0, 0))
    skyline(low, 1800, 8, body="#05101a", amp=0.55, ground=120)
    cover_img = None

    def base_bg(idx):
        return bgs[idx].copy()

    def add_snow(img, t):
        for k, lay in enumerate(flakes):
            sp = (90 + 60 * k) * t
            off = int(sp) % RH
            img.alpha_composite(lay, (int(8 * math.sin(t * 1.3 + k)), off - RH))
            img.alpha_composite(lay, (int(8 * math.sin(t * 1.3 + k)), off))

    def intro_frame(t):
        img = sky.copy()
        img.alpha_composite(city)
        glow(img, (W // 2, 1160), 520, "#ffb347", 50)
        wreath(img, W // 2, 1300, 330, 88, lit=1, phase=t * 6, candle_h=190)
        add_snow(img, t)
        dr = Dr(img)
        p1, p2, p3 = (ease(t / 0.5), back((t - 0.15) / 0.55), back((t - 0.4) / 0.55))
        dr.text((W // 2, 330), "27.–29. NOVEMBER", font=M(36, 800), fill=(255, 217, 138, int(255 * p1)), anchor="ma")
        for i, tx in enumerate(("Første advent", "i Ålesund")):
            pp = (p2, p3)[i]
            dr.text((W // 2, 420 + i * 170 + (1 - pp) * 80), tx, font=FR(150, 800, True), fill=(255, 244, 220, int(255 * min(1, pp))), anchor="ma")
        dr.text((W // 2, 830), "Jul, barn og lys fra fredag til søndag", font=F(44, 650), fill=(255, 244, 220, int(255 * ease((t - 0.7) / 0.4))), anchor="ma")
        return img

    def scene_frame(i, t):
        dur, bi, kind, chip, title, sub, badge = scenes[i]
        img = base_bg(bi)
        img.alpha_composite(low)
        add_snow(img, t + i * 3)
        dr = Dr(img)
        # symbol
        ps = back(t / 0.45)
        glyph(img, kind, W // 2, 540, 520 * SCALE.get(kind, 1) * max(0.01, ps), t)
        dr = Dr(img)
        # chip
        a = ease((t - 0.05) / 0.25)
        dr.text((W // 2, 880), chip, font=M(58, 800), fill=(255, 217, 138, int(255 * a)), anchor="ma")
        for k, tx in enumerate(title):
            pp = back((t - 0.12 - k * 0.1) / 0.4)
            dr.text((W // 2, 970 + k * 150 + (1 - pp) * 90), tx, font=FR(138 if len(tx) < 12 else 112, 800, True), fill=(255, 244, 220, int(255 * min(1, pp))), anchor="ma")
        dr.text((W // 2, 1300), sub, font=F(44, 700), fill=(255, 244, 220, int(255 * ease((t - 0.35) / 0.3))), anchor="ma")
        if badge:
            pp = back((t - 0.3) / 0.4)
            f = B(60, 800)
            w = dr.textlength(badge, font=f) + 80
            lay = Image.new("RGBA", (int(w), 120), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle((0, 0, w - 1, 119), radius=60, fill=GOLD)
            ld.text((w / 2, 62), badge, font=f, fill="#2a0d3d", anchor="mm")
            lay = lay.rotate(-6, expand=True, resample=Image.BICUBIC)
            lay = lay.resize((max(1, int(lay.width * max(0.01, pp))), max(1, int(lay.height * max(0.01, pp)))))
            img.alpha_composite(lay, (W - 120 - lay.width, 330 - lay.height // 2))
        return img

    def outro_frame(t):
        img = sky.copy()
        img.alpha_composite(city)
        glow(img, (W // 2, 1160), 520, "#ffb347", 50)
        wreath(img, W // 2, 1300, 330, 88, lit=1, phase=t * 6, candle_h=190)
        add_snow(img, t + 40)
        dr = Dr(img)
        for k, (tx, f, y) in enumerate((("Alt som skjer i helga", FR(84, 800, True), 380), ("kaskjerda.no", B(120, 800), 520), ("Lagre og send til dem du skal gå med", F(42, 700), 690))):
            pp = ease((t - k * 0.25) / 0.45)
            dr.text((W // 2, y + (1 - pp) * 50), tx, font=f, fill=((255, 217, 138, int(255 * pp)) if k == 1 else (255, 244, 220, int(255 * pp))), anchor="ma")
        return img

    path = folder / ("reel-adventshelg.mp4" if with_audio else "reel-adventshelg-stille.mp4")
    tmp = folder / "_video.mp4"
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{RH}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", str(tmp)], stdin=subprocess.PIPE)
    bounds = [0.0, intro]
    for s in scenes:
        bounds.append(bounds[-1] + s[0])
    bounds.append(bounds[-1] + outro)
    prev_last = None
    for f in range(n):
        T = f / FPS
        seg = max(i for i in range(len(bounds) - 1) if T >= bounds[i]) if T < bounds[-1] else len(bounds) - 2
        lt = T - bounds[seg]
        if seg == 0:
            img = intro_frame(lt)
        elif seg <= len(scenes):
            img = scene_frame(seg - 1, lt)
            if lt < 0.3 and prev_last is not None:  # ny scene sklir inn nedenfra
                p = ease(lt / 0.3)
                base = prev_last.copy()
                base.alpha_composite(img, (0, int((1 - p) * RH)))
                img = base
        else:
            img = outro_frame(lt)
            if lt < 0.3 and prev_last is not None:
                p = ease(lt / 0.3)
                base = prev_last.copy()
                base.alpha_composite(img, (0, int((1 - p) * RH)))
                img = base
        if f == int(0.9 * FPS) and with_audio:
            img.convert("RGB").save(folder / "reel-forside.png")
        proc.stdin.write(img.convert("RGB").tobytes())
        # sist ferdige bilde i hver scene, til overgangen
        nxt = (f + 1) / FPS
        if nxt >= bounds[seg + 1] if seg + 1 < len(bounds) else False:
            prev_last = img.copy()
    proc.stdin.close()
    proc.wait()
    if with_audio:
        wav = folder / "_lyd.wav"
        jingle(wav, total)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-i", str(wav), "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(path)], check=True)
        wav.unlink()
        tmp.unlink()
    else:
        tmp.rename(path)


def jingle(path, total, sr=44100):
    """Rolig bjelle-melodi (egenlaget, pentaton C-dur) med slede-bjeller. Ingen opphavsrett å ta hensyn til."""
    n = int(total * sr)
    out = np.zeros(n)
    bpm = 100
    beat = 60 / bpm
    notes = {"C": 523.25, "D": 587.33, "E": 659.25, "G": 783.99, "A": 880.0, "c": 1046.5, "g": 392.0, "e": 329.63, "a": 440.0}
    melody = "E G c G E G A G | E G c A G E D C | D E G E D C D E | G A c A G E G g".replace("|", "").split()
    rnd = np.random.RandomState(1)

    def bell(freq, start, length=1.6, amp=0.22):
        i0 = int(start * sr)
        if i0 >= n:
            return
        t = np.arange(int(length * sr)) / sr
        env = np.exp(-t * 3.2) * (1 - np.exp(-t * 400))
        w = (np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 5) + 0.25 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t * 9)) * env * amp
        j = min(n, i0 + len(w))
        out[i0:j] += w[:j - i0]

    t = 0.25
    k = 0
    while t < total - 1.2:
        bell(notes[melody[k % len(melody)]], t)
        if k % 4 == 0:
            bell(notes["g" if (k // 4) % 2 == 0 else "e"] / 1.0, t, 2.2, 0.20)
        t += beat * 0.5
        k += 1
    # slede-bjeller
    t = 0.0
    while t < total - 0.5:
        i0 = int(t * sr)
        ln = int(0.09 * sr)
        nz = rnd.randn(ln) * np.exp(-np.arange(ln) / (0.02 * sr)) * 0.05
        nz = nz - np.convolve(nz, np.ones(24) / 24, "same")  # grov høypass
        out[i0:i0 + ln] += nz[:max(0, min(ln, n - i0))]
        t += beat * 0.5
    fade = np.minimum(1, np.minimum(np.arange(n) / sr / 0.4, (n - np.arange(n)) / sr / 1.5))
    out = out * fade
    out = out / max(0.01, np.abs(out).max()) * 0.85
    pcm = (out * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    folder = Path(args[0] if args else "adventshelg")
    folder.mkdir(parents=True, exist_ok=True)
    only = [a for a in sys.argv[1:] if a.startswith("--")]
    if not only or "--bilder" in only:
        carousel(folder)
    if not only or "--reel" in only:
        reel_frames(folder, True)
        reel_frames(folder, False)


if __name__ == "__main__":
    main()
