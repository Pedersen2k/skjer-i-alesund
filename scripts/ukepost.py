"""To faste Instagram-karuseller for uka, i tillegg til helgeposten:

- «Under hundrelappen» (søndag ettermiddag): det som er gratis eller koster høyst 100 kr hele neste uke, ett per bilde.
- «Uka i Ålesund» (mandag morgen): ett tips for hver dag mandag–torsdag, hver dag i sin farge, pluss de samme
  dagsbildene i historieformat (1080 × 1920).

Bildene lages av scripts/pages.py ved hver publisering og ligger i uka/. Teksten lages av
.github/workflows/ukepost.yml og legges i et issue, så eieren får den på e-post. Alt kommer fra
data/events.json (og data/past.json for dager som er over) og data/kino.json. Ingenting finnes på.

Kjør: python3 scripts/ukepost.py billig|uka [fil]
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path

import pages
import helgepost
from helgepost import font, no_emoji, fit

W, H, STORY = 1080, 1350, 1920
PAD = 72
INK, LIGHT, SOFT, GOLD, CORAL, GREEN, MUTED, CARD, LINE = "#0a171b", "#e8f1ef", "#c9dad8", "#f7c873", "#ff8a6b", "#6cc98a", "#8fa8ab", "#13252d", "#25414a"
DAY_COLOR = ["#5ab7bf", "#f7c873", "#ec78ab", "#f08a4b"]  # mandag–torsdag
DAYS = 4
BILLIG_MAX = 100   # kr
BILLIG_MIN = 3     # færre enn dette: ingen post den uka
BILLIG_SLIDES = 4  # flest egne bilder; resten samles på siste bilde
# Arrangementer for bedrifter og fagfolk står på nettsiden, men er ikke tips til folk flest
INTERN = re.compile(r"fagseminar|næringsliv|nettverkstreff|fagsamling|frokostmøte|for bedrifter", re.I)
CAT_RANK = {"konsert": 0, "standup": 0, "show": 0, "barn": 1, "sport": 1, "quiz": 2, "klubb": 2, "happening": 3}


def week_start(today):
    """Mandagen postene gjelder: denne ukas mandag, men søndag er det neste uke."""
    return today + datetime.timedelta(days=1) if today.weekday() == 6 else today - datetime.timedelta(days=today.weekday())


def load():
    """Kommende arrangementer pluss de som nettopp er over, så bildene for uka ikke endrer seg når mandagen er forbi."""
    events = json.loads((pages.ROOT / "data" / "events.json").read_text())["events"]
    seen = {e["id"] for e in events}
    past = pages.ROOT / "data" / "past.json"
    if past.exists():
        events += [e for e in json.loads(past.read_text()).get("events", []) if e["id"] not in seen]
    kino = pages.ROOT / "data" / "kino.json"
    films = json.loads(kino.read_text()).get("films", []) if kino.exists() else []
    return events, films


def ok(e):
    return e.get("cat") not in pages.SEPARATE and not e.get("soldOut") and not e.get("uncertain") and not INTERN.search(e["title"])


def n_dates(e):
    return 1 + len({s[:10] for s in e.get("moreShows", [])} - {e["date"]})


# --- Utvalg ---

def billig(events, mon):
    """(egne bilder, resten). Egne bilder: de billigste som ikke går hver uke, fylt opp med faste innslag til tre.
    Hvert element er arrangementet på første dag i uka, med «days» = alle dagene. Tomt når uka har for få."""
    by_id = {}
    for o in pages.occurrences([e for e in events if ok(e) and e.get("priceMin") is not None and e["priceMin"] <= BILLIG_MAX],
                               mon, mon + datetime.timedelta(days=6)):
        by_id.setdefault(o["id"], []).append(o)
    full = {e["id"]: e for e in events}
    items = []
    for occ in by_id.values():
        occ.sort(key=lambda o: o["date"])
        e = full[occ[0]["id"]]
        items.append({**occ[0], "days": [o["date"] for o in occ], "fast": e.get("cat") == "quiz" or n_dates(e) >= 4})
    if len(items) < BILLIG_MIN:
        return [], []
    order = lambda o: (o["priceMin"], o["date"], o.get("time") or "")
    once = sorted([o for o in items if not o["fast"]], key=order)
    fast = sorted([o for o in items if o["fast"]], key=order)
    main = once[:BILLIG_SLIDES]
    while len(main) < BILLIG_MIN and fast:
        main.append(fast.pop(0))
    rest = fast + once[BILLIG_SLIDES:]
    when = lambda o: (o["date"], o.get("time") or "")
    return sorted(main, key=when), sorted(rest, key=when)


def kino_tip(films, day):
    """Kveldens kino når dagen ellers er tom: antall filmer og de tre nyeste med forestilling fra kl. 17."""
    iso = day.isoformat()
    today = [(f, sorted(s["start"][11:16] for s in f.get("shows", []) if s["start"].startswith(iso))) for f in films]
    today = [(f, ts) for f, ts in today if ts]
    evening = [(f, [t for t in ts if t >= "17:00"]) for f, ts in today]
    evening = sorted([(f, ts) for f, ts in evening if ts], key=lambda x: x[0].get("premiere") or "", reverse=True)[:3]
    if not evening:
        return None
    return {"kino": True, "count": len(today), "rows": sorted((ts[0], f["title"]) for f, ts in evening)}


def tips(events, films, mon, taken=()):
    """Ett tips per dag mandag–torsdag: helst noe som ikke alt er med i «Under hundrelappen», helst konsert, standup
    eller show, helst en ny kategori og ikke samme arrangement to dager. Tom dag: kino. Ingen kino heller: dagen utelates."""
    out, used_cat, used_id = [], set(), set()
    for i in range(DAYS):
        day = mon + datetime.timedelta(days=i)
        cands = pages.occurrences([e for e in events if ok(e)], day, day)
        if cands:
            cands.sort(key=lambda e: (e["id"] in taken, e["id"] in used_id, CAT_RANK.get(e["cat"], 3), e["cat"] in used_cat,
                                      e.get("priceMin") is None, -(e.get("priceMin") or 0), e.get("time") or ""))
            tip = cands[0]
            used_cat.add(tip["cat"])
            used_id.add(tip["id"])
            also = sorted(cands[1:], key=lambda e: e.get("time") or "")
            out.append({"day": day, "i": i, "tip": tip, "also": also})
        else:
            k = kino_tip(films, day)
            if k:
                out.append({"day": day, "i": i, "tip": k, "also": []})
    return out


def also_text(also, limit=3):
    parts = []
    for e in also[:limit]:
        p = " (gratis)" if e.get("priceMin") == 0 else f" ({e['price']})" if e.get("priceMin") is not None and e["priceMin"] <= BILLIG_MAX else ""
        parts.append(brief(e["title"]) + p)
    if len(also) > limit:
        parts.append(f"+ {len(also) - limit} til")
    return " · ".join(parts)


def brief(title, limit=26):
    """Kort navn til «Også i dag»: lange titler kuttes før «med …» og «hos …», så ikke et halvt navn blir stående."""
    t = no_emoji(title)
    if len(t) > limit:
        t = re.split(r"\s(?:med|hos)\s", t)[0]
    return pages.short_name(t, 30)


def span(a, b):
    mo = lambda d: pages.MO[d.month - 1][:3]
    return f"{a.day}.–{b.day}. {mo(b)}" if a.month == b.month else f"{a.day}. {mo(a)}–{b.day}. {mo(b)}"


def kr(e):
    return "0,-" if e["priceMin"] == 0 else f"{e['priceMin']:g},-"


# --- Tegning ---

def B(size, w=800):
    return font("BricolageGrotesque.ttf", size, weight=w, optical=min(96, size), width=100)


def F(size, w=500):
    return font("Figtree.ttf", size, weight=w)


def M(size, w=700):
    return font("JetBrainsMono.ttf", size, weight=w)


def wrap(dr, text, f, width):
    lines, cur = [], ""
    for word in text.split():
        t = f"{cur} {word}".strip()
        if cur and dr.textlength(t, font=f) > width:
            lines.append(cur)
            cur = word
        else:
            cur = t
    return lines + [cur] if cur else lines


def block(dr, text, mk, sizes, width, max_lines=2):
    """Største skriftstørrelse der teksten får plass på max_lines linjer. Ellers minste størrelse, kortet ned med …"""
    for s in sizes:
        f = mk(s)
        lines = wrap(dr, text, f, width)
        if len(lines) <= max_lines and all(dr.textlength(l, font=f) <= width for l in lines):
            return f, s, balance(dr, lines, f)
    lines = lines[:max_lines - 1] + [fit(dr, " ".join(lines[max_lines - 1:]), f, width)]
    return f, s, lines


def balance(dr, lines, f):
    """To linjer deles der de blir mest like lange, så ikke ett ord blir hengende alene."""
    if len(lines) != 2:
        return lines
    words = " ".join(lines).split()
    splits = [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]
    limit = max(dr.textlength(l, font=f) for l in lines)
    fits = [p for p in splits if max(dr.textlength(x, font=f) for x in p) <= limit]
    return list(min(fits, key=lambda p: abs(dr.textlength(p[0], font=f) - dr.textlength(p[1], font=f)))) if fits else lines


_logo = {}


def logo(size):
    from PIL import Image, ImageDraw
    if size not in _logo:
        im = Image.open(pages.ROOT / "profilbilde.png").convert("RGB").resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
        _logo[size] = (im, mask.resize((size, size), Image.LANCZOS))
    return _logo[size]


def footer(img, dr, bottom, fg, right="", right_fill=None, right_font=None):
    """Logo og adresse nede til venstre, valgfri tekst til høyre. Gir øverste kant tilbake."""
    size = 68
    y = bottom - size
    im, mask = logo(size)
    img.paste(im, (PAD, y), mask)
    dr.text((PAD + size + 20, y + size // 2), "kaskjerda.no", font=B(34, 700), fill=fg, anchor="lm")
    if right:
        dr.text((W - PAD, y + size // 2), right, font=right_font or M(30), fill=right_fill or fg, anchor="rm")
    return y


def pill(dr, x, y, text):
    f = F(32, 700)
    w = dr.textlength(text, font=f)
    dr.rounded_rectangle((x, y, x + w + 48, y + 62), radius=31, fill="#3a2a10", outline="#6b4c17", width=2)
    dr.text((x + 24, y + 31), text, font=f, fill="#ffb547", anchor="lm")
    return 62


def few(e):
    return e.get("few") and not e.get("soldOut") and pages.few_ok(e, datetime.date.fromisoformat(e["date"]))


def stack(items, y):
    """items: (høyde, luft etterpå, tegnefunksjon(y)). Tegner dem under hverandre fra y."""
    for h, gap, draw in items:
        draw(y)
        y += h + gap


def stack_h(items):
    return sum(h + gap for h, gap, _ in items) - (items[-1][1] if items else 0)


def text_item(dr, lines, f, size, fill, x, gap, lh=1.04):
    step = round(size * lh)

    def draw(y):
        for i, l in enumerate(lines):
            dr.text((x, y + i * step), l, font=f, fill=fill)
    return (step * len(lines), gap, draw)


def new(bg, h=H):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, h), bg)
    return img, ImageDraw.Draw(img)


def uka_cover(days, mon, path):
    img, dr = new(INK)
    dr.text((PAD, PAD), f"UKE {mon.isocalendar()[1]} · {span(mon, mon + datetime.timedelta(days=DAYS - 1)).upper()}", font=M(34), fill=GOLD)
    im, mask = logo(76)
    img.paste(im, (W - PAD - 76, PAD - 16), mask)
    f = B(150)
    dr.text((PAD - 6, 150), "Uka i", font=f, fill=LIGHT)
    dr.text((PAD - 6, 150 + 142), "Ålesund", font=f, fill=LIGHT)
    for i, l in enumerate(wrap(dr, "Mandag til torsdag: ett tips for hver dag →", F(44), W - 2 * PAD)):
        dr.text((PAD, 478 + i * 54), l, font=F(44), fill=SOFT)
    row = 172
    y = H - row * len(days)
    for d in days:
        dr.rectangle((0, y, W, y + row), fill=DAY_COLOR[d["i"]])
        dr.text((PAD, y + row // 2), pages.WD_SHORT[d["i"]], font=B(76), fill=INK, anchor="lm")
        t = d["tip"]
        label = "Kinokveld på ODEON" if t.get("kino") else pages.short_name(no_emoji(t["title"]), 40) + (" · gratis" if t.get("priceMin") == 0 else "")
        ft = F(46, 700)
        dr.text((PAD + 232, y + row // 2), fit(dr, label, ft, W - 2 * PAD - 232), font=ft, fill=INK, anchor="lm")
        y += row
    img.save(path, optimize=True)


def uka_day(d, n, total, path, h=H):
    """Dagsbildet: stor ukedag på dagens farge, tipset i et mørkt kort. h=STORY gir historieformat med luft til Instagrams knapper."""
    story = h != H
    color = DAY_COLOR[d["i"]]
    img, dr = new(color, h)
    top = 250 if story else 64
    day = d["day"]
    dr.text((PAD, top), f"{day.day}. {pages.MO[day.month - 1].upper()}", font=M(34), fill=INK)
    dr.text((PAD - 10, top + 30), pages.WD_SHORT[d["i"]], font=B(280), fill=INK)
    head_end = top + 30 + 290
    foot = footer(img, dr, h - (270 if story else 56), INK, "" if story else f"{n} / {total}")

    also = also_text(d["also"])
    also_lines = wrap(dr, also, F(36, 600), W - 2 * PAD)[:2] if also else []
    also_h = (44 + 46 * len(also_lines)) if also_lines else 0
    if also_lines:
        ay = foot - 36 - also_h
        dr.text((PAD, ay), "OGSÅ I DAG", font=M(30), fill=INK)
        for i, l in enumerate(also_lines):
            dr.text((PAD, ay + 44 + i * 46), l, font=F(36, 600), fill=INK)
    elif d["tip"].get("kino"):
        also_h = 44 + 46
        ay = foot - 36 - also_h
        dr.text((PAD, ay), "HELE PROGRAMMET", font=M(30), fill=INK)
        dr.text((PAD, ay + 44), "kaskjerda.no/kino", font=F(36, 600), fill=INK)

    inner, x = W - 2 * PAD - 104, PAD + 52
    t = d["tip"]
    items = [(34, 26, lambda y: dr.text((x, y), "DAGENS TIPS", font=M(32), fill=color))]
    if t.get("kino"):
        items.append(text_item(dr, ["Kinokveld"], B(96), 96, LIGHT, x, 20))
        items.append(text_item(dr, [f"{t['count']} filmer på ODEON Ålesund i dag"], F(40), 40, SOFT, x, 30, 1.25))
        for time, title in t["rows"]:
            def row(y, time=time, title=title):
                dr.text((x, y), time, font=M(42), fill=GOLD)
                dr.text((x + 178, y - 2), fit(dr, title, F(44, 700), inner - 178), font=F(44, 700), fill=LIGHT)
            items.append((50, 14, row))
    else:
        f, s, lines = block(dr, no_emoji(t["title"]), B, (96, 88, 78, 68), inner)
        items.append(text_item(dr, lines, f, s, LIGHT, x, 26))
        if t.get("time"):
            items.append(text_item(dr, [f"kl. {t['time']}"], M(50), 50, GOLD, x, 22, 1.2))
        price = pages.price_text(t)
        fm = F(40)

        def meta(y, price=price):
            free = price == "Gratis"
            tail = " · " + (price if price != "Pris hos arrangør" else "pris hos arrangør")
            venue = fit(dr, t["venue"], fm, inner - dr.textlength(tail, font=F(40, 700)))
            dr.text((x, y), venue, font=fm, fill=SOFT)
            vx = x + dr.textlength(venue, font=fm)
            if free:
                dr.text((vx, y), " · ", font=fm, fill=SOFT)
                dr.text((vx + dr.textlength(" · ", font=fm), y), "Gratis", font=F(40, 700), fill=GREEN)
            else:
                dr.text((vx, y), tail, font=fm, fill=SOFT)
        items.append((50, 26, meta))
        if few(t):
            items.append((62, 0, lambda y: pill(dr, x, y, "Få billetter igjen")))
    ch = stack_h(items) + 100
    lo, hi = head_end + 24, foot - 36 - also_h - (36 if also_h else 0)
    cy = max(lo, lo + (hi - lo - ch) // 2)
    dr.rounded_rectangle((PAD, cy, W - PAD, cy + ch), radius=36, fill=INK)
    stack(items, cy + 52)
    img.save(path, optimize=True)


def billig_cover(main, rest, mon, path):
    img, dr = new(GOLD)
    sun = mon + datetime.timedelta(days=6)
    dr.text((PAD, PAD), f"UKA I ÅLESUND · {span(mon, sun).upper()}", font=M(34), fill=INK)
    allv = main + rest
    n, g = len(allv), sum(1 for e in allv if e["priceMin"] == 0)
    sub = f"{n} ting å finne på i uke {mon.isocalendar()[1]}. " + (
        "Alt er gratis." if g == n else f"{g} er gratis." if g > 1 else "Én er gratis." if g == 1 else f"Fra {min(e['priceMin'] for e in allv):g} kr.")
    foot = footer(img, dr, H - 56, INK, "Sveip →", right_font=F(34, 700))
    f, s, lines = block(dr, "Under hundrelappen", B, (104,), W - 2 * PAD)
    sub_lines = wrap(dr, sub, F(44), W - 2 * PAD)
    y = foot - 64 - 54 * len(sub_lines)
    for i, l in enumerate(sub_lines):
        dr.text((PAD, y + i * 54), l, font=F(44), fill=INK)
    y -= 24 + round(s * 1.0) * len(lines)
    for i, l in enumerate(lines):
        dr.text((PAD - 4, y + i * s), l, font=f, fill=INK)
    dr.text((PAD - 14, y - 356), "100,-", font=B(330), fill=INK)
    img.save(path, optimize=True)


def day_label(e):
    ds = [datetime.date.fromisoformat(d) for d in e["days"]]
    d = ds[0]
    more = f" · OGSÅ {', '.join(pages.WD_SHORT[x.weekday()].upper() for x in ds[1:3])}" if len(ds) > 1 else ""
    return f"{pages.WD[d.weekday()].upper()} {d.day}. {pages.MO[d.month - 1][:3].upper()}{more}"


def cta(dr, y):
    dr.rounded_rectangle((PAD, y, W - PAD, y + 96), radius=24, fill=CARD, outline=LINE, width=2)
    f = F(36, 600)
    a = "Alt som skjer, med pris: "
    dr.text((PAD + 32, y + 48), a, font=f, fill=LIGHT, anchor="lm")
    dr.text((PAD + 32 + dr.textlength(a, font=f), y + 48), "kaskjerda.no", font=f, fill=GOLD, anchor="lm")


def billig_slide(e, n, total, last, path):
    img, dr = new(INK)
    dr.text((PAD, PAD), day_label(e), font=M(34), fill=MUTED)
    foot = footer(img, dr, H - 56, LIGHT, f"{n} / {total}", MUTED)
    bottom = foot - 36
    if last:
        cta(dr, foot - 28 - 96)
        bottom = foot - 28 - 96 - 36
    inner = W - 2 * PAD
    items = [(306, 48, lambda y: dr.text((PAD - 14, y - 50), kr(e), font=B(360), fill=GOLD))]
    title = no_emoji(e["title"])
    f, s, lines = block(dr, title, B, (100, 88, 76), inner)
    if lines[-1].endswith("…"):  # lange titler får tre linjer i stedet for å kuttes
        f, s, lines = block(dr, title, B, (68, 60), inner, 3)
    items.append(text_item(dr, lines, f, s, LIGHT, PAD, 24))
    if e.get("time"):
        items.append(text_item(dr, [f"kl. {e['time']}"], M(50), 50, CORAL, PAD, 20, 1.2))
    items.append(text_item(dr, wrap(dr, e["venue"], F(42), inner)[:2], F(42), 42, SOFT, PAD, 26, 1.25))
    if few(e):
        items.append((62, 0, lambda y: pill(dr, PAD, y, "Gratis, men få billetter igjen" if e["priceMin"] == 0 else "Få billetter igjen")))
    top = PAD + 70
    stack(items, max(top, top + (bottom - top - stack_h(items)) // 2))
    img.save(path, optimize=True)


def billig_rest(rest, n, total, path, limit=5):
    img, dr = new(INK)
    dr.text((PAD, PAD), "FLERE DENNE UKA", font=M(34), fill=MUTED)
    foot = footer(img, dr, H - 56, LIGHT, f"{n} / {total}", MUTED)
    cta(dr, foot - 28 - 96)
    dr.text((PAD - 4, PAD + 62), "Også under", font=B(92), fill=LIGHT)
    dr.text((PAD - 4, PAD + 62 + 90), "hundrelappen", font=B(92), fill=LIGHT)
    y, inner = PAD + 300, W - 2 * PAD - 190
    for e in rest[:limit]:
        d = datetime.date.fromisoformat(e["date"])
        dr.text((PAD, y + 6), kr(e), font=M(44), fill=GOLD)
        dr.text((PAD + 190, y), fit(dr, no_emoji(e["title"]), B(50), inner), font=B(50), fill=LIGHT)
        sub = " · ".join(p for p in [pages.WD_SHORT[d.weekday()].lower() + (f" {e['time']}" if e.get("time") else ""), e["venue"]] if p)
        dr.text((PAD + 190, y + 62), fit(dr, sub, F(33), inner), font=F(33), fill=SOFT)
        y += 134
    if len(rest) > limit:
        dr.text((PAD + 190, y + 4), f"+ {len(rest) - limit} til på nettsiden", font=F(34, 600), fill=GOLD)
    img.save(path, optimize=True)


# --- Filnavn, bilder og tekst ---

def uka_names(days):
    return [f"uka-{i}.png" for i in range(1, len(days) + 2)] if days else []


def story_names(days):
    return [f"historie-{pages.WD_SHORT[d['i']].lower()}.png" for d in days]


def billig_names(main, rest):
    return [f"billig-{i}.png" for i in range(1, len(main) + 2 + bool(rest))] if main else []


def plan(today):
    events, films = load()
    mon = week_start(today)
    main, rest = billig(events, mon)
    days = tips(events, films, mon, {e["id"] for e in main + rest})
    return mon, main, rest, days


def render_all(today, folder):
    """Lager alle bildene i folder (uka/). Kalles fra pages.py ved hver publisering."""
    mon, main, rest, days = plan(today)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.png"):
        old.unlink()
    if days:
        names = uka_names(days)
        uka_cover(days, mon, folder / names[0])
        for d, name, sname in zip(days, names[1:], story_names(days)):
            uka_day(d, names.index(name) + 1, len(names), folder / name)
            uka_day(d, 0, 0, folder / sname, STORY)
    if main:
        names = billig_names(main, rest)
        billig_cover(main, rest, mon, folder / names[0])
        for i, e in enumerate(main):
            billig_slide(e, i + 2, len(names), not rest and i == len(main) - 1, folder / names[i + 1])
        if rest:
            billig_rest(rest, len(names), len(names), folder / names[-1])
    return uka_names(days) + story_names(days) + billig_names(main, rest)


def img_md(names, alt, v):
    return "\n\n".join(f"![{alt}, bilde {i}]({pages.BASE}uka/{n}?v={v})" for i, n in enumerate(names, 1))


def ev_line(e, day=True):
    d = datetime.date.fromisoformat(e["date"])
    price = pages.price_text(e)
    return (f"{pages.WD[d.weekday()].capitalize()}: " if day else "") + f"{no_emoji(e['title'])}, {e['venue']}" + (
        f" kl. {e['time']}" if e.get("time") else "") + (f" – {price.lower()}" if price != "Pris hos arrangør" else "")


def billig_body(mon, main, rest, v):
    sun = mon + datetime.timedelta(days=6)
    names = billig_names(main, rest)
    evs = main + rest
    caption = "\n".join(
        [f"Under hundrelappen i Ålesund denne uka 💸", f"Gratis og billig, {pages.range_text(mon, sun)}:", ""]
        + [f"▪️ {ev_line(e)}" for e in sorted(evs, key=lambda e: (e['date'], e.get('time') or ''))]
        + ["", "🎟️ Alt som skjer, med priser og billettlenker: kaskjerda.no (lenke i bio)", "💾 Lagre innlegget og send det til en venn!", "",
           " ".join(dict.fromkeys(helgepost.hashtags(evs, mon, sun) + ["#gratis", "#billig"]))])
    return f"""Her er ukas «Under hundrelappen»: {len(evs)} arrangementer som er gratis eller koster høyst {BILLIG_MAX} kr. Post den søndag kveld.

