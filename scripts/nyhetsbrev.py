"""Ukentlig nyhetsbrev: ett personlig brev per kombinasjon av temaer (design E: en seksjon per tema).

Brevet bygges av data/events.json, samme program som siden. E-postsikker HTML (tabeller og inline-stiler, 600 px) og
en ren tekstversjon. Uten temaer får leseren «alt»: arrangementene dag for dag.

Kjør: python3 scripts/nyhetsbrev.py [--themes standup,konsert] [--out mappe]   (skriver brev.html og brev.txt)
MailerLite-kodene {$unsubscribe} og {$url} fylles ut av tjenesten når brevet sendes.
"""
import argparse
import datetime
import json
from html import escape
from pathlib import Path

import pages

ROOT = Path(__file__).resolve().parent.parent
TZ = pages.TZ
DAYS_AHEAD = 10          # brevet sendes torsdag og dekker til og med søndagen uka etter
PER_THEME = 4            # så mange arrangementer per tema vises i brevet
ALL_MAX = 10             # og så mange når leseren ikke har valgt tema
UNSUB = "{$unsubscribe}"
COLORS = {"konsert": "#1f6f78", "standup": "#b5531c", "show": "#6a4fa3", "barn": "#2f8a4c", "klubb": "#a83167",
          "happening": "#8a6d12", "quiz": "#7a4fb0", "sport": "#2b5fa8"}
EMOJI = {"konsert": "🎵", "standup": "🎤", "show": "🎭", "barn": "🧸", "klubb": "🪩", "happening": "✨", "quiz": "❓", "sport": "⚽"}
FONT = "Arial,Helvetica,sans-serif"
MONO = "'Courier New',monospace"


def day_short(date):
    d = datetime.date.fromisoformat(date)
    return f"{d.day}. {pages.MO[d.month - 1][:3]}"


def page_url(e):
    return pages.BASE + f"arrangement/{e['id']}/"


def pick(events, today, theme=None):
    """Arrangementene i vinduet (én gang per arrangement, første dag), valgfritt bare ett tema."""
    end = today + datetime.timedelta(days=DAYS_AHEAD)
    seen, out = set(), []
    for e in pages.occurrences(events, today, end):
        if (theme and e["cat"] != theme) or e["id"] in seen:
            continue
        seen.add(e["id"])
        out.append(e)
    return out


def total_ahead(events, theme, today):
    return len({e["id"] for e in events if e["cat"] == theme and e["date"] >= today.isoformat()})


def row_html(e):
    price = pages.price_text(e)
    when = day_short(e["date"]) + (f" · {e['time']}" if e.get("time") else "")
    extra = "" if not e.get("moreShows") else " · flere datoer"
    return (f'<tr><td style="padding:9px 0;border-bottom:1px solid #ddd6c6;font:500 12px {MONO};color:#a8451f;width:62px;vertical-align:top">{escape(day_short(e["date"]))}</td>'
            f'<td style="padding:9px 8px 9px 0;border-bottom:1px solid #ddd6c6;font:14px/1.35 {FONT};color:#1b2b30;vertical-align:top">'
            f'<a href="{escape(page_url(e))}" style="color:#1b2b30;font-weight:bold;text-decoration:underline">{escape(e["title"])}</a><br>'
            f'<span style="font-size:12.5px;color:#5a7177">{escape(e["venue"])}{(" · " + e["time"]) if e.get("time") else ""}{extra}</span></td>'
            f'<td style="padding:9px 0;border-bottom:1px solid #ddd6c6;font:500 12px {MONO};color:#1b2b30;text-align:right;white-space:nowrap;vertical-align:top">{escape(price)}</td></tr>')


def section_html(theme, evs, more):
    color = COLORS[theme]
    head = (f'<tr><td colspan="3" style="padding:22px 0 4px;font:bold 17px {FONT};color:{color};border-bottom:2px solid {color}">'
            f'{EMOJI[theme]} {escape(pages.CAT_LABEL[theme])}</td></tr>')
    if not evs:
        return head + f'<tr><td colspan="3" style="padding:10px 0;font:14px {FONT};color:#5a7177">Ingenting nytt de neste dagene.</td></tr>' + _more(theme, more)
    return head + "".join(row_html(e) for e in evs) + _more(theme, more)


def _more(theme, n):
    if n <= 0:
        return ""
    url = pages.BASE + pages.CATS[theme][0] + "/"
    return (f'<tr><td colspan="3" style="padding:8px 0 0;font:bold 13px {FONT}"><a href="{url}" style="color:#e0583a;text-decoration:none">'
            f'+ {n} til i {escape(pages.CAT_LABEL[theme].lower())} fremover →</a></td></tr>')


