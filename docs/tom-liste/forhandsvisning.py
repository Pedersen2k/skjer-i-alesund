"""Forhåndsvisning av bedre tomme lister på forsiden (Claude-artefakt, flere filer).

Når filtrene gir null treff, viser siden i dag bare en tekstlinje. Forslagene:
T1 tegning + én knapp («Prøv neste 7 dager →»), T2 knapper som fjerner ett filter om gangen med antall treff,
T3 de nærmeste treffene uten datofilteret, T4 tegning + knappene fra T2, T5 lun tekst + snarveier og «Tips oss»,
T6 «T1 med reserve»: tegning, én stor knapp med valget som gir flest treff, og ett–to små alternativer under (Claudes valg).
Velgeren nederst lager en tom liste (søk uten treff, filtre uten treff, tom «★ Mine») og bytter tema.

Bygger på _site/ (kjør scripts/pages.py først). Skriver preview/tom-liste/. Valg i adressen: #t6-sok-kveld osv.

Kjør: python3 scripts/pages.py && python3 docs/tom-liste/forhandsvisning.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
OUT = ROOT / "preview" / "tom-liste"

page = (SITE / "index.html").read_text()
page = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", page, flags=re.I)
page = re.sub(r'<meta (charset|name="viewport"|property="og:[^"]*"|name="twitter:[^"]*"|name="theme-color")[^>]*>\s*', "", page)
page = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', "", page)
page = re.sub(r"<title>[^<]*</title>", '<title>Tomme lister</title>\n<meta name="claude:viewport-fit-sides" content="cover">', page, count=1)
page = page.replace('const GOATCOUNTER = "kaskjerda";', 'const GOATCOUNTER = "";', 1)

extra = r"""
<style>
.tlpick { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding: 8px max(10px, env(safe-area-inset-right, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(10px, env(safe-area-inset-left, 0px));
  display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; justify-content: center; background: #000e; backdrop-filter: blur(10px); font: 600 13px/1.3 "Figtree", system-ui, sans-serif; color: #fff; }
.tlpick .lbl { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: #fff9; }
.tlpick .seg { display: inline-flex; flex-wrap: wrap; border: 1px solid #fff5; border-radius: 10px; overflow: hidden; }
.tlpick button { font: 700 13px/1 "Figtree", system-ui, sans-serif; color: #fff; background: #222; border: 0; padding: 0 10px; min-height: 38px; cursor: pointer; }
.tlpick button[aria-pressed="true"] { background: #f7c873; color: #10282f; }
.tlpick p { margin: 0; flex: 1 1 100%; text-align: center; font-weight: 500; color: #fffc; max-width: 70ch; }
.tlpick .row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; justify-content: center; }
body { padding-bottom: 200px; }

/* Felles for forslagene */
.tomt { display: grid; justify-items: center; text-align: center; gap: 10px; padding: 26px 16px 30px; margin: 10px 0; border: 1px dashed var(--line); border-radius: 18px; background: color-mix(in srgb, var(--surface) 55%, transparent); }
.tomt .art { width: 132px; height: 96px; color: var(--muted); }
.tomt h3 { margin: 0; font: 800 19px/1.2 var(--font-display); color: var(--fg); text-wrap: balance; max-width: 30ch; }
.tomt p { margin: 0; color: var(--muted); font-size: 14px; max-width: 42ch; }
.tomt .go { display: inline-flex; align-items: center; gap: 6px; min-height: 44px; padding: 0 18px; border-radius: 12px; border: 0; background: var(--accent); color: var(--accent-ink); font: 700 15px var(--font-body); cursor: pointer; text-decoration: none; }
.tomt .opts { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; max-width: 520px; }
.tomt .opt { display: inline-flex; align-items: center; gap: 6px; min-height: 40px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--line); background: var(--surface); color: var(--fg); font: 600 13.5px var(--font-body); cursor: pointer; }
.tomt .opt b { font: 700 12px var(--font-mono); color: var(--accent); }
.tomt .opt.all { border-style: dashed; color: var(--muted); }
.tomt .near { width: 100%; max-width: 520px; display: grid; gap: 8px; text-align: left; }
.tomt .near a { display: grid; grid-template-columns: 64px 1fr auto; gap: 10px; align-items: center; padding: 10px 12px; border-radius: 12px; border: 1px solid var(--line); border-left: 4px solid var(--c); background: var(--surface); color: var(--fg); text-decoration: none; }
.tomt .near a small { color: var(--muted); display: block; font-size: 12.5px; }
.tomt .near a .d { font: 700 12.5px/1.2 var(--font-mono); color: var(--accent); }
.tomt .near a .pr { font: 600 12.5px var(--font-mono); white-space: nowrap; }
.tomt .links { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 16px; font-weight: 600; font-size: 14px; }
.tomt .links a, .tomt .links button { color: var(--sea); background: none; border: 0; padding: 0; font: inherit; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }
html[data-tema="kveld"] .tomt .links a, html[data-tema="kveld"] .tomt .links button { color: var(--gold); }
.tomt.t5 { border-style: solid; text-align: left; justify-items: start; }
.tomt.t5 h3 { max-width: none; }
.tomt.t6 .go { min-height: 48px; padding: 0 22px; font-size: 16px; }
.tomt.t6 .go .n { font: 700 12.5px/1 var(--font-mono); padding: 4px 7px; border-radius: 999px; background: color-mix(in srgb, var(--accent-ink) 18%, transparent); }
.tomt.t6 .links { font-size: 13.5px; font-weight: 500; gap: 4px 14px; align-items: center; }
.tomt.t6 .links .eller { color: var(--muted); }
.tomt.t6 .links button { min-height: 32px; }
@keyframes tlspot { 50% { opacity: .55; } }
.tomt .art .spot { animation: tlspot 3s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) { .tomt .art .spot { animation: none; } }
</style>
<nav class="tlpick" aria-label="Velg forslag, situasjon og tema">
  <div class="row"><span class="lbl">Forslag</span><div class="seg" role="group" aria-label="Forslag"><button type="button" data-v="t0">Nå</button><button type="button" data-v="t1">T1</button><button type="button" data-v="t2">T2</button><button type="button" data-v="t3">T3</button><button type="button" data-v="t4">T4</button><button type="button" data-v="t5">T5</button><button type="button" data-v="t6">T6</button></div></div>
  <div class="row"><span class="lbl">Lag tom liste</span><div class="seg" role="group" aria-label="Situasjon"><button type="button" data-s="sok">Søk uten treff</button><button type="button" data-s="barn">Barn i kveld</button><button type="button" data-s="gratis">Gratis standup</button><button type="button" data-s="mine">Tom ★ Mine</button></div>
  <div class="seg" role="group" aria-label="Tema"><button type="button" data-t="kveld">Mørkt</button><button type="button" data-t="jul">Jul</button><button type="button" data-t="lys">Lyst</button></div></div>
  <p id="tltxt"></p>
</nav>
<script>
(() => {
  const TXT = {
    t0: "Nå: én tekstlinje.",
    t1: "T1 Tegning + én knapp: en liten tegning, en vennlig setning og den ene knappen som mest sannsynlig gir treff.",
    t2: "T2 Fjern ett filter: knapper som fjerner ett filter om gangen, med hvor mange treff du da får. Bare knapper som faktisk gir treff vises.",
    t3: "T3 Nærmeste treff: de tre nærmeste arrangementene som passer filtrene dine, uansett dato.",
    t4: "T4 Tegning + knapper: tegningen fra T1 og knappene fra T2.",
    t5: "T5 Lun tekst: en kort setning, snarveier til helgen og hele programmet, og «Tips oss» hvis noe mangler.",
    t6: "T6 T1 med reserve: én stor knapp med det valget som gir flest treff, og ett–to små alternativer under. Mitt valg.",
  };
  const SIT = { sok: "Søk uten treff", barn: "Barn i kveld", gratis: "Gratis standup", mine: "Tom ★ Mine" };
  const parts = () => (location.hash.slice(1) || "t6-barn-kveld").split("-");
  const v = () => (TXT[parts()[0]] ? parts()[0] : "t6"), sit = () => (SIT[parts()[1]] ? parts()[1] : "barn"), t = () => (["kveld", "jul", "lys"].includes(parts()[2]) ? parts()[2] : "kveld");
  const go = (a, b, c) => { location.hash = `${a}-${b}-${c}`; };

  // Små tegninger (strek i tekstfarge, aksent i sidens farge)
  const ART = {
    scene: `<svg class="art" viewBox="0 0 132 96" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path class="spot" d="M66 6 L40 78 H92 Z" fill="var(--accent)" opacity=".18" stroke="none"/>
      <path d="M10 78 H122"/><path d="M14 8 C30 30 30 60 16 78 M118 8 C102 30 102 60 116 78"/><path d="M10 8 H122"/>
      <circle cx="66" cy="6" r="3" fill="var(--accent)" stroke="var(--accent)"/><path d="M52 88 h28" opacity=".5"/></svg>`,
    sok: `<svg class="art" viewBox="0 0 132 96" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true">
      <circle cx="58" cy="42" r="24"/><path d="M76 60 L98 82"/><path d="M50 36 q8 -8 16 0" stroke="var(--accent)"/><circle cx="58" cy="50" r="1.6" fill="currentColor"/>
      <path d="M22 84 h8 M104 18 l4 4 m0 -4 l-4 4 M18 22 h6" opacity=".5"/></svg>`,
    mine: `<svg class="art" viewBox="0 0 132 96" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" aria-hidden="true">
      <path d="M66 14 l9 19 21 3 -15 15 4 21 -19 -10 -19 10 4 -21 -15 -15 21 -3 Z" stroke-dasharray="5 5"/>
      <path class="spot" d="M66 30 l4 9 10 1 -7 7 2 10 -9 -5 -9 5 2 -10 -7 -7 10 -1 Z" fill="var(--accent)" stroke="none" opacity=".5"/></svg>`,
  };

  // Hvor mange treff gir en endring? Endrer state midlertidig og regner med sidens egen filterfunksjon.
  const snapshot = () => ({ when: state.when, cats: new Set(state.cats), venue: state.venue, price: state.price, q: state.q, favOnly: state.favOnly });
  function count(patch) {
    const s = snapshot(); Object.assign(state, patch);
    const n = collapseQuiz(E.filter(e => e.d >= TODAY && WHEN[state.when][1](e.d) && matchesBase(e))).length;
    Object.assign(state, s); return n;
  }
  function apply(patch) {
    Object.assign(state, patch);
    $("when").querySelectorAll("[data-w]").forEach(x => x.setAttribute("aria-pressed", x.dataset.w === state.when));
    $("cats").querySelectorAll("[data-c]").forEach(x => x.setAttribute("aria-pressed", state.cats.has(x.dataset.c)));
    $("venue").value = state.venue; $("price").value = state.price; $("q").value = state.q; setFavOnly(state.favOnly); syncFilters();
    render();
  }
  const whenName = w => (WHEN[w] ? WHEN[w][0] : w).toLowerCase();
  // Knapper som fjerner ett filter om gangen
  function options() {
    const o = [];
    if (state.favOnly) o.push(["Vis alle, ikke bare ★ Mine", { favOnly: false }]);
    if (state.q) o.push([`Tøm søket «${state.q}»`, { q: "" }]);
    if (state.when !== "alt") {
      const week = ["ikveld", "helg"].includes(state.when) ? count({ when: "uke" }) : 0, all = count({ when: "alt" });
      if (week) o.push(["Neste 7 dager", { when: "uke" }]);
      if (all > week) o.push(["Alle datoer", { when: "alt" }]);
    }
    if (state.cats.size) o.push(["Alle kategorier", { cats: new Set() }]);
    if (state.venue) o.push(["Alle scener", { venue: "" }]);
    if (state.price !== "") o.push(["Alle priser", { price: "" }]);
    return o.map(([label, p]) => [label, p, count(p)]).filter(x => x[2] > 0).slice(0, 4);
  }
  const RESET = { when: "alt", cats: new Set(), venue: "", price: "", q: "", favOnly: false };
  const headline = () => state.favOnly ? "Ingen lagrede arrangementer passer her" : state.q ? `Fant ingenting på «${esc(state.q)}»` : state.when === "ikveld" ? "Ingenting som passer i kveld" : "Ingenting passer filtrene dine";
  const art = () => ART[state.favOnly ? "mine" : state.q ? "sok" : "scene"];
  const btns = list => list.map(([l, , n], i) => `<button type="button" class="opt" data-i="${i}">${esc(l)} <b>${n}</b></button>`).join("") + `<button type="button" class="opt all" data-reset>Nullstill alt</button>`;
  let current = [];
  function nearest() {
    const s = snapshot(); state.when = "alt";
    const n = E.filter(e => e.d >= TODAY && matchesBase(e)).sort((a, b) => a.d - b.d).slice(0, 3); Object.assign(state, s); return n;
  }
  const dstr = d => `${["søn","man","tir","ons","tor","fre","lør"][d.getDay()]} ${d.getDate()}.${d.getMonth() + 1}.`;
  function build() {
    current = options();
    const best = current[0];
    switch (v()) {
      case "t1": return `<div class="tomt">${art()}<h3>${headline()}</h3><p>Det er ikke registrert noe som passer akkurat nå.</p>${best ? `<button type="button" class="go" data-i="0">${esc(best[0])} → <span style="opacity:.75">(${best[2]})</span></button>` : `<button type="button" class="go" data-reset>Se hele programmet →</button>`}</div>`;
      case "t2": return `<div class="tomt"><h3>${headline()}</h3><p>Prøv å fjerne ett av filtrene:</p><div class="opts">${btns(current)}</div></div>`;
      case "t3": { const n = nearest(); return `<div class="tomt"><h3>${headline()}</h3>${n.length ? `<p>Dette er det nærmeste som passer, uansett dato:</p><div class="near">${n.map(e => `<a href="#ev-${esc(e.id)}" style="--c:var(--c-${e.cat})"><span class="d">${dstr(e.d)}${e.time ? "<br>" + esc(e.time) : ""}</span><span>${esc(e.title)}<small>${esc(e.venue)}</small></span><span class="pr">${esc(e.priceMin === 0 ? "Gratis" : e.price || "")}</span></a>`).join("")}</div><button type="button" class="opt" data-when-alt>Se alle datoer →</button>` : `<button type="button" class="go" data-reset>Se hele programmet →</button>`}</div>`; }
      case "t4": return `<div class="tomt">${art()}<h3>${headline()}</h3><p>Prøv å fjerne ett av filtrene:</p><div class="opts">${btns(current)}</div></div>`;
      case "t6": {
        // Valget med flest treff blir den store knappen; de neste to + «Nullstill alt» blir små lenker under
        const rank = current.map((x, i) => [x, i]).sort((a, b) => b[0][2] - a[0][2]);
        const [top, ...rest] = rank;
        if (!top) return `<div class="tomt">${art()}<h3>${headline()}</h3><button type="button" class="go" data-reset>Se hele programmet →</button></div>`;
        const small = rest.slice(0, 2).map(([[l, , n], i]) => `<button type="button" data-i="${i}">${esc(l)} (${n})</button>`).join("");
        return `<div class="tomt t6">${art()}<h3>${headline()}</h3><button type="button" class="go" data-i="${top[1]}">${esc(top[0][0])} → <span class="n">${top[0][2]}</span></button><div class="links"><span class="eller">eller</span>${small}<button type="button" data-reset>Nullstill alt</button></div></div>`;
      }
      case "t5": return `<div class="tomt t5"><h3>${headline()}. Det skjer mye annet!</h3><div class="links"><button type="button" data-when="helg">Se denne helgen →</button><button type="button" data-reset>Hele programmet →</button><a href="kontakt/">Mangler det noe? Tips oss →</a></div></div>`;
    }
    return "";
  }
  const orig = render;
  render = function () { orig(); const em = document.querySelector("#list .empty"); if (em && v() !== "t0" && E.length) em.outerHTML = build(); };
  $("list").addEventListener("click", e => {
    const b = e.target.closest(".tomt [data-i], .tomt [data-reset], .tomt [data-when], .tomt [data-when-alt]"); if (!b) return;
    e.stopPropagation();
    if (b.dataset.reset !== undefined) return apply({ ...RESET, cats: new Set() });
    if (b.dataset.when) return apply({ when: b.dataset.when, cats: new Set(), venue: "", price: "", q: "", favOnly: false });
    if (b.dataset.whenAlt !== undefined) return apply({ when: "alt" });
    const o = current[+b.dataset.i]; if (o) apply(o[1]);
  }, true);

  function scenario(s) {
    const base = { ...RESET, cats: new Set() };
    if (s === "sok") apply({ ...base, q: "trompetkonkurranse" });
    if (s === "barn") apply({ ...base, when: "ikveld", cats: new Set(["barn"]) });
    if (s === "gratis") apply({ ...base, cats: new Set(["standup"]), price: "0" });
    if (s === "mine") { try { favs.clear(); store.set("skjer-favs", []); } catch {} apply({ ...base, favOnly: true }); }
    setTimeout(() => document.getElementById("list").scrollIntoView({ block: "start" }), 50);
  }
  function setTema(x) {
    document.querySelectorAll('link[href="tema-kveld.css"],link[href="tema-jul.css"]').forEach(l => l.remove());
    const root = document.documentElement;
    if (x === "lys") { delete root.dataset.tema; root.dataset.theme = "light"; }
    else { root.dataset.tema = x; delete root.dataset.theme; document.head.insertAdjacentHTML("beforeend", `<link rel="stylesheet" href="tema-${x}.css">`); }
  }
  let lastSit = "";
  function applyHash() {
    setTema(t());
    document.querySelectorAll(".tlpick [data-v]").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === v()));
    document.querySelectorAll(".tlpick [data-s]").forEach(b => b.setAttribute("aria-pressed", b.dataset.s === sit()));
    document.querySelectorAll(".tlpick [data-t]").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === t()));
    document.getElementById("tltxt").textContent = TXT[v()];
    if (sit() !== lastSit) { lastSit = sit(); scenario(sit()); } else render();
  }
  document.querySelectorAll(".tlpick [data-v]").forEach(b => b.addEventListener("click", () => go(b.dataset.v, sit(), t())));
  document.querySelectorAll(".tlpick [data-s]").forEach(b => b.addEventListener("click", () => { lastSit = ""; go(v(), b.dataset.s, t()); if (b.dataset.s === sit()) applyHash(); }));
  document.querySelectorAll(".tlpick [data-t]").forEach(b => b.addEventListener("click", () => go(v(), sit(), b.dataset.t)));
  addEventListener("hashchange", applyHash);
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
    shutil.copy(SITE / f, OUT / f)
for f in ("events.json", "kino.json"):
    if (SITE / "data" / f).exists():
        shutil.copy(SITE / "data" / f, OUT / "data" / f)
print("Skrev", OUT)