### Bilder (Instagram-karusell, 1080 × 1350)
Det er {len(names)} bilder. Trykk på hvert bilde og lagre det, og legg dem ut sammen som karusell.

{img_md(names, "Under hundrelappen", v)}

### Bildetekst
```text
{caption}
```

Tips: del innlegget i historien etterpå med lenkeklistremerke til kaskjerda.no. Sjekk gjerne prisene før du poster; programmet hentes automatisk og kan endre seg. Dette issuet lukkes når neste ukes post kommer.
"""


def uka_body(mon, days, v):
    names, stories = uka_names(days), story_names(days)
    lines = []
    for d in days:
        wd = pages.WD[d["i"]].upper()
        t = d["tip"]
        lines.append(f"{wd}: " + (f"Kinokveld på ODEON, {t['count']} filmer (" + ", ".join(f"{title} {time}" for time, title in t["rows"]) + ")"
                                  if t.get("kino") else ev_line(t, day=False)))
    evs = [d["tip"] for d in days if not d["tip"].get("kino")]
    thu = mon + datetime.timedelta(days=DAYS - 1)
    caption = "\n".join(
        ["Uka i Ålesund, mandag til torsdag 🌊", "Ett tips for hver dag:", ""] + lines
        + ["", "🎟️ Hele programmet med priser og billettlenker: kaskjerda.no (lenke i bio)", "💾 Lagre innlegget, så har du uka klar!", "",
           " ".join(helgepost.hashtags(evs, mon, thu))])
    story_list = "\n\n".join(f"**{pages.WD[d['i']].capitalize()}**\n\n![Historie {pages.WD[d['i']]}]({pages.BASE}uka/{n}?v={v})" for d, n in zip(days, stories))
    return f"""Her er «Uka i Ålesund» for {pages.range_text(mon, thu)}: ett tips for hver dag. Post karusellen mandag.

