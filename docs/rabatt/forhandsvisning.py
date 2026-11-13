"""Forhåndsvisning av filter for rabatterte billetter (student, barn og unge, DNB-kunde, tidlig kjøp) på forsiden.

Rabattene finnes i dag bare som tekst i notatet («Rabatt: Studentbillett / ÅSS 179 kr.»), fra billettypene på Tikkio.
Forhåndsvisningen leser dem ut av notatet i nettleseren. Bygges det, bør sync.py lagre dem som eget felt
(`discounts`) og ta med alle rabattbillettene, ikke bare de to billigste som i dag.

Forslagene:
R1 nye valg i Pris-menyen (minst endring), R2 egen «% Rabatt»-knapp ved ★ Mine med en liten meny,
R3 «Vis prisen for: Voksen | Student | Barn og unge» over lista (kortene viser din pris),
R4 rabattmerker på kortene (trykk på et merke for å filtrere), R5 en stripe som kinostripa.

Bygger på _site/ (kjør scripts/pages.py først). Skriver preview/rabatt/. Valg i adressen: #r1-kveld osv.

Kjør: python3 scripts/pages.py && python3 docs/rabatt/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "rabatt"

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Rabattfilter</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)


def hook(old, new):
    global page
    assert old in page, old
    page = page.replace(old, new)


# Kroker forslagene bruker: filter i matchesBase() og et ekstra merke ved prisen på kortet
hook("  priceOk(e) &&\n", "  priceOk(e) && (!window.DISCOK || window.DISCOK(e)) &&\n")
hook("${priceHtml(e)}${fewHtml(e)}</div>", "${priceHtml(e)}${window.DISCPILL ? window.DISCPILL(e) : \"\"}${fewHtml(e)}</div>")

extra = r"""
<style>
.rbpick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 8px max(10px, env(safe-area-inset-right, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(10px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; justify-content: center; background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.rbpick .lbl { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: #fff9; }
.rbpick .seg { display: inline-flex; flex-wrap: wrap; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.rbpick button { font: 700 13px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 10px; min-height: 38px; cursor: pointer; }
.rbpick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.rbpick p { margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; max-width: 72ch; }
.rbpick .row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; justify-content: center; }
body { padding-bottom: 210px; }

/* Rabattmerke på kortet */
.disc { font: 700 10.5px/1 var(--font-body); color: var(--sea, #0f6e74); background: color-mix(in srgb, var(--sea, #0f6e74) 12%, transparent); border: 1px solid color-mix(in srgb, var(--sea, #0f6e74) 40%, transparent); border-radius: 99px; padding: 4px 7px; white-space: nowrap; cursor: pointer; }
html[data-tema] .disc { color: #7fd6c8; background: #7fd6c81a; border-color: #7fd6c855; }
.disc b { font: 700 10.5px/1 var(--font-mono); }
.discs { display: flex; flex-direction: column; gap: 4px; align-items: end; }
.disc.on { background: var(--accent); color: var(--accent-ink); border-color: var(--accent); }

/* R2: knapp + liten meny */
#rbbtn { position: relative; }
#rbbtn .n { font: 700 11px/1 var(--font-mono); padding: 3px 6px; border-radius: 99px; background: var(--accent); color: var(--accent-ink); }
.rbpop { position: fixed; z-index: 40; margin-top: 6px; width: min(330px, calc(100vw - 32px)); padding: 14px; border-radius: 14px; border: 1px solid var(--line); background: var(--surface); box-shadow: 0 14px 40px #0006; display: grid; gap: 10px; }
.rbpop h4 { margin: 0; font: 800 15px var(--font-display); }
.rbpop .opts { display: flex; flex-wrap: wrap; gap: 6px; }
.rbpop .opts button, .rbseg button, .rbstrip button { font: 600 13.5px var(--font-body); min-height: 40px; padding: 0 12px; border-radius: 999px; border: 1px solid var(--line); background: var(--bg); color: var(--fg); cursor: pointer; display: inline-flex; gap: 6px; align-items: center; }
.rbpop .opts button[aria-pressed="true"], .rbstrip button[aria-pressed="true"] { background: var(--accent); color: var(--accent-ink); border-color: var(--accent); }
.rbpop .opts b, .rbstrip b { font: 700 11.5px var(--font-mono); opacity: .8; }
.rbpop small { color: var(--muted); font-size: 12.5px; line-height: 1.35; }

/* R3: «Vis prisen for» */
.rbseg { margin: 8px 0 6px; display: grid; gap: 6px; }
.rbseg .lab { font: 600 12px var(--font-mono); color: var(--muted); letter-spacing: .04em; text-transform: uppercase; }
.rbseg .sg { display: grid; grid-template-columns: repeat(3, 1fr); gap: 3px; padding: 3px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
.rbseg .sg button { border: 0; border-radius: 7px; background: transparent; color: var(--muted); justify-content: center; min-height: 40px; }
.rbseg .sg button[aria-pressed="true"] { background: var(--fg); color: var(--bg); }
.rbseg .only { font-size: 13.5px; color: var(--muted); display: flex; gap: 8px; align-items: center; min-height: 32px; }
.rbseg .only input { width: 18px; height: 18px; accent-color: var(--accent); }
.price .was { display: block; text-align: right; font: 500 11px var(--font-mono); color: var(--muted); text-decoration: line-through; }
.price .who { display: block; text-align: right; font: 700 10px var(--font-body); color: #7fd6c8; letter-spacing: .02em; }
html:not([data-tema]) .price .who { color: var(--sea, #0f6e74); }

/* R5: stripe */
.rbstrip { display: flex; flex-wrap: wrap; gap: 8px 10px; align-items: center; margin: 4px 0 14px; padding: 10px 14px; border-radius: 10px; border: 1px solid var(--line); background: color-mix(in srgb, #7fd6c8 10%, var(--surface)); font-size: 14px; }
.rbstrip .t { flex: 1 1 200px; }
.rbstrip .x { border-style: dashed; color: var(--muted); }
@media (max-width: 640px) {
  html.r2 .qwrap { grid-column: span 2; }
  html.r2 #rbbtn { order: 2; grid-column: span 1; justify-content: center; min-height: 44px; padding-inline: 4px; }
  .rbpop { left: 16px; right: 16px; width: auto; }
}
</style>
<nav class="rbpick" aria-label="Velg forslag og tema">
  <div class="row"><span class="lbl">Forslag</span><div class="seg" role="group" aria-label="Forslag"><button type="button" data-v="r0">Nå</button><button type="button" data-v="r1">R1</button><button type="button" data-v="r2">R2</button><button type="button" data-v="r3">R3</button><button type="button" data-v="r4">R4</button><button type="button" data-v="r5">R5</button></div>
  <div class="seg" role="group" aria-label="Tema"><button type="button" data-t="kveld">Mørkt</button><button type="button" data-t="jul">Jul</button><button type="button" data-t="lys">Lyst</button></div></div>
  <p id="rbtxt"></p>
</nav>
<script>
(() => {
  const TXT = {
    r0: "Nå: rabattene står bare i notatet på kortet («Rabatt: Studentbillett 179 kr»). Ingen måte å filtrere på.",
    r1: "R1 Pris-menyen: tre nye valg under «Rabatt» i Pris-menyen (Studentpris, Barn og unge, DNB-kunde). Velger du ett, får kortene et merke med rabattprisen. Minst endring, virker likt på mobil og PC. Mitt valg.",
    r2: "R2 Egen knapp: «% Rabatt» ved ★ Mine åpner en liten meny med rabattypene og antall. På mobil deler den raden med søk og Mine.",
    r3: "R3 Vis prisen for: Voksen | Student | Barn og unge over lista. Kortene viser din pris stort og ordinær pris overstreket. Huk av «bare de med …» for å filtrere. Valget huskes.",
    r4: "R4 Merker på kortene: alle kort med kjent rabatt får små merker («Student 179 kr»). Trykk på et merke for å vise bare de med samme rabatt. Ingen nye knapper i filtrene.",
    r5: "R5 Stripe: en stripe som kinostripa («Studentpris på 7 arrangementer, fra 100 kr»), med knapper for hver rabattype.",
  };
  const KINDS = [
    ["student", "Student", "Studentpris", /student|ÅSS/i],
    ["ung", "Barn og unge", "Barn og unge", /barn|ungdom|under \d+|junior/i],
    ["dnb", "DNB-kunde", "DNB-kunde", /DNB|DBN/i],
    ["tidlig", "Tidlig kjøp", "Tidlig kjøp", /early|presale|tidlig/i],
  ];
  const KIND = Object.fromEntries(KINDS.map(k => [k[0], k]));
  // Rabatter fra notatet: «Rabatt: navn 179 kr, navn 100 kr.» og «gratis for barn …»
  const cache = new Map();
  function discs(e) {
    if (cache.has(e.id)) return cache.get(e.id);
    const n = e.note || "", out = [];
    const m = n.match(/Rabatt: (.*?\d+ kr)\./);
    if (m) for (const part of m[1].split(/, (?=[^,]*\d+ kr)/)) {
      const p = part.match(/^(.*?)\s(\d+) kr$/); if (!p) continue;
      const name = p[1], price = +p[2];
      const k = KINDS.find(k => k[3].test(name) && !(k[0] === "ung" && /voksen/i.test(name)));
      if (k && !out.some(o => o.k === k[0])) out.push({ k: k[0], price });
    }
    if (/gratis for barn/i.test(n) && !out.some(o => o.k === "ung")) out.push({ k: "ung", price: 0 });
    cache.set(e.id, out); return out;
  }
  const discOf = (e, k) => discs(e).find(d => d.k === k);
  const kr = p => p === 0 ? "gratis" : p + " kr";
  const upcoming = () => E.filter(e => e.d >= TODAY);
  const ids = k => new Set(upcoming().filter(e => discOf(e, k)).map(e => e.id));
  const count = k => ids(k).size;
  const minPrice = k => Math.min(...upcoming().map(e => discOf(e, k)).filter(Boolean).map(d => d.price));
  const live = () => KINDS.filter(k => count(k[0]));

  const parts = () => (location.hash.slice(1) || "r1-kveld").split("-");
  const v = () => (TXT[parts()[0]] ? parts()[0] : "r1"), t = () => (["kveld", "jul", "lys"].includes(parts()[1]) ? parts()[1] : "kveld");
  const go = (a, b) => { location.hash = `${a}-${b}`; };

  let disc = "", who = "voksen", only = false;
  const pill = (e, k, on) => { const d = discOf(e, k); return d ? `<span class="disc${on ? " on" : ""}" data-k="${k}">${KIND[k][1]} <b>${kr(d.price)}</b></span>` : ""; };
  const origPrice = priceHtml;

  function setup() {
    document.querySelectorAll("#rbbtn,.rbpop,.rbseg,.rbstrip,#rbgroup").forEach(x => x.remove());
    document.documentElement.classList.toggle("r2", v() === "r2");
    disc = ""; only = false;
    window.DISCOK = null; window.DISCPILL = null; priceHtml = origPrice;
    const V = v();
    if (V === "r1" || V === "r2" || V === "r5") {
      window.DISCOK = e => !disc || !!discOf(e, disc);
      window.DISCPILL = e => disc ? pill(e, disc, false) : "";
    }
    if (V === "r1") {
      $("price").insertAdjacentHTML("beforeend", `<optgroup id="rbgroup" label="Rabatt">${live().map(k => `<option value="d:${k[0]}">${k[2]} (${count(k[0])})</option>`).join("")}</optgroup>`);
    }
    if (V === "r2") {
      $("favonly").insertAdjacentHTML("afterend", `<button id="rbbtn" class="chip" type="button" aria-expanded="false" aria-pressed="false">% Rabatt</button>`);
      $("rbbtn").onclick = ev => {
        ev.stopPropagation();
        const open = document.querySelector(".rbpop"); if (open) { open.remove(); $("rbbtn").setAttribute("aria-expanded", "false"); return; }
        const b = $("rbbtn").getBoundingClientRect();
        document.body.insertAdjacentHTML("beforeend", `<div class="rbpop" style="top:${b.bottom}px;${innerWidth > 640 ? `left:${b.left}px` : ""}"><h4>Vis bare med rabatt for …</h4><div class="opts">${live().map(k => `<button type="button" data-k="${k[0]}" aria-pressed="${disc === k[0]}">${k[1]} <b>${count(k[0])}</b></button>`).join("")}</div><small>Rabattene hentes fra billettsidene. Mange arrangører (bl.a. Parken) viser ikke rabattene sine, så det kan finnes flere hos arrangøren.</small></div>`);
        $("rbbtn").setAttribute("aria-expanded", "true");
      };
    }
    if (V === "r3") {
      $("viewseg").insertAdjacentHTML("afterend", `<div class="rbseg"><span class="lab">Vis prisen for</span><div class="sg">${[["voksen", "Voksen"], ["student", "Student"], ["ung", "Barn og unge"]].map(([k, l]) => `<button type="button" data-who="${k}" aria-pressed="${who === k}">${l}</button>`).join("")}</div><label class="only" ${who === "voksen" ? "hidden" : ""}><input type="checkbox" id="rbonly"> Bare de med ${who === "student" ? "studentpris" : "pris for barn og unge"} (<span id="rbn"></span>)</label></div>`);
      window.DISCOK = e => who === "voksen" || !only || !!discOf(e, who);
      priceHtml = e => {
        const d = who !== "voksen" && discOf(e, who);
        if (!d || e.soldOut) return origPrice(e);
        return `<span class="price"><span class="who">${KIND[who][1]}</span>${kr(d.price)}${e.price ? `<span class="was">${esc(e.price)}</span>` : ""}</span>`;
      };
    }
    if (V === "r4") {
      window.DISCOK = e => !disc || !!discOf(e, disc);
      window.DISCPILL = e => { const d = discs(e); return d.length ? `<span class="discs">${d.map(x => pill(e, x.k, disc === x.k)).join("")}</span>` : ""; };
    }
    if (V === "r5") {
      const s = $("kinostrip") || $("list");
      s.insertAdjacentHTML("beforebegin", `<div class="rbstrip"></div>`);
    }
    $("price").value = state.price = "";
    render();
  }
  function stripHtml() {
    const k = disc || "student";
    return `<span class="t">${disc ? `Viser ${count(k)} arrangementer med <b style="font:inherit;opacity:1">${KIND[k][2].toLowerCase()}</b>` : `Studentpris på <b style="font:inherit;opacity:1">${count("student")} arrangementer</b>, fra ${kr(minPrice("student"))}`}</span>${live().map(x => `<button type="button" data-k="${x[0]}" aria-pressed="${disc === x[0]}">${x[1]} <b>${count(x[0])}</b></button>`).join("")}${disc ? `<button type="button" class="x" data-k="">Vis alle</button>` : ""}`;
  }
  const origRender = render;
  render = function () {
    origRender();
    const st = document.querySelector(".rbstrip"); if (st) st.innerHTML = stripHtml();
    if ($("rbbtn")) { $("rbbtn").innerHTML = disc ? `% ${KIND[disc][1]} <span class="n">${count(disc)}</span>` : "% Rabatt"; $("rbbtn").setAttribute("aria-pressed", !!disc); }
    if ($("rbn")) $("rbn").textContent = count(who);
  };
  // Pris-menyen: «d:student» er et rabattvalg, ellers vanlig prisfilter
  $("price").addEventListener("change", e => {
    const val = e.target.value;
    if (val.startsWith("d:")) { e.stopImmediatePropagation(); disc = val.slice(2); state.price = ""; render(); }
    else disc = "";
  }, true);
  document.addEventListener("click", e => {
    const b = e.target.closest(".rbpop [data-k], .rbstrip [data-k], .disc[data-k]");
    if (b) { e.preventDefault(); e.stopPropagation(); disc = disc === b.dataset.k ? "" : b.dataset.k; const p = document.querySelector(".rbpop"); if (p) p.remove(); render(); return; }
    const w = e.target.closest(".rbseg [data-who]");
    if (w) { who = w.dataset.who; only = false; setup(); return; }
    if (!e.target.closest(".rbpop")) { const p = document.querySelector(".rbpop"); if (p) p.remove(); }
  }, true);
  document.addEventListener("change", e => { if (e.target.id === "rbonly") { only = e.target.checked; render(); } });

  function setTema(x) {
    document.querySelectorAll('link[href="tema-kveld.css"],link[href="tema-jul.css"]').forEach(l => l.remove());
    const root = document.documentElement;
    if (x === "lys") { delete root.dataset.tema; root.dataset.theme = "light"; }
    else { root.dataset.tema = x; delete root.dataset.theme; document.head.insertAdjacentHTML("beforeend", `<link rel="stylesheet" href="tema-${x}.css">`); }
  }
  function applyHash() {
    setTema(t());
    document.querySelectorAll(".rbpick [data-v]").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === v()));
    document.querySelectorAll(".rbpick [data-t]").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === t()));
    $("rbtxt").textContent = TXT[v()];
    setup();
  }
  document.querySelectorAll(".rbpick [data-v]").forEach(b => b.addEventListener("click", () => go(b.dataset.v, t())));
  document.querySelectorAll(".rbpick [data-t]").forEach(b => b.addEventListener("click", () => go(v(), b.dataset.t)));
  addEventListener("hashchange", applyHash);
  window.RB = { discs, count };
  const wait = setInterval(() => { if (typeof E !== "undefined" && E.length) { clearInterval(wait); applyHash(); } }, 100);
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
