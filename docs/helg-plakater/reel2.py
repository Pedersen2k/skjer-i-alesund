"""Reel nr. 2: «Hva er du i humør til?» Kinetisk tekst, snurrende stråler, snø og natt-Ålesund (1080 x 1920, 17 s).
Samme musikk (lyd.py) som reel.py. Kjør: python3 docs/helg-plakater/reel2.py [ut.mp4] [YYYY-MM-DD]
"""
import datetime, json, math, random, subprocess, sys, tempfile
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import lag
import reel
from reel import cl, out_back, out_cubic, pulse, place, cached, FPS, BEAT
from lag import W, INK, CREAM, YEL, PINK, BLUE, GREEN, ORANGE, RED, F, shadow_text, burst, interesting, MONTHS, pages

H = 1920
CYAN = "#3be8ff"
DUR = [2] + [2] * 6 + [3]
START = [sum(DUR[:i]) for i in range(len(DUR))]
TOTAL = sum(DUR)
DAYAB = {4: "FRE", 5: "LØR", 6: "SØN"}

# (ord, bakgrunn topp, bakgrunn bunn, strålefarge, ordfarge, passer(e))
MOODS = [
    ("LE?", "#5b1fb8", "#ff4f8b", "#ffffff22", YEL, lambda e: e["cat"] == "standup"),
    ("DANSE?", "#0c0a2e", "#7a1fff", "#3be8ff33", CYAN, lambda e: e["cat"] == "klubb"),
    ("KOSE\nDEG?", "#0f8f66", "#19c98b", "#ffffff2a", YEL, lambda e: pages.price_text(e) == "Gratis" and e["cat"] == "happening"),
    ("JULE-\nSTEMNING?", "#7a0f1f", "#e0262f", "#ffd93b33", CREAM, lambda e: e["cat"] == "konsert" and "advent" in e["title"].lower()),
    ("MED\nBARNA?", "#ff7a1a", "#ffd93b", "#ffffff44", INK, lambda e: e["cat"] == "barn"),
    ("LIVE\nMUSIKK?", "#1a2fcc", "#3b6bff", "#ffffff22", YEL, lambda e: e["cat"] == "konsert" and "jul" not in e["title"].lower() and "advent" not in e["title"].lower()),
]


# ---------- bakgrunn ----------
def grad(c1, c2):
    def mk():
        a = Image.new("RGB", (W, H), c1)
        b = Image.new("RGB", (W, H), c2)
        return Image.composite(b, a, Image.linear_gradient("L").resize((W, H)))
    return cached(("g", c1, c2), mk)


def skyline_tile():
    def mk():
        im = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
        rnd = random.Random(9)
        d = ImageDraw.Draw(im)
        x = 0
        while x < W:
            w = rnd.choice([80, 100, 120, 150])
            h = rnd.choice([70, 110, 150, 190])
            top = 330 - h
            d.rectangle((x, top, x + w, 330), fill="#0b0918")
            k = rnd.choice(["gable", "tower", "flat", "gable"])
            if k == "gable":
                d.polygon([(x - 4, top), (x + w / 2, top - w * 0.45), (x + w + 4, top)], fill="#0b0918")
            elif k == "tower":
                d.rectangle((x + w * .38, top - 50, x + w * .62, top), fill="#0b0918")
                d.polygon([(x + w * .32, top - 50), (x + w / 2, top - 105), (x + w * .68, top - 50)], fill="#0b0918")
            for wy in range(top + 16, 330 - 12, 34):
                for wx in range(int(x + 12), int(x + w - 14), 28):
                    if rnd.random() < .5:
                        d.rectangle((wx, wy, wx + 11, wy + 17), fill=rnd.choice([YEL, YEL, "#ffb347", "#ffe9a0"]))
            x += w + 8
        return im
    return cached(("sky",), mk)


def snow(img, t, seed=1, n=90):
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for i in range(n):
        x0, y0, sp, r = rnd.random() * W, rnd.random() * H, 90 + rnd.random() * 160, 2 + rnd.random() * 6
        x = (x0 + 40 * math.sin(t * 1.5 + i)) % W
        y = (y0 + t * sp) % H
        d.ellipse((x - r, y - r, x + r, y + r), fill="#ffffffcc")