### Bilder (Instagram-karusell, 1080 × 1350)
Det er {len(names)} bilder. Trykk på hvert bilde og lagre det, og legg dem ut sammen som karusell.

{img_md(names, "Uka i Ålesund", v)}

### Bildetekst
```text
{caption}
```

### Dagens bilde til historien (1080 × 1920)
Legg ut dagens bilde i historien om morgenen den dagen, med lenkeklistremerke til kaskjerda.no.

{story_list}

Tipsene er valgt automatisk (ikke julebord, utsolgte eller arrangementer for bedrifter, og helst noe annet enn det som var med i «Under hundrelappen»). Bytt gjerne ut et bilde hvis du vet om noe bedre. Dette issuet lukkes når neste ukes post kommer.
"""


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else ""
    if kind not in ("billig", "uka"):
        sys.exit("Bruk: python3 scripts/ukepost.py billig|uka [fil]")
    today = datetime.datetime.now(pages.TZ).date()
    mon, main_, rest, days = plan(today)
    v = today.isoformat()
    if kind == "billig":
        title = f"Under hundrelappen: {pages.range_text(mon, mon + datetime.timedelta(days=6))}"
        body = billig_body(mon, main_, rest, v) if main_ else ""
    else:
        title = f"Uka i Ålesund: {pages.range_text(mon, mon + datetime.timedelta(days=DAYS - 1))}"
        body = uka_body(mon, days, v) if days else ""
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(body)
    else:
        print(title + "\n\n" + (body or "(ingen post denne uka)"))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"title={title}\nskip={'false' if body else 'true'}\n")


if __name__ == "__main__":
    main()
