"""Forhåndsvisning: hvor «For arrangører» skal synes øverst på forsiden (Claude-artefakt, flere filer).

P1 knapp i toppstripa ved «English», P2 lenke i ingressen, P3 smal kunngjøringsstripe helt øverst (kan lukkes),
P4 eget kort over lista (som kinostripa), P5 «Mangler det noe?»-boksen flyttet opp med to valg,
P6 = P1 + arrangørlenke i «Mangler det noe?»-boksen nederst. «Nå» er slik forsiden er i dag.

Bygger på _site/ (kjør scripts/pages.py først). Skriver preview/arrangor-plassering/. Variant i adressen: #p1 … #p6 (#na = i dag).

Kjør: python3 scripts/pages.py && python3 docs/arrangor-plassering/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "arrangor-plassering"

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Arrangørlenke på forsiden</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11v2a1 1 0 0 0 1 1h2l5 4V6L6 10H4a1 1 0 0 0-1 1z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/></svg>'

extra = r"""
<style>
.pv { display: none !important; }
body.v-p1 .pv-p1, body.v-p6 .pv-p1, body.v-p2 .pv-p2, body.v-p3 .pv-p3, body.v-p4 .pv-p4, body.v-p5 .pv-p5, body.v-p6 .pv-p6 { display: revert !important; }
body.v-p5 .missing.orig { display: none; }
body.v-p6 .missing.orig { display: none; }

/* P1 knapp i toppstripa */
.arrbtn svg { color: var(--accent) !important; }
.arrbtn .ls { display: none; }
@media (max-width: 520px) { .arrbtn .ll { display: none; } .arrbtn .ls { display: inline !important; } }
/* Koordinatene øverst til venstre får ikke plass ved siden av en knapp til på smale telefoner */
@media (max-width: 440px) { body.v-p1 .topbar > .eyebrow, body.v-p6 .topbar > .eyebrow { display: none; } }

/* P2 lenke i ingressen */
.lede .pv-p2 a { color: var(--accent); font-weight: 600; white-space: nowrap; }

/* P3 kunngjøringsstripe */
.arrbar { display: flex; align-items: center; gap: 10px; justify-content: center; margin: -8px -16px 14px; padding: 9px 44px 9px 16px; position: relative;
  background: color-mix(in srgb, var(--accent) 16%, var(--surface)); border-bottom: 1px solid var(--line); font: 500 14px/1.35 var(--font-body); color: var(--fg); text-align: center; }
.arrbar a { color: var(--accent); font-weight: 700; text-decoration: none; white-space: nowrap; }
.arrbar button { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); width: 36px; height: 36px; border: 0; background: none; color: var(--muted); font-size: 20px; cursor: pointer; }

/* P4 kort over lista */
.arrcard { display: flex; align-items: center; gap: 14px; margin: 0 0 14px; padding: 12px 14px; border: 1px solid var(--line); border-radius: 14px; background: var(--surface); text-decoration: none; color: var(--fg); }
.arrcard .ic { flex: none; width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; background: color-mix(in srgb, var(--accent) 18%, transparent); color: var(--accent); }
.arrcard .ic svg { width: 22px; height: 22px; }
.arrcard b { display: block; font: 800 16px/1.2 var(--font-display); }
.arrcard span { font-size: 13.5px; color: var(--muted); }
.arrcard i { margin-left: auto; font-style: normal; color: var(--accent); font-weight: 700; }

/* P5 «Mangler det noe?» øverst med to valg */
.arrduo { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 0 0 14px; }
.arrduo a { display: block; padding: 11px 13px; border: 1px solid var(--line); border-radius: 12px; background: var(--surface); text-decoration: none; color: var(--fg); }
.arrduo b { display: block; font: 700 14.5px/1.25 var(--font-body); }
.arrduo span { font-size: 12.5px; color: var(--muted); }
.arrduo a:last-child b { color: var(--accent); }

/* P6 nederst: to lenker i boksen */
.missing2 { margin: 22px 0; padding: 14px 16px; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; }
.missing2 b { display: block; margin-bottom: 4px; }
.missing2 a { color: var(--accent); font-weight: 600; }

