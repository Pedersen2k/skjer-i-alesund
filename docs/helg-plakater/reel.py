"""Helge-reel (1080 x 1920, 30 fps, 17 s) med egen musikk. Samme data og stil som lag.py.

Kjør: python3 docs/helg-plakater/reel.py [ut.mp4] [YYYY-MM-DD]
"""
import datetime, json, math, subprocess, sys, tempfile
from multiprocessing import Pool
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import lag
from lag import (W, INK, CREAM, YEL, PINK, BLUE, GREEN, ORANGE, F, halftone, skyline, burst, sticker_layer,
                 shadow_text, card_layer, interesting, DAY_BG, DAY_FG, DAYS, MONTHS, pages)

H = 1920
FPS = 30
BEAT = 0.5
TR = 0.25  # overgang før scenegrensen
DURS = [2, 3, 4, 3, 2, 3]  # hook, fre, lør, søn, gratis, outro
STARTS = [sum(DURS[:i]) for i in range(len(DURS))]
TOTAL = sum(DURS)


# ---------- easing ----------
def cl(x): return max(0.0, min(1.0, x))
def out_back(x, k=1.9):
    x = cl(x) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2
def out_cubic(x): return 1 - (1 - cl(x)) ** 3
def pulse(t):  # beat-puls 1..0
    return math.exp(-((t % BEAT) / BEAT) * 7)


def place(img, layer, cx, cy, scale=1.0, angle=0.0):
    if scale <= 0.02:
        return
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BILINEAR)
    if angle:
        layer = layer.rotate(angle, resample=Image.BILINEAR, expand=True)
    img.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)), layer)


def slam(img, layer, cx, cy, t, t0, angle=0.0, big=2.4):
    """Treffer inn fra stor og lander med overshoot, så beat-puls. t og t0 i sekunder."""
    if t < t0:
        return
    a = (t - t0) / 0.22
    sc = 1 + (big - 1) * (1 - out_back(a, 1.2)) if a < 1 else 1.0
    sc *= 1 + 0.045 * pulse(t - t0 if t - t0 > 0.22 else 0)
    place(img, layer, cx, cy, sc, angle)


def pop(img, layer, cx, cy, t, t0, angle=0.0):
    if t < t0:
        return
    place(img, layer, cx, cy, max(0.01, out_back((t - t0) / 0.25)), angle)


def fly(img, layer, cx, cy, t, t0, side):
    if t < t0:
        return
    k = out_back((t - t0) / 0.28, 1.1)
    place(img, layer, cx + side * (1 - k) * 1300, cy, 1.0 + 0.0)


# ---------- lag som gjenbrukes ----------
_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def bg_layer(color, dot, seed, kind="top"):
    def mk():
        im = Image.new("RGB", (W, H), color)
        halftone(im, dot, 0, 0, W, 760, step=30, rmax=13)
        # skyline nederst (lagd på 1350-lerret, flyttes til bunnen)
        sk = Image.new("RGBA", (W, 1350), (0, 0, 0, 0))
        skyline(sk, seed=seed)
        im.paste(sk.crop((0, 1160, W, 1350)), (0, H - 190), sk.crop((0, 1160, W, 1350)))
        return im.convert("RGBA")
    return cached(("bg", color, dot, seed), mk)


