"""Forhåndsvisning av dagsoverskrifter som blir liggende øverst mens man blar (Claude-artefakt, flere filer).

«Nå» er slik forsiden er i dag. D1 datokolonnen følger med, D2 et bånd over hele bredden, D3 en liten pille som flyter
øverst, D4 en ukestripe med dagene som knapper. Alle tar hensyn til filterlinja, som glir bort når man blar nedover på
mobil og kommer tilbake når man blar litt opp. Velgeren nederst bytter også tema (mørkt, jul, lyst).

Bygger på _site/ (kjør scripts/pages.py først). Skriver preview/dagsoverskrift/. Variant i adressen: #d1 … #d4 (#na = i dag).

Kjør: python3 scripts/pages.py && python3 docs/dagsoverskrift/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "dagsoverskrift"

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Dagsoverskrift som følger med</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

extra = r"""
<style>
:root { --top: 0px; }
.dspick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 8px max(10px, env(safe-area-inset-right, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(10px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; justify-content: center; background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.dspick .seg { display: inline-flex; flex-wrap: wrap; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.dspick button { font: 700 13.5px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 12px; min-height: 40px; cursor: pointer; }
.dspick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.dspick p { margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; max-width: 62ch; }
body { padding-bottom: 150px; }

/* D1 Datokolonnen følger med */
body.ds-d1 .day > .date { position: sticky; top: calc(var(--top) + 12px); align-self: start; transition: top .22s ease; }

/* D2 Bånd over hele bredden */
body.ds-d2 .day { grid-template-columns: 1fr; padding-top: 0; }
body.ds-d2 .day > .date { display: none; }
.dband { position: sticky; top: var(--top); z-index: 3; display: flex; align-items: baseline; gap: 10px; margin: 0 -2px 10px; padding: 10px 12px; border-radius: 0 0 12px 12px;
  background: color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); transition: top .22s ease; }
.dband b { font: 800 18px/1.1 var(--font-display); }
.dband b em { font-style: normal; color: var(--accent); }
.dband span { font-size: 12.5px; color: var(--muted); margin-left: auto; white-space: nowrap; }

/* D3 Flytende pille */
.dpill { position: fixed; z-index: 4; left: 50%; top: calc(var(--top) + 10px); transform: translate(-50%, -8px); opacity: 0; pointer-events: none;
  padding: 7px 14px; border-radius: 999px; background: var(--fg); color: var(--bg); font: 700 13px/1.2 var(--font-body); box-shadow: 0 8px 20px #0006; transition: opacity .2s, transform .2s, top .22s ease; white-space: nowrap; }
.dpill.on { opacity: 1; transform: translate(-50%, 0); }
.dpill small { font-weight: 500; opacity: .75; margin-left: 6px; }

/* D4 Ukestripe */
.dweek { position: sticky; top: var(--top); z-index: 4; display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; padding: 8px 0; margin-bottom: 4px;
  background: color-mix(in srgb, var(--bg) 90%, transparent); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); transition: top .22s ease; }
.dweek button { border: 1px solid var(--line); background: var(--surface); color: var(--fg); border-radius: 12px; min-height: 52px; padding: 4px 0; cursor: pointer; display: grid; gap: 2px; place-items: center; font: inherit; }
.dweek button small { font: 600 10.5px/1 var(--font-mono); text-transform: uppercase; color: var(--muted); }
.dweek button b { font: 800 17px/1 var(--font-display); }
.dweek button i { width: 5px; height: 5px; border-radius: 50%; background: var(--accent); }
.dweek button[disabled] { opacity: .35; cursor: default; }
.dweek button[disabled] i { visibility: hidden; }
.dweek button.on { background: var(--accent); border-color: var(--accent); color: var(--accent-ink, #1a0b07); }
.dweek button.on small { color: inherit; }
.dweek button.on i { background: currentColor; }
</style>
<div class="dpill" id="dpill" aria-hidden="true"></div>
<nav class="dspick" aria-label="Velg variant og tema">
  <div class="seg" role="group" aria-label="Variant"><button type="button" data-v="na">Nå</button><button type="button" data-v="d1">D1</button><button type="button" data-v="d2">D2</button><button type="button" data-v="d3">D3</button><button type="button" data-v="d4">D4</button></div>
  <div class="seg" role="group" aria-label="Tema"><button type="button" data-t="kveld">Mørkt</button><button type="button" data-t="jul">Jul</button><button type="button" data-t="lys">Lyst</button></div>
  <p id="dstxt"></p>
</nav>
<script>
(() => {
  const TXT = {
    na: "Nå: slik det er i dag. Datoen står bare ved første arrangement den dagen.",
    d1: "D1 Datoen følger med: datokolonnen til venstre blir stående øverst til neste dag skyver den bort. Minst endring.",
    d2: "D2 Dagsbånd: et bånd over hele bredden med dag, dato og antall. Det neste båndet skyver det forrige bort.",
    d3: "D3 Flytende pille: en liten pille øverst viser hvilken dag du er på. Lista er som før.",
    d4: "D4 Ukestripe: de neste 7 dagene som knapper øverst. Dagen du er på lyser, og trykk hopper til en dag.",
  };
  const FULL = { "man": "mandag", "tir": "tirsdag", "ons": "onsdag", "tor": "torsdag", "fre": "fredag", "lør": "lørdag", "søn": "søndag" };
  const v = () => (Object.keys(TXT).includes(location.hash.slice(1)) ? location.hash.slice(1) : "d1");
  const ctl = document.querySelector(".controls");
  const info = s => { const d = s.querySelector(".date"); const wd = (d?.querySelector(".wd")?.textContent || "").trim().toLowerCase(), num = d?.querySelector(".num")?.textContent.trim(), mo = d?.querySelector(".mo")?.textContent.trim().toLowerCase(), rel = d?.querySelector(".rel")?.textContent.trim() || "";
    return { wd, full: FULL[wd] || wd, num, mo, rel, n: s.querySelectorAll(".events > article").length }; };
  function setTop() { const gone = ctl.classList.contains("gone") || ctl.closest(".kalmode-hidden"); const h = gone ? 0 : ctl.getBoundingClientRect().height; document.documentElement.style.setProperty("--top", `${Math.max(0, h)}px`); }
  function current() { const t = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--top")) + 60; let cur = null;
    for (const s of document.querySelectorAll("#list .day")) { if (s.getBoundingClientRect().top <= t) cur = s; else break; } return cur; }
  function decorate() {
    const cur = v(), list = document.getElementById("list");
    list.querySelectorAll(".dband,.dweek").forEach(x => x.remove());
    const days = [...list.querySelectorAll(".day")];
    if (cur === "d2") days.forEach(s => { const i = info(s); s.insertAdjacentHTML("afterbegin", `<div class="dband"><b>${i.full[0].toUpperCase() + i.full.slice(1)} <em>${i.num}. ${i.mo}</em></b><span>${i.rel ? i.rel + " · " : ""}${i.n} ${i.n === 1 ? "arrangement" : "arrangementer"}</span></div>`); });
    if (cur === "d4" && days.length) {
      const map = new Map(days.map(s => [s.querySelector(".date .num")?.textContent.trim() + s.querySelector(".date .mo")?.textContent.trim(), s]));
      const now = new Date(), btns = [];
      for (let k = 0; k < 7; k++) { const d = new Date(now); d.setDate(now.getDate() + k); const key = String(d.getDate()) + ["jan","feb","mar","apr","mai","jun","jul","aug","sep","okt","nov","des"][d.getMonth()];
        const wd = ["søn","man","tir","ons","tor","fre","lør"][d.getDay()]; const s = [...map.entries()].find(([kk]) => kk.toLowerCase() === key)?.[1];
        btns.push(`<button type="button" ${s ? `data-k="${days.indexOf(s)}"` : "disabled"}><small>${k === 0 ? "i dag" : wd}</small><b>${d.getDate()}</b><i></i></button>`); }
      list.insertAdjacentHTML("afterbegin", `<div class="dweek" role="group" aria-label="Hopp til dag">${btns.join("")}</div>`);
    }
    tick();
  }
  function tick() {
    setTop();
    const cur = v(), s = current(), pill = document.getElementById("dpill");
    if (cur === "d3" && s && s !== document.querySelector("#list .day")) { const i = info(s); pill.innerHTML = `${i.full[0].toUpperCase() + i.full.slice(1)} ${i.num}. ${i.mo}<small>${i.rel || i.n + " arr."}</small>`; pill.classList.add("on"); }
    else pill.classList.remove("on");
    if (cur === "d4") { const days = [...document.querySelectorAll("#list .day")], k = s ? days.indexOf(s) : 0;
      document.querySelectorAll(".dweek button").forEach(b => b.classList.toggle("on", +b.dataset.k === k)); }
  }
  addEventListener("scroll", () => requestAnimationFrame(tick), { passive: true });
  new MutationObserver(() => requestAnimationFrame(tick)).observe(ctl, { attributes: true, attributeFilter: ["class"] });
  document.addEventListener("click", e => { const b = e.target.closest(".dweek button[data-k]"); if (!b) return;
    const s = document.querySelectorAll("#list .day")[+b.dataset.k]; const top = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--top"));
    scrollTo({ top: s.getBoundingClientRect().top + scrollY - top - 70, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" }); });
  const orig = render;
  render = function () { orig(); decorate(); };
  function setTema(t) {
    document.querySelectorAll('link[href="tema-kveld.css"],link[href="tema-jul.css"]').forEach(l => l.remove());
    const root = document.documentElement;
    if (t === "lys") { delete root.dataset.tema; root.dataset.theme = "light"; }
    else { root.dataset.tema = t; delete root.dataset.theme; document.head.insertAdjacentHTML("beforeend", `<link rel="stylesheet" href="tema-${t}.css">`); }
    document.querySelectorAll(".dspick [data-t]").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === t));
  }
  function apply() {
    const cur = v();
    document.body.className = document.body.className.replace(/\bds-\w+/g, "").trim() + " ds-" + cur;
    document.querySelectorAll(".dspick [data-v]").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === cur));
    document.getElementById("dstxt").textContent = TXT[cur];
    render();
  }
  document.querySelectorAll(".dspick [data-v]").forEach(b => b.addEventListener("click", () => { location.hash = b.dataset.v; }));
  document.querySelectorAll(".dspick [data-t]").forEach(b => b.addEventListener("click", () => setTema(b.dataset.t)));
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