def rays(img, t, color, spin=14, n=16):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    cx, cy, R = W / 2, 900, 2300
    a0 = math.radians(t * spin)
    for i in range(n):
        a1 = a0 + 2 * math.pi * i / n
        a2 = a1 + math.pi / n
        d.polygon([(cx, cy), (cx + R * math.cos(a1), cy + R * math.sin(a1)), (cx + R * math.cos(a2), cy + R * math.sin(a2))], fill=color)
    img.alpha_composite(ov)


def backdrop(t, top, bot, ray, seed):
    img = grad(top, bot).convert("RGBA")
    if ray:
        rays(img, t, ray)
    sk = skyline_tile()
    off = int((t * 70) % W)
    for xx in (-off, W - off):
        img.alpha_composite(sk, (xx, H - 330)) if xx > -W else None
    snow(img, t, seed)
    return img


# ---------- kinetiske bokstaver ----------
def letter(ch, size, fill):
    def mk():
        f = F(size)
        adv = f.getlength(ch)
        im = Image.new("RGBA", (int(adv + size * .5), int(size * 1.5)), (0, 0, 0, 0))
        shadow_text(ImageDraw.Draw(im), (im.width / 2, im.height / 2), ch, f, fill, off=max(6, size // 26), outline=max(5, size // 34), anchor="mm")
        return im
    return cached(("l", ch, size, fill), mk)


def word(img, text, t, t0, fill, cx, cy, scale=1.0, maxsize=380, stagger=0.04):
    if t < t0:
        return
    lines = text.split("\n")
    d = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    size = maxsize
    while size > 60 and max(sum(F(size).getlength(c) for c in ln) for ln in lines) > 900:
        size -= 6
    f = F(size)
    lh = size * 0.92
    i = 0
    for j, ln in enumerate(lines):
        wdt = sum(f.getlength(c) for c in ln)
        x = -wdt / 2
        for c in ln:
            adv = f.getlength(c)
            a = (t - t0 - i * stagger) / 0.22
            if a > 0 and c != " ":
                pop = out_back(a, 2.2)
                wave = 10 * math.sin(t * 7 + i * .7) * (1 if a > 1 else 0)
                lx = (x + adv / 2) * scale
                ly = ((j - (len(lines) - 1) / 2) * lh + wave - (1 - out_cubic(a)) * 90) * scale
                place(img, letter(c, size, fill), cx + lx, cy + ly, max(.02, pop) * scale)
            x += adv
            i += 1


# ---------- svarkort ----------
def days_text(ev_days):
    return " · ".join(DAYAB[d] for d in sorted(ev_days))


def answer_layer(e, days, times):
    def mk():
        w, h = 980, 640
        im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((20 + 14, 20 + 14, w + 14, h + 14), 36, fill=INK)
        d.rounded_rectangle((20, 20, w, h), 36, fill=CREAM, outline=INK, width=8)
        d.text((70, 78), "DET BLIR:", font=F(38, "ExtraBold"), fill="#6b6578")
        # tittel i opptil 2 linjer
        words = e["title"].split()
        best = None
        for size in range(104, 50, -4):
            f = F(size)
            lines, cur = [], ""
            for wd in words:
                nxt = (cur + " " + wd).strip()
                if f.getlength(nxt) <= w - 120:
                    cur = nxt
                else:
                    lines.append(cur)
                    cur = wd
            lines.append(cur)
            if len(lines) <= 2 and all(f.getlength(l) <= w - 120 for l in lines):
                best = (f, lines)
                break
        f, lines = best or (F(50), [e["title"][:30]])
        y = 120
        for ln in lines:
            d.text((70, y), ln, font=f, fill=INK)
            y += int(f.size * 1.05)
        d.text((70, y + 14), e["venue"].upper(), font=F(40, "ExtraBold"), fill="#4b4758")
        return im
    return cached(("ans", e["id"]), mk)


def chips(e, days, times):
    def mk():
        txt1, txt2 = days, times
        f = F(54)
        tmp = ImageDraw.Draw(Image.new("RGB", (4, 4)))
        w1, w2 = tmp.textlength(txt1, font=f) + 60, tmp.textlength(txt2, font=f) + 60
        im = Image.new("RGBA", (int(w1 + w2 + 60), 130), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x = 10
        for txt, wd, col, fg in ((txt1, w1, INK, YEL), (txt2, w2, PINK, INK)):
            d.rounded_rectangle((x + 8, 18, x + wd + 8, 108), 22, fill=INK)
            d.rounded_rectangle((x, 10, x + wd, 100), 22, fill=col, outline=INK, width=6)
            d.text((x + wd / 2, 56), txt, font=f, fill=fg, anchor="mm")
            x += wd + 30
        return im
    return cached(("chips", txt1 if (txt1 := days) else "", times), mk)


def price_burst(e):
    p = pages.price_text(e)
    if p in ("Pris hos arrangør",):
        return None
    if p == "Utsolgt":
        return None
    txt, col = ("GRATIS", GREEN) if p == "Gratis" else (p.replace(" kr", "") + "\nKR", YEL)
    def mk():
        lay = burst(150, col, 16).copy()
        d = ImageDraw.Draw(lay)
        lines = txt.split("\n")
        f = F(60 if len(lines) == 1 and len(txt) > 5 else 76 if len(lines) == 1 else 62)
        if len(lines) == 2:
            d.text((lay.width // 2, lay.height // 2 - 14), lines[0], font=F(66 if len(lines[0]) <= 4 else 50 if len(lines[0]) <= 6 else 40), fill=INK, anchor="mm")
            d.text((lay.width // 2, lay.height // 2 + 50), lines[1], font=F(40), fill=INK, anchor="mm")
        else:
            d.text((lay.width // 2, lay.height // 2), txt, font=f, fill=INK, anchor="mm")
        return lay
    return cached(("pb", e["id"]), mk)


# ---------- data ----------
class Data: pass


def build(today):
    data = json.loads((lag.ROOT / "data" / "events.json").read_text())
    start, sun = pages.weekend_range(today)
    evs = pages.occurrences([e for e in data["events"] if e["date"] >= today.isoformat() and e["cat"] not in pages.SEPARATE], start, sun)
    D = Data()
    D.evs, D.start, D.sun = evs, start, sun
    good = interesting(evs)
    seen, picks = set(), []
    for mood in MOODS:
        cands = {}
        for e in good:
            if mood[5](e) and not e.get("soldOut") and e["id"] not in seen:
                cands.setdefault(e["id"], []).append(e)
        if not cands:
            continue
        best = sorted(cands.values(), key=lambda g: (-len({x["date"] for x in g}), g[0]["date"], g[0].get("time") or ""))[0]
        seen.add(best[0]["id"])
        first = sorted(best, key=lambda x: x["date"])[0]
        days = days_text({datetime.date.fromisoformat(x["date"]).weekday() for x in best})
        times = (first.get("time") or "hele dagen").replace(" og ", " / ")
        picks.append((mood, first, days, times))
    D.picks = picks
    D.rest = len({e["id"] for e in evs}) - len(picks)
    return D


# ---------- scener ----------
def sc_hook(D, t, img):
    bg = backdrop(t, "#0d0b1f", "#1c1650", "#ffffff10", 2)
    img.alpha_composite(bg)
    words = [("HVA", CREAM), ("ER DU", PINK), ("I HUMØR", CYAN), ("TIL?", YEL)]
    k = min(3, int(max(0, t) / BEAT))
    txt, col = words[k]
    word(img, txt, t, k * BEAT, col, W // 2, 900, maxsize=360 if k != 2 else 300)


def sc_mood(D, i, t, img):
    mood, e, days, times = D.picks[i]
    _, top, bot, ray, fill, _f = mood
    bg = backdrop(t, top, bot, ray, 10 + i)
    img.alpha_composite(bg)
    # ordet: stort i midten, så opp og krymper
    p = out_cubic((t - 0.9) / 0.25)
    cy = 900 + (340 - 900) * p
    sc = 1 + (0.46 - 1) * p
    word(img, mood[0], t, 0.0, fill, W // 2, cy, sc, maxsize=400)
    if t >= 1.0:
        a = out_back((t - 1.0) / 0.3, 1.2)
        lay = answer_layer(e, days, times)
        place(img, lay, W // 2, 1060 + (1 - a) * 900, 1.0, -1.5)
    if t >= 1.4:
        place(img, chips(e, days, times), W // 2 - 10, 1290, out_back((t - 1.4) / 0.25), 0)
    pb = price_burst(e)
    if pb is not None and t >= 1.65:
        place(img, pb, 870, 690, 0.8 * out_back((t - 1.65) / 0.25) * (1 + .04 * pulse(t)), 10 + 4 * math.sin(t * 5))


def sc_outro(D, t, img):
    bg = backdrop(t, "#ffd93b", "#ff9a3b", "#ff4f8b33", 20)
    img.alpha_composite(bg)
    word(img, "ALT\nDETTE", t, 0.0, INK, W // 2, 560, maxsize=330)
    word(img, f"+ {D.rest} TIL", t, 0.5, PINK, W // 2, 960, maxsize=200)
    word(img, "I ÅLESUND", t, 1.0, BLUE, W // 2, 1160, maxsize=190)
    if t >= 2.0:
        place(img, lag.sticker_layer("kaskjerda.no", -2, INK, YEL, 120, (50, 22)), W // 2, 1370, out_back((t - 2.0) / 0.25) * (1 + .05 * pulse(t)))
    if t >= 2.5:
        place(img, reel.cached(("lagre",), reel._lagre), 890, 1530, out_back((t - 2.5) / 0.3), 10)


def scene(D, i, t):
    img = Image.new("RGBA", (W, H))
    if i == 0: sc_hook(D, t, img)
    elif i <= len(D.picks): sc_mood(D, i - 1, t, img)
    else: sc_outro(D, t, img)
    return img


def idx(D, k):
    """Sceneliste: hook, humør (så mange det ble), outro. Tider fordeles som i DUR hvis alle seks finnes."""
    return k


def frame(args):
    D, n = args
    t = n / FPS
    order = [0] + list(range(1, len(D.picks) + 1)) + [len(MOODS) + 1]
    starts = [0, 2] + [2 + 2 * j for j in range(1, len(D.picks))] + [2 + 2 * len(D.picks)]
    k = max(m for m in range(len(starts)) if starts[m] <= t + 1e-9)
    tl = t - starts[k]
    img = scene(D, order[k] if order[k] <= len(D.picks) or k == 0 else len(D.picks) + 1, tl)
    sh = 0
    if tl < 0.3:
        a = (1 - tl / 0.3) ** 2 * 20
        s2 = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        s2.paste(img, (int(a * math.sin(tl * 90)), int(a * math.cos(tl * 70))))
        img = s2
    if tl < 0.12 and k > 0:  # hvit blits ved hvert kutt
        fl = Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - tl / 0.12))))
        img.alpha_composite(fl)
    return img.convert("RGB").tobytes()


def init(D_):
    global _D
    _D = D_


def frame_w(n):
    return frame((_D, n))


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "helg-reel-humor.mp4"
    today = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else datetime.date.today()
    D = build(today)
    total = 2 + 2 * len(D.picks) + 3
    import lyd
    tmp = Path(tempfile.mkdtemp())
    wav = tmp / "lyd.wav"
    lyd.skriv(wav)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", str(wav), "-t", str(total), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    with Pool(4, initializer=init, initargs=(D,)) as pool:
        for fr in pool.imap(frame_w, range(total * FPS), chunksize=4):
            p.stdin.write(fr)
    p.stdin.close()
    p.wait()
    print("ferdig:", out, f"{total} s,", len(D.picks), "humør")


if __name__ == "__main__":
    main()
