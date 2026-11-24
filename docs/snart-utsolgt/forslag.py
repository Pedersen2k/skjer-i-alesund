"""«Allerede utsolgt – ikke vent på resten»: innlegg 1080 × 1350 om julekonsertene (forslag 24. nov 2026).

Parken merker nesten alt «få billetter igjen», så som på nettsiden stoles det på Parkens merke bare 14 dager
før konserten. I dag er det derfor bare to pålitelige «få igjen» (Erlend Gunstveit i kveld, symfoniorkesteret
søndag), mens tre julekonserter allerede er utsolgt. Innlegget bruker de utsolgte som grunn til å kjøpe nå.

Kjør (med JUL_FRA=2026-11-24 og FONT_DIR satt): python3 docs/snart-utsolgt/forslag.py docs/snart-utsolgt
"""
import datetime
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "julekonsert-instagram"))
import forslag as f
from forslag import B, F, M, FR, W, fit, wrap, short, tm, price, d_of, grad, snow, star, brand, pages, Image, ImageDraw, ImageFilter

H = 1350
TODAY = f.FROM


def sold_out():
    """Utsolgte julekonserter fra i dag (også de som er merket utsolgt for hånd i manual.json)."""
    events = json.loads((pages.ROOT / "data" / "events.json").read_text())["events"]
    out = []
    for e in events:
        sold = e.get("soldOut") or f.MANUAL.get(e["id"], {}).get("soldOut")
        if sold and e["cat"] == "konsert" and pages.is_jul(e, f.CFG) and TODAY <= d_of(e) <= f.TO:
            out.append(e)
    return sorted(out, key=lambda e: e["date"])


SOLD = sold_out()
# Fortsatt billetter: de pålitelige «få igjen» først, så et utvalg av de store konsertene (redaksjonelt valg)
PICKS = ["Ålesund symfoniorkester", "SKRUK", "Emil Solli-Tangen", "Christel Alsos", "Bugge Wesseltoft"]


def picks(n=5):
    by = {short(e): e for e in f.EV}
    out = [by[p] for p in PICKS if p in by]
    return out[:n]


def tonight():
    return [e for e in f.EV if e.get("few") and d_of(e) == TODAY]


def wd(d):
    return f"{pages.WD[d.weekday()][:3]} {d.day}.{d.month:02d}"


