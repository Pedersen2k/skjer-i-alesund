"""Forhåndsvisning av fem forslag til tittelen på forsiden («Ka skjer i Ålesund?» i stedet for «Skjer i Ålesund»).

T0 slik det er i dag. T1 Spørsmålet (bare ny tekst, spørsmålstegnet vipper inn), T2 Retting (Hva strekes over, «Ka» skrives for hånd over),
T3 Snakkeboble (logoen sier «Ka skjer»), T4 Rullende svar (i kveld? i helga? på Parken? … stopper på i Ålesund?), T5 Neonskilt.
Alle har teksten «Ka skjer i Ålesund?» for skjermlesere og søkemotorer. Animasjonene står stille med «Reduser bevegelse».

Bygger på _site/ (kjør scripts/pages.py først). Skriver preview/tittel/. Valg i adressen: #t3-jul osv.

Kjør: python3 scripts/pages.py && python3 docs/tittel/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "tittel"

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Ka skjer-tittel</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

extra = r"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Caveat:wght@700&family=Tilt+Neon&display=swap">
<style>
.tipick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 8px max(10px, env(safe-area-inset-right, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(10px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; justify-content: center; background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.tipick .seg { display: inline-flex; flex-wrap: wrap; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.tipick button { font: 700 13px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 11px; min-height: 40px; cursor: pointer; }
.tipick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.tipick .again { border: 1px solid #fff5; border-radius: 10px; }
.tipick p { margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; max-width: 70ch; }
.tipick .row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; justify-content: center; }
body { padding-bottom: 170px; }

/* Felles: egne elementer (ikke span), så kveldstemaets gradient på «h1 span» bare treffer «Ålesund». */
h1 b, h1 i, h1 em, h1 s, h1 mark { font: inherit; font-style: inherit; }
h1 .nw { white-space: nowrap; }

/* ---- T1 Spørsmålet ---- */
h1.t1 .q { display: inline-block; color: var(--accent); transform: rotate(8deg); transform-origin: 40% 90%; animation: t1q .9s .25s cubic-bezier(.3,1.6,.5,1) both; }
@keyframes t1q { 0% { transform: rotate(-40deg) scale(.2); opacity: 0; } 60% { transform: rotate(16deg) scale(1.12); opacity: 1; } 100% { transform: rotate(8deg) scale(1); } }

/* ---- T2 Retting ---- */
h1.t2 { padding-top: .42em; }
h1.t2 .fix { position: relative; display: inline-block; }
h1.t2 s { text-decoration: none; opacity: .4; position: relative; }
h1.t2 s::after { content: ""; position: absolute; left: -6%; right: -6%; top: 52%; height: .085em; border-radius: .05em; background: var(--accent); transform: rotate(-7deg) scaleX(0); transform-origin: 0 50%; animation: t2strek .45s .35s ease-out forwards; }
@keyframes t2strek { to { transform: rotate(-7deg) scaleX(1); } }
h1.t2 b { position: absolute; left: 50%; bottom: 72%; font: 700 .78em/1 "Caveat", cursive; color: var(--accent); white-space: nowrap; letter-spacing: 0; transform: translateX(-50%) rotate(-9deg); clip-path: inset(0 100% 0 0); animation: t2skriv .5s .85s steps(8, end) forwards; }
h1.t2 b::after { content: "‸"; position: absolute; left: 50%; top: 92%; font-size: .55em; transform: translateX(-50%); opacity: .8; }
@keyframes t2skriv { to { clip-path: inset(0 -20% -60% 0); } }

/* ---- T3 Snakkeboble ---- */
h1.t3 mark { position: relative; display: inline-block; background: var(--accent); color: var(--accent-ink, var(--bg)); padding: .04em .3em .1em; margin: 0 .06em 0 .14em; border-radius: .34em; transform-origin: -10% 90%; animation: t3pop .55s .2s cubic-bezier(.3,1.5,.5,1) both; }
h1.t3 mark::before { content: ""; position: absolute; left: -.2em; bottom: .1em; width: .42em; height: .36em; background: inherit; clip-path: polygon(100% 0, 0 100%, 100% 72%); }
@keyframes t3pop { 0% { transform: scale(.1) rotate(-12deg); opacity: 0; } 70% { transform: scale(1.06) rotate(1deg); opacity: 1; } 100% { transform: scale(1) rotate(-1.5deg); } }
h1.t3 mark .dots { display: inline-block; }
html[data-tema="jul"] h1.t3 mark { color: #3a0b12; }

/* ---- T4 Rullende svar ---- */
h1.t4 em { display: block; }
h1.t4 .roll { display: block; height: 1.12em; overflow: hidden; }
h1.t4 .track { display: block; transition: transform .45s cubic-bezier(.6,-0.25,.3,1.3); }
h1.t4 .track > i { display: block; height: 1.12em; line-height: 1.12; color: var(--accent); white-space: nowrap; }
h1.t4 .track > i:last-child { color: inherit; }
h1.t4 .dot { display: inline-flex; vertical-align: .9em; margin-left: .25em; font: 800 max(.22em, 11px)/1 var(--font-body); font-style: normal; letter-spacing: .02em; color: var(--accent-ink, #fff); background: var(--accent); border-radius: 99px; padding: .3em .55em; }

/* ---- T5 Neonskilt ---- */
h1.t5 { --neon: #ff5f8f; }
html[data-tema="jul"] h1.t5 { --neon: #ffc95c; }
html[data-tema="kveld"] h1.t5 { --neon: #ff7a5c; }
h1.t5 .sign { display: inline-block; position: relative; padding: .14em .38em .2em; border-radius: .18em; background: radial-gradient(120% 140% at 50% 40%, #241a26, #0d0a10); box-shadow: inset 0 0 0 2px #ffffff12, inset 0 0 30px #0009, 0 12px 30px #0005; font: 400 1em/1 "Tilt Neon", system-ui, sans-serif; letter-spacing: .01em; }
h1.t5 .sign::before, h1.t5 .sign::after { content: ""; position: absolute; top: .12em; width: .1em; height: .1em; border-radius: 50%; background: #ffffff30; }
h1.t5 .sign::before { left: .12em; } h1.t5 .sign::after { right: .12em; }
h1.t5 .sign b { color: #fff7f2; text-shadow: 0 0 .03em #fff, 0 0 .1em var(--neon), 0 0 .25em var(--neon), 0 0 .55em var(--neon); animation: t5flimr 2.2s .2s both; }
h1.t5 .sign b.sist { animation-delay: .9s; }
@keyframes t5flimr { 0%, 6% { opacity: .12; text-shadow: none; } 7%, 9% { opacity: 1; } 10%, 15% { opacity: .2; text-shadow: none; } 16%, 30% { opacity: 1; } 31% { opacity: .35; } 33%, 100% { opacity: 1; } }
h1.t5 .sub { display: block; font-size: .56em; margin-top: .18em; }

@media (prefers-reduced-motion: reduce) {
  h1.t1 .q, h1.t3 mark, h1.t5 .sign b { animation: none !important; }
  h1.t2 s::after { animation: none; transform: rotate(-7deg); }
  h1.t2 b { animation: none; clip-path: none; }
  h1.t4 .track { transition: none; }
}
</style>
<nav class="tipick" aria-label="Velg tittel og tema">
  <div class="row"><div class="seg" role="group" aria-label="Tittel"><button type="button" data-v="t0">I dag</button><button type="button" data-v="t1">T1</button><button type="button" data-v="t2">T2</button><button type="button" data-v="t3">T3</button><button type="button" data-v="t4">T4</button><button type="button" data-v="t5">T5</button></div>
  <div class="seg" role="group" aria-label="Tema"><button type="button" data-t="jul">Jul</button><button type="button" data-t="kveld">Mørkt</button><button type="button" data-t="lys">Lyst</button></div>
  <button type="button" class="again" id="tiagain">↻ Spill av</button></div>
  <p id="titxt"></p>
</nav>
<script>
(() => {
  const TXT = {
    t0: "I dag: «Skjer i Ålesund».",
    t1: "T1 Spørsmålet: bare ny tekst, «Ka skjer i Ålesund?», og spørsmålstegnet vipper inn. Minst endring.",
    t2: "T2 Retting: «Hva» strekes over, og «Ka» skrives for hånd over, som en lærer som retter til sunnmørsk.",
    t3: "T3 Snakkeboble: jugendgavlen i logoen spør «Ka skjer» i en boble som spretter ut.",
    t4: "T4 Rullende svar: siste del ruller gjennom i kveld, i helga, på Parken, for ungene og jula, og stopper på «i Ålesund?». Tallene kommer fra programmet.",
    t5: "T5 Neonskilt: «Ka skjer» som et neonskilt som flimrer på, som utenfor et konsertlokale.",
  };
  const h1 = document.querySelector(".brand h1");
  const parts = () => (location.hash.slice(1) || "t3-jul").split("-");
  const v = () => (TXT[parts()[0]] ? parts()[0] : "t3"), t = () => (["kveld", "jul", "lys"].includes(parts()[1]) ? parts()[1] : "jul");
  const go = (a, b) => { location.hash = `${a}-${b}`; };
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let timer;

  // Antall i kveld / helga / Parken / barn fra programmet (samme data som forsiden)
  function counts() {
    const ev = (typeof E !== "undefined" ? E : []).filter(e => e && e.date);
    const oslo = new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Oslo" }).format(new Date());
    const day = s => String(s).slice(0, 10);
    const now = new Date(oslo + "T12:00"), wd = now.getDay(), toFri = wd === 0 ? -2 : wd === 6 ? -1 : 5 - wd;
    const fri = new Date(now); fri.setDate(now.getDate() + toFri);
    const iso = d => new Intl.DateTimeFormat("sv-SE").format(d), sun = new Date(fri); sun.setDate(fri.getDate() + 2);
    const all = ev.flatMap(e => [e.date, ...(e.moreShows || [])].map(d => ({ e, d: day(d) })));
    const n = f => new Set(all.filter(f).map(x => x.e.id)).size;
    return { kveld: n(x => x.d === oslo), helg: n(x => x.d >= iso(fri) && x.d <= iso(sun)),
      parken: n(x => x.d >= oslo && /parken/i.test(x.e.venue || "")), barn: n(x => x.d >= oslo && x.e.cat === "barn") };
  }
  function t4html() {
    const c = counts(), m = new Date().getMonth();
    const w = [["i kveld?", c.kveld], ["i helga?", c.helg], ["på Parken?", c.parken], ["for ungene?", c.barn]];
    if (m === 10 || m === 11) w.push(["i jula?", 0]);
    const dot = n => (n ? `<b class="dot">${n}</b>` : "");
    return `<em aria-hidden="true">Ka skjer</em><i class="roll" aria-hidden="true"><i class="track">${w.map(([a, n]) => `<i>${a}${dot(n)}</i>`).join("")}<i>i <span>Ålesund</span>?</i></i></i>`;
  }
  const HTML = {
    t0: () => `Skjer i <span>Ålesund</span>`,
    t1: () => `Ka skjer <i class="nw">i <span>Ålesund</span><b class="q">?</b></i>`,
    t2: () => `<i class="fix"><s>Hva</s><b>Ka</b></i> skjer <i class="nw">i <span>Ålesund</span>?</i>`,
    t3: () => `<mark>Ka skjer</mark> <i class="nw">i <span>Ålesund</span>?</i>`,
    t4: t4html,
    t5: () => `<i class="sign"><b>Ka</b> <b class="sist">skjer</b></i><i class="sub">i <span>Ålesund</span>?</i>`,
  };
  function roll() {
    clearTimeout(timer);
    const tr = h1.querySelector(".track"); if (!tr) return;
    const items = tr.children.length; let i = 0;
    tr.style.transform = "";
    if (REDUCE) { tr.style.transform = `translateY(${-(items - 1) * 1.12}em)`; return; }
    const step = () => { i++; tr.style.transform = `translateY(${-i * 1.12}em)`; if (i < items - 1) timer = setTimeout(step, 1300); };
    timer = setTimeout(step, 1400);
  }
  function setTema(x) {
    document.querySelectorAll('link[href="tema-kveld.css"],link[href="tema-jul.css"]').forEach(l => l.remove());
    document.querySelectorAll(".jd-wreath,.jd-wreath-note").forEach(el => (el.style.display = x === "jul" ? "" : "none"));
    const root = document.documentElement;
    if (x === "lys") { delete root.dataset.tema; root.dataset.theme = "light"; }
    else { root.dataset.tema = x; delete root.dataset.theme; document.head.insertAdjacentHTML("beforeend", `<link rel="stylesheet" href="tema-${x}.css">`); }
  }
  function draw() {
    h1.className = v();
    h1.innerHTML = HTML[v()]();
    if (v() === "t0") h1.removeAttribute("aria-label"); else h1.setAttribute("aria-label", "Ka skjer i Ålesund?");
    roll();
  }
  function apply() {
    setTema(t());
    draw();
    document.querySelectorAll(".tipick [data-v]").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === v()));
    document.querySelectorAll(".tipick [data-t]").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === t()));
    document.getElementById("titxt").textContent = TXT[v()];
  }
  document.querySelectorAll(".tipick [data-v]").forEach(b => b.addEventListener("click", () => go(b.dataset.v, t())));
  document.querySelectorAll(".tipick [data-t]").forEach(b => b.addEventListener("click", () => go(v(), b.dataset.t)));
  document.getElementById("tiagain").addEventListener("click", draw);
  addEventListener("hashchange", apply);
  apply();
  // T4 trenger programmet: tegn på nytt når data er lastet
  let tries = 0; const wait = setInterval(() => { if ((typeof E !== "undefined" ? E : []).length || ++tries > 40) { clearInterval(wait); if (v() === "t4") draw(); } }, 250);
})();
</script>
"""
page = page.rstrip() + "\n" + extra
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)
(OUT / "index.html").write_text(page)
for f in ("stil.css", "tema-kveld.css", "tema-jul.css"):
    if (SITE / f).exists():
        shutil.copy(SITE / f, OUT / f)
for f in ("events.json", "kino.json"):
    if (SITE / "data" / f).exists():
        shutil.copy(SITE / "data" / f, OUT / "data" / f)
print("Skrev", OUT)
