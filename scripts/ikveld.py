"""«I kveld»: én Instagram-historie hver dag (1080 × 1920).

Kveldens tips vises helt (tittel, tid, sted, pris). Resten av kvelden står under som uskarpe rader med
«+ N til i kveld», og en pil peker ned til plassen der lenkemerket til kaskjerda.no/i-dag skal stå.
Hver ukedag har sin fargeovergang, så historien blir gjenkjennelig. Forslagene den ble valgt fra (variant G)
ligger i docs/ikveld-historie/.

Bildet lages av scripts/pages.py ved hver publisering (i-kveld/historie.png). Teksten lages av
.github/workflows/ikveld.yml hver morgen og legges i et issue, så eieren får det på e-post.
Alt kommer fra data/events.json (og data/kino.json når kvelden er tom). Ingenting finnes på.

Kjør: python3 scripts/ikveld.py [fil]            (teksten til issuet)
      python3 scripts/ikveld.py --bilde fil.png [ÅÅÅÅ-MM-DD]
"""
import datetime
import os
import re
import sys
from pathlib import Path

import pages
import ukepost as u
from ukepost import B, F, M, PAD, W, block, fit, no_emoji, logo

H = 1920
EVENING = "16:00"   # det som starter før dette, er ikke «i kveld»
ROWS = 3            # uskarpe rader under tipset
RECENT = 3          # samme tips gjentas ikke før etter så mange dager
LINK = "kaskjerda.no/i-dag/?ref=ig-story"
# Fargeovergang (øverst til venstre → nederst til høyre) og fargen på «+ N til»-pillen for hver ukedag.
# Mandag–torsdag starter i fargene fra «Uka i Ålesund».
DAY_STYLE = [
    (["#1fb5b5", "#2a6fdb", "#6a2bd9"], "#ffd23f"),  # mandag: blågrønn
    (["#f7b733", "#f0743e", "#c81d63"], "#ffffff"),  # tirsdag: gull
    (["#ec78ab", "#b23ad9", "#4b1fa8"], "#ffd23f"),  # onsdag: rosa
    (["#f08a4b", "#e0434f", "#7a1f5c"], "#ffd23f"),  # torsdag: oransje
    (["#ff3d7f", "#8a2be2", "#1b1f6b"], "#ffd23f"),  # fredag: magenta
    (["#3fd18a", "#0f9fa8", "#1d4fbf"], "#ffd23f"),  # lørdag: grønn
    (["#a78bfa", "#6366f1", "#2e2a7a"], "#ffd23f"),  # søndag: lilla
]
INK = "#0a171b"
LABEL = {"konsert": "KONSERT", "standup": "STANDUP", "show": "SHOW", "happening": "HAPPENING", "quiz": "QUIZ",
         "barn": "FOR BARN", "klubb": "KLUBB", "sport": "SPORT"}
# Verifiserte Instagram-kontoer (se HANDOFF.md), til tagging i historien
HANDLES = [("terminalen", "@terminalen_byscene"), ("løvenvold", "@lovenvoldtheater"), ("dampsentralen", "@dampsentralen"),
           ("liv & røre", "@livogrore_moa"), ("o'connor", "@oconnors_alesund"), ("bryt", "@bryt_tapas"),
           ("parken", "@parken_kulturhus"), ("sobra", "@sobrascene"), ("color line stadion", "@aalesundsfk")]


def tm(e):
    m = re.search(r"\d{1,2}:\d{2}", e.get("time") or "")
    return m.group(0).zfill(5) if m else ""


def pick(day, events, films, avoid=()):
    ev = [e for e in pages.occurrences([e for e in events if u.ok(e)], day, day) if not tm(e) or tm(e) >= EVENING]
    if not ev:
        k = u.kino_tip(films, day)
        return (k, []) if k else (None, [])
    tip = min(ev, key=lambda e: (e["id"] in avoid, u.CAT_RANK.get(e["cat"], 3), e.get("priceMin") is None, -(e.get("priceMin") or 0), tm(e)))
    return tip, sorted((e for e in ev if e is not tip), key=tm)