def few_pill(dr, x, y, bg, fg, text="få igjen", size=26):
    tw = dr.textlength(text, font=F(size, 800))
    dr.rounded_rectangle((x, y, x + tw + 32, y + size + 18), radius=(size + 18) // 2, fill=bg)
    dr.text((x + 16, y + (size + 18) // 2), text, font=F(size, 800), fill=fg, anchor="lm")
    return tw + 32


# ───────────── A For seint / ikke for seint ─────────────

def var_a():
    img = Image.new("RGB", (W, H), "#fbf3e4")
    top = grad(W, 560, [(0, "#1d0f2e"), (1, "#3a0a1a")], 0.3)
    img.paste(top, (0, 0))
    snow(img, 4, 50)
    dr = ImageDraw.Draw(img)
    dr.text((72, 70), "JULEKONSERTENE I ÅLESUND", font=M(28), fill="#f2c46b")
    dr.text((66, 112), "For seint", font=FR(110, 750, True), fill="#ffffff")
    y = 270
    for e in SOLD:
        name = short(e)
        fnt = B(54, 800)
        dr.text((72, y), name, font=fnt, fill="#b9a7b4")
        tw = dr.textlength(name, font=fnt)
        dr.line((66, y + 34, 78 + tw, y + 30), fill="#e3344f", width=7)
        dr.text((W - 72, y + 30), "UTSOLGT", font=M(30, 800), fill="#e3344f", anchor="rm")
        y += 82
    # nedre halvdel
    dr.text((66, 600), "Ikke for seint ennå", font=FR(84, 750, True), fill="#2a0610")
    y = 720
    rows = tonight() + picks(5 - len(tonight()))
    for e in rows:
        d = d_of(e)
        dr.text((72, y + 6), "I KVELD" if d == TODAY else wd(d).upper(), font=M(28, 800), fill="#b3122e")
        x = 300
        name = fit(dr, short(e), B(46, 800), W - x - 70)
        dr.text((x, y - 4), name, font=B(46, 800), fill="#2a0610")
        meta = " · ".join(p for p in (tm(e), e["venue"], price(e)) if p)
        dr.text((x, y + 50), fit(dr, meta, F(28, 600), W - x - 230), font=F(28, 600), fill="#6b4a3a")
        if e.get("few"):
            few_pill(dr, x + dr.textlength(fit(dr, meta, F(28, 600), W - x - 230), font=F(28, 600)) + 16, y + 48, "#e3344f", "#ffffff", size=22)
        y += 106
    brand(img, dr, 72, H - 100, "#2a0610", 52)
    dr.text((W - 72, H - 74), "Alle julekonsertene →", font=B(36, 800), fill="#b3122e", anchor="rm")
    return img


# ───────────── B Avgangstavla ─────────────

def var_b():
    img = Image.new("RGB", (W, H), "#0b0b0c")
    dr = ImageDraw.Draw(img)
    amber, dim = "#ffb21e", "#5a4310"
    dr.text((60, 80), "AVGANGER · JULEKONSERTER", font=M(56, 800), fill=amber)
    dr.text((60, 160), "Noen har allerede gått. Rekk resten.", font=F(36, 600), fill="#e8e2d0")
    for x, h in ((60, "DATO"), (230, "KONSERT"), (790, "STATUS")):
        dr.text((x, 250), h, font=M(24), fill=dim)
    dr.line((60, 290, W - 60, 290), fill=dim, width=2)
    rows = sorted([(e, "sold") for e in SOLD] + [(e, "few" if e.get("few") else "ok") for e in tonight() + picks(4)],
                  key=lambda r: (r[0]["date"], tm(r[0])))
    y = 310
    for e, st in rows:
        col = "#6e6655" if st == "sold" else amber
        dr.rectangle((50, y, W - 50, y + 104), fill="#151516")
        dr.text((60, y + 18), f"{d_of(e).day:02d}.{d_of(e).month:02d}", font=M(36, 800), fill=col)
        dr.text((230, y + 14), fit(dr, short(e).upper(), M(32, 800), 540), font=M(32, 800), fill=col)
        dr.text((230, y + 60), fit(dr, f"{tm(e)} {e['venue']}", M(22, 600), 540), font=M(22, 600), fill="#8a7440" if st != "sold" else "#4d473c")
        lab, bg, fg = {"sold": ("UTSOLGT", "#3a1218", "#e3344f"), "few": ("FÅ IGJEN", "#e3344f", "#ffffff"),
                       "ok": ("BILLETTER", "#1c3a26", "#6cd98f")}[st]
        if st == "few" and d_of(e) == TODAY:
            lab = "I KVELD"
        dr.rounded_rectangle((790, y + 22, 1020, y + 80), radius=8, fill=bg)
        dr.text((905, y + 51), lab, font=M(28, 800), fill=fg, anchor="mm")
        y += 116
    brand(img, dr, 60, H - 96, "#e8e2d0", 52)
    dr.text((W - 60, H - 70), "kaskjerda.no/julekonserter", font=M(24), fill=dim, anchor="rm")
    return img


# ───────────── C Ønskelista ─────────────

def var_c():
    img = Image.new("RGB", (W, H), "#2f5d46")
    snow(img, 8, 90)
    dr = ImageDraw.Draw(img)
    # Papir, litt skrått
    paper = Image.new("RGBA", (900, 1180), (0, 0, 0, 0))
    pd = ImageDraw.Draw(paper)
    pd.rectangle((0, 0, 900, 1180), fill="#fffaf0")
    for yy in range(250, 1150, 78):
        pd.line((40, yy, 860, yy), fill="#cfe0ef", width=2)
    pd.line((110, 0, 110, 1180), fill="#f2a3ab", width=3)
    for k in range(6):
        pd.ellipse((36, 120 + k * 180, 66, 150 + k * 180), fill="#2f5d46")
    red, ink = "#c0182f", "#24324a"
    pd.text((140, 70), "Ønskeliste", font=FR(100, 700, True), fill=red)
    pd.text((146, 185), "julekonserter, før de er borte", font=FR(40, 500, True), fill=ink)
    rows = [(e, True) for e in SOLD] + [(e, False) for e in tonight() + picks(4)]
    rows.sort(key=lambda r: r[0]["date"])
    yy = 262
    for e, gone in rows:
        pd.rectangle((140, yy + 12, 184, yy + 56), outline=ink, width=4)
        name = short(e)
        fnt = FR(46, 600, True)
        name = fit(pd, name, fnt, 600)
        pd.text((210, yy + 6), name, font=fnt, fill="#9a9aa6" if gone else ink)
        tw = pd.textlength(name, font=fnt)
        if gone:
            pd.line((150, yy + 22, 176, yy + 48), fill=red, width=5)
            pd.line((176, yy + 22, 150, yy + 48), fill=red, width=5)
            pd.line((204, yy + 38, 214 + tw, yy + 32), fill=red, width=5)
            if tw < 470:
                pd.text((228 + tw, yy + 14), "utsolgt!", font=FR(36, 700, True), fill=red)
        else:
            pd.text((228 + tw, yy + 18), f"{d_of(e).day}.{d_of(e).month}", font=FR(34, 500, True), fill="#6a7a90")
        yy += 78
    pd.text((140, yy + 30), "Resten: kaskjerda.no", font=FR(44, 700, True), fill=red)
    paper = paper.rotate(-2.5, resample=Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", paper.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 120), mask=paper.getchannel("A"))
    base = img.convert("RGBA")
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)), (110, 120))
    base.alpha_composite(paper, (80, 70))
    img = base.convert("RGB")
    return img


# ───────────── D Stemplene ─────────────

def stub(e, sold, w=440, h=270):
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), radius=22, fill="#fff4dc")
    for cy in (20 + h * 0.62,):
        d.ellipse((2, cy - 18, 38, cy + 18), fill=(0, 0, 0, 0))
        d.ellipse((2 + w, cy - 18, 38 + w, cy + 18), fill=(0, 0, 0, 0))
    for xx in range(50, 20 + w - 20, 22):
        d.line((xx, 20 + h * 0.62, xx + 10, 20 + h * 0.62), fill="#c9b48f", width=3)
    ink = "#2a0610"
    d.text((46, 44), "JULEKONSERT", font=M(20), fill="#b3122e")
    lines = wrap(d, short(e), FR(48, 800), w - 60)[:2]
    y = 74
    for ln in lines:
        d.text((44, y), ln, font=FR(48, 800), fill=ink)
        y += 52
    dd = d_of(e)
    d.text((46, 20 + h * 0.62 + 22), f"{wd(dd)} · {tm(e)}", font=B(34, 800), fill=ink)
    d.text((46, 20 + h * 0.62 + 66), fit(d, e["venue"], F(24, 650), w - 60), font=F(24, 650), fill="#6b4a3a")
    if sold:
        st = Image.new("RGBA", (380, 120), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        sd.rounded_rectangle((6, 6, 374, 114), radius=14, outline=(227, 52, 79, 235), width=8)
        sd.text((190, 60), "UTSOLGT", font=B(64, 800), fill=(227, 52, 79, 235), anchor="mm")
        st = st.rotate(16, resample=Image.BICUBIC, expand=True)
        im.alpha_composite(st, ((w + 40 - st.width) // 2 + 20, (h + 40 - st.height) // 2))
    return im


def var_d():
    img = grad(W, H, [(0, "#3a0a1a"), (0.6, "#1d0f2e"), (1, "#0d0a1e")], 0.2)
    snow(img, 12, 80)
    dr = ImageDraw.Draw(img)
    n = len(SOLD)
    words = {1: "Én", 2: "To", 3: "Tre", 4: "Fire", 5: "Fem"}.get(n, str(n))
    dr.text((72, 70), "JULEKONSERTENE I ÅLESUND", font=M(28), fill="#f2c46b")
    dr.text((66, 112), f"{words} er allerede borte.", font=FR(76, 750, True), fill="#ffffff")
    dr.text((66, 204), "Hvem blir den neste?", font=FR(76, 500, True), fill="#f2c46b")
    items = [(e, True) for e in SOLD[:3]] + [(e, False) for e in (tonight() + picks(3))[:3]]
    base = img.convert("RGBA")
    rnd = random.Random(2)
    for k, (e, sold) in enumerate(items):
        s = stub(e, sold)
        if sold:
            s.putalpha(s.getchannel("A").point(lambda a: int(a * 0.78)))
        s = s.rotate(rnd.uniform(-4, 4), resample=Image.BICUBIC, expand=True)
        x = 50 + (k % 2) * 500
        y = 290 + (k // 2) * 282
        base.alpha_composite(s, (x, y))
    img = base.convert("RGB")
    dr = ImageDraw.Draw(img)
    brand(img, dr, 72, H - 100, "#ffffff", 52)
    dr.text((W - 72, H - 74), "Sikre deg billett →", font=B(36, 800), fill="#f2c46b", anchor="rm")
    return img


if __name__ == "__main__":
    out = Path(sys.argv[1])
    print("utsolgt:", [short(e) for e in SOLD], "| i kveld:", [short(e) for e in tonight()], "| utvalg:", [short(e) for e in picks()])
    f.sheet([("A For seint", var_a()), ("B Avgangstavla", var_b()), ("C Ønskelista", var_c()), ("D Stemplene", var_d())],
            out / "forslag.png", scale=0.5)