def build(themes, events, today):
    """Gir (emne, html, tekst) for en leser som har valgt disse temaene (tom liste = alt)."""
    themes = [t for t in themes if t in pages.CATS]
    end = today + datetime.timedelta(days=DAYS_AHEAD)
    span = f"{day_short(today.isoformat())} – {day_short(end.isoformat())}"
    sections, text = [], []
    if themes:
        label = " · ".join(pages.CAT_LABEL[t].upper() for t in themes)
        intro = "Her er det du har valgt:"
        for t in themes:
            evs = pick(events, today, t)
            shown = evs[:PER_THEME]
            more = total_ahead(events, t, today) - len(shown)
            sections.append(section_html(t, shown, more))
            text.append(f"{pages.CAT_LABEL[t].upper()}\n" + ("\n".join(_line(e) for e in shown) or "Ingenting nytt de neste dagene.")
                        + (f"\n+ {more} til: {pages.BASE}{pages.CATS[t][0]}/" if more > 0 else ""))
        subject = "Helgetips: " + " og ".join(pages.CAT_LABEL[t].lower() for t in themes[:2]) + (" m.m." if len(themes) > 2 else "") + f" i Ålesund ({span})"
    else:
        label = "ALT SOM SKJER"
        intro = "Dette skjer i Ålesund de neste dagene:"
        evs = pick(events, today)[:ALL_MAX]
        day = None
        rows = ""
        for e in evs:
            if e["date"] != day:
                day = e["date"]
                d = datetime.date.fromisoformat(day)
                rows += (f'<tr><td colspan="3" style="padding:16px 0 4px;font:bold 13px {MONO};color:#a8451f;border-bottom:2px solid #1b2b30">'
                         f'{pages.WD[d.weekday()].upper()} {d.day}. {pages.MO[d.month - 1][:3].upper()}</td></tr>')
            rows += row_html(e)
        sections.append(rows)
        text.append("\n".join(_line(e) for e in evs) + f"\nHele programmet: {pages.BASE}")
        subject = f"Dette skjer i Ålesund ({span})"
    html = f"""<!doctype html>
<html lang="nb"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(subject)}</title></head>
<body style="margin:0;padding:0;background:#d9d5cb">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#d9d5cb"><tr><td align="center" style="padding:18px 8px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#f4f1ea">
<tr><td style="background:#10282f;padding:20px 24px">
  <div style="font:bold 24px {FONT};color:#ffffff;letter-spacing:-0.5px">Hei! Her er <span style="color:#ff8a6b">ditt</span> brev</div>
  <div style="font:12px {MONO};color:#f7c873;letter-spacing:1px;margin-top:6px">{escape(label)}</div></td></tr>
<tr><td style="padding:6px 24px 8px">
  <p style="font:15px/1.5 {FONT};color:#1b2b30;margin:14px 0 0">{escape(intro)}</p>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{"".join(sections)}</table>
  <p style="font:13px/1.5 {FONT};color:#5a7177;margin:22px 0 0">Vil du ha noe annet? <a href="{pages.BASE}nyhetsbrev/" style="color:#5a7177">Endre valgene dine</a> eller se <a href="{pages.BASE}" style="color:#5a7177">hele programmet</a>.</p>
</td></tr>
<tr><td style="padding:16px 24px 20px;border-top:1px solid #ddd6c6;font:11.5px/1.5 {FONT};color:#7a8a8e">
  Du får dette brevet fordi du meldte deg på nyhetsbrevet på kaskjerda.no. <a href="{UNSUB}" style="color:#7a8a8e">Meld deg av</a>.<br>
  Datoer og priser kan endres, så sjekk alltid hos arrangøren før du kjøper billett.</td></tr>
</table></td></tr></table></body></html>
"""
    plain = f"{subject}\n\n{intro}\n\n" + "\n\n".join(text) + f"\n\nEndre valg: {pages.BASE}nyhetsbrev/\nMeld deg av: {UNSUB}\n"
    return subject, html, plain


def _line(e):
    price = pages.price_text(e)
    return f"{day_short(e['date'])} {e.get('time') or ''} {e['title']}, {e['venue']} ({price})".replace("  ", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--themes", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--today", default="")
    a = ap.parse_args()
    today = datetime.date.fromisoformat(a.today) if a.today else datetime.datetime.now(TZ).date()
    events = json.loads((ROOT / "data" / "events.json").read_text())["events"]
    subject, html, plain = build([t for t in a.themes.split(",") if t], events, today)
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "brev.html").write_text(html)
        (out / "brev.txt").write_text(plain)
    print(subject)


if __name__ == "__main__":
    main()
