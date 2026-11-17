import sys, datetime
sys.path.insert(0, "/home/user/skjer-i-alesund/scripts")
import pages, ukepost as u
from ukepost import B, F, M, PAD, W, INK, LIGHT, SOFT, GOLD, GREEN, MUTED, CARD, LINE, wrap, block, fit, no_emoji, logo
from PIL import Image, ImageDraw
H = 1920
OUT = sys.argv[1]
day = datetime.date.fromisoformat(sys.argv[2])
events, films = u.load()
import re
def tm(e):
    m = re.search(r"\d{1,2}:\d{2}", e.get("time") or "")
    return m.group(0) if m else ""
ev = sorted(pages.occurrences([e for e in events if u.ok(e)], day, day), key=tm)
head = f"{pages.WD[day.weekday()].upper()} {day.day}. {pages.MO[day.month-1].upper()}"
CC = {"konsert": "#5ab7bf", "standup": "#f7c873", "show": "#ec78ab", "happening": "#f08a4b", "quiz": "#9b8cf0", "barn": "#6cc98a", "klubb": "#ec78ab", "sport": "#6cc98a"}
LABEL = {"konsert": "Konsert", "standup": "Standup", "show": "Show", "happening": "Happening", "quiz": "Quiz", "barn": "Barn", "klubb": "Klubb", "sport": "Sport"}

def tm(e):
    m = re.search(r"\d{1,2}:\d{2}", e.get("time") or "")
    return m.group(0) if m else ""

def price(e):
    p = pages.price_text(e)
    return "pris hos arrangør" if p == "Pris hos arrangør" else p