def plan(day):
    """Kveldens tips og resten av kvelden. Helst ikke samme tips som de tre siste dagene (regnes ut på nytt,
    så valget er det samme hele dagen). Tom kveld: kino i stedet. Ingen kino heller: ingen historie."""
    events, films = u.load()
    used = []
    for back in range(RECENT, 0, -1):
        t, _ = pick(day - datetime.timedelta(days=back), events, films, used[-RECENT:])
        if t and not t.get("kino"):
            used.append(t["id"])
    return pick(day, events, films, used[-RECENT:])


def handle(e):
    v = (e.get("venue") or "").lower()
    return next((h for k, h in HANDLES if k in v), "")


# --- Tegning ---

def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(colors):
    """Diagonal fargeovergang. Uten numpy: bygges i lav oppløsning og skaleres opp (glatt nok)."""
    from PIL import Image
    w, h = 54, 96
    stops = [hexc(c) for c in colors]
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = min(1, max(0, 0.82 * y / (h - 1) - 0.25 * x / (w - 1) + 0.2))
            i = min(len(stops) - 2, int(t * (len(stops) - 1)))
            k = t * (len(stops) - 1) - i
            px[x, y] = tuple(round(a + (b - a) * k) for a, b in zip(stops[i], stops[i + 1]))
    return img.resize((W, H), Image.BICUBIC)


def glow_spot(img, xy, r, color, alpha=140):
    from PIL import Image, ImageDraw, ImageFilter
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse((xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r), fill=hexc(color) + (alpha,))
    return Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(160))).convert("RGB")


def price(e):
    p = pages.price_text(e)
    return "pris hos arrangør" if p == "Pris hos arrangør" else p


