import sys, datetime, re, math, random
sys.path.insert(0, "/home/user/skjer-i-alesund/scripts")
import numpy as np
import pages, ukepost as u
from ukepost import B, F, M, PAD, W, block, fit, no_emoji, logo, wrap
from PIL import Image, ImageDraw, ImageFilter
H = 1920
OUT, day = sys.argv[1], datetime.date.fromisoformat(sys.argv[2])
events, films = u.load()
def tm(e):
    m = re.search(r"\d{1,2}:\d{2}", e.get("time") or ""); return m.group(0) if m else ""
ev = [e for e in pages.occurrences([e for e in events if u.ok(e)], day, day) if tm(e) >= "16:00" or not tm(e)]
ev.sort(key=tm)
tip = sorted(ev, key=lambda e: (u.CAT_RANK.get(e["cat"], 3), e.get("priceMin") is None, -(e.get("priceMin") or 0), tm(e)))[0]
rest = [e for e in ev if e is not tip]
WD = pages.WD[day.weekday()]
DATE = f"{WD.upper()} {day.day}. {pages.MO[day.month-1].upper()}"
LABEL = {"konsert": "KONSERT", "standup": "STANDUP", "show": "SHOW", "happening": "HAPPENING", "quiz": "QUIZ", "barn": "FOR BARN", "klubb": "KLUBB", "sport": "SPORT"}
def price(e):
    p = pages.price_text(e); return "pris hos arrangør" if p == "Pris hos arrangør" else p
def hexc(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def grad(stops, angle=0.0):
    """stops: [(pos, '#hex')]; diagonal gradient."""
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
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse((xy[0]-r, xy[1]-r, xy[0]+r, xy[1]+r), fill=hexc(color) + (alpha,))
    img.paste(Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(blur))).convert("RGB"))

def glow(img, draw_fn, color, radius=22, strength=2):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(lay), hexc(color) + (255,))
    g = lay.filter(ImageFilter.GaussianBlur(radius))
    base = img.convert("RGBA")
    for _ in range(strength): base = Image.alpha_composite(base, g)
    base = Image.alpha_composite(base, lay)
    img.paste(base.convert("RGB"))

