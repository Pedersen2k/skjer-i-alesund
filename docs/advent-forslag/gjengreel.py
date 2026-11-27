"""Reel «Flimmer-gjengen tenner lys nr. 2» (2. søndag i advent, 6. desember 2026).
22 sekunder, 1080×1920, 24 bilder/s. Lyd legges på i Instagram.
Arrangementene leses fra data/events.json (ingenting er funnet på).
Kjør: python3 gjengreel.py            (lager gjeng-reel.mp4)
      python3 gjengreel.py --stills   (lager gjeng-reel-stills.png)"""
import json, math, random, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from PIL import Image, ImageDraw, ImageFilter
from ukepost import B, F, M, block, logo
import reel as R
import gjeng as G
from reel import Gl, flame, sparks, snow, strand, wreath, back, clamp, W, H, FPS, GOLD

R.IGNITE = 9.0                      # lyslenka tennes når lys nr. 2 tennes
LIGHT = 9.0
BOUNDS = [0, 3.4, 6.6, 10.6, 18.0, 22.0]
DUR = BOUNDS[-1]
CONFETTI = [(random.Random(i).random(), random.Random(i + 99).random(), random.Random(i + 7).uniform(.6, 1.4),
             random.Random(i + 3).choice(R.PAL + [(255, 255, 255)]), random.Random(i + 5).random() * 6) for i in range(130)]


# ---------- arrangementer fra events.json ----------
def hent(tittel, dato="2026-12-06"):
    d = json.load(open(ROOT / "data/events.json", encoding="utf-8"))
    for e in (d["events"] if isinstance(d, dict) else d):
        if e["title"] == tittel and str(e.get("date", ""))[:10] == dato:
            return e
    raise SystemExit(f"fant ikke «{tittel}» {dato} i events.json")


KORT = []
for navn, tittel in (("Flimmer", "Førjulssøndag på Sunnmøre museum"), ("Per", "Adventskonsert med AaUM"),
                     ("Stjerna", "Marie Løvås Duo – julekonsert")):
    e = hent(tittel)
    pris = "GRATIS" if e["price"].lower() == "gratis" else e["price"]
    KORT.append((navn, f"SØNDAG 6. DESEMBER · KL. {int(e['time'][:2])}", e["title"], e["venue"], pris))

# ---------- figurer som ferdige bilder ----------
CHARS = [("Per", G.pepper, (0, 0)), ("Lykta", G.lykt, (0, 260)), ("Flimmer", G.flimmer, (0, 330)),
         ("Gnist", G.gnist, (0, 410)), ("Stjerna", G.stjerne, (0, 190)), ("Lysa", G.pare, (0, 235))]
GLOW = {"Flimmer": (330, (255, 150, 60)), "Lykta": (260, (255, 200, 90)), "Gnist": (410, (255, 210, 120)),
        "Stjerna": (190, (255, 220, 120)), "Lysa": (235, (255, 150, 220))}
SPR = {}
NOW = [0.0]


def lag_sprites():
    G.NOFLAME = True
    for navn, fn, _ in CHARS:
        for st in (0, 1, 2):
            G.STATE = st
            lag = Image.new("RGBA", (700, 760), (0, 0, 0, 0))
            fn(ImageDraw.Draw(lag), ImageDraw.Draw(Image.new("RGB", (700, 760))), 350, 640)
            kontur = lag.split()[3].filter(ImageFilter.MaxFilter(21))
            ut = Image.new("RGBA", lag.size, (0, 0, 0, 0))
            ut.paste(Image.new("RGBA", lag.size, (14, 12, 34, 255)), mask=kontur)
            ut.alpha_composite(lag)
            bb = ut.getbbox(); bb = (bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)
            SPR[(navn, st)] = (ut.crop(bb), (350 - bb[0], 640 - bb[1]))   # bilde, føttene (midt/bunn)
    G.STATE = 0


def hoyde(navn):
    return SPR[(navn, 0)][0].height


def put(im, g, navn, x, y, s=1.0, sx=1.0, sy=1.0, rot=0.0, st=0, glow=1.0, flamme=True):
    """Setter figuren med føttene i (x, y). s = skala, sx/sy = klem og strekk."""
    spr, (fx, fy) = SPR[(navn, st)]
    w, h = max(2, int(spr.width * s * sx)), max(2, int(spr.height * s * sy))
    img = spr.resize((w, h), Image.BILINEAR)
    ax, ay = fx * s * sx, fy * s * sy
    if rot:
        img = img.rotate(rot, Image.BICUBIC, expand=True)
        ax, ay = img.width / 2, img.height - 0.04 * img.height
    im.paste(img, (int(x - ax), int(y - ay)), img)
    if navn == "Flimmer" and flamme:
        flame(ImageDraw.Draw(im), g, x, y - 288 * s * sy, 1.5 * s, NOW[0], 7)
    if navn in GLOW and glow > 0:
        dy, col = GLOW[navn]
        g.dot(x, y - dy * s * sy, 130 * s, col, .55 * glow)
    return (x, y)


