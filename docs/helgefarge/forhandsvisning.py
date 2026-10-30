"""Forhåndsvisning av svak egen farge på helgedagene (fredag–søndag) i lista på forsiden (Claude-artefakt, flere filer).

«Nå» er slik forsiden er i dag. H1 svak bakgrunn, H2 farget dato, H3 strek langs helgen, H4 «Helg»-merke, H5 helgeskille
med overskrift, H6 lørdag og søndag litt sterkere enn fredag, H7 glød i datoen. Velgeren nederst bytter også tema.

Bygger på _site/ (kjør scripts/pages.py først). Skriver preview/helgefarge/. Variant i adressen: #h1 … #h7 (#na = i dag).

Kjør: python3 scripts/pages.py && python3 docs/helgefarge/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "helgefarge"

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Helgefarge</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

extra = r"""
<style>
/* Helgefargen per tema: gull i mørkt tema, gull på rødt i jul, varm rav i lyst tema */
:root { --hf: #b7791f; --hf-ink: #ffffff; }
html[data-tema="kveld"] { --hf: #f7c873; --hf-ink: #10282f; }
html[data-tema="jul"] { --hf: #e9c06a; --hf-ink: #3a0b12; }
.hfpick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 8px max(10px, env(safe-area-inset-right, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(10px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; justify-content: center; background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.hfpick .seg { display: inline-flex; flex-wrap: wrap; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.hfpick button { font: 700 13.5px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 11px; min-height: 40px; cursor: pointer; }
.hfpick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.hfpick p { margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; max-width: 62ch; }
body { padding-bottom: 150px; }

/* H1 Svak bakgrunn bak hele helgedagen */
body.hf-h1 .day.helg { background: color-mix(in srgb, var(--hf) 10%, transparent); border-radius: 14px; padding-inline: 10px; margin-inline: -10px; border-bottom-color: transparent; }

/* H2 Farget dato */
body.hf-h2 .day.helg .date .num, body.hf-h2 .day.helg .date .wd { color: var(--hf); }

/* H3 Strek langs helgen */
body.hf-h3 .day.helg { box-shadow: inset 3px 0 0 var(--hf); padding-left: 12px; margin-left: -12px; }

/* H4 «Helg»-merke under datoen + svak bakgrunn */
body.hf-h4 .day.helg { background: color-mix(in srgb, var(--hf) 7%, transparent); border-radius: 14px; padding-inline: 10px; margin-inline: -10px; }
.hftag { display: inline-block; margin-top: 6px; font: 700 10px/1 var(--font-body); letter-spacing: .08em; text-transform: uppercase; color: var(--hf-ink); background: var(--hf); border-radius: 999px; padding: 4px 7px; }

/* H5 Helgeskille: overskrift før fredag og svak tone over hele helgen */
.hfhead { display: flex; align-items: center; gap: 10px; margin: 18px 0 2px; font: 800 13px/1 var(--font-body); letter-spacing: .1em; text-transform: uppercase; color: var(--hf); }
.hfhead::after { content: ""; flex: 1; height: 1px; background: color-mix(in srgb, var(--hf) 45%, transparent); }
.hfhead span { font-weight: 500; letter-spacing: 0; text-transform: none; color: var(--muted); }
body.hf-h5 .day.helg { background: color-mix(in srgb, var(--hf) 7%, transparent); padding-inline: 10px; margin-inline: -10px; }
body.hf-h5 .day.helg.forste { border-radius: 14px 14px 0 0; }
body.hf-h5 .day.helg.siste { border-radius: 0 0 14px 14px; border-bottom-color: transparent; }

/* H6 Fredag svakest, lørdag og søndag litt sterkere */
body.hf-h6 .day.helg { border-radius: 14px; padding-inline: 10px; margin-inline: -10px; border-bottom-color: transparent; }
body.hf-h6 .day.fre { background: color-mix(in srgb, var(--hf) 5%, transparent); }
body.hf-h6 .day.lor, body.hf-h6 .day.son { background: color-mix(in srgb, var(--hf) 12%, transparent); }

/* H7 Glød i datoen */
body.hf-h7 .day.helg .date { background: radial-gradient(60px 70px at 30% 35%, color-mix(in srgb, var(--hf) 22%, transparent), transparent 70%); border-radius: 12px; padding: 6px 4px 8px 6px; margin: -6px 0 0 -6px; }
body.hf-h7 .day.helg .date .num { color: var(--hf); }
</style>
<nav class="hfpick" aria-label="Velg variant og tema">
  <div class="seg" role="group" aria-label="Variant"><button type="button" data-v="na">Nå</button><button type="button" data-v="h1">H1</button><button type="button" data-v="h2">H2</button><button type="button" data-v="h3">H3</button><button type="button" data-v="h4">H4</button><button type="button" data-v="h5">H5</button><button type="button" data-v="h6">H6</button><button type="button" data-v="h7">H7</button></div>
  <div class="seg" role="group" aria-label="Tema"><button type="button" data-t="kveld">Mørkt</button><button type="button" data-t="jul">Jul</button><button type="button" data-t="lys">Lyst</button></div>
  <p id="hftxt"></p>
</nav>
<script>
(() => {
  const TXT = {
    na: "Nå: alle dager ser like ut.",
    h1: "H1 Svak bakgrunn: fredag, lørdag og søndag får en svak gylden flate bak seg.",
    h2: "H2 Farget dato: bare datoen for helgedagene blir gyllen. Ellers likt.",
    h3: "H3 Strek: en tynn gyllen strek langs venstre kant av helgedagene.",
    h4: "H4 «Helg»-merke: et lite merke under datoen og en svak flate.",
    h5: "H5 Helgeskille: «Helgen 30. okt – 1. nov» som overskrift, og helgen samlet i én svak flate.",
    h6: "H6 Trinnvis: fredag svakest, lørdag og søndag litt sterkere.",
    h7: "H7 Glød: datoen for helgedagene får en svak gyllen glød.",
  };
  const v = () => (Object.keys(TXT).includes(location.hash.slice(1)) ? location.hash.slice(1) : "h1");
  const KEY = { "fre": "fre", "lør": "lor", "søn": "son" };
  function decorate() {
    const list = document.getElementById("list"), cur = v();
    list.querySelectorAll(".hftag,.hfhead").forEach(x => x.remove());
    const days = [...list.querySelectorAll(".day")];
    days.forEach(s => { s.classList.remove("helg", "fre", "lor", "son", "forste", "siste");
      const wd = (s.querySelector(".date .wd")?.textContent || "").trim().toLowerCase();
      if (KEY[wd]) s.classList.add("helg", KEY[wd]); });
    // Sammenhengende helger (fredag–søndag som står etter hverandre i lista)
    const groups = []; let g = [];
    days.forEach((s, i) => { if (s.classList.contains("helg")) { g.push(s); } if (!s.classList.contains("helg") || i === days.length - 1) { if (g.length) groups.push(g); g = []; } });
    groups.forEach(gr => { gr[0].classList.add("forste"); gr[gr.length - 1].classList.add("siste"); });
    if (cur === "h4") days.filter(s => s.classList.contains("helg")).forEach(s => s.querySelector(".date").insertAdjacentHTML("beforeend", `<span class="hftag">Helg</span>`));
    if (cur === "h5") groups.forEach(gr => { const a = gr[0].querySelector(".date"), b = gr[gr.length - 1].querySelector(".date");
      const t = s => `${s.querySelector(".num").textContent.trim()}. ${s.querySelector(".mo").textContent.trim().toLowerCase()}`;
      gr[0].insertAdjacentHTML("beforebegin", `<div class="hfhead">Helgen <span>${gr.length > 1 ? t(a) + " – " + t(b) : t(a)}</span></div>`); });
  }
  const orig = render;
  render = function () { orig(); decorate(); };
  function setTema(t) {
    document.querySelectorAll('link[href="tema-kveld.css"],link[href="tema-jul.css"]').forEach(l => l.remove());
    const root = document.documentElement;
    if (t === "lys") { delete root.dataset.tema; root.dataset.theme = "light"; }
    else { root.dataset.tema = t; delete root.dataset.theme; document.head.insertAdjacentHTML("beforeend", `<link rel="stylesheet" href="tema-${t}.css">`); }
    document.querySelectorAll(".hfpick [data-t]").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === t));
  }
  function apply() {
    const cur = v();
    document.body.className = document.body.className.replace(/\bhf-\w+/g, "").trim() + " hf-" + cur;
    document.querySelectorAll(".hfpick [data-v]").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === cur));
    document.getElementById("hftxt").textContent = TXT[cur];
    render();
  }
  document.querySelectorAll(".hfpick [data-v]").forEach(b => b.addEventListener("click", () => { location.hash = b.dataset.v; }));
  document.querySelectorAll(".hfpick [data-t]").forEach(b => b.addEventListener("click", () => setTema(b.dataset.t)));
  addEventListener("hashchange", apply);
  setTema(document.documentElement.dataset.tema === "jul" ? "jul" : "kveld");
  const wait = setInterval(() => { if (typeof E !== "undefined" && E.length) { clearInterval(wait); apply(); } }, 100);
})();
</script>
"""
page = page.rstrip() + "\n" + extra

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "index.html").write_text(page)
for f in ("stil.css", "tema-kveld.css", "tema-jul.css"):
    shutil.copy(SITE / f, OUT / f)
for f in ("events.json", "kino.json"):
    if (SITE / "data" / f).exists():
        shutil.copy(SITE / "data" / f, OUT / "data" / f)
print("Skrev", OUT)
