"""Forhåndsvisning av animasjon når man trykker ★, og overgang mellom Liste og Kalender (Claude-artefakt, flere filer).

Stjerne: S0 ingen (i dag), S1 pop, S2 gnister, S3 pop + Mine-telleren hopper, S4 stjerna flyr til «★ Mine», S5 ring.
Overgang: O0 ingen (i dag), O1 tone inn, O2 skyv sidelengs, O3 View Transitions (nettleserens egen myke overgang),
O4 zoom, O5 rull ut ovenfra. Alt respekterer «Reduser bevegelse» (prefers-reduced-motion).

Bygger på _site/ (kjør scripts/pages.py først). Skriver preview/stjerne-overgang/. Valg i adressen: #s1-o1-kveld osv.

Kjør: python3 scripts/pages.py && python3 docs/stjerne-overgang/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "stjerne-overgang"

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Stjerne og overgang</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

extra = r"""
<style>
.sopick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 8px max(10px, env(safe-area-inset-right, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(10px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; justify-content: center; background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.sopick .lbl { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: #fff9; }
.sopick .seg { display: inline-flex; flex-wrap: wrap; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.sopick button { font: 700 13px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 10px; min-height: 38px; cursor: pointer; }
.sopick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.sopick p { margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; max-width: 70ch; }
.sopick .row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; justify-content: center; }
body { padding-bottom: 190px; }

/* ---- Stjerne ---- */
.fav { position: relative; }
@keyframes sopop { 0% { transform: scale(1); } 35% { transform: scale(1.5) rotate(-12deg); } 65% { transform: scale(.88) rotate(4deg); } 100% { transform: scale(1); } }
@keyframes sounpop { 0% { transform: scale(1); } 40% { transform: scale(.7); } 100% { transform: scale(1); } }
@keyframes sobump { 0% { transform: scale(1); } 40% { transform: scale(1.18); } 100% { transform: scale(1); } }
@keyframes sospark { from { transform: translate(-50%, -50%) rotate(var(--a)) translateY(0) scale(1); opacity: 1; } to { transform: translate(-50%, -50%) rotate(var(--a)) translateY(-26px) scale(.3); opacity: 0; } }
@keyframes soring { from { transform: translate(-50%, -50%) scale(.4); opacity: .9; } to { transform: translate(-50%, -50%) scale(2.1); opacity: 0; } }
.fav.so-pop { animation: sopop .42s cubic-bezier(.3,1.6,.5,1); }
.fav.so-unpop { animation: sounpop .25s ease; }
#favonly.so-bump, #favn.so-bump { animation: sobump .35s ease; }
.so-spark { position: absolute; left: 50%; top: 50%; width: 5px; height: 5px; border-radius: 50%; background: var(--accent); pointer-events: none; animation: sospark .5s ease-out forwards; }
.so-spark:nth-child(even) { background: var(--gold, #f7c873); }
.so-ring { position: absolute; left: 50%; top: 50%; width: 30px; height: 30px; border-radius: 50%; border: 2px solid var(--accent); pointer-events: none; animation: soring .5s ease-out forwards; }
.so-fly { position: fixed; z-index: 70; font-size: 22px; line-height: 1; color: var(--accent); pointer-events: none; transition: transform .6s cubic-bezier(.5,-0.3,.6,1), opacity .6s; }

/* ---- Overgang ---- */
@keyframes sofade { from { opacity: 0; } }
@keyframes soslideR { from { opacity: 0; transform: translateX(28px); } }
@keyframes soslideL { from { opacity: 0; transform: translateX(-28px); } }
@keyframes sozoom { from { opacity: 0; transform: scale(.96); } }
@keyframes sounroll { from { clip-path: inset(0 0 100% 0); opacity: .4; } to { clip-path: inset(0 0 0 0); opacity: 1; } }
#list.so-o1 { animation: sofade .28s ease; }
#list.so-o2r { animation: soslideR .3s cubic-bezier(.2,.8,.2,1); }
#list.so-o2l { animation: soslideL .3s cubic-bezier(.2,.8,.2,1); }
#list.so-o4 { animation: sozoom .3s cubic-bezier(.2,.8,.2,1); transform-origin: 50% 0; }
#list.so-o5 { animation: sounroll .4s cubic-bezier(.2,.8,.2,1); }
::view-transition-old(root), ::view-transition-new(root) { animation-duration: .32s; }
@media (prefers-reduced-motion: reduce) {
  .fav.so-pop, .fav.so-unpop, #favonly.so-bump, #favn.so-bump, #list[class*="so-o"] { animation: none !important; }
  .so-spark, .so-ring, .so-fly { display: none; }
}
</style>
<nav class="sopick" aria-label="Velg animasjon og tema">
  <div class="row"><span class="lbl">Stjerne</span><div class="seg" role="group" aria-label="Stjerne"><button type="button" data-s="s0">Ingen</button><button type="button" data-s="s1">S1</button><button type="button" data-s="s2">S2</button><button type="button" data-s="s3">S3</button><button type="button" data-s="s4">S4</button><button type="button" data-s="s5">S5</button></div></div>
  <div class="row"><span class="lbl">Liste ↔ Kalender</span><div class="seg" role="group" aria-label="Overgang"><button type="button" data-o="o0">Ingen</button><button type="button" data-o="o1">O1</button><button type="button" data-o="o2">O2</button><button type="button" data-o="o3">O3</button><button type="button" data-o="o4">O4</button><button type="button" data-o="o5">O5</button></div>
  <div class="seg" role="group" aria-label="Tema"><button type="button" data-t="kveld">Mørkt</button><button type="button" data-t="jul">Jul</button><button type="button" data-t="lys">Lyst</button></div></div>
  <p id="sotxt"></p>
</nav>
<script>
(() => {
  const ST = { s0: "Ingen: slik det er i dag.", s1: "S1 Pop: stjerna spretter opp og vipper litt.", s2: "S2 Gnister: pop og små gnister ut fra stjerna.", s3: "S3 Pop + teller: stjerna spretter, og tallet på «★ Mine» hopper.", s4: "S4 Flyr til Mine: en stjerne flyr opp til «★ Mine», som hopper når den lander.", s5: "S5 Ring: en ring brer seg ut fra stjerna, som en dråpe i vann." };
  const OT = { o0: "Ingen: slik det er i dag.", o1: "O1 Tone inn: den nye visningen toner rolig fram.", o2: "O2 Skyv: kalenderen skyves inn fra høyre, lista fra venstre.", o3: "O3 Nettleserens egen overgang (View Transitions): myk kryssblending. Virker i Chrome, Edge og Safari 18; ellers som O1.", o4: "O4 Zoom: den nye visningen vokser litt fram.", o5: "O5 Rull ut: den nye visningen rulles ut ovenfra." };
  const parts = () => (location.hash.slice(1) || "s1-o1-kveld").split("-");
  const s = () => (ST[parts()[0]] ? parts()[0] : "s1"), o = () => (OT[parts()[1]] ? parts()[1] : "o1"), t = () => (["kveld", "jul", "lys"].includes(parts()[2]) ? parts()[2] : "kveld");
  const go = (a, b, c) => { location.hash = `${a}-${b}-${c}`; };
  const restart = (el, cls) => { if (!el) return; el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); el.addEventListener("animationend", () => el.classList.remove(cls), { once: true }); };

  // Stjerne: lista tegnes på nytt etter et trykk, så animasjonen legges på den nye knappen
  document.addEventListener("click", e => {
    const b = e.target.closest("#list .fav"); if (!b || s() === "s0") return;
    const id = b.dataset.id, on = b.getAttribute("aria-pressed") !== "true", from = b.getBoundingClientRect();
    setTimeout(() => {
      const nb = document.querySelector(`#list .fav[data-id="${CSS.escape(id)}"]`);
      if (!on) { restart(nb, "so-unpop"); return; }
      restart(nb, "so-pop");
      if (s() === "s2" && nb) for (let i = 0; i < 8; i++) { const sp = document.createElement("i"); sp.className = "so-spark"; sp.style.setProperty("--a", `${i * 45}deg`); nb.appendChild(sp); setTimeout(() => sp.remove(), 600); }
      if (s() === "s5" && nb) { const r = document.createElement("i"); r.className = "so-ring"; nb.appendChild(r); setTimeout(() => r.remove(), 600); }
      if (s() === "s3") restart(document.getElementById("favonly"), "so-bump");
      if (s() === "s4") { const to = document.getElementById("favonly").getBoundingClientRect(), f = document.createElement("span"); f.className = "so-fly"; f.textContent = "★";
        f.style.left = `${from.left + from.width / 2 - 11}px`; f.style.top = `${from.top + from.height / 2 - 11}px`; document.body.appendChild(f);
        requestAnimationFrame(() => requestAnimationFrame(() => { f.style.transform = `translate(${to.left + 18 - from.left - from.width / 2}px, ${to.top + to.height / 2 - from.top - from.height / 2}px) scale(.6)`; f.style.opacity = ".2"; }));
        setTimeout(() => { f.remove(); restart(document.getElementById("favonly"), "so-bump"); }, 620); }
    }, 0);
  }, true);

  // Overgang mellom Liste og Kalender
  const seg = document.getElementById("viewseg"), orig = seg.onclick;
  seg.onclick = e => {
    const b = e.target.closest("[data-view]"); if (!b || b.dataset.view === state.view) return;
    const toCal = b.dataset.view === "kal", list = document.getElementById("list"), mode = o();
    if (mode === "o3" && document.startViewTransition && !matchMedia("(prefers-reduced-motion: reduce)").matches) { document.startViewTransition(() => orig(e)); return; }
    orig(e);
    const cls = { o1: "so-o1", o3: "so-o1", o2: toCal ? "so-o2r" : "so-o2l", o4: "so-o4", o5: "so-o5" }[mode];
    if (cls) restart(list, cls);
  };

  function setTema(x) {
    document.querySelectorAll('link[href="tema-kveld.css"],link[href="tema-jul.css"]').forEach(l => l.remove());
    const root = document.documentElement;
    if (x === "lys") { delete root.dataset.tema; root.dataset.theme = "light"; }
    else { root.dataset.tema = x; delete root.dataset.theme; document.head.insertAdjacentHTML("beforeend", `<link rel="stylesheet" href="tema-${x}.css">`); }
  }
  function apply() {
    setTema(t());
    document.querySelectorAll(".sopick [data-s]").forEach(b => b.setAttribute("aria-pressed", b.dataset.s === s()));
    document.querySelectorAll(".sopick [data-o]").forEach(b => b.setAttribute("aria-pressed", b.dataset.o === o()));
    document.querySelectorAll(".sopick [data-t]").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === t()));
    document.getElementById("sotxt").innerHTML = `${ST[s()]}<br>${OT[o()]}<br><small>Trykk ☆ på et arrangement, og bytt mellom Liste og Kalender.</small>`;
  }
  document.querySelectorAll(".sopick [data-s]").forEach(b => b.addEventListener("click", () => go(b.dataset.s, o(), t())));
  document.querySelectorAll(".sopick [data-o]").forEach(b => b.addEventListener("click", () => go(s(), b.dataset.o, t())));
  document.querySelectorAll(".sopick [data-t]").forEach(b => b.addEventListener("click", () => go(s(), o(), b.dataset.t)));
  addEventListener("hashchange", apply);
  apply();
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