def title_layer(text, fill, max_size=330, rot=0, shadow=INK):
    def mk():
        d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        f = F(max_size)
        while d.textlength(text, font=f) > 940:
            f = F(f.size - 6)
        lay = Image.new("RGBA", (W, int(f.size * 1.5)), (0, 0, 0, 0))
        shadow_text(ImageDraw.Draw(lay), (W // 2, lay.height // 2), text, f, fill, shadow=shadow, off=max(10, f.size // 18), outline=max(6, f.size // 30), anchor="mm")
        return lay
    return cached(("t", text, fill, max_size, shadow), mk)


def stick(text, bg, fg=INK, size=48, angle=0, pad=(30, 16)):
    return cached(("s", text, bg, fg, size, angle), lambda: sticker_layer(text, angle, bg, fg, size, pad))


def burst_layer(size, color, spikes=18):
    return cached(("b", size, color, spikes), lambda: burst(size, color, spikes))


def card_l(e, tilt, chip=None):
    return cached(("c", e["id"], e["date"], tilt, chip), lambda: card_layer(e, tilt, chip)[0])


# ---------- utvalg ----------
def score(e):
    s = 0
    p = pages.price_text(e)
    if p == "Gratis": s += 4
    if e["cat"] in ("konsert", "standup", "show"): s += 2
    if e["cat"] == "barn": s += 1
    if e.get("soldOut"): s -= 1
    if "mesterskap" in e["title"].lower(): s -= 5
    return s


def pick(evs, day, n=4):
    items = [e for e in interesting([x for x in evs if x["date"] == day.isoformat()]) if e["cat"] != "klubb"]
    best = sorted(items, key=lambda e: -score(e))[:n]
    return sorted(best, key=lambda e: e.get("time") or "00:00"), len(items)


# ---------- scener ----------
class Data:
    pass


def build(today):
    data = json.loads((lag.ROOT / "data" / "events.json").read_text())
    start, sun = pages.weekend_range(today)
    evs = pages.occurrences([e for e in data["events"] if e["date"] >= today.isoformat() and e["cat"] not in pages.SEPARATE], start, sun)
    D = Data()
    D.evs, D.start, D.sun = evs, start, sun
    D.days = {}
    for i in range((sun - start).days + 1):
        day = start + datetime.timedelta(days=i)
        if day.weekday() in DAY_BG:
            chosen, n_int = pick(evs, day)
            night = [x for x in evs if x["date"] == day.isoformat() and x["cat"] == "klubb"]
            D.days[day.weekday()] = dict(day=day, chosen=chosen, n=len([x for x in evs if x["date"] == day.isoformat()]),
                                         night=list(dict.fromkeys(x["venue"] for x in night)), rest=n_int - len(chosen))
    D.free = [e for e in interesting(evs) if pages.price_text(e) == "Gratis"][:2]
    return D


def sc_hook(D, t, img):
    bgc = bg_layer(BLUE, "#4a66ff", 3)
    img.paste(bgc, (0, 0))
    d = ImageDraw.Draw(img)
    # sol
    k = 1 + 0.03 * pulse(t if t >= 0 else 0)
    for i, c in enumerate([PINK, ORANGE, YEL]):
        r = (260 - i * 36) * k
        d.ellipse((780 - r, 520 - r, 780 + r, 520 + r), fill=c)
    place(img, burst_layer(150, YEL), 230, 400, 1 + 0.05 * pulse(t), -10 + 3 * math.sin(t * 6)) if t >= 0 else None
    if t >= 0:
        lay = Image.new("RGBA", (300, 200), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.text((150, 70), "HER", font=F(64), fill=INK, anchor="mm")
        ld.text((150, 130), "SKJER DET", font=F(40), fill=INK, anchor="mm")
        place(img, lay, 230, 400, 1 + 0.05 * pulse(t), -10 + 3 * math.sin(t * 6))
    slam(img, title_layer("HELGA", YEL, 340), W // 2, 880, t, 0.0, -4)
    pop(img, stick("I ÅLESUND", PINK, INK, 100, 3, (44, 20)), W // 2 - 60, 1120, t, 0.5, 3)
    span = f"{D.start.day}.–{D.sun.day}. {MONTHS[D.sun.month]}"
    pop(img, title_layer(span, CREAM, 110), W // 2, 1290, t, 1.0)
    n = len(D.evs)
    bl = cached(("cnt", n), lambda: _count_layer(n))
    place(img, bl, 850, 1520, out_back((t - 1.5) / 0.3) * (1 + 0.05 * pulse(t)), 8) if t >= 1.5 else None


def _count_layer(n):
    lay = burst(160, GREEN, 14).copy()
    d = ImageDraw.Draw(lay)
    d.text((lay.width // 2, lay.height // 2 - 20), str(n), font=F(130), fill=INK, anchor="mm")
    d.text((lay.width // 2, lay.height // 2 + 60), "TING Å GJØRE", font=F(30), fill=INK, anchor="mm")
    return lay


def sc_day(D, wd, t, img):
    info = D.days.get(wd)
    bg = DAY_BG[wd]
    dot = "#ffffff88" if bg == YEL else "#ffffff55"
    img.paste(bg_layer(bg, dot, wd), (0, 0))
    if not info:
        return
    day = info["day"]
    namecol = lag.CREAM if bg != BLUE else YEL
    slam(img, title_layer(DAYS[wd], namecol, 260), W // 2, 430, t, 0.0, -2.5)
    pop(img, stick(f"{day.day}. {MONTHS[day.month]}", CREAM, INK, 56, 2, (34, 14)), 300, 640, t, 0.5, 2)
    pop(img, stick(f"{info['n']} ARRANGEMENT", YEL if bg != YEL else PINK, INK, 44, -2, (30, 14)), 770, 640, t, 0.5, -2)
    y = 780
    for i, e in enumerate(info["chosen"]):
        tilt = [-1.2, 0.9, -0.7, 1.1][i % 4]
        fly(img, card_l(e, tilt), W // 2, y + 80, t, 1.0 + 0.5 * i, 1 if i % 2 else -1)
        y += 190
    t_n = 1.0 + 0.5 * len(info["chosen"])
    if info["night"]:
        txt = "NATTA: " + " · ".join(info["night"])
        pop(img, stick(txt if len(txt) < 62 else txt[:60] + "…", INK, CREAM, 30, 0, (26, 12)), W // 2, y + 20, t, t_n)
    if info["rest"] > 0:
        pop(img, stick(f"+ {info['rest']} til på kaskjerda.no", CREAM, INK, 34, -1, (26, 12)), W // 2, y + 100, t, t_n + 0.5)


def sc_free(D, t, img):
    img.paste(bg_layer(GREEN, "#ffffff55", 11), (0, 0))
    slam(img, title_layer("GRATIS", YEL, 320), W // 2, 440, t, 0.0, 3)
    pop(img, stick("ingen billett. bare dukk opp.", CREAM, INK, 44, -2, (28, 12)), W // 2, 660, t, 0.5, -2)
    y = 860
    for i, e in enumerate(D.free):
        wd = pages.WD[datetime.date.fromisoformat(e["date"]).weekday()][:3].upper()
        chip = f"{wd} {(e.get('time') or '').split(' og ')[0]}".strip()
        fly(img, card_l(e, [-1.2, 1][i % 2], chip), W // 2, y + 80, t, 1.0 + 0.5 * i, 1 if i % 2 else -1)
        y += 200


def sc_outro(D, t, img):
    img.paste(bg_layer(YEL, "#ffffff88", 5), (0, 0))
    for txt, y, a, c, t0 in [("FANT DU", 420, -3, INK, 0.0), ("NOE Å", 640, 2, PINK, 0.5), ("GJØRE?", 860, -2, BLUE, 1.0)]:
        slam(img, title_layer(txt, c, 240, shadow=CREAM if c == INK else INK), W // 2, y, t, t0, a)
    if t >= 2.0:
        k = out_back((t - 2.0) / 0.25)
        place(img, stick("kaskjerda.no", INK, YEL, 110, -2, (50, 22)), W // 2, 1180, k * (1 + 0.05 * pulse(t)), -2)
    if t >= 2.5:
        place(img, stick("ALT SOM SKJER. MED PRISER.", CREAM, INK, 44, 2, (30, 14)), W // 2, 1330, out_back((t - 2.5) / 0.25), 2)
    if t >= 2.5:
        lay = cached(("lagre",), lambda: _lagre())
        place(img, lay, 880, 1500, out_back((t - 2.5) / 0.3), 10)


def _lagre():
    lay = burst(120, PINK, 14).copy()
    d = ImageDraw.Draw(lay)
    d.text((lay.width // 2, lay.height // 2 - 22), "LAGRE", font=F(44), fill=INK, anchor="mm")
    d.text((lay.width // 2, lay.height // 2 + 28), "& DEL", font=F(44), fill=INK, anchor="mm")
    return lay


def scene(D, i, t):
    img = Image.new("RGBA", (W, H))
    if i == 0: sc_hook(D, t, img)
    elif i == 1: sc_day(D, 4, t, img)
    elif i == 2: sc_day(D, 5, t, img)
    elif i == 3: sc_day(D, 6, t, img)
    elif i == 4: sc_free(D, t, img)
    else: sc_outro(D, t, img)
    return img


def frame(args):
    D, n = args
    t = n / FPS
    i = max(k for k in range(len(STARTS)) if STARTS[k] <= t + 1e-9)
    tl = t - STARTS[i]
    img = scene(D, i, tl)
    nxt = i + 1
    if nxt < len(STARTS) and t > STARTS[nxt] - TR:
        p = out_cubic((t - (STARTS[nxt] - TR)) / TR)
        inc = scene(D, nxt, t - STARTS[nxt])
        canvas = Image.new("RGBA", (W, H))
        canvas.paste(img, (int(-p * W * 0.3), 0))
        canvas.paste(inc, (int((1 - p) * W), 0))
        img = canvas
    # kamerarist ved scenestart (treffer)
    sh = 0
    ts = t - STARTS[i]
    if 0 <= ts < 0.3 and i > 0 or (i == 0 and ts < 0.3):
        a = (1 - ts / 0.3) ** 2 * 16
        dx, dy = int(a * math.sin(ts * 90)), int(a * math.cos(ts * 70))
        shifted = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        shifted.paste(img, (dx, dy))
        img = shifted
    return img.convert("RGB").tobytes()


def init(D_):
    global _D
    _D = D_


def frame_w(n):
    return frame((_D, n))


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "helg-reel.mp4"
    today = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else datetime.date.today()
    D = build(today)
    import lyd
    tmp = Path(tempfile.mkdtemp())
    wav = tmp / "lyd.wav"
    lyd.skriv(wav)
    nfr = TOTAL * FPS
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", str(wav), "-t", str(TOTAL), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    with Pool(4, initializer=init, initargs=(D,)) as pool:
        for fr in pool.imap(frame_w, range(nfr), chunksize=4):
            p.stdin.write(fr)
    p.stdin.close()
    p.wait()
    print("ferdig:", out)


if __name__ == "__main__":
    main()
