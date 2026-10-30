"""Forhåndsvisning av sterkere kategorifarge på kortene på forsiden (Claude-artefakt, flere filer).

«Nå» er slik kortene er i dag (4 px fargekant). S1–S6 er forslagene fra del 3 i docs/deling-ikveld-farge-forslag.html,
lagt på de ekte kortene: S1 bred kant med symbol, S2 fane øverst, S3 fylt kategorimerke, S4 klokkeslett i fargeblokk,
S5 hele kortet i farge, S6 symbolrute. Velgeren nederst bytter også tema (mørkt, jul, lyst).

Bygger på _site/ (kjør scripts/pages.py først). Skriver preview/kategorifarge/. Variant i adressen: #s1 … #s6 (#na = i dag).

Kjør: python3 scripts/pages.py && python3 docs/kategorifarge/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "kategorifarge"

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Kategorifarge på kortene</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

extra = r"""
<style>
.kfpick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 8px max(10px, env(safe-area-inset-right, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(10px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; justify-content: center; background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.kfpick .seg { display: inline-flex; flex-wrap: wrap; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.kfpick button { font: 700 13.5px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 11px; min-height: 40px; cursor: pointer; }
.kfpick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.kfpick p { margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; max-width: 62ch; }
body { padding-bottom: 150px; }
.kfi { width: 16px; height: 16px; flex: none; }

/* S1 Bred kant med symbol */
html body.kf-s1 .ev:not(.match) { position: relative; padding-left: 58px; border-left-width: 1px !important; border-left-color: var(--line) !important; }
body.kf-s1 .kfedge { position: absolute; left: 0; top: 0; bottom: 0; width: 44px; background: var(--c); border-radius: 11px 0 0 11px; display: grid; place-items: center; color: #0a171b; }
body.kf-s1 .kfedge .kfi { width: 20px; height: 20px; }
body.kf-s1 .ev:not(.match) .meta .tag { display: none; }
html[data-tema="jul"] body.kf-s1 .ev:not(.match) { border-left-color: #6b2530 !important; }

/* S2 Fane øverst */
html body.kf-s2 .ev:not(.match) { padding-top: 0; overflow: hidden; border-left-width: 1px !important; border-color: color-mix(in srgb, var(--c) 45%, var(--line)) !important; }
body.kf-s2 .kftab { grid-column: 1 / -1; grid-row: 1; margin: 0 -14px 8px; padding: 6px 14px; background: color-mix(in srgb, var(--c) 85%, #0a171b); color: #0a171b; font: 700 11.5px/1 var(--font-mono, monospace); letter-spacing: .1em; text-transform: uppercase; display: flex; align-items: center; gap: 7px; }
body.kf-s2 .kftab .kfi { width: 14px; height: 14px; }
body.kf-s2 .ev:not(.match) .side { grid-row: 2 / span 2; }
body.kf-s2 .ev:not(.match) .meta .tag { display: none; }

/* S3 Fylt kategorimerke */
html body.kf-s3 .ev:not(.match) { border-left-width: 1px !important; border-left-color: var(--line) !important; }
html[data-tema="jul"] body.kf-s3 .ev:not(.match) { border-left-color: #6b2530 !important; }
body.kf-s3 .ev .meta .tag { display: inline-flex; align-items: center; gap: 5px; background: var(--c); color: #0a171b; border-radius: 999px; padding: 4px 9px 4px 7px; font-size: 11px; }
body.kf-s3 .ev .meta .tag .kfi { width: 13px; height: 13px; }

/* S4 Timeplan: klokkeslett i fargeblokk */
html body.kf-s4 .ev:not(.match) { position: relative; padding-left: 78px; overflow: hidden; border-left-width: 1px !important; }
body.kf-s4 .kfclock { position: absolute; left: 0; top: 0; bottom: 0; width: 64px; background: color-mix(in srgb, var(--c) 26%, var(--surface)); border-right: 3px solid var(--c); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; color: var(--c); }
body.kf-s4 .kfclock b { font: 700 15px/1 var(--font-mono, monospace); color: var(--fg); }
body.kf-s4 .kfclock .kfi { width: 18px; height: 18px; }
body.kf-s4 .ev:not(.match) .meta .t { display: none; }

/* S5 Hele kortet i farge */
html body.kf-s5 .ev:not(.match) { background: linear-gradient(160deg, color-mix(in srgb, var(--c) 42%, var(--surface)), color-mix(in srgb, var(--c) 14%, var(--surface)) 75%) !important; border-color: color-mix(in srgb, var(--c) 55%, var(--line)) !important; }
body.kf-s5 .ev .meta .tag { color: var(--fg); background: color-mix(in srgb, var(--bg) 40%, transparent); border-radius: 6px; padding: 3px 6px; }

/* S6 Symbolrute */
html body.kf-s6 .ev:not(.match) { position: relative; padding-left: 70px; border-left-width: 1px !important; border-left-color: var(--line) !important; }
html[data-tema="jul"] body.kf-s6 .ev:not(.match) { border-left-color: #6b2530 !important; }
body.kf-s6 .kftile { position: absolute; left: 12px; top: 12px; width: 44px; height: 44px; border-radius: 12px; background: color-mix(in srgb, var(--c) 22%, var(--surface)); border: 1px solid color-mix(in srgb, var(--c) 55%, var(--line)); color: var(--c); display: grid; place-items: center; }
body.kf-s6 .kftile .kfi { width: 22px; height: 22px; }
</style>
<nav class="kfpick" aria-label="Velg variant og tema">
  <div class="seg" role="group" aria-label="Variant"><button type="button" data-v="na">Nå</button><button type="button" data-v="s1">S1</button><button type="button" data-v="s2">S2</button><button type="button" data-v="s3">S3</button><button type="button" data-v="s4">S4</button><button type="button" data-v="s5">S5</button><button type="button" data-v="s6">S6</button></div>
  <div class="seg" role="group" aria-label="Tema"><button type="button" data-t="kveld">Mørkt</button><button type="button" data-t="jul">Jul</button><button type="button" data-t="lys">Lyst</button></div>
  <p id="kftxt"></p>
</nav>
<script>
(() => {
  const TXT = {
    na: "Nå: slik kortene er i dag. 4 px fargekant og kategorinavnet i farget tekst.",
    s1: "S1 Bred kant med symbol: kanten blir 44 px bred med et symbol for kategorien. Kategorinavnet tas bort fra linja.",
    s2: "S2 Fane øverst: en smal fargelist over kortet med symbol og kategorinavn.",
    s3: "S3 Fylt kategorimerke: kortet er nøytralt, kategorien blir et fylt merke med symbol.",
    s4: "S4 Timeplan: klokkeslettet står i en fargeblokk til venstre med symbolet over.",
    s5: "S5 Hele kortet i farge: tydelig farget fra hjørnet og nedover.",
    s6: "S6 Symbolrute: en liten rute med symbolet foran tittelen, som ikonene i en app.",
  };
  const ICON = {
    konsert: '<path d="M9 18V5l11-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
    standup: '<rect x="9" y="2.5" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M8.5 21h7"/>',
    show: '<path d="M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.6 6.6 19.5l1.2-6L3.3 9.3l6.1-.7Z"/>',
    barn: '<ellipse cx="12" cy="9" rx="5.5" ry="6.5"/><path d="M12 15.5l-1 1.5h2l-1-1.5M12 17c0 2-2 2.5-2 4.5"/>',
    klubb: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="2.2"/><path d="M12 3.5a8.5 8.5 0 0 1 8.5 8.5"/>',
    happening: '<path d="M12 2.5v5M12 16.5v5M2.5 12h5M16.5 12h5M5.3 5.3l3.2 3.2M15.5 15.5l3.2 3.2M5.3 18.7l3.2-3.2M15.5 8.5l3.2-3.2"/>',
    quiz: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .9-1 1.6v.6"/><circle cx="12" cy="17" r=".6"/>',
    julebord: '<path d="M12 2.5l6 9h-3.5l4.5 6.5H5l4.5-6.5H6Z"/><path d="M12 18v3.5"/>',
    sport: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5l4 3-1.5 4.5h-5L8 10.5Z"/>',
  };
  const ico = c => `<svg class="kfi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[c] || ICON.happening}</svg>`;
  const v = () => (Object.keys(TXT).includes(location.hash.slice(1)) ? location.hash.slice(1) : "na");
  let tema = "kveld";
  function decorate() {
    const cur = v();
    document.querySelectorAll("#list article.ev:not(.match)").forEach(a => {
      a.querySelectorAll(".kfedge,.kftab,.kfclock,.kftile,.tag .kfi").forEach(x => x.remove());
      const c = ((a.getAttribute("style") || "").match(/--c-([a-z]+)/) || [])[1] || "happening";
      const label = a.querySelector(".meta .tag")?.textContent || "";
      const t = (a.querySelector(".meta .t")?.textContent.match(/\d\d:\d\d/) || ["–"])[0];
      if (cur === "s1") a.insertAdjacentHTML("afterbegin", `<span class="kfedge">${ico(c)}</span>`);
      if (cur === "s2") a.insertAdjacentHTML("afterbegin", `<div class="kftab">${ico(c)}${label}</div>`);
      if (cur === "s3") a.querySelector(".meta .tag")?.insertAdjacentHTML("afterbegin", ico(c));
      if (cur === "s4") a.insertAdjacentHTML("afterbegin", `<div class="kfclock">${ico(c)}<b>${t}</b></div>`);
      if (cur === "s6") a.insertAdjacentHTML("afterbegin", `<span class="kftile">${ico(c)}</span>`);
    });
  }
  const orig = render;
  render = function () { orig(); decorate(); };
  function setTema(t) {
    tema = t;
    document.querySelectorAll('link[href="tema-kveld.css"],link[href="tema-jul.css"]').forEach(l => l.remove());
    const root = document.documentElement;
    if (t === "lys") { delete root.dataset.tema; root.dataset.theme = "light"; }
    else { root.dataset.tema = t; delete root.dataset.theme; document.head.insertAdjacentHTML("beforeend", `<link rel="stylesheet" href="tema-${t}.css">`); }
    document.querySelectorAll(".kfpick [data-t]").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === t));
  }
  function apply() {
    const cur = v();
    document.body.className = document.body.className.replace(/\bkf-\w+/g, "").trim() + " kf-" + cur;
    document.querySelectorAll(".kfpick [data-v]").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === cur));
    document.getElementById("kftxt").textContent = TXT[cur];
    render();
  }
  document.querySelectorAll(".kfpick [data-v]").forEach(b => b.addEventListener("click", () => { location.hash = b.dataset.v; }));
  document.querySelectorAll(".kfpick [data-t]").forEach(b => b.addEventListener("click", () => setTema(b.dataset.t)));
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