.pick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 8px 10px calc(8px + env(safe-area-inset-bottom, 0px));
  display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; justify-content: center; background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.pick .seg { display: inline-flex; flex-wrap: wrap; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.pick button { font: 700 13.5px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 11px; min-height: 40px; cursor: pointer; }
.pick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.pick p { margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; max-width: 62ch; }
body { padding-bottom: 150px; }
</style>
<nav class="pick" aria-label="Velg forslag og tema">
  <div class="seg" role="group" aria-label="Forslag"><button type="button" data-v="na">Nå</button><button type="button" data-v="p1">P1</button><button type="button" data-v="p2">P2</button><button type="button" data-v="p3">P3</button><button type="button" data-v="p4">P4</button><button type="button" data-v="p5">P5</button><button type="button" data-v="p6">P6</button></div>
  <div class="seg" role="group" aria-label="Tema"><button type="button" data-t="kveld">Mørkt</button><button type="button" data-t="jul">Jul</button><button type="button" data-t="lys">Lyst</button></div>
  <p id="ptxt"></p>
</nav>
<script>
(() => {
  const TXT = {
    na: "Nå: arrangørsiden er bare lenket fra snarveiene helt nederst.",
    p1: "P1 Knapp i toppstripa: «For arrangører» ved «English» («Arrangør» på mobil). Alltid synlig, tar nesten ikke plass.",
    p2: "P2 Lenke i ingressen: «Arrangerer du noe? Kom med gratis →» sist i teksten under logoen.",
    p3: "P3 Kunngjøringsstripe helt øverst: «Arrangerer du noe i Ålesund? Kom med gratis →». Kan lukkes med ×.",
    p4: "P4 Eget kort over lista, som kinostripa. Mest synlig, men tar plass fra programmet.",
    p5: "P5 «Tips oss» og «For arrangører» som to små kort øverst, i stedet for boksen nederst.",
    p6: "P6 = P1, pluss at «Mangler det noe?»-boksen nederst får to lenker: tips oss og for arrangører. (Claude anbefaler denne.)",
  };
  const ICON = `__ICON__`;
  const topr = document.querySelector(".topr"), lang = document.getElementById("langbtn");
  lang.insertAdjacentHTML("beforebegin", `<a class="langbtn arrbtn pv pv-p1" href="arrangor/">${ICON}<span class="ll">For arrangører</span><span class="ls">Arrangør</span></a>`);
  document.querySelector(".lede").insertAdjacentHTML("beforeend", `<span class="pv pv-p2"> Arrangerer du noe? <a href="arrangor/">Kom med gratis →</a></span>`);
  document.querySelector("header.top").insertAdjacentHTML("afterbegin", `<div class="arrbar pv pv-p3">Arrangerer du noe i Ålesund? <a href="arrangor/">Kom med gratis →</a><button type="button" aria-label="Lukk">×</button></div>`);
  document.querySelector(".arrbar button").onclick = e => e.target.parentElement.style.visibility = "hidden";
  document.querySelector("header.top").insertAdjacentHTML("afterend",
    `<a class="arrcard pv pv-p4" href="arrangor/"><span class="ic">${ICON}</span><span><b>Arrangerer du noe i Ålesund?</b><span>Få det med i programmet. Gratis, vi lenker til billettsiden din.</span></span><i>→</i></a>` +
    `<div class="arrduo pv pv-p5"><a href="kontakt/"><b>Mangler det noe?</b><span>Tips oss om et arrangement</span></a><a href="arrangor/"><b>For arrangører →</b><span>Kom med gratis</span></a></div>`);
  const miss = document.querySelector(".missing");
  miss.classList.add("orig");
  miss.insertAdjacentHTML("afterend", `<div class="missing2 pv pv-p6"><b>Mangler det noe?</b><a href="kontakt/">Tips oss om et arrangement</a> eller meld fra om en feil. Arrangerer du selv? <a href="arrangor/">Slik kommer du med →</a></div>`);
  // P4 og P5 skal stå over kontrollene på mobil også: flytt dem inn i header
  const head = document.querySelector("header.top");
  head.appendChild(document.querySelector(".arrcard")); head.appendChild(document.querySelector(".arrduo"));

  const v = () => (Object.keys(TXT).includes(location.hash.slice(1)) ? location.hash.slice(1) : "p6");
  function setTema(t) {
    document.querySelectorAll('link[href="tema-kveld.css"],link[href="tema-jul.css"]').forEach(l => l.remove());
    const root = document.documentElement;
    if (t === "lys") { delete root.dataset.tema; root.dataset.theme = "light"; }
    else { root.dataset.tema = t; delete root.dataset.theme; document.head.insertAdjacentHTML("beforeend", `<link rel="stylesheet" href="tema-${t}.css">`); }
    document.querySelectorAll(".pick [data-t]").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === t));
  }
  function apply() {
    const cur = v();
    document.body.className = document.body.className.replace(/\bv-\w+/g, "").trim() + " v-" + cur;
    document.querySelectorAll(".pick [data-v]").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === cur));
    document.getElementById("ptxt").textContent = TXT[cur];
    const bar = document.querySelector(".arrbar"); if (bar) bar.style.visibility = "";
  }
  document.querySelectorAll(".pick [data-v]").forEach(b => b.addEventListener("click", () => { location.hash = b.dataset.v; }));
  document.querySelectorAll(".pick [data-t]").forEach(b => b.addEventListener("click", () => setTema(b.dataset.t)));
  addEventListener("hashchange", apply);
  setTema(document.documentElement.dataset.tema === "jul" ? "jul" : "kveld");
  apply();
})();
</script>
""".replace("__ICON__", ICON)
page = page.rstrip() + "\n" + extra

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "arrangor").mkdir()
(OUT / "index.html").write_text(page)
for f in ("stil.css", "tema-kveld.css", "tema-jul.css"):
    shutil.copy(SITE / f, OUT / f)
for f in ("events.json", "kino.json"):
    if (SITE / "data" / f).exists():
        shutil.copy(SITE / "data" / f, OUT / "data" / f)
shutil.copy(SITE / "arrangor" / "index.html", OUT / "arrangor" / "index.html")
print("Skrev", OUT)