def render(day, path):
    """Lager historien for day i path. Gir False når det ikke er noe å vise."""
    from PIL import Image, ImageDraw, ImageFilter
    tip, rest = plan(day)
    if not tip:
        return False
    colors, accent = DAY_STYLE[day.weekday()]
    img = glow_spot(gradient(colors), (950, 280), 260, "#ffffff", 70)
    dr = ImageDraw.Draw(img)
    dr.text((PAD, 250), f"{pages.WD[day.weekday()].upper()} {day.day}. {pages.MO[day.month - 1].upper()}", font=M(34), fill="#ffffff")
    dr.text((PAD - 8, 290), "I kveld", font=B(190), fill="#ffffff")

    # Tipskortet
    x, inner, top = PAD + 44, W - 2 * PAD - 88, 540
    mark = colors[-1]
    if tip.get("kino"):
        lines, f, s = ["Kinokveld på ODEON"], B(76), 76
        sub = [(t, title) for t, title in tip["rows"]]
    else:
        f, s, lines = block(dr, no_emoji(tip["title"]), B, (88, 78, 68, 60), inner, 2)
        sub = []
    step = round(s * 1.02)
    body = 70 + len(lines) * step + 20 + (len(sub) * 58 if sub else 66 + 56) + 50
    dr.rounded_rectangle((PAD, top, W - PAD, top + body), radius=40, fill="#ffffff")
    dr.text((x, top + 45), "KVELDENS TIPS" + ("" if tip.get("kino") or tip["cat"] not in LABEL else " · " + LABEL[tip["cat"]]),
            font=M(32), fill=mark)
    y = top + 100
    for l in lines:
        dr.text((x - 4, y), l, font=f, fill=INK)
        y += step
    y += 20
    if sub:
        for t, title in sub:
            dr.text((x, y), t, font=M(42), fill=colors[1])
            dr.text((x + 170, y), fit(dr, title, F(42, 700), inner - 170), font=F(42, 700), fill=INK)
            y += 58
    else:
        if tm(tip):
            dr.text((x, y), f"kl. {tm(tip)}", font=M(52), fill=colors[1])
        y += 66
        venue_price = f"{tip['venue']} · {price(tip)}"
        dr.text((x, y), fit(dr, venue_price, F(40, 600), inner), font=F(40, 600), fill=INK)

    # Resten av kvelden, uskarpt
    ry = top + body + 40
    if rest:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for i, e in enumerate(rest[:ROWS]):
            yy = ry + i * 130
            d.rounded_rectangle((PAD, yy, W - PAD, yy + 110), radius=30, fill=(255, 255, 255, 70))
            d.text((PAD + 40, yy + 55), tm(e), font=M(44), fill=(255, 255, 255, 255), anchor="lm")
            d.text((PAD + 200, yy + 55), fit(d, no_emoji(e["title"]), F(44, 700), W - 2 * PAD - 240), font=F(44, 700),
                   fill=(255, 255, 255, 255), anchor="lm")
        img = Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(9))).convert("RGB")
        dr = ImageDraw.Draw(img)
        label = f"+ {len(rest)} til i kveld"
        fl = B(64, 800)
        lw = dr.textlength(label, font=fl)
        cy = ry + 65 * min(ROWS, len(rest)) - 10
        dr.rounded_rectangle(((W - lw) // 2 - 44, cy - 56, (W + lw) // 2 + 44, cy + 56), radius=56, fill=accent)
        dr.text((W // 2, cy), label, font=fl, fill=INK, anchor="mm")
        end = ry + 130 * min(ROWS, len(rest))
    else:
        dr.text((W // 2, ry + 60), "Hele programmet", font=B(64, 800), fill="#ffffff", anchor="mm")
        end = ry + 120

    # Pil ned til lenkemerket (plassen under pila er tom med vilje), logo nederst
    cx, ay = W // 2, min(1400, end + 30)
    dr.line((cx, ay, cx, ay + 60), fill="#ffffff", width=8)
    dr.line((cx - 26, ay + 36, cx, ay + 64), fill="#ffffff", width=8)
    dr.line((cx + 26, ay + 36, cx, ay + 64), fill="#ffffff", width=8)
    im, mask = logo(64)
    img.paste(im, (PAD, 1660), mask)
    dr.text((PAD + 84, 1692), "kaskjerda.no", font=B(34, 700), fill="#ffffff", anchor="lm")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    return True


def render_all(today, folder):
    """Kalles fra pages.py ved hver publisering: i-kveld/historie.png for i dag."""
    path = folder / "historie.png"
    if path.exists():
        path.unlink()
    return render(today, path)


# --- Teksten til issuet ---

def ev_line(e):
    return f"{tm(e) or 'hele dagen'} {no_emoji(e['title'])}, {e['venue']} – {price(e)}"


def body(day, v):
    tip, rest = plan(day)
    if not tip:
        return ""
    wd = pages.WD[day.weekday()]
    if tip.get("kino"):
        tip_text = "Kinokveld på ODEON: " + ", ".join(f"{title} {t}" for t, title in tip["rows"])
        tags = ""
    else:
        tip_text = ev_line(tip)
        h = handle(tip)
        tags = f"\n- **Tagg arrangøren:** {h} (da deler de den gjerne videre)" if h else ""
    rest_text = "\n".join(f"- {ev_line(e)}" for e in rest) or "- (ingenting annet i kveld)"
    return f"""Dagens «I kveld»-historie for {wd} {day.day}. {pages.MO[day.month - 1]}.

![I kveld, {wd}]({pages.BASE}i-kveld/historie.png?v={v})

### Slik legger du den ut
1. Trykk på bildet og lagre det.
2. Legg det ut i historien på Instagram (og Facebook, om du vil). Helst før kl. 16, mens folk planlegger kvelden.
3. **Lenkemerke** under pila: `https://{LINK}`{tags}

### Kveldens tips
{tip_text}

### Resten av kvelden (uskarpt på bildet)
{rest_text}

Tipset er valgt automatisk (ikke julebord, utsolgte, usikre eller arrangementer for bedrifter; helst konsert, standup eller show). Sjekk gjerne hos arrangøren før du poster; programmet kan endre seg. `?ref=ig-story` i lenka gjør at besøkene vises som «ig-story» i GoatCounter. Dette issuet lukkes når morgendagens historie kommer.
"""


def main():
    today = datetime.datetime.now(pages.TZ).date()
    if len(sys.argv) > 2 and sys.argv[1] == "--bilde":
        day = datetime.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else today
        print("lagret" if render(day, Path(sys.argv[2])) else "ingenting i kveld")
        return
    title = f"I kveld: {pages.WD[today.weekday()]} {today.day}. {pages.MO[today.month - 1]}"
    text = body(today, today.isoformat())
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text)
    else:
        print(title + "\n\n" + (text or "(ingen historie i dag)"))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"title={title}\nskip={'false' if text else 'true'}\n")


if __name__ == "__main__":
    main()