def idle(t, ph, amp=14):
    u = abs(math.sin(t * 3.2 + ph))
    return -amp * u, 1 - .04 * (1 - u) * 0 + .035 * (1 - u), 1 + .06 * u - .035


def stand(t, navn, slot, y=1790):
    """Tilstand (blunk) og tidsfaser per figur."""
    ph = slot * 1.3
    return ph, (1 if ((t + ph) % 3.6) > 3.47 else 0)


# ---------- rutenett ----------
SLOT = {n: 128 + i * 165 for i, (n, _, _) in enumerate(CHARS)}
FIT = {}
for n in SLOT: FIT[n] = None


def fit(navn):
    if FIT[navn] is None:
        h = hoyde(navn); w = SPR[(navn, 0)][0].width
        FIT[navn] = min(1.5, 400 / h, 250 / w)
    return FIT[navn]


def scene_of(t):
    for i in range(5):
        if t < BOUNDS[i + 1]: return i
    return 4


def tekst(im, lab, title, dy=0, y0=330):
    d = ImageDraw.Draw(im)
    d.text((W // 2, y0 + dy), lab, font=M(46), fill=GOLD, anchor="ma")
    f, _, ls = block(d, title, B, (104, 96, 88, 80), W - 120, 2)
    y = y0 + 70 + dy
    for l in ls:
        d.text((W // 2, y), l, font=f, fill=(255, 255, 255), anchor="ma"); y += int(f.size * 1.08)


def boble(d, x, y, w, txt, tail=(-60, 40), size=(50, 46, 42)):
    f, _, ls = block(d, txt, F, size, w - 60, 3)
    hh = len(ls) * int(f.size * 1.12) + 56
    d.rounded_rectangle((x, y, x + w, y + hh), 40, fill=(255, 255, 255))
    d.polygon([(x + 4, y + hh - 70), (x + 4, y + hh - 14), (x + tail[0], y + hh + tail[1])], fill=(255, 255, 255))
    yy = y + 28
    for l in ls:
        d.text((x + 34, yy), l, font=f, fill=(46, 22, 76)); yy += int(f.size * 1.12)


def konfetti(d, g, t, t0, t1):
    if not t0 <= t < t1: return
    a = t - t0
    for x0, y0, v, col, ph in CONFETTI:
        x = x0 * W + 60 * math.sin(a * 2 + ph)
        y = -40 + (y0 * 500 + a * 520 * v) % (H + 80) if False else -60 + a * 520 * v + y0 * 300
        if y > H: continue
        w = 14 * math.cos(a * 7 + ph); h = 22
        d.polygon([(x - w, y - h), (x + w, y - h + 4), (x + w, y + h), (x - w, y + h - 4)], fill=col)


def burst(d, g, t, t0, x, y, col):
    a = t - t0
    if not 0 <= a < 1.2: return
    r = random.Random(int(t0 * 13 + x))
    for _ in range(40):
        ang = r.random() * math.tau; sp = r.uniform(90, 330)
        px, py = x + math.cos(ang) * sp * a, y + math.sin(ang) * sp * a + 120 * a * a
        f = 1 - a / 1.2; c = tuple(int(v * f) for v in r.choice((col, (255, 255, 230), GOLD)))
        d.ellipse((px - 6, py - 6, px + 6, py + 6), fill=c); g.dot(px, py, 28, c, .7)


def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


# ---------- scenene ----------
def render(t, sc):
    k = clamp((t - LIGHT + .2) / 1.0)
    im = Image.blend(R.BGD, R.BG, k) if sc != 3 else R.BG.copy()
    NOW[0] = t
    d = ImageDraw.Draw(im); g = Gl()
    snow(d, t); strand(d, g, t)
    local = t - BOUNDS[sc]
    pos = None
    if sc != 3:
        pos = wreath(d, g, t, [-5, LIGHT, None, None])
    c2 = (pos[1][0], pos[1][1] - 112) if pos else (413, 682)
    flyg = (7.7, 8.9)                                    # Gnist flyr opp
    hjem = (10.0, 10.6)                                  # …og tilbake

    if sc == 0:
        # Flimmer alene, flammen flimrer
        e = back(local / .5)
        ph, st = stand(t, "Flimmer", 0)
        talk = 1.0 < local < 3.0 and int(t * 7) % 2 == 0
        st = 2 if talk else (1 if (t % 2.7) > 2.6 else 0)
        sc_ = 1.5
        x, y = 215, 1700
        dy, sx, sy = idle(t, 0, 9)
        put(im, g, "Flimmer", x, y + dy, sc_ * e, sx, sy, st=st, glow=0)
        tekst(im, "2. SØNDAG I ADVENT", "Ett lys er tent …", (1 - back(local / .5)) * 70)
        d = ImageDraw.Draw(im)
        bp = back((local - .6) / .4) if local > .6 else 0
        boble(d, 355, 1330 + (1 - bp) * 40, 665, "Hjelp! Bare ett lys brenner. Det er jo 6. desember!" if local < 2.0
              else "Vi må ha lys nr. 2. Hvor er gjengen?!", (-70, 50))

    elif sc in (1, 2):
        # gjengen popper inn; i scene 2 telles ned og Gnist skyter opp
        order = ["Flimmer", "Per", "Lykta", "Gnist", "Stjerna", "Lysa"]
        for i, n in enumerate(order):
            t_in = BOUNDS[1] + .15 + i * .36
            if t < t_in: continue
            e = back((t - t_in) / .55)
            ph, st = stand(t, n, i)
            talk = (t_in + .55 < t < t_in + 1.3) and int(t * 9) % 2 == 0
            if talk: st = 2
            x, y = SLOT[n], 1790
            dy, sx, sy = idle(t, ph, 16)
            jump = (1 - clamp((t - t_in) / .55)) * 520
            away = n == "Gnist" and flyg[0] <= t < hjem[1]
            if away: continue
            if n == "Gnist" and t > hjem[0] and sc == 2: pass
            put(im, g, n, x, y + dy - jump * (1 - e) * 0 - jump, fit(n) * clamp(e) * (1 if e <= 1.1 else 1.0), sx, sy, st=st)
            if sc == 1 and t_in + .2 < t < t_in + 1.6 and n != "Flimmer" or (sc == 1 and n == "Flimmer" and t_in + .2 < t < t_in + 1.6):
                d = ImageDraw.Draw(im)
                tw = d.textlength(n, font=B(40)) + 44
                yt = y + dy - jump - hoyde(n) * fit(n) * clamp(e)
                d.rounded_rectangle((x - tw / 2, yt - 78, x + tw / 2, yt - 18), 28, fill=(255, 255, 255))
                d.text((x, yt - 48), n, font=B(40), fill=(46, 22, 76), anchor="mm")
        if sc == 1:
            tekst(im, "6. DESEMBER", "Gjengen er samla!", (1 - back(local / .5)) * 70)
        else:
            tekst(im, "TA-DA!" if t > LIGHT else "TRE … TO … ÉN …", "Lys nr. 2 er tent!" if t > LIGHT else "Gnist fikser det!", (1 - back(local / .5)) * 70 if t < LIGHT else 0)
            d = ImageDraw.Draw(im)
            for n_, t0 in (("3", 6.9), ("2", 7.5), ("1", 8.1)) if False else ():
                pass
            # nedtelling: 3, 2, 1 før oppskytingen (7.7)
            for sifre, a0, a1 in (("3", 6.75, 7.1), ("2", 7.1, 7.45), ("1", 7.45, 7.8)):
                if a0 <= t < a1:
                    u = (t - a0) / (a1 - a0); sz = int(260 * back(u * 2.4) * (1 - .25 * clamp((u - .7) / .3)))
                    if sz > 5:
                        d.text((W // 2, 960), sifre, font=B(max(10, sz)), fill=GOLD, anchor="mm", stroke_width=8, stroke_fill=(14, 12, 34))
            # Gnist: oppskyting langs en bue til lys nr. 2, tilbake til slottet
            gx, gy = SLOT["Gnist"], 1790
            tgt = (c2[0] - 6, c2[1] + 120)
            ctr = (880, 1250)
            def gpos(tt):
                if tt < flyg[0]: return None
                if tt < flyg[1]: return bez((gx, gy - 140), ctr, tgt, back((tt - flyg[0]) / (flyg[1] - flyg[0]) * .9 + .0) if False else (tt - flyg[0]) / (flyg[1] - flyg[0]))
                if tt < hjem[0]: return (tgt[0] + 8 * math.sin(t * 12), tgt[1] + 5 * math.sin(t * 9))
                if tt < hjem[1]: return bez(tgt, (180, 1050), (gx, gy - 140), (tt - hjem[0]) / (hjem[1] - hjem[0]))
                return None
            p = gpos(t)
            if p:
                # sporet etter raketten
                for j in range(1, 14):
                    q = gpos(t - j * .035)
                    if q is None: continue
                    f = 1 - j / 14; c = tuple(int(v * f) for v in R.PAL[j % 4])
                    r_ = 4 + 11 * f
                    d.ellipse((q[0] - r_, q[1] + 60 - r_, q[0] + r_, q[1] + 60 + r_), fill=c); g.dot(q[0], q[1] + 60, 36 * f + 8, c, .8)
                q2 = gpos(t + .03) or p
                ang = math.degrees(math.atan2(q2[0] - p[0], -(q2[1] - p[1] + 1e-6))) if t < hjem[0] or t >= hjem[0] else 0
                if flyg[1] <= t < hjem[0]: ang = 0
                ph, st = stand(t, "Gnist", 3)
                put(im, g, "Gnist", p[0], p[1] + 140, fit("Gnist") * 1.35, rot=-ang * .8, st=2 if t < flyg[1] else 0)
                d = ImageDraw.Draw(im)
            if t < flyg[0] + .6 and t >= flyg[0]:
                u = (t - flyg[0]) / .6
                d.text((SLOT["Gnist"] + 60, 1500 - 120 * u), "FWOOSH!", font=B(int(70 * back(u * 2))), fill=(255, 230, 150), anchor="mm")
            # lys nr. 2 tennes (LIGHT = 9.0): lysring, gnister, konfetti
            a = t - LIGHT
            if 0 <= a < .7:
                g.dot(c2[0], c2[1], 150 + 700 * a, (255, 200, 120), .9 * (1 - a / .7))
            sparks(d, g, c2[0], c2[1], LIGHT, t)
            burst(d, g, t, LIGHT + .1, 230, 520, GOLD); burst(d, g, t, LIGHT + .35, 860, 600, (255, 150, 200))
            burst(d, g, t, LIGHT + .6, 540, 430, (140, 220, 255))
            konfetti(d, g, t, LIGHT, LIGHT + 3.2)
            if LIGHT < t < LIGHT + .9:
                u = (t - LIGHT) / .9
                d.text((c2[0] + 250, c2[1] - 120 - 60 * u), "PUFF!", font=B(int(86 * back(u * 2.2))), fill=(255, 245, 190), anchor="mm")

    elif sc == 3:
        # tre arrangementer, hver med sin presentatør
        dur = (BOUNDS[4] - BOUNDS[3]) / 3
        local = max(0.0, local); i = min(2, int(local / dur)); lc = local - i * dur
        navn, lab, tittel, sted, pris = KORT[i]
        e = back(lc / .45); ex = clamp((lc - (dur - .3)) / .3)
        konfetti(d, g, t, LIGHT, LIGHT + 3.2)
        # figur
        jump = (1 - clamp(lc / .5)) * 600
        s_ = 1.55 if navn == "Per" else 1.2
        s_ = min(s_, 520 / hoyde(navn), 620 / SPR[(navn, 0)][0].width)
        st = 2 if (.5 < lc < dur - .4 and int(t * 8) % 2 == 0) else (1 if (t % 2.4) > 2.3 else 0)
        dy, sx, sy = idle(t, i, 18)
        put(im, g, navn, 540 + (0 if navn != "Stjerna" else 0), 1800 + dy - jump + ex * 700, s_ * clamp(e + .0), sx, sy, st=st)
        # kort
        cx0, cy0, cw, ch = 70, 430, 940, 760
        sc2 = clamp(e) * (1 - ex * .3); yoff = ex * -900 + (1 - clamp(e)) * 200
        y0 = cy0 + yoff
        lagk = Image.new("RGBA", (cw + 40, ch + 140), (0, 0, 0, 0)); kd = ImageDraw.Draw(lagk)
        kd.rounded_rectangle((20, 20, 20 + cw, 20 + ch), 56, fill=(255, 255, 255, 245))
        kd.polygon([(20 + cw // 2 - 50, 20 + ch - 6), (20 + cw // 2 + 50, 20 + ch - 6), (20 + cw // 2, 20 + ch + 100)], fill=(255, 255, 255, 245))
        lab_f = M(40); tw = kd.textlength(lab, font=lab_f) + 56
        kd.rounded_rectangle((60, 70, 60 + tw, 140), 35, fill=(46, 22, 76))
        kd.text((60 + tw / 2, 105), lab, font=lab_f, fill=GOLD, anchor="mm")
        f, _, ls = block(kd, tittel, B, (96, 88, 80, 72), cw - 100, 3)
        yy = 190
        for l in ls:
            kd.text((70, yy), l, font=f, fill=(46, 22, 76)); yy += int(f.size * 1.1)
        kd.text((70, 20 + ch - 225), sted, font=M(52), fill=(110, 70, 140))
        pf = B(78); pw = kd.textlength(pris, font=pf) + 70
        kd.rounded_rectangle((60, 20 + ch - 150, 60 + pw, 20 + ch - 40), 55, fill=(255, 190, 60) if pris == "GRATIS" else (46, 22, 76))
        kd.text((60 + pw / 2, 20 + ch - 95), pris, font=pf, fill=(46, 22, 76) if pris == "GRATIS" else GOLD, anchor="mm")
        rot = (1 - clamp(e)) * -8 + 1.2 * math.sin(t * 2)
        if sc2 > .03:
            lagk = lagk.resize((max(2, int(lagk.width * sc2)), max(2, int(lagk.height * sc2))), Image.BILINEAR).rotate(rot, Image.BICUBIC, expand=True)
            im.paste(lagk, (int(W / 2 - lagk.width / 2), int(y0 + (ch + 140) * (1 - sc2) / 2)), lagk)
        im = g.apply(im); d = ImageDraw.Draw(im)
        d.text((W // 2, 150 + 0), "I DAG, SØNDAG 6. DESEMBER", font=M(40), fill=GOLD, anchor="ma") if False else None
        tekst(im, "TIPS FRA GJENGEN", "Dette skjer i dag", 0, 150) if False else None
        d = ImageDraw.Draw(im)
        d.text((W // 2, 250), "TIPS FRA GJENGEN", font=M(46), fill=GOLD, anchor="ma")
        d.text((W // 2, 320), "Dette skjer i dag", font=B(92), fill=(255, 255, 255), anchor="ma")
        return im

    else:
        # finale: kransen med to lys, hele gjengen hopper
        ee = back(local / .5)
        konfetti(d, g, t, BOUNDS[4] + .0, BOUNDS[4] + 1.3)
        for i, n in enumerate(["Flimmer", "Per", "Lykta", "Gnist", "Stjerna", "Lysa"]):
            ph = i * .9
            u = abs(math.sin(t * 4.2 + ph))
            dy = -34 * u; sy = 1 + .1 * u - .04; sx = 1 / sy ** .5
            st = 2 if (n == "Flimmer" and int(t * 8) % 2 == 0 and local < 3) else (1 if ((t + ph) % 3.4) > 3.27 else 0)
            put(im, g, n, SLOT[n], 1790 + dy, fit(n), sx, sy, st=st)
        # liten logo og adresse
        lg, mask = logo(120); im.paste(lg, (210, 1205), mask); d = ImageDraw.Draw(im)
        d.text((360, 1215), "kaskjerda.no", font=B(70), fill=(255, 255, 255)); d.text((362, 1295), "lenke i bio", font=F(34), fill=(230, 220, 255))
        tekst(im, "NESTE LYS 13. DESEMBER", "Følg gjengen. Vi lyser opp desember!", (1 - ee) * 70)
        d = ImageDraw.Draw(im)

    im = g.apply(im)
    return im


def frame(t):
    sc = scene_of(t)
    for i in range(1, 5):
        b = BOUNDS[i]
        if abs(t - b) < .09:
            return Image.blend(render(t, i - 1), render(t, i), (t - (b - .09)) / .18)
    return render(t, sc)


if __name__ == "__main__":
    lag_sprites()
    if "--stills" in sys.argv:
        ts = (1.5, 2.8, 4.2, 5.6, 7.3, 8.4, 9.4, 10.2, 12.0, 14.0, 16.5, 19.0, 21.0)
        sh = Image.new("RGB", (5 * 432, 3 * 768))
        for k, t in enumerate(ts):
            sh.paste(frame(t).resize((432, 768)), ((k % 5) * 432, (k // 5) * 768))
        sh.save("gjeng-reel-stills.png"); print("stills ok")
    else:
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-movflags", "+faststart", "gjeng-reel.mp4"],
                             stdin=subprocess.PIPE)
        for n in range(int(DUR * FPS)):
            p.stdin.write(frame(n / FPS).tobytes())
        p.stdin.close(); p.wait(); print("reel ok")
