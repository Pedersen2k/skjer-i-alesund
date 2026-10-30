"""Forhåndsvisning av tre måter å koble «I kveld»-filteret på forsiden til siden i-kveld/ (Claude-artefakt, flere filer).

1 Stripe: når «I kveld» er valgt, står en lenke «Se kvelden som tidslinje» øverst i lista.
2 Rett til siden: «I kveld» øverst åpner i-kveld/ i stedet for å filtrere lista.
3 Tidslinje på forsiden: med «I kveld» valgt får lista en grønn «Nå»-strek, og det som har startet blir grått.

Bygger på _site/ (kjør scripts/pages.py først). Velg med #v1, #v2 eller #v3 i adressen, eller velgeren nederst.
Skriver preview/ikveld/.

Kjør: python3 scripts/pages.py && python3 docs/ikveld-forside/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "ikveld"

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>I kveld på forsiden</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

extra = r"""
<style>
.kvpick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 10px max(12px, env(safe-area-inset-right, 0px)) calc(10px + env(safe-area-inset-bottom, 0px)) max(12px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; justify-content: center; background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.kvpick .seg { display: inline-flex; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.kvpick button { font: 700 14px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 14px; min-height: 42px; cursor: pointer; }
.kvpick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.kvpick p { margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; max-width: 60ch; }
body { padding-bottom: 120px; }
/* 1 Stripe */
.kvstrip { display: flex; align-items: center; gap: 12px; margin: 0 0 14px; padding: 12px 14px; border-radius: 12px; text-decoration: none; color: var(--fg);
  background: var(--surface); border: 1px solid var(--line); border-left: 5px solid #2fa865; }
.kvstrip .ic { flex: none; width: 34px; height: 34px; border-radius: 50%; display: grid; place-items: center; background: #2fa86522; color: #2fa865; font: 800 15px/1 system-ui; }
.kvstrip b { display: block; font: 700 15px/1.25 var(--font-display); }
.kvstrip small { display: block; color: var(--muted); font-size: 13px; }
.kvstrip .go { margin-left: auto; font-weight: 700; color: var(--accent); white-space: nowrap; }
html[data-tema="kveld"] .kvstrip .go { color: var(--gold); }
/* 2 Rett til siden */
.chip.when.kvlink::after, #mwhen.kvlink + * { content: " ↗"; }
/* 3 Tidslinje på forsiden */
.kvnow { position: relative; height: 0; margin: 4px 0 8px; border-top: 2px solid #2fa865; }
html[data-tema="kveld"] .kvnow, html[data-tema="jul"] .kvnow { border-color: #7ee0a1; }
.kvnow span { position: absolute; left: 0; top: -11px; font: 700 12px/20px var(--font-mono); color: #fff; background: #2fa865; border-radius: 6px; padding: 0 6px; }
html[data-tema="kveld"] .kvnow span, html[data-tema="jul"] .kvnow span { background: #7ee0a1; color: #0b2a17; }
.ev.kvpast { opacity: .5; }
.kvrel { display: inline-flex; align-items: center; gap: 5px; font: 700 11.5px/1 var(--font-body); border-radius: 999px; padding: 4px 8px; white-space: nowrap; }
.kvrel.soon { color: #1e8a4f; background: #e3f4ea; border: 1px solid #1e8a4f; }
html[data-tema="kveld"] .kvrel.soon, html[data-tema="jul"] .kvrel.soon { color: #7ee0a1; background: #1c3b2a; border-color: #7ee0a1; }
.kvrel.soon::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.kvrel.went { color: var(--muted); border: 1px dashed var(--line); }
</style>
<nav class="kvpick" aria-label="Velg løsning">
  <div class="seg" role="group"><button type="button" data-v="v1">1 Stripe</button><button type="button" data-v="v2">2 Rett til siden</button><button type="button" data-v="v3">3 Tidslinje her</button></div>
  <p id="kvtxt"></p>
</nav>
<script>
(() => {
  const TXT = {
    v1: "«I kveld» filtrerer lista som i dag. Øverst i lista står en lenke til tidslinjen på i-kveld/.",
    v2: "Trykk «I kveld» øverst: siden i-kveld/ åpnes i stedet for at lista filtreres. Forsiden er ellers som før.",
    v3: "Med «I kveld» valgt får lista en grønn Nå-strek, «om 20 min» og grå kort for det som har startet. Ingen ny side.",
  };
  const v = () => (["v1", "v2", "v3"].includes(location.hash.slice(1)) ? location.hash.slice(1) : "v1");
  const oslo = () => { const p = Object.fromEntries(new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Oslo", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date()).map(x => [x.type, x.value])); return +p.hour * 60 + +p.minute; };
  const hm = m => String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0");
  const mins = t => { const [h, m] = t.split(":").map(Number); return h * 60 + m; };
  const setWhen = w => { state.when = w; document.querySelectorAll("#when [data-w]").forEach(x => x.setAttribute("aria-pressed", x.dataset.w === w)); const m = document.getElementById("mwhen"); if (m) m.value = w; };
  const orig = render;
  render = function () {
    orig();
    if (state.when !== "ikveld" || state.view === "kal") return;
    const now = oslo(), list = document.getElementById("list");
    const cards = [...list.querySelectorAll("article.ev")].map(a => { const t = a.querySelector(".meta .t")?.textContent.match(/(\d\d):(\d\d)/); return { a, m: t ? mins(t[0]) : null }; });
    if (v() === "v1") {
      const left = cards.filter(c => c.m !== null && c.m >= now).length;
      list.insertAdjacentHTML("afterbegin", `<a class="kvstrip" href="i-kveld/"><span class="ic">◷</span><span><b>Se kvelden som tidslinje</b><small>${left ? `${left} ${left === 1 ? "arrangement starter" : "arrangementer starter"} etter kl. ${hm(now)}` : "Alt i dag har startet"}</small></span><span class="go">I kveld →</span></a>`);
    }
    if (v() === "v3") {
      let put = false;
      for (const c of cards) {
        if (c.m === null) continue;
        const d = c.m - now, meta = c.a.querySelector(".meta");
        if (!put && d >= 0) { c.a.insertAdjacentHTML("beforebegin", `<div class="kvnow"><span>Nå ${hm(now)}</span></div>`); put = true; }
        if (d < 0) { c.a.classList.add("kvpast"); meta.insertAdjacentHTML("beforeend", `<span class="kvrel went">startet ${hm(c.m)}</span>`); }
        else if (d <= 90) meta.insertAdjacentHTML("beforeend", `<span class="kvrel soon">${d === 0 ? "starter nå" : "om " + (d >= 60 ? `${Math.floor(d / 60)} t ${d % 60 ? (d % 60) + " min" : ""}` : `${d} min`)}</span>`);
      }
      const last = cards.filter(c => c.m !== null).pop();
      if (!put && last) last.a.insertAdjacentHTML("afterend", `<div class="kvnow"><span>Nå ${hm(now)}</span></div>`);
    }
  };
  // 2: «I kveld» øverst åpner siden i stedet for å filtrere
  document.addEventListener("click", e => { const b = e.target.closest('#when [data-w="ikveld"]'); if (b && v() === "v2") { e.stopImmediatePropagation(); e.preventDefault(); location.href = "i-kveld/"; } }, true);
  document.addEventListener("change", e => { if (e.target.id === "mwhen" && e.target.value === "ikveld" && v() === "v2") { e.stopImmediatePropagation(); location.href = "i-kveld/"; } }, true);
  function apply() {
    const cur = v();
    document.querySelectorAll(".kvpick [data-v]").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === cur));
    document.getElementById("kvtxt").textContent = TXT[cur];
    const chip = document.querySelector('#when [data-w="ikveld"]');
    if (chip) { chip.classList.toggle("kvlink", cur === "v2"); chip.textContent = cur === "v2" ? "I kveld ↗" : "I kveld"; }
    const opt = document.querySelector('#mwhen option[value="ikveld"]');
    if (opt) opt.textContent = cur === "v2" ? "I kveld ↗" : "I kveld";
    setWhen(cur === "v2" ? "alt" : "ikveld");
    render();
  }
  document.querySelectorAll(".kvpick [data-v]").forEach(b => b.addEventListener("click", () => { location.hash = b.dataset.v; }));
  addEventListener("hashchange", () => { apply(); scrollTo(0, 0); });
  // Programmet hentes asynkront; vent til lista er fylt første gang
  const wait = setInterval(() => { if (typeof E !== "undefined" && E.length) { clearInterval(wait); apply(); } }, 100);
})();
</script>
"""
page = page.rstrip() + "\n" + extra

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "i-kveld").mkdir()
(OUT / "index.html").write_text(page)
for f in ("stil.css", "tema-kveld.css", "tema-jul.css"):
    shutil.copy(SITE / f, OUT / f)
for f in ("events.json", "kino.json"):
    if (SITE / "data" / f).exists():
        shutil.copy(SITE / "data" / f, OUT / "data" / f)
kv = (SITE / "i-kveld" / "index.html").read_text().replace('src="https://gc.zgo.at/count.js"', 'src=""')
(OUT / "i-kveld" / "index.html").write_text(kv)
print("Skrev", OUT)
