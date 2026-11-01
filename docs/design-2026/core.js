/* Felles kjerne for de tre designforslagene: leser data/events.json, gjør om til kort per arrangement og gir hjelpefunksjoner. Ingen tracking. */
const CATS = { konsert: "Konsert", standup: "Standup", show: "Show", barn: "Barn & familie", klubb: "Klubb", happening: "Happening", quiz: "Quiz", sport: "Sport" };
const OSLO = new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Oslo" });
const TODAY = OSLO.format(new Date());
const WD = ["søn", "man", "tir", "ons", "tor", "fre", "lør"], WDL = ["søndag", "mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag"];
const MO = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"], MOL = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"];
const pd = iso => new Date(iso + "T12:00:00");
const addDays = (iso, n) => { const d = pd(iso); d.setDate(d.getDate() + n); return OSLO.format(d); };
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const safeUrl = u => /^https?:\/\//.test(u || "") ? u : "#";
const $ = id => document.getElementById(id);
function weekendRange() { const d = pd(TODAY), w = d.getDay(); const fri = w === 0 ? addDays(TODAY, -2) : w === 6 ? addDays(TODAY, -1) : addDays(TODAY, (5 - w + 7) % 7); return [fri, addDays(fri, 2)]; }
function prep(raw) {
  return raw.filter(e => e.cat !== "julebord" && e.date >= TODAY).map(e => {
    const more = [...new Set((e.moreShows || []).map(s => s.slice(0, 10)).filter(x => x !== e.date))];
    return { ...e, d: pd(e.date), more, free: e.priceMin === 0, sold: !!e.soldOut, few: !!e.few, label: CATS[e.cat] || "Happening" };
  }).sort((a, b) => (a.date + (a.time || "")) < (b.date + (b.time || "")) ? -1 : 1);
}
const favs = (() => { let s = new Set(); try { s = new Set(JSON.parse(localStorage.getItem("skjer-favs") || "[]")); } catch {} return { has: id => s.has(id), size: () => s.size, toggle(id) { s.has(id) ? s.delete(id) : s.add(id); try { localStorage.setItem("skjer-favs", JSON.stringify([...s])); } catch {} return s.has(id); } }; })();
function dayName(iso) { if (iso === TODAY) return "I dag"; if (iso === addDays(TODAY, 1)) return "I morgen"; return WDL[pd(iso).getDay()]; }
function priceText(e) { return e.sold ? "Utsolgt" : e.free ? "Gratis" : e.price && e.price !== "Pris hos arrangør" ? e.price : "Pris hos arrangør"; }
function matches(e, f) {
  if (f.cat && e.cat !== f.cat) return false;
  if (f.when === "i-dag" && e.date !== TODAY) return false;
  if (f.when === "helg") { const [a, b] = weekendRange(); if (e.date < a || e.date > b) return false; }
  if (f.when === "uke" && e.date > addDays(TODAY, 6)) return false;
  if (f.day && e.date !== f.day) return false;
  if (f.free && !e.free) return false;
  if (f.mine && !favs.has(e.id)) return false;
  if (f.q) { const t = (e.title + " " + e.venue + " " + e.label + " " + (e.note || "")).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""); if (!f.q.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").split(/\s+/).every(w => t.includes(w))) return false; }
  return true;
}
function byDay(list) { const m = new Map(); list.forEach(e => { if (!m.has(e.date)) m.set(e.date, []); m.get(e.date).push(e); }); return [...m.entries()]; }
function addJsonLd(list) {
  const el = document.createElement("script"); el.type = "application/ld+json";
  el.textContent = JSON.stringify({ "@context": "https://schema.org", "@graph": list.slice(0, 20).map(e => ({ "@type": "Event", name: e.title, startDate: e.date + (e.time ? "T" + e.time + ":00+01:00" : ""), eventStatus: "https://schema.org/EventScheduled", eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode", location: { "@type": "Place", name: e.venue, address: { "@type": "PostalAddress", addressLocality: "Ålesund", addressCountry: "NO" } }, ...(e.priceMin != null ? { offers: { "@type": "Offer", price: e.priceMin, priceCurrency: "NOK", url: e.url, availability: e.sold ? "https://schema.org/SoldOut" : "https://schema.org/InStock" } } : {}), isAccessibleForFree: e.free || undefined })) });
  document.head.append(el);
}
async function loadEvents() { const r = await fetch("data/events.json"); return prep((await r.json()).events); }
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const revealIO = reduceMotion || !("IntersectionObserver" in window) ? null : new IntersectionObserver(es => es.forEach(x => { if (x.isIntersecting) { x.target.classList.add("in"); revealIO.unobserve(x.target); } }), { rootMargin: "0px 0px -6% 0px" });
function reveal(root) { root.querySelectorAll(".rv:not(.in)").forEach(el => revealIO ? revealIO.observe(el) : el.classList.add("in")); }
