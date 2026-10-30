"""Forhåndsvisning av større nedtrekksmenyer i filterlinja på mobil (Claude-artefakt, flere filer).

«Nå» er slik det er i dag (rundt 35 px). M1 bare høyere (44 px), M2 44 px uten den ekstra tellelinja (antallet står i
søkefeltet), M3 44 px med symbol i hver meny, M4 48 px og større tekst, M5 én «Filtre»-knapp som folder ut menyene.

Forsiden vises i en mobilramme (390 px) inne i artefakten, så mobiloppsettet gjelder også på PC. Velgeren nederst i
rammen bytter variant og tema, og viser hvor høy filterlinja blir.

Bygger på _site/ (kjør scripts/pages.py først). Skriver preview/nedtrekk/ (index.html = rammen, side.html = forsiden).

Kjør: python3 scripts/pages.py && python3 docs/nedtrekk/forhandsvisning.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "nedtrekk"

ICONS = {  # små symboler som bakgrunnsbilde i menyene (M3)
    "mwhen": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%238fa8ab" stroke-width="2" stroke-linecap="round"><rect x="3.5" y="5" width="17" height="15" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/></svg>',
    "mcat": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%238fa8ab" stroke-width="2" stroke-linejoin="round"><path d="M3 12V4h8l10 10-8 8Z"/><circle cx="7.5" cy="8.5" r="1.3" fill="%238fa8ab"/></svg>',
    "venue": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%238fa8ab" stroke-width="2"><path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.4"/></svg>',
    "price": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%238fa8ab" stroke-width="2" stroke-linejoin="round"><path d="M4 7h16v10H4Z"/><circle cx="12" cy="12" r="2.4"/></svg>',
}
icon_css = "\n".join(
    f'  body.mm-m3 #{k} {{ background-image: url(\'data:image/svg+xml;utf8,{v.replace(chr(39), "")}\'), linear-gradient(45deg, transparent 50%, var(--muted) 50%), linear-gradient(135deg, var(--muted) 50%, transparent 50%); '
    f'background-position: 10px 50%, calc(100% - 15px) 50%, calc(100% - 10px) 50%; background-size: 17px 17px, 5px 5px, 5px 5px; }}'
    for k, v in ICONS.items())

extra = """
<style>
.mmpick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 8px 10px calc(8px + env(safe-area-inset-bottom, 0px)); display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; justify-content: center;
  background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.mmpick .seg { display: inline-flex; flex-wrap: wrap; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.mmpick button { font: 700 13.5px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 11px; min-height: 40px; cursor: pointer; }
.mmpick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.mmpick p { margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; }
.mmpick p b { color: #f7c873; }
body { padding-bottom: 170px; }
.mmfilter, .mmpanel { display: none; }
@media (max-width: 640px) {
  /* M1 bare høyere */
  body.mm-m1 .controls select.chip, body.mm-m1 .search, body.mm-m1 #favonly { min-height: 44px; }
  /* M2 44 px, antallet i søkefeltet i stedet for egen linje */
  body.mm-m2 .controls select.chip, body.mm-m2 .search, body.mm-m2 #favonly { min-height: 44px; }
  body.mm-m2 .controls .count { display: none; }
  /* M3 44 px med symbol */
  body.mm-m3 .controls select.chip, body.mm-m3 .search, body.mm-m3 #favonly { min-height: 44px; }
  body.mm-m3 .controls select.chip { padding-left: 34px; background-repeat: no-repeat; }
""" + icon_css + """
  /* M4 48 px og større tekst */
  body.mm-m4 .controls select.chip, body.mm-m4 .search, body.mm-m4 #favonly { min-height: 48px; font-size: 15px; }
  body.mm-m4 .controls { gap: 8px; }
  /* M5 Filtre-knapp som folder ut menyene */
  body.mm-m5 .search { grid-column: span 2; min-height: 44px; }
  body.mm-m5 #favonly { min-height: 44px; }
  body.mm-m5 .mmfilter { display: inline-flex; order: 2; grid-column: span 1; min-height: 44px; justify-content: center; gap: 5px; font-weight: 600; }
  body.mm-m5 .mmfilter b { display: inline-grid; place-items: center; min-width: 18px; height: 18px; border-radius: 9px; background: var(--accent); color: var(--accent-ink); font-size: 11px; }
  body.mm-m5 #favonly { order: 3; }
  body.mm-m5 .controls select.chip { display: none; }
  body.mm-m5.mm-open .controls select.chip { display: inline-flex; min-height: 48px; font-size: 15px; }
  body.mm-m5 #mwhen { order: 4; } body.mm-m5 #mcat { order: 5; } body.mm-m5 #venue { order: 6; } body.mm-m5 #price { order: 7; }
  body.mm-m5 .controls .count { order: 8; }
}
</style>
<nav class="mmpick" aria-label="Velg variant og tema">
  <div class="seg" role="group" aria-label="Variant"><button type="button" data-v="na">Nå</button><button type="button" data-v="m1">M1</button><button type="button" data-v="m2">M2</button><button type="button" data-v="m3">M3</button><button type="button" data-v="m4">M4</button><button type="button" data-v="m5">M5</button></div>
  <div class="seg" role="group" aria-label="Tema"><button type="button" data-t="kveld">Mørkt</button><button type="button" data-t="jul">Jul</button><button type="button" data-t="lys">Lyst</button></div>
  <p id="mmtxt"></p>
</nav>
<script>
(() => {
  const TXT = {
    na: "Nå: slik det er i dag.",
    m1: "M1 Bare høyere: alle menyer, søk og Mine blir 44 px. Ellers likt.",
    m2: "M2 Høyere, men tettere: 44 px, og antallet står i søkefeltet («Søk i 153 …») i stedet for på egen linje.",
    m3: "M3 Med symbol: 44 px og et lite symbol foran hver meny (kalender, merkelapp, sted, pris).",
    m4: "M4 Store: 48 px og større tekst. Lettest å treffe, men filterlinja blir høyest.",
    m5: "M5 Filtre-knapp: søk, «Filtre» og Mine på én linje. «Filtre» folder ut de fire menyene (48 px). Lavest filterlinje.",
  };
  const ctl = document.querySelector(".controls"), q = document.getElementById("q");
  const btn = document.createElement("button"); btn.type = "button"; btn.className = "chip mmfilter"; btn.setAttribute("aria-expanded", "false");
  ctl.querySelector(".row:last-child").appendChild(btn);
  const active = () => [state.when !== "alt", state.cats.size > 0, !!state.venue, state.price !== ""].filter(Boolean).length;
  const label = () => { const n = active(); btn.innerHTML = `Filtre${n ? ` <b>${n}</b>` : ""}`; };
  btn.addEventListener("click", () => { const o = !document.body.classList.contains("mm-open"); document.body.classList.toggle("mm-open", o); btn.setAttribute("aria-expanded", o); measure(); });
  const parts = () => (location.hash.slice(1) || "m1-kveld").split("-");
  const v = () => (TXT[parts()[0]] ? parts()[0] : "m1"), t = () => (["kveld", "jul", "lys"].includes(parts()[1]) ? parts()[1] : "kveld");
  function measure() {
    requestAnimationFrame(() => { const sel = document.getElementById("mwhen"), shown = getComputedStyle(sel).display !== "none";
      document.getElementById("mmtxt").innerHTML = `${TXT[v()]}<br>Filterlinja: <b>${Math.round(ctl.getBoundingClientRect().height)} px</b> høy · nedtrekk: <b>${shown ? Math.round(sel.getBoundingClientRect().height) + " px" : "skjult"}</b>`; });
  }
  function setTema(x) {
    document.querySelectorAll('link[href="tema-kveld.css"],link[href="tema-jul.css"]').forEach(l => l.remove());
    const root = document.documentElement;
    if (x === "lys") { delete root.dataset.tema; root.dataset.theme = "light"; }
    else { root.dataset.tema = x; delete root.dataset.theme; document.head.insertAdjacentHTML("beforeend", `<link rel="stylesheet" href="tema-${x}.css">`); }
  }
  function apply() {
    document.body.className = document.body.className.replace(/\\bmm-\\w+/g, "").trim() + " mm-" + v();
    document.body.classList.remove("mm-open"); btn.setAttribute("aria-expanded", "false");
    setTema(t());
    document.querySelectorAll(".mmpick [data-v]").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === v()));
    document.querySelectorAll(".mmpick [data-t]").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === t()));
    q.placeholder = v() === "m2" ? `Søk i ${E.length} arrangementer …` : "Søk …";
    label(); measure();
  }
  document.querySelectorAll(".mmpick [data-v]").forEach(b => b.addEventListener("click", () => { location.hash = b.dataset.v + "-" + t(); }));
  document.querySelectorAll(".mmpick [data-t]").forEach(b => b.addEventListener("click", () => { location.hash = v() + "-" + b.dataset.t; }));
  addEventListener("hashchange", apply);
  const orig = render; render = function () { orig(); label(); };
  const wait = setInterval(() => { if (typeof E !== "undefined" && E.length) { clearInterval(wait); apply(); } }, 100);
})();
</script>
"""

frame = """<title>Større nedtrekk på mobil</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root { --bg: #0a171b; --fg: #e8f1ef; --muted: #8fa8ab; --line: #25414a; color-scheme: dark; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.5 system-ui, sans-serif;
  padding-block: 20px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.wrap { max-width: 900px; margin: 0 auto; display: grid; gap: 14px; justify-items: center; }
h1 { font: 800 26px/1.15 system-ui, sans-serif; margin: 0; text-align: center; }
p { margin: 0; color: var(--muted); max-width: 60ch; text-align: center; }
iframe { width: 390px; max-width: 100%; height: min(860px, 86vh); border: 1px solid var(--line); border-radius: 28px; background: var(--bg); }
</style>
<div class="wrap">
  <h1>Større nedtrekk på mobil</h1>
  <p>Forsiden vises i en mobilramme (390 px). Velg variant og tema nederst i rammen. Under velgeren står hvor høy filterlinja blir.</p>
  <iframe src="side.html#m1-kveld" title="Forsiden på mobil"></iframe>
</div>
"""

page = (SITE / "index.html").read_text().replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)
page = page.replace("</body>", extra + "</body>", 1)
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "side.html").write_text(page)
(OUT / "index.html").write_text(frame)
for f in ("stil.css", "tema-kveld.css", "tema-jul.css", "favicon-48.png", "apple-touch-icon.png"):
    if (SITE / f).exists():
        shutil.copy(SITE / f, OUT / f)
for f in ("events.json", "kino.json"):
    if (SITE / "data" / f).exists():
        shutil.copy(SITE / "data" / f, OUT / "data" / f)
print("Skrev", OUT)
