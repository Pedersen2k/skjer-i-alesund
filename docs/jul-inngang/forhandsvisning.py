"""Forslag: veien fra forsiden til jule-sidene (E1-E3) og nissen som henger foran filtermenyen (N1-N3).

Bygger på forsiden i _site/ (kjør scripts/pages.py først), med juletemaet slått på og julekortet vist uansett dato.
Velg i adressen: preview/jul-inngang/index.html#e2-n1 (e1-e3 = inngang, e0 = slik det er i dag; n0-n3 = nisse).
Skriver preview/jul-inngang/.

Kjør: python3 scripts/pages.py && python3 docs/jul-inngang/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "preview" / "jul-inngang"
SITE = ROOT / "_site"


def count(path):
    m = re.search(r"(\d+) arrangementer", (SITE / path / "index.html").read_text())
    return int(m.group(1)) if m else 0


THEMES = [("julekonserter-i-alesund", "Julekonserter", "🎶"), ("jul-for-barn-i-alesund", "Jul for barn", "🧒"),
          ("julemarked-i-alesund", "Julemarked", "🎄"), ("romjul-og-nyttar-i-alesund", "Romjul og nyttår", "✨"),
          ("julebord", "Julebord", "🍽️")]
import json
PICK = """
#pickbar { position: fixed; z-index: 40; left: 8px; right: 8px; bottom: calc(8px + env(safe-area-inset-bottom, 0px)); display: flex; flex-wrap: wrap; gap: 6px; align-items: center; padding: 8px; border-radius: 14px; background: #1a0509f2; border: 1px solid #e9c06a88; box-shadow: 0 10px 30px #000a; }
#pickbar b { font: 700 11px var(--font-mono); color: #e9c06a; text-transform: uppercase; letter-spacing: .08em; margin-right: 2px; }
#pickbar button { min-height: 40px; padding: 0 12px; border-radius: 99px; border: 1px solid #ffffff33; background: transparent; color: #fbeedd; font: 600 13px var(--font-body); cursor: pointer; }
#pickbar button[aria-pressed="true"] { background: #e9c06a; color: #2a1405; border-color: #e9c06a; }
body { padding-bottom: 130px; }
"""
INFO = json.dumps([{"href": p, "navn": n, "ikon": i, "n": count(p)} for p, n, i in THEMES], ensure_ascii=False)

CSS = """
/* E1: stripe med snarveier under julekortet */
.je1 { display: flex; flex-wrap: wrap; gap: 8px; margin: -4px 0 16px; }
.je1 a { display: inline-flex; gap: 6px; align-items: baseline; padding: 11px 14px; min-height: 44px; border-radius: 99px; background: #ffffff0d; border: 1px solid #e9c06a66; color: #fbeedd; text-decoration: none; font: 600 14.5px var(--font-body); }
.je1 a b { font: 600 12px var(--font-mono); color: #e9c06a; }
/* E2: kortet folder seg ut til fliser */
.je2 { display: none; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px; }
.julcard.open .je2 { display: grid; }
.je2 a { display: grid; gap: 2px; padding: 12px; border-radius: 10px; background: #00000030; box-shadow: inset 0 0 0 1px #e9c06a66; }
.je2 a span { font-size: 22px; line-height: 1; } .je2 a strong { font: 700 15px var(--font-body); } .je2 a em { font: 600 12px var(--font-mono); color: #e9c06a; font-style: normal; }
.je2tog { margin-top: 12px; width: 100%; padding: 11px; min-height: 44px; border-radius: 99px; border: 1px solid #e9c06a99; background: transparent; color: #fbeedd; font: 700 14px var(--font-body); cursor: pointer; }
/* E3: julekortet blir en liten «julekalender» med fem pakker */
.je3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 14px; }
.je3 a { display: grid; justify-items: center; gap: 4px; padding: 14px 6px 10px; border-radius: 6px; background: linear-gradient(180deg, #5a1620, #451018); border: 1.5px solid #e9c06a; box-shadow: inset 0 0 0 3px #451018, inset 0 0 0 4px #e9c06a55; text-align: center; }
.je3 a span { font-size: 24px; line-height: 1; } .je3 a strong { font: 700 15px/1.1 "Cormorant Garamond", Georgia, serif; color: #fbeedd; } .je3 a em { font: 600 11px var(--font-mono); color: #e9c06a; font-style: normal; }
.je3 a:last-child { grid-column: span 1; }
/* nissen */
body.n1 .jd-peek { z-index: 4; }
body.n2 .jd-peek-wrap { display: none; }
body.n2 .julcard .jd-in { display: block; }
.jd-in { display: none; position: absolute !important; right: 14px; top: -2px; width: 80px; height: 66px; overflow: hidden; pointer-events: none; }
.jd-in svg { position: absolute; left: 0; bottom: 0; width: 80px; height: 66px; }
body.n3 .jd-peek { transition: opacity .2s; }
"""

JS = """
(function () {
  var INFO = %s, st = document.createElement("style"); st.textContent = %s; document.head.append(st);
  var cur = (location.hash || "#e2-n1").slice(1).split("-"), E = cur[0] || "e2", N = cur[1] || "n1";
  var link = function (x, inner) { return '<a href="#" onclick="return false">' + inner + '</a>'; };
  function clean() {
    document.querySelectorAll(".je1,.je2,.je2tog,.je3,.jd-in").forEach(function (x) { x.remove(); });
    var jc = document.getElementById("julcard"); if (jc) { jc.classList.remove("open"); var b = jc.querySelector(".julbtns"); if (b) b.style.display = ""; }
    document.body.classList.remove("n0", "n1", "n2", "n3");
  }
  function apply() {
    var jc = document.getElementById("julcard"); if (!jc || jc.hidden || !document.querySelector(".jd-peek svg")) return false;
    clean(); document.body.classList.add(N);
    if (E === "e1") jc.insertAdjacentHTML("afterend", '<nav class="je1" aria-label="Jul i Ålesund">' + INFO.map(function (x) { return link(x, x.navn + ' <b>' + x.n + '</b>'); }).join("") + '</nav>');
    if (E === "e2") { jc.insertAdjacentHTML("beforeend", '<button type="button" class="je2tog" id="je2tog" aria-expanded="false">Velg tema ▾</button><div class="je2">' + INFO.map(function (x) { return link(x, '<span>' + x.ikon + '</span><strong>' + x.navn + '</strong><em>' + x.n + ' arrangementer</em>'); }).join("") + '</div>');
      document.getElementById("je2tog").onclick = function () { var o = jc.classList.toggle("open"); this.textContent = o ? "Skjul ▴" : "Velg tema ▾"; this.setAttribute("aria-expanded", o); }; }
    if (E === "e3") { var b = jc.querySelector(".julbtns"); if (b) b.style.display = "none"; jc.insertAdjacentHTML("beforeend", '<div class="je3">' + INFO.map(function (x) { return link(x, '<span>' + x.ikon + '</span><strong>' + x.navn + '</strong><em>' + x.n + '</em>'); }).join("") + '<a href="#" onclick="return false"><span>🎁</span><strong>Alt i jula</strong><em>50</em></a></div>'); }
    if (N === "n2") { var d = document.createElement("div"); d.className = "jd-in"; d.append(document.querySelector(".jd-peek svg").cloneNode(true)); jc.append(d); }
    document.querySelectorAll("#pickbar button").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.v === E || b.dataset.v === N)); });
    return true;
  }
  var bar = document.createElement("div"); bar.id = "pickbar";
  bar.innerHTML = '<b>Inngang</b><button data-v="e0">I dag</button><button data-v="e1">E1</button><button data-v="e2">E2</button><button data-v="e3">E3</button><b>Nisse</b><button data-v="n0">I dag</button><button data-v="n1">Bak menyen</button><button data-v="n3">Tones ut</button>';
  bar.onclick = function (ev) { var v = ev.target.dataset && ev.target.dataset.v; if (!v) return; if (v[0] === "e") E = v; else N = v; try { history.replaceState(null, "", "#" + E + "-" + N); } catch (x) {} apply(); var jc = document.getElementById("julcard"); if (jc) jc.scrollIntoView({ block: "center" }); };
  document.body.append(bar);
  var t = setInterval(function () { if (apply()) clearInterval(t); }, 150);
  var ctl = document.querySelector(".controls");
  function fade() { var p = document.querySelector(".jd-peek"); if (!p) return; if (N !== "n3") { p.style.opacity = ""; return; } var k = Math.max(0, Math.min(1, (p.getBoundingClientRect().top - ctl.getBoundingClientRect().bottom) / 60)); p.style.opacity = k; }
  addEventListener("scroll", fade, { passive: true }); setInterval(fade, 300);
})();
""" % (INFO, json.dumps(CSS + PICK))

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<meta charset="utf-8">\n<title>Veien til jule-sidene</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
loader = re.search(r'<script>try\{const q=new URLSearchParams\(location\.search\)\.get\("tema"\).*?</script>', page)
assert loader
page = page.replace(loader.group(0), '<script>document.documentElement.dataset.tema="jul"</script>\n<link rel="stylesheet" href="tema-jul.css">', 1)
page = page.replace("const JULSEASON = (() => {", "const JULSEASON = true || (() => {", 1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)
page = page.replace("</body>", "<script>" + JS + "</script></body>") if "</body>" in page else page + "<script>" + JS + "</script>"

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "index.html").write_text(page)
shutil.copy(ROOT / "data" / "events.json", OUT / "data" / "events.json")
shutil.copy(ROOT / "tema-jul.css", OUT / "tema-jul.css")
print("Skrev", OUT)
