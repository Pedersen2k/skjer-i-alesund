"""Forslag: «Sveip for å tenne lysene» (1. søndag i advent 2026). Karusell 5 × (1080×1350) + historie (1080×1920).
Lyslenka går sømløst gjennom alle bildene og tennes pære for pære jo lenger man sveiper.
Kjør: python3 lag.py   (fra denne mappen; trenger scripts/ på stien)"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from PIL import Image, ImageDraw, ImageFilter
from ukepost import B, F, M, block, logo, W, H, PAD

N = 5
CW = W * N
BG = ((12, 16, 46), (38, 22, 70), (96, 40, 84))   # natt → skumring (topp, midt, bunn)
GOLD = (255, 207, 112)


def sky(w, h):
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / h
        a, b, k = (BG[0], BG[1], t / .6) if t < .6 else (BG[1], BG[2], (t - .6) / .4)
        d.line([(0, y), (w, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3)))
    import random
    r = random.Random(7)
    for _ in range(260):
        x, y = r.randrange(w), r.randrange(int(h * .55))
        s = r.choice((1, 1, 2)); c = r.randrange(150, 255)
        d.ellipse((x, y, x + s, y + s), fill=(c, c, 255))
    # byen (silhuett) nederst
    r = random.Random(3); x = 0
    while x < w:
        bw = r.randrange(40, 120); bh = r.randrange(50, 190)
        d.rectangle((x, h - bh, x + bw, h), fill=(14, 12, 34))
        if r.random() < .5:
            d.polygon([(x, h - bh), (x + bw, h - bh), (x + bw // 2, h - bh - r.randrange(25, 60))], fill=(14, 12, 34))
        for wy in range(h - bh + 14, h - 8, 26):
            for wx in range(x + 10, x + bw - 12, 22):
                if r.random() < .35: d.rectangle((wx, wy, wx + 7, wy + 11), fill=(255, 196, 96))
        x += bw + r.randrange(0, 14)
    return im


def lights(canvas):
    """Lyslenke i bue per bilde. Pærene tennes jevnt fra venstre mot høyre."""
    n = 56
    glow = Image.new("RGB", canvas.size, (0, 0, 0)); gd = ImageDraw.Draw(glow)
    d = ImageDraw.Draw(canvas)
    pts = []
    for i in range(n + 1):
        x = CW * i / n
        k = (x % W) / W
        y = 150 + 70 * math.sin(math.pi * k)
        pts.append((x, y))
    d.line(pts, fill=(30, 26, 40), width=4)
    for i, (x, y) in enumerate(pts):
        p = x / CW
        lit = min(1, max(0, (p - .02) / .62))              # 0 til 1 over de fem bildene
        on = (i * 37 % 100) / 100 < lit or p > .7          # tilfeldig rekkefølge, alle tent mot slutten
        y2 = y + 22
        col = [(255, 120, 90), GOLD, (140, 220, 255), (255, 170, 220)][i % 4] if on else (60, 56, 74)
        if on:
            gd.ellipse((x - 34, y2 - 34, x + 34, y2 + 34), fill=tuple(int(c * .8) for c in col))
        d.ellipse((x - 9, y2 - 9, x + 9, y2 + 12), fill=col)
        d.rectangle((x - 4, y2 - 16, x + 4, y2 - 8), fill=(30, 26, 40))
    g = glow.filter(ImageFilter.GaussianBlur(26))
    from PIL import ImageChops
    return ImageChops.screen(canvas, g)


def wreath(img, cx, cy, r, lit):
    d = ImageDraw.Draw(img)
    import random
    rr = random.Random(5)
    for i in range(190):
        a = rr.random() * math.tau; rad = r + rr.randrange(-22, 22)
        x, y = cx + rad * math.cos(a), cy + rad * .55 * math.sin(a)
        c = rr.choice(((24, 96, 56), (30, 120, 70), (18, 76, 46)))
        d.ellipse((x - 16, y - 12, x + 16, y + 12), fill=c)
    for i in range(4):
        a = math.radians(200 + i * 46 - 0)
        x = cx + r * math.cos(a) * .95; y = cy + r * .55 * math.sin(a)
        d.rectangle((x - 13, y - 70, x + 13, y), fill=(240, 232, 214))
        if i < lit:
            fl = Image.new("RGB", img.size, (0, 0, 0)); fd = ImageDraw.Draw(fl)
            fd.ellipse((x - 70, y - 150, x + 70, y - 10), fill=(180, 110, 30))
            from PIL import ImageChops
            img.paste(ImageChops.screen(img, fl.filter(ImageFilter.GaussianBlur(30))))
            d = ImageDraw.Draw(img)
            d.polygon([(x, y - 112), (x - 11, y - 82), (x, y - 70), (x + 11, y - 82)], fill=(255, 226, 140))
        else:
            d.line((x, y - 70, x, y - 80), fill=(60, 50, 50), width=3)


def lake(img, cx, cy, rx, ry):
    """Lysparken rundt Lillevatnet: ring av små lys."""
    from PIL import ImageChops
    gl = Image.new("RGB", img.size, (0, 0, 0)); gd = ImageDraw.Draw(gl); d = ImageDraw.Draw(img)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(18, 28, 70), outline=(40, 60, 120), width=3)
    for i in range(46):
        a = math.tau * i / 46
        for k, (s, o) in enumerate(((1.0, 0), (1.22, 1))):
            x, y = cx + rx * s * math.cos(a + o * .07), cy + ry * s * math.sin(a + o * .07)
            col = GOLD if (i + k) % 3 else (255, 140, 110)
            gd.ellipse((x - 26, y - 26, x + 26, y + 26), fill=tuple(int(c * .7) for c in col))
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=col)
            # speiling
    img.paste(ImageChops.screen(img, gl.filter(ImageFilter.GaussianBlur(18))))


def text(d, x, y, s, f, fill=(255, 255, 255), anchor="la"):
    d.text((x, y), s, font=f, fill=fill, anchor=anchor)


def dim(im, y0, y1, a=215):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rectangle((0, y0, im.width, y1), fill=(14, 12, 34, a))
    im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))


def slide_text(i, im):
    if i in (1, 2, 3): dim(im, 1130, H)
    d = ImageDraw.Draw(im)
    if i == 0:
        wreath(im, W // 2, 900, 300, 1); d = ImageDraw.Draw(im)
        text(d, PAD, 330, "SVEIP FOR Å", M(40), GOLD)
        text(d, PAD, 385, "TENNE LYSENE", B(120), (255, 255, 255))
        text(d, PAD, 520, "Første advent i Ålesund:", F(48), (230, 220, 255))
        text(d, PAD, 580, "tre steder lyser opp helga.", F(48), (230, 220, 255))
        text(d, W - PAD, 1230, "sveip  →", M(44), GOLD, "ra")
    elif i == 1:
        lake(im, W // 2, 930, 330, 170); d = ImageDraw.Draw(im)
        text(d, PAD, 300, "LØRDAG 28. NOV", M(40), GOLD)
        f, _, ls = block(d, "Lysparken tennes i Spjelkavik", B, (110, 100, 90), W - 2 * PAD, 3)
        y = 355
        for l in ls: text(d, PAD, y, l, f); y += int(f.size * 1.05)
        text(d, PAD, 1170, "17:00 julekonsert · 17:30 lysene tennes · 17:45 fyrverkeri", F(34), (230, 220, 255))
        text(d, PAD, 1230, "Lillevatnet · Gratis", M(40), GOLD)
    elif i == 2:
        d.polygon([(W // 2 - 150, 1120), (W // 2 + 150, 1120), (W // 2 + 150, 880), (W // 2, 700), (W // 2 - 150, 880)], fill=(14, 12, 34))
        d.rectangle((W // 2 - 20, 560, W // 2 + 20, 720), fill=(14, 12, 34))
        d.polygon([(W // 2 - 20, 560), (W // 2 + 20, 560), (W // 2, 480)], fill=(14, 12, 34))
        for x in (W // 2 - 70, W // 2 + 40):
            d.rectangle((x, 900, x + 30, 1000), fill=(255, 196, 96))
        text(d, PAD, 300, "SØNDAG 29. NOV · 1. ADVENT", M(40), GOLD)
        f, _, ls = block(d, "Ålesund symfoniorkester: Adventskonsert", B, (96, 88, 80), W - 2 * PAD, 3)
        y = 355
        for l in ls: text(d, PAD, y, l, f); y += int(f.size * 1.05)
        text(d, PAD, 1170, "Nøtteknekkeren, orgelsymfoni og allsang, barnekoret 123.klang", F(30), (230, 220, 255))
        text(d, PAD, 1230, "kl. 17 · Ålesund kirke · 105–280 kr", M(40), GOLD)
    elif i == 3:
        wreath(im, W // 2, 850, 300, 1); d = ImageDraw.Draw(im)
        text(d, PAD, 300, "OG HOS OSS", M(40), GOLD)
        text(d, PAD, 355, "Første lys på", B(100)); text(d, PAD, 465, "kaskjerda.no", B(100), GOLD)
        text(d, PAD, 1160, "Adventskransen på forsiden tennes søndag.", F(42), (230, 220, 255))
        text(d, PAD, 1225, "Ett lys per søndag, helt til jul. Gå inn og se.", F(42), (230, 220, 255))
    else:
        text(d, PAD, 330, "ALT SOM SKJER", M(40), GOLD)
        text(d, PAD, 385, "i desember", B(130)); text(d, PAD, 520, "finner du her", B(130))
        text(d, PAD, 700, "Lagre innlegget", F(60), GOLD); text(d, PAD, 780, "og send det til den du tenner lys med.", F(46))
        lg, mask = logo(150); im.paste(lg, (PAD, 1000), mask)
        text(d, PAD + 190, 1030, "kaskjerda.no", B(64)); text(d, PAD + 190, 1105, "lenke i bio", F(40), (230, 220, 255))
    if i < N - 1: text(d, W - PAD, 80, f"{i + 1}/{N}", M(34), (200, 200, 230), "ra")


def story():
    h = 1920
    im = sky(W, h).crop((0, 0, W, h)); d = ImageDraw.Draw(im)
    wreath(im, W // 2, 1000, 330, 1); d = ImageDraw.Draw(im)
    text(d, W // 2, 300, "1. ADVENT", M(56), GOLD, "ma")
    text(d, W // 2, 380, "Tre steder tenner", B(104), (255, 255, 255), "ma"); text(d, W // 2, 495, "lyset i helga", B(104), (255, 255, 255), "ma")
    for j, (a, b) in enumerate((("Lør 17:00", "Lysparken, Spjelkavik"), ("Søn 17:00", "Symfoniorkesteret, kirka"), ("Søndag", "Adventskransen på kaskjerda.no"))):
        y = 1380 + j * 120
        d.rounded_rectangle((PAD, y, W - PAD, y + 98), 49, fill=(255, 255, 255))
        text(d, PAD + 40, y + 49, a, B(40), (96, 40, 84), "lm"); text(d, PAD + 330, y + 49, b, F(36), (30, 20, 60), "lm")
    dim(im, 1760, h, 230); d = ImageDraw.Draw(im); text(d, W // 2, 1810, "↓ lenkemerke: kaskjerda.no/i-dag", M(40), GOLD, "ma")
    return im


if __name__ == "__main__":
    base = sky(CW, H)
    base = lights(base)
    for i in range(N):
        s = base.crop((i * W, 0, (i + 1) * W, H)); slide_text(i, s)
        s.save(f"advent-{i + 1}.png")
    story().save("advent-historie.png")
    print("ok")