def sticker(dr, y, col):
    w = 560; x = (W - w) // 2
    for i in range(x, x + w, 28):
        dr.line((i, y, min(i+14, x+w), y), fill=col, width=3); dr.line((i, y+110, min(i+14, x+w), y+110), fill=col, width=3)
    for j in range(y, y + 110, 28):
        dr.line((x, j, x, min(j+14, y+110)), fill=col, width=3); dr.line((x+w, j, x+w, min(j+14, y+110)), fill=col, width=3)
    dr.text((W//2, y+55), "lenkemerke her", font=F(30, 600), fill=col, anchor="mm")

def brand(img, dr, y, fg):
    im, mask = logo(64); img.paste(im, (PAD, y), mask)
    dr.text((PAD + 84, y + 32), "kaskjerda.no", font=B(34, 700), fill=fg, anchor="lm")

def more_text():
    n = len(rest)
    return f"+ {n} til i kveld" if n else "Hele programmet"

def arrow(dr, cx, y, col, w=8):
    dr.line((cx, y, cx, y + 60), fill=col, width=w)
    dr.line((cx - 26, y + 36, cx, y + 64), fill=col, width=w); dr.line((cx + 26, y + 36, cx, y + 64), fill=col, width=w)

def tip_block(dr, y, fg, sub, sizes=(150, 130, 112, 96, 84), lines=3):
    f, s, ls = block(dr, no_emoji(tip["title"]), B, sizes, W - 2*PAD, lines)
    for l in ls: dr.text((PAD - 6, y), l, font=f, fill=fg); y += round(s * 0.98)
    return y

# ---- E: Solnedgang ----
def E():
    img = grad([(0, "#2b0f5c"), (0.45, "#d6246e"), (0.8, "#ff8a3d"), (1, "#ffc94a")], angle=0.35)
    blob(img, (900, 420), 260, "#ff5fa2"); blob(img, (150, 1300), 300, "#ffb03b", alpha=160)
    dr = ImageDraw.Draw(img)
    dr.text((PAD, 250), DATE, font=M(34), fill="#ffe3f0")
    glow(img, lambda d, c: d.text((PAD - 8, 290), "I kveld", font=B(210), fill=c), "#ffffff", 26, 1)
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle((PAD, 560, PAD + 20 + dr.textlength(LABEL[tip["cat"]], font=M(32)) + 40, 620), radius=30, fill="#ffffff")
    dr.text((PAD + 30, 590), LABEL[tip["cat"]], font=M(32), fill="#c41d63", anchor="lm")
    y = tip_block(dr, 660, "#ffffff", None, (128, 112, 96, 84), 2)
    y += 20
    dr.text((PAD, y), f"kl. {tm(tip)}", font=M(76), fill="#2b0f5c"); y += 104
    dr.text((PAD, y), f"{tip['venue']} · {price(tip)}", font=F(46, 700), fill="#2b0f5c")
    # teaser
    t = more_text(); f = B(72, 800); tw = dr.textlength(t, font=f)
    dr.rounded_rectangle(((W - tw)//2 - 50, 1280, (W + tw)//2 + 50, 1400), radius=60, fill="#2b0f5c")
    dr.text((W//2, 1340), t, font=f, fill="#ffc94a", anchor="mm")
    arrow(dr, W//2, 1410, "#2b0f5c")
    sticker(dr, 1500, "#2b0f5c"); brand(img, dr, 1660, "#2b0f5c")
    return img

# ---- F: Neon ----
def Fv():
    img = grad([(0, "#07021a"), (0.6, "#190a3d"), (1, "#0b1f3a")])
    blob(img, (200, 300), 260, "#7a1fff", alpha=120); blob(img, (950, 1250), 300, "#00c2ff", alpha=90)
    dr = ImageDraw.Draw(img)
    r = random.Random(4)
    for _ in range(90):
        x, y, s = r.randrange(W), r.randrange(220, 1900), r.choice([2, 2, 3])
        dr.ellipse((x, y, x+s, y+s), fill=(200, 210, 255))
    dr.text((PAD, 250), DATE, font=M(34), fill="#7fe8ff")
    glow(img, lambda d, c: d.text((PAD - 8, 290), "I kveld", font=B(210, 700), fill=c), "#ff3fb4", 24, 3)
    dr = ImageDraw.Draw(img)
    f, s, ls = block(dr, no_emoji(tip["title"]), B, (104, 92, 80, 70), W - 2*PAD - 100, 2)
    bottom = 700 + len(ls) * s + 24 + 100 + 60 + 50
    glow(img, lambda d, c: d.rounded_rectangle((PAD, 590, W - PAD, bottom), radius=44, outline=c, width=6), "#3fe0ff", 20, 2)
    dr = ImageDraw.Draw(img)
    dr.text((PAD + 50, 640), "DAGENS TIPS · " + LABEL[tip["cat"]], font=M(32), fill="#7fe8ff")
    y = 700
    for l in ls: dr.text((PAD + 44, y), l, font=f, fill="#ffffff"); y += round(s)
    y += 24
    glow(img, lambda d, c: d.text((PAD + 50, y), f"kl. {tm(tip)}", font=M(72), fill=c), "#ffd23f", 14, 2)
    dr = ImageDraw.Draw(img)
    dr.text((PAD + 50, y + 100), fit(dr, f"{tip['venue']} · {price(tip)}", F(44, 600), W - 2*PAD - 100), font=F(44, 600), fill="#d9d4ff")
    t = more_text()
    glow(img, lambda d, c: d.text((W//2, 1330), t, font=B(76, 800), fill=c, anchor="mm"), "#ffd23f", 18, 2)
    dr = ImageDraw.Draw(img)
    arrow(dr, W//2, 1395, "#ffd23f")
    sticker(dr, 1500, "#7fe8ff"); brand(img, dr, 1660, "#ffffff")
    return img

# ---- G: Hemmelig liste ----
def G():
    img = grad([(0, "#00a6a6"), (0.55, "#2a6fdb"), (1, "#6a2bd9")], angle=-0.3)
    blob(img, (950, 280), 260, "#7dffcf", alpha=150)
    dr = ImageDraw.Draw(img)
    dr.text((PAD, 250), DATE, font=M(34), fill="#e6fff8")
    dr.text((PAD - 8, 290), "I kveld", font=B(190), fill="#ffffff")
    # tipskort
    dr.rounded_rectangle((PAD, 540, W - PAD, 980), radius=40, fill="#ffffff")
    dr.text((PAD + 44, 585), "KVELDENS TIPS", font=M(32), fill="#2a6fdb")
    f, s, ls = block(dr, no_emoji(tip["title"]), B, (88, 78, 68, 60), W - 2*PAD - 88, 2)
    y = 640
    for l in ls: dr.text((PAD + 40, y), l, font=f, fill="#0a171b"); y += round(s * 1.02)
    dr.text((PAD + 44, 980 - 130), f"kl. {tm(tip)}", font=M(52), fill="#d6246e")
    dr.text((PAD + 44, 980 - 66), fit(dr, f"{tip['venue']} · {price(tip)}", F(40, 600), W - 2*PAD - 88), font=F(40, 600), fill="#0a171b")
    # uskarpe rader
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    yy = 1020
    for e in rest[:3]:
        d.rounded_rectangle((PAD, yy, W - PAD, yy + 110), radius=30, fill=(255, 255, 255, 70))
        d.text((PAD + 40, yy + 55), tm(e), font=M(44), fill=(255, 255, 255, 255), anchor="lm")
        d.text((PAD + 200, yy + 55), fit(d, no_emoji(e["title"]), F(44, 700), W - 2*PAD - 240), font=F(44, 700), fill=(255, 255, 255, 255), anchor="lm")
        yy += 130
    img.paste(Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(9))).convert("RGB"))
    dr = ImageDraw.Draw(img)
    if rest:
        t = more_text(); f = B(64, 800); tw = dr.textlength(t, font=f)
        cy = 1020 + 65 * min(3, len(rest)) - 10
        dr.rounded_rectangle(((W - tw)//2 - 44, cy - 56, (W + tw)//2 + 44, cy + 56), radius=56, fill="#ffd23f")
        dr.text((W//2, cy), t, font=f, fill="#0a171b", anchor="mm")
    arrow(dr, W//2, 1410, "#ffffff")
    sticker(dr, 1500, "#ffffff"); brand(img, dr, 1660, "#ffffff")
    return img

# ---- H: Billett ----
def Hv():
    img = grad([(0, "#ffcf3f"), (1, "#ff7a3d")], angle=0.5)
    dr = ImageDraw.Draw(img)
    for i in range(-H, W + H, 90):
        dr.line((i, 0, i + H, H), fill=(255, 190, 70), width=26)
    dr.text((PAD, 250), DATE, font=M(34), fill="#3a1200")
    dr.text((PAD - 8, 290), "I kveld", font=B(190), fill="#3a1200")
    tw, th = 920, 760
    t = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    d.rounded_rectangle((0, 0, tw, th), radius=36, fill="#1b0f2e")
    for cx in (0, tw): d.ellipse((cx - 40, 520 - 40, cx + 40, 520 + 40), fill=(0, 0, 0, 0))
    for x in range(60, tw - 40, 36): d.line((x, 520, x + 18, 520), fill="#ffcf3f", width=4)
    d.text((56, 60), "BILLETT · " + LABEL[tip["cat"]], font=M(30), fill="#ffcf3f")
    f, s, ls = block(d, no_emoji(tip["title"]), B, (96, 84, 72, 62), tw - 112, 3)
    y = 120
    for l in ls: d.text((54, y), l, font=f, fill="#ffffff"); y += round(s * 1.02)
    d.text((56, 560), f"kl. {tm(tip)}", font=M(60), fill="#ff8ac0")
    d.text((56, 650), fit(d, f"{tip['venue']} · {price(tip)}", F(40, 600), tw - 112), font=F(40, 600), fill="#ffffff")
    sh = Image.new("RGBA", (tw + 120, th + 120), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((60, 80, tw + 60, th + 80), radius=36, fill=(80, 20, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(24))
    rot = lambda im: im.rotate(-4, resample=Image.BICUBIC, expand=True)
    base = img.convert("RGBA")
    s2, t2 = rot(sh), rot(t)
    base.alpha_composite(s2, ((W - s2.width)//2, 500)); base.alpha_composite(t2, ((W - t2.width)//2 + 0, 520))
    img = base.convert("RGB"); dr = ImageDraw.Draw(img)
    txt = more_text(); f = B(70, 800)
    dr.text((W//2, 1380), txt, font=f, fill="#3a1200", anchor="mm")
    arrow(dr, W//2, 1418, "#3a1200", 7)
    sticker(dr, 1500, "#3a1200"); brand(img, dr, 1660, "#3a1200")
    return img

for name, fn in [("E", E), ("F", Fv), ("G", G), ("H", Hv)]:
    fn().save(f"{OUT}/{name}-{day.isoformat()}.png")
print(day, "tips:", tip["title"], "| resten:", len(rest))