def sticker(dr, y, dark=True, w=560):
    """Plass til Instagrams lenkemerke (bare markert i forslaget)."""
    x = (W - w) // 2
    col = "#8fa8ab" if dark else "#0a171b"
    for i in range(x, x + w, 28):
        dr.line((i, y, min(i + 14, x + w), y), fill=col, width=3); dr.line((i, y + 110, min(i + 14, x + w), y + 110), fill=col, width=3)
    for j in range(y, y + 110, 28):
        dr.line((x, j, x, min(j + 14, y + 110)), fill=col, width=3); dr.line((x + w, j, x + w, min(j + 14, y + 110)), fill=col, width=3)
    dr.text((W // 2, y + 55), "lenkemerke: kaskjerda.no/i-dag", font=F(30, 600), fill=col, anchor="mm")

def brand(img, dr, y, fg):
    im, mask = logo(64); img.paste(im, (PAD, y), mask)
    dr.text((PAD + 84, y + 32), "kaskjerda.no", font=B(34, 700), fill=fg, anchor="lm")

def night(h=H, top=(8, 20, 34), bot=(26, 40, 66)):
    img = Image.new("RGB", (W, h))
    dr = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        dr.line((0, y, W, y), fill=tuple(round(a + (b - a) * t) for a, b in zip(top, bot)))
    return img, dr

def stars(dr, n=70, seed=7, ymax=700):
    import random; r = random.Random(seed)
    for _ in range(n):
        x, y, s = r.randrange(W), r.randrange(240, ymax), r.choice([2, 2, 3, 4])
        dr.ellipse((x, y, x + s, y + s), fill=(232, 241, 239, r.randrange(90, 220)) if False else "#c9dad8")

# --- A: Kveldslista ---
def A():
    img, dr = night()
    stars(dr)
    dr.ellipse((W - PAD - 130, 250, W - PAD, 380), fill="#f7c873"); dr.ellipse((W - PAD - 100, 232, W - PAD + 20, 352), fill=(10, 22, 37))
    dr.text((PAD, 260), head, font=M(34), fill=GOLD)
    dr.text((PAD - 8, 300), "I kveld", font=B(200), fill=LIGHT)
    dr.text((PAD, 530), f"{len(ev)} ting å gjøre i Ålesund", font=F(44), fill=SOFT)
    y = 640
    for e in ev[:6]:
        dr.line((PAD, y, W - PAD, y), fill="#2d4560", width=2)
        dr.text((PAD, y + 40), tm(e), font=M(48), fill=GOLD)
        x = PAD + 190; inner = W - PAD - x
        f, s, lines = block(dr, no_emoji(e["title"]), B, (56, 50, 44) if len(ev) <= 3 else (48, 44), inner, 2 if len(ev) <= 3 else 1)
        for i, l in enumerate(lines): dr.text((x, y + 34 + i * round(s * 1.05)), l, font=f, fill=LIGHT)
        ty = y + 34 + len(lines) * round(s * 1.05) + 10
        p = price(e)
        dr.text((x, ty), fit(dr, f"{e['venue']} · ", F(36), inner - 260), font=F(36), fill=SOFT)
        dr.text((x + dr.textlength(fit(dr, f"{e['venue']} · ", F(36), inner - 260), font=F(36)), ty), p, font=F(36, 700), fill=GREEN if p == "Gratis" else SOFT)
        y = ty + (76 if len(ev) <= 3 else 64)
    dr.line((PAD, y, W - PAD, y), fill="#2d4560", width=2)
    sticker(dr, 1500)
    brand(img, dr, 1660, LIGHT)
    return img

# --- B: Plakat (kveldens tips stort, resten under) ---
def Bv():
    tip = sorted(ev, key=lambda e: (u.CAT_RANK.get(e["cat"], 3), e.get("priceMin") is None, tm(e)))[0]
    rest = [e for e in ev if e is not tip]
    col = CC.get(tip["cat"], GOLD)
    img = Image.new("RGB", (W, H), col); dr = ImageDraw.Draw(img)
    dr.text((PAD, 260), "I KVELD · " + head, font=M(34), fill=INK)
    dr.text((PAD, 320), LABEL.get(tip["cat"], "").upper(), font=M(34), fill=INK)
    f, s, lines = block(dr, no_emoji(tip["title"]), B, (170, 150, 130, 112, 96) if len(rest) < 3 else (130, 112, 96), W - 2 * PAD, 3)
    y = 400
    for l in lines: dr.text((PAD - 6, y), l, font=f, fill=INK); y += round(s * 1.0)
    y += 30
    dr.text((PAD, y), f"kl. {tm(tip)}", font=M(80), fill=INK); y += 110
    dr.text((PAD, y), f"{tip['venue']} · {price(tip)}", font=F(46, 700), fill=INK)
    # resten
    by = max(1000, y + 100)
    bh = 100 + 64 * len(rest[:4]) + 30
    dr.rounded_rectangle((PAD, by, W - PAD, by + bh), radius=36, fill=INK)
    dr.text((PAD + 48, by + 44), "OGSÅ I KVELD", font=M(30), fill=col)
    yy = by + 100
    for e in rest[:4]:
        dr.text((PAD + 48, yy), tm(e), font=M(38), fill=GOLD)
        dr.text((PAD + 200, yy - 2), fit(dr, no_emoji(e["title"]), F(40, 700), W - 2 * PAD - 250), font=F(40, 700), fill=LIGHT)
        yy += 64
    sticker(dr, 1500, dark=False)
    brand(img, dr, 1660, INK)
    return img

# --- C: Klokka (tidslinje) ---
def C():
    img = Image.new("RGB", (W, H), "#0a171b"); dr = ImageDraw.Draw(img)
    dr.text((PAD, 260), head, font=M(34), fill=MUTED)
    dr.text((PAD - 8, 300), "I kveld", font=B(170), fill=GOLD)
    dr.text((PAD, 500), "Klokke for klokke", font=F(44), fill=SOFT)
    lx = PAD + 20
    y0, y = 620, 620
    rows = []
    for e in ev[:5]:
        rows.append((y, e)); y += 230 if len(ev) <= 3 else 180
    dr.line((lx, y0 + 20, lx, rows[-1][0] + 20), fill=LINE, width=6)
    for y, e in rows:
        c = CC.get(e["cat"], GOLD)
        dr.ellipse((lx - 18, y + 2, lx + 18, y + 38), fill=c)
        dr.text((lx + 50, y), tm(e), font=M(44), fill=c)
        dr.text((lx + 210, y + 6), LABEL.get(e["cat"], "").upper(), font=M(28), fill=c)
        inner = W - PAD - lx - 50
        dr.text((lx + 50, y + 58), fit(dr, no_emoji(e["title"]), B(56, 750), inner), font=B(56, 750), fill=LIGHT)
        p = price(e)
        dr.text((lx + 50, y + 128), fit(dr, f"{e['venue']} · {p}", F(36), inner), font=F(36), fill=GREEN if p == "Gratis" else SOFT)
    sticker(dr, 1500)
    brand(img, dr, 1660, LIGHT)
    return img

# --- D: Kort (hvert arrangement som eget fargekort) ---
def D():
    img = Image.new("RGB", (W, H), "#e8f1ef"); dr = ImageDraw.Draw(img)
    dr.text((PAD, 260), head, font=M(34), fill=INK)
    dr.text((PAD - 8, 300), "I kveld", font=B(170), fill=INK)
    import math
    cx, cy = W - PAD - 60, 400
    dr.polygon([(cx + (60 if i % 2 == 0 else 25) * math.sin(i * math.pi / 5), cy - (60 if i % 2 == 0 else 25) * math.cos(i * math.pi / 5)) for i in range(10)], fill="#f08a4b")
    y = 540
    inner = W - 2 * PAD - 80
    many = len(ev) > 3
    for e in ev[:5]:
        c = CC.get(e["cat"], GOLD)
        f, s, lines = block(dr, no_emoji(e["title"]), B, (60, 54, 48) if not many else (52, 46), inner, 1 if many else 2)
        lh = round(s * 1.05)
        h = 34 + 50 + len(lines) * lh + 12 + 44 + 30
        dr.rounded_rectangle((PAD, y, W - PAD, y + h), radius=32, fill=c)
        dr.text((PAD + 40, y + 34), tm(e), font=M(40), fill=INK)
        dr.text((W - PAD - 40, y + 34), price(e), font=F(36, 800), fill=INK, anchor="ra")
        for i, l in enumerate(lines): dr.text((PAD + 40, y + 90 + i * lh), l, font=f, fill=INK)
        dr.text((PAD + 40, y + 90 + len(lines) * lh + 12), e["venue"], font=F(34, 600), fill=INK)
        y += h + 20
    sticker(dr, 1500, dark=False)
    brand(img, dr, 1660, INK)
    return img

for name, fn in [("A", A), ("B", Bv), ("C", C), ("D", D)]:
    fn().save(f"{OUT}/{name}-{day.isoformat()}.png")
