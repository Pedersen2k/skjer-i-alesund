"""Forhåndsvisning av bedre søk på forsiden (Claude-artefakt, flere filer).

«Nå» er søket slik det er i dag: tittel, sted og kategori må inneholde nøyaktig det du skriver.
S1 Tolerant søk (usynlig): æ/ø/å og aksenter likestilles, én skrivefeil per ord tåles (to i lange ord),
   notatet (artister, medvirkende) søkes også, og en liten synonymliste (nutcracker, stand up, comedy …).
S2 «Mente du …?»: søket er som i dag, men gir det null treff, foreslås nærmeste ord som faktisk finnes.
S3 Forslag mens du skriver: en liste under søkefeltet med arrangementer, steder, kategorier og egne sider.
S4 Treff andre steder: en stripe øverst i lista når søket også treffer julebord, kino eller andre datoer.
S5 S1 + S2 + S4 (Claudes valg).

Bygger på _site/ (kjør scripts/pages.py først). Skriver preview/sok/. Valg i adressen: #s5-0-kveld
(forslag, eksempelsøk nr., tema).

Kjør: python3 scripts/pages.py && python3 docs/sok/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "sok"

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Bedre søk</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)
# Kroken: forslagene kan bytte ut selve treff-regelen
old = '(!state.q || (e.title + " " + e.venue + " " + (CATS[e.cat] || "")).toLowerCase().includes(state.q));'
assert page.count(old) == 1
page = page.replace(old, '(!state.q || (window.QMATCH ? QMATCH(e, state.q) : (e.title + " " + e.venue + " " + (CATS[e.cat] || "")).toLowerCase().includes(state.q)));')

extra = r"""
<style>
.sqpick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 8px max(10px, env(safe-area-inset-right, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(10px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; justify-content: center; background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.sqpick .lbl { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: #fff9; }
.sqpick .seg { display: inline-flex; flex-wrap: wrap; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.sqpick button { font: 700 13px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 10px; min-height: 36px; cursor: pointer; }
.sqpick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.sqpick p { font-size: 12.5px; margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; max-width: 72ch; }
.sqpick .row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; justify-content: center; }
body { padding-bottom: 230px; }

/* S2 Mente du */
.mente { margin: 0; font-size: 15px; color: var(--fg); }
.mente button { font: 700 15px var(--font-body); color: var(--accent); background: none; border: 0; padding: 0 2px; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }
/* S3 Forslag mens du skriver */
.qwrap { position: relative; }
.sqsug { position: absolute; z-index: 30; left: 0; right: 0; top: calc(100% + 6px); margin: 0; padding: 6px; list-style: none; background: var(--surface); border: 1px solid var(--line); border-radius: 14px; box-shadow: 0 12px 30px #0006; max-height: 60vh; overflow: auto; }
.sqsug li button, .sqsug li a { display: grid; grid-template-columns: 22px minmax(0, 1fr) auto; gap: 10px; align-items: center; width: 100%; min-height: 44px; padding: 6px 10px; border: 0; border-radius: 10px; background: none; color: var(--fg); font: 500 14.5px/1.25 var(--font-body); text-align: left; text-decoration: none; cursor: pointer; }
.sqsug li button:hover, .sqsug li a:hover, .sqsug li .on { background: color-mix(in srgb, var(--accent) 12%, transparent); }
.sqsug .ic { width: 18px; height: 18px; color: var(--muted); }
.sqsug small { color: var(--muted); font: 600 12px var(--font-mono); white-space: nowrap; }
.sqsug .hd { padding: 8px 10px 2px; font: 700 10.5px var(--font-body); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.sqsug mark { background: none; color: var(--accent); font-weight: 700; }
/* S4 Treff andre steder */
.sqelse { display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 14px; }
.sqelse a, .sqelse button { display: inline-flex; align-items: center; gap: 8px; min-height: 40px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--line); background: var(--surface); color: var(--fg); font: 600 13.5px var(--font-body); text-decoration: none; cursor: pointer; }
.sqelse b { font: 700 12px var(--font-mono); color: var(--accent); }
.sqelse .lead { width: 100%; margin: 0; font-size: 13px; color: var(--muted); }
.sqinfo { margin: 4px 0 12px; font-size: 13.5px; color: var(--muted); }
.sqinfo b { color: var(--fg); }
</style>
<nav class="sqpick" aria-label="Velg forslag, søk og tema">
  <div class="row"><span class="lbl">Forslag</span><div class="seg" role="group" aria-label="Forslag"><button type="button" data-v="na">Nå</button><button type="button" data-v="s1">S1</button><button type="button" data-v="s2">S2</button><button type="button" data-v="s3">S3</button><button type="button" data-v="s4">S4</button><button type="button" data-v="s5">S5</button></div>
  <div class="seg" role="group" aria-label="Tema"><button type="button" data-t="kveld">Mørkt</button><button type="button" data-t="jul">Jul</button><button type="button" data-t="lys">Lyst</button></div></div>
  <div class="row"><span class="lbl">Prøv å søke</span><div class="seg" role="group" aria-label="Eksempelsøk" id="sqex"></div></div>
  <p id="sqtxt"></p>
</nav>
<script>
(() => {
  const TXT = {
    na: "Nå: tittel, sted eller kategori må inneholde nøyaktig det du skriver. Skrivefeil, ø/o og engelske ord gir null treff.",
    s1: "S1 Tolerant søk: æ/ø/å likestilles med ae/o/a, én skrivefeil per ord tåles, artistene i notatet søkes også, og noen engelske og vanlige ord oversettes. Ingenting nytt å se på, det bare virker.",
    s2: "S2 «Mente du …?»: søket er som i dag, men gir det null treff, foreslår siden det nærmeste ordet som faktisk finnes i programmet.",
    s3: "S3 Forslag mens du skriver: en liste under søkefeltet med arrangementer, steder, kategorier og egne sider (julebord, kino). Trykk for å gå rett dit.",
    s4: "S4 Treff andre steder: en stripe øverst når søket også treffer julebord, filmer på kino eller andre datoer enn filteret viser.",
    s5: "S5 S1 + S2 + S4: tolerant søk, «Mente du …?» når ingenting passer, og stripen med treff andre steder. Mitt valg (S3 kan komme senere).",
  };
  const EX = ["juletru", "notteknekkeren", "nutcracker", "kalvø", "stand up", "julebord", "løvenvol", "batman", "aalesund kirke"];
  document.getElementById("sqex").innerHTML = EX.map((q, i) => `<button type="button" data-q="${i}">${q}</button>`).join("") + `<button type="button" data-q="x">Tøm</button>`;

  const parts = () => (location.hash.slice(1) || "s5-0-kveld").split("-");
  const v = () => (TXT[parts()[0]] ? parts()[0] : "s5"), qi = () => parts()[1] || "0", t = () => (["kveld", "jul", "lys"].includes(parts()[2]) ? parts()[2] : "kveld");
  const go = (a, b, c) => { location.hash = `${a}-${b}-${c}`; };
  const has = x => v() === x || (v() === "s5" && ["s1", "s2", "s4"].includes(x));

  // Felles: likestill æ/ø/å, aksenter og «aa»
  const fold = s => s.toLowerCase().replace(/æ/g, "ae").replace(/[øö]/g, "o").replace(/[åä]/g, "a").replace(/aa/g, "a").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9 ]+/g, " ").replace(/\s+/g, " ").trim();
  // Små synonymer (engelsk og vanlige skrivemåter) → ord som står i programmet
  const SYN = { "nutcracker": "notteknekker", "christmas": "jul", "xmas": "jul", "stand up": "standup", "comedy": "standup", "komedie": "standup", "concert": "konsert", "kids": "barn", "family": "barn", "familie": "barn", "football": "aafk", "fotball": "aafk", "theatre": "teater", "theater": "teater", "church": "kirke", "kyrkje": "kirke", "dance": "dans", "club": "klubb" };
  function lev(a, b) {
    if (Math.abs(a.length - b.length) > 2) return 9;
    let p = Array.from({ length: b.length + 1 }, (_, j) => j);
    for (let i = 1; i <= a.length; i++) { const c = [i]; for (let j = 1; j <= b.length; j++) c[j] = Math.min(p[j] + 1, c[j - 1] + 1, p[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); p = c; }
    return p[b.length];
  }
  const tol = w => w.length >= 8 ? 2 : w.length >= 5 ? 1 : 0;
  // Et søkeord passer et ord i teksten hvis det er starten på ordet, eller nesten (skrivefeil)
  const wordOk = (w, toks) => toks.some(t => t.startsWith(w) || (tol(w) && (lev(w, t) <= tol(w) || (t.length > w.length && lev(w, t.slice(0, w.length)) <= tol(w)))));
  const textOf = e => fold(`${e.title} ${e.venue} ${CATS[e.cat] || ""} ${e.cat} ${e.note || ""}`);
  const cache = new Map();
  const toksOf = e => { let x = cache.get(e); if (!x) { x = textOf(e).split(" "); cache.set(e, x); } return x; };
  function expand(q) { let f = fold(q); for (const [k, s] of Object.entries(SYN)) f = f.replace(new RegExp(`\\b${k}\\b`, "g"), s); return f; }
  const tolerant = (e, q) => { const toks = toksOf(e); return expand(q).split(" ").filter(Boolean).every(w => wordOk(w, toks) || toks.join("").includes(w)); };
  const strict = (e, q) => (e.title + " " + e.venue + " " + (CATS[e.cat] || "")).toLowerCase().includes(q);
  const M = (e, q) => has("s1") ? tolerant(e, q) : strict(e, q);

  // Ordforråd for «Mente du» og forslagslista
  let VOCAB = null, FILMS = [];
  fetch("data/kino.json").then(r => r.json()).then(k => { FILMS = k.films || []; }).catch(() => {});
  function vocab() {
    if (VOCAB) return VOCAB;
    VOCAB = new Map();
    [...E, ...JB].forEach(e => `${e.title} ${e.venue} ${CATS[e.cat] || ""}`.split(/[\s,.:;!?()«»"'–—/|&+-]+/).forEach(w => { const f = fold(w); if (f.length >= 3 && !/^\d+$/.test(f) && !VOCAB.has(f)) VOCAB.set(f, w.toLowerCase()); }));
    return VOCAB;
  }
  function suggest(q) {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean), out = [];
    const cands = words.map(w => {
      const fw = fold(w); if (vocab().has(fw)) return [w];
      const best = [...vocab()].map(([f, orig]) => [orig, Math.min(lev(fw, f), f.length > fw.length ? lev(fw, f.slice(0, fw.length)) + .5 : 9)]).filter(x => x[1] <= Math.max(2, Math.ceil(fw.length / 3))).sort((a, b) => a[1] - b[1]).slice(0, 2).map(x => x[0]);
      return best.length ? best : [w];
    });
    const combos = cands.reduce((acc, c) => acc.flatMap(a => c.map(x => a.concat(x))), [[]]).map(a => a.join(" "));
    combos.forEach(c => { if (c !== q.toLowerCase() && !out.includes(c)) { const n = E.filter(e => e.d >= TODAY && M(e, c.toLowerCase())).length; if (n) out.push([c, n]); } });
    return out.slice(0, 2);
  }
  const setQ = q => { $("q").value = q; state.q = q.trim().toLowerCase(); render(); };

  // S2 og S4 legges oppå lista etter render()
  function decorate() {
    const list = $("list");
    list.querySelectorAll(".sqelse,.mente,.sqinfo").forEach(x => x.remove());
    if (!state.q) return;
    const tomt = list.querySelector(".tomt");
    if (has("s2") && tomt) {
      const s = suggest(state.q);
      if (s.length) tomt.querySelector("h3").insertAdjacentHTML("afterend", `<p class="mente">Mente du ${s.map(([c, n], i) => `${i ? "eller " : ""}<button type="button" data-mente="${esc(c)}">${esc(c)}</button> <small>(${n})</small>`).join(" ")}?</p>`);
    }
    if (has("s4")) {
      const bits = [];
      const jb = JB.filter(e => e.d >= TODAY && M(e, state.q)).length;
      if (jb) bits.push(`<a href="julebord/">Julebord-siden <b>${jb}</b></a>`);
      const fl = FILMS.filter(f => has("s1") ? fold(f.title).includes(fold(state.q)) || tolerant({ title: f.title, venue: "", cat: "", note: (f.genres || []).join(" ") }, state.q) : f.title.toLowerCase().includes(state.q)).length;
      if (fl) bits.push(`<a href="kino/">På kino <b>${fl}</b></a>`);
      if (state.when !== "alt") { const all = E.filter(e => e.d >= TODAY && matchesBase(e)).length, now = E.filter(e => e.d >= TODAY && WHEN[state.when][1](e.d) && matchesBase(e)).length; if (all > now && now) bits.push(`<button type="button" data-allq>Andre datoer <b>${all - now}</b></button>`); }
      if (bits.length) (tomt ? tomt : list.firstElementChild)?.insertAdjacentHTML(tomt ? "afterend" : "beforebegin", `<div class="sqelse"><p class="lead">Søket ditt treffer også:</p>${bits.join("")}</div>`);
    }
  }
  const orig = render;
  render = function () { orig(); if (E.length) decorate(); };
  $("list").addEventListener("click", ev => {
    const m = ev.target.closest("[data-mente]"); if (m) { ev.stopPropagation(); return setQ(m.dataset.mente); }
    const a = ev.target.closest("[data-allq]"); if (a) { ev.stopPropagation(); state.when = "alt"; syncFilters(); $("when").querySelectorAll("[data-w]").forEach(x => x.setAttribute("aria-pressed", x.dataset.w === "alt")); render(); }
  }, true);

  // S3 Forslag mens du skriver
  const IC = {
    ev: `<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>`,
    sted: `<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>`,
    kat: `<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h10M4 18h6"/></svg>`,
    side: `<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>`,
  };
  const ul = document.createElement("ul"); ul.className = "sqsug"; ul.hidden = true; $("q").parentElement.appendChild(ul);
  const hi = (s, q) => { const i = fold(s).indexOf(fold(q)); return i < 0 || fold(s).length !== s.length ? esc(s) : esc(s.slice(0, i)) + "<mark>" + esc(s.slice(i, i + q.length)) + "</mark>" + esc(s.slice(i + q.length)); };
  function sug() {
    const q = $("q").value.trim();
    if (v() !== "s3" || q.length < 2) { ul.hidden = true; return; }
    const m = e => tolerant(e, q.toLowerCase());
    const evs = E.filter(e => e.d >= TODAY && m(e)).sort((a, b) => a.d - b.d).slice(0, 4);
    const venues = [...new Set(E.map(e => e.venue))].filter(x => tolerant({ title: x, venue: "", cat: "", note: "" }, q)).slice(0, 2);
    const cats = Object.entries(CATS).filter(([k, l]) => tolerant({ title: l, venue: "", cat: k, note: "" }, q)).slice(0, 2);
    const jb = JB.filter(e => e.d >= TODAY && m(e)).length, fl = FILMS.filter(f => fold(f.title).includes(fold(q))).length;
    const rows = [];
    if (evs.length) rows.push(`<li class="hd">Arrangementer</li>` + evs.map(e => `<li><button type="button" data-sev="${esc(e.id)}">${IC.ev}<span>${hi(e.title, q)}</span><small>${WD[e.d.getDay()]} ${e.d.getDate()}. ${MO[e.d.getMonth()]}</small></button></li>`).join(""));
    if (venues.length || cats.length) rows.push(`<li class="hd">Steder og kategorier</li>` + venues.map(x => `<li><button type="button" data-sv="${esc(x)}">${IC.sted}<span>${hi(x, q)}</span><small>${E.filter(e => e.venue === x && e.d >= TODAY).length}</small></button></li>`).join("") + cats.map(([k, l]) => `<li><button type="button" data-sc="${k}">${IC.kat}<span>${hi(l, q)}</span><small>${E.filter(e => e.cat === k && e.d >= TODAY).length}</small></button></li>`).join(""));
    if (jb || fl) rows.push(`<li class="hd">Andre sider</li>` + (jb ? `<li><a href="julebord/">${IC.side}<span>Julebord</span><small>${jb}</small></a></li>` : "") + (fl ? `<li><a href="kino/">${IC.side}<span>Kino</span><small>${fl} ${fl === 1 ? "film" : "filmer"}</small></a></li>` : ""));
    ul.innerHTML = rows.join("") || `<li class="hd">Ingen forslag</li>`; ul.hidden = false;
  }
  $("q").addEventListener("input", sug); $("q").addEventListener("focus", sug);
  document.addEventListener("click", ev => { if (!ev.target.closest(".qwrap")) ul.hidden = true; });
  ul.addEventListener("click", ev => {
    const b = ev.target.closest("button"); if (!b) return; ul.hidden = true;
    if (b.dataset.sev) { const id = b.dataset.sev; state.when = "alt"; syncFilters(); setQ(""); const el = $("ev-" + id); if (el) { el.scrollIntoView({ block: "center" }); el.animate([{ outline: "2px solid var(--accent)" }, { outline: "2px solid transparent" }], { duration: 1800 }); } }
    if (b.dataset.sv) { state.venue = b.dataset.sv; $("venue").value = state.venue; setQ(""); }
    if (b.dataset.sc) { state.cats = new Set([b.dataset.sc]); $("cats").querySelectorAll("[data-c]").forEach(x => x.setAttribute("aria-pressed", state.cats.has(x.dataset.c))); syncFilters(); setQ(""); }
  });

  function setTema(x) {
    document.querySelectorAll('link[href="tema-kveld.css"],link[href="tema-jul.css"]').forEach(l => l.remove());
    const root = document.documentElement;
    if (x === "lys") { delete root.dataset.tema; root.dataset.theme = "light"; }
    else { root.dataset.tema = x; delete root.dataset.theme; document.head.insertAdjacentHTML("beforeend", `<link rel="stylesheet" href="tema-${x}.css">`); }
  }
  function applyHash() {
    setTema(t());
    window.QMATCH = has("s1") ? tolerant : null;
    document.querySelectorAll(".sqpick [data-v]").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === v()));
    document.querySelectorAll(".sqpick [data-q]").forEach(b => b.setAttribute("aria-pressed", b.dataset.q === qi()));
    document.querySelectorAll(".sqpick [data-t]").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === t()));
    document.getElementById("sqtxt").textContent = TXT[v()];
    state.when = "alt"; state.cats = new Set(); state.venue = ""; state.price = ""; setFavOnly(false); syncFilters();
    $("when").querySelectorAll("[data-w]").forEach(x => x.setAttribute("aria-pressed", x.dataset.w === "alt")); $("venue").value = ""; $("price").value = "";
    $("cats").querySelectorAll("[data-c]").forEach(x => x.setAttribute("aria-pressed", "false"));
    setQ(EX[+qi()] ?? "");
    if (v() === "s3" && EX[+qi()]) setTimeout(() => { $("q").focus(); sug(); }, 50);
    else ul.hidden = true;
    setTimeout(() => (v() === "s3" ? $("q") : $("list")).scrollIntoView({ block: "start" }), 60);
  }
  document.querySelectorAll(".sqpick [data-v]").forEach(b => b.addEventListener("click", () => go(b.dataset.v, qi(), t())));
  document.querySelectorAll(".sqpick [data-q]").forEach(b => b.addEventListener("click", () => go(v(), b.dataset.q, t())));
  document.querySelectorAll(".sqpick [data-t]").forEach(b => b.addEventListener("click", () => go(v(), qi(), b.dataset.t)));
  addEventListener("hashchange", applyHash);
  const wait = setInterval(() => { if (typeof E !== "undefined" && E.length) { clearInterval(wait); setTimeout(applyHash, 300); } }, 100);
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
