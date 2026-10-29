// Juledesign-forslag for forsiden (gren design/jul). JULDESIGN.apply("peis" | "sno" | "lys" | "kofte" | "pepperkake" | "advent" | "")
// setter html[data-jul], slår av kveldstemaet mens forslaget vises, laster skriftene og legger inn pynten. Ikke i bruk på kaskjerda.no.
(() => {
  const FONTS = {
    peis: "Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,600..700,100,1;1,9..144,600..700,100,1",
    vinterkveld: "Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,600..700,100,1;1,9..144,600..700,100,1",
    frost: "Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,600..700,100,1;1,9..144,600..700,100,1",
    juletre: "Playfair+Display:ital,wght@0,700;0,800;1,700",
    lys: "Young+Serif",
    kofte: "DM+Serif+Display",
    pepperkake: "Fredoka:wght@500;600;700",
    advent: "Cormorant+Garamond:ital,wght@0,700;1,700",
  };
  const DARK = { peis: 1, sno: 1, lys: 1, advent: 1, vinterkveld: 1, juletre: 1, frost: 1, rodtrad: 1 };
  const root = document.documentElement;
  const startTema = root.dataset.tema || "", startTheme = root.getAttribute("data-theme");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let stops = [];
  const svgEl = (tag, attrs) => { const e = document.createElementNS("http://www.w3.org/2000/svg", tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };
  const rnd = (a, b) => a + Math.random() * (b - a);

  function font(name) {
    if (!FONTS[name] || document.getElementById("jd-font-" + name)) return;
    const l = document.createElement("link");
    l.id = "jd-font-" + name; l.rel = "stylesheet";
    l.href = `https://fonts.googleapis.com/css2?family=${FONTS[name]}&display=swap`;
    document.head.appendChild(l);
  }

  function clear() {
    stops.forEach(f => f()); stops = [];
    document.querySelectorAll(".jd-decor").forEach(e => e.remove());
    document.querySelectorAll(".day").forEach(d => d.style.backgroundImage = "");
  }

  // Partikler på et lerret (glør som stiger, snø som faller). Stopper når forslaget byttes.
  function particles(canvas, make, step) {
    const ctx = canvas.getContext("2d"); let w, h, ps = [], raf;
    const size = () => { const r = canvas.getBoundingClientRect(), dpr = devicePixelRatio || 1; w = r.width; h = r.height; canvas.width = w * dpr; canvas.height = h * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); };
    size(); addEventListener("resize", size);
    ps = Array.from({ length: make.count(w, h) }, () => make.one(w, h, true));
    const tick = () => { ctx.clearRect(0, 0, w, h); ps.forEach((p, i) => { if (!step(p, w, h, ctx)) ps[i] = make.one(w, h, false); }); if (!reduce) raf = requestAnimationFrame(tick); };
    tick();
    stops.push(() => { cancelAnimationFrame(raf); removeEventListener("resize", size); });
  }


  // Jugendgavler med snø på taket og lys i vinduene, tegnet ut fra bredden; med lights=true henger en lysslynge mellom gavlene
  function skyline(top, fill, lights) {
    const W = 760, H = 120, s = svgEl("svg", { class: "jd-decor jd-skyline jd-anim", viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "xMidYMax slice", "aria-hidden": "true" });
    let x = -10, seed = 7; const r = () => (seed = (seed * 9301 + 49297) % 233280) / 233280; const peaks = [];
    while (x < W) {
      const bw = 46 + r() * 40, bh = 46 + r() * 44, y = H - bh, g = svgEl("g", {});
      const kind = r(), mid = x + bw / 2;
      const roof = kind < .4 ? `M${x} ${y} L${mid} ${y - 26} L${x + bw} ${y} Z` : kind < .75
        ? `M${x} ${y} C${x} ${y - 14} ${mid - 10} ${y - 12} ${mid - 8} ${y - 26} L${mid + 8} ${y - 26} C${mid + 10} ${y - 12} ${x + bw} ${y - 14} ${x + bw} ${y} Z`
        : `M${x} ${y} L${x} ${y - 8} Q${mid} ${y - 34} ${x + bw} ${y - 8} L${x + bw} ${y} Z`;
      peaks.push([mid, y - (kind < .75 ? 26 : 20)]);
      g.append(svgEl("path", { d: roof, fill }), svgEl("rect", { x, y, width: bw, height: bh, fill }));
      g.append(svgEl("path", { d: roof.replace(/Z$/, ""), fill: "none", stroke: "#f4f8ff", "stroke-width": 4, "stroke-linejoin": "round", "stroke-linecap": "round", opacity: .95 }));
      for (let wy = y + 10; wy < H - 14; wy += 18) for (let wx = x + 8; wx < x + bw - 12; wx += 16)
        if (r() > .35) g.append(svgEl("rect", { x: wx, y: wy, width: 7, height: 10, rx: 1.5, fill: r() > .3 ? "#ffd27a" : "#ffb34a", opacity: .5 + r() * .5 }));
      s.append(g); x += bw + 2;
    }
    if (lights) {
      const cols = ["#ff5b4f", "#ffd27a", "#5fd38a", "#6fb6ff"]; let k = 0;
      for (let i = 0; i < peaks.length - 1; i++) {
        const [x0, y0] = peaks[i], [x1, y1] = peaks[i + 1], sag = 16;
        s.append(svgEl("path", { d: `M${x0} ${y0} Q${(x0 + x1) / 2} ${Math.max(y0, y1) + sag * 2} ${x1} ${y1}`, fill: "none", stroke: "#0006", "stroke-width": 1 }));
        for (let t = .2; t < .85; t += .2) {
          const bx = (1 - t) * (1 - t) * x0 + 2 * (1 - t) * t * (x0 + x1) / 2 + t * t * x1, by = (1 - t) * (1 - t) * y0 + 2 * (1 - t) * t * (Math.max(y0, y1) + sag * 2) + t * t * y1, c = cols[k++ % cols.length];
          const g = svgEl("g", { class: "jd-bulb", style: `animation-delay:${(k * .41 % 2.6).toFixed(2)}s` });
          g.append(svgEl("circle", { cx: bx, cy: by + 3, r: 6, fill: c, opacity: .25 }), svgEl("circle", { cx: bx, cy: by + 3, r: 2.4, fill: c })); s.append(g);
        }
      }
    }
    s.append(svgEl("rect", { x: 0, y: H - 6, width: W, height: 6, fill: "#eef3ff" }));
    top.appendChild(s);
  }
  function snowfall(density = 9000) {
    const fx = Object.assign(document.createElement("div"), { className: "jd-decor jd-fixed" }); const c = Object.assign(document.createElement("canvas"), { className: "jd-snow" });
    c.style.cssText = "width:100%;height:100%"; fx.appendChild(c); document.body.appendChild(fx);
    particles(c, { count: (w, h) => Math.round(w * h / density), one: (w, h, init) => ({ x: rnd(0, w), y: init ? rnd(0, h) : -6, r: rnd(.8, 2.6), vy: rnd(.3, 1.1), sway: rnd(0, 6.28) }) },
      (p, w, h, ctx) => { p.y += p.vy; p.sway += .012; p.x += Math.sin(p.sway) * .4; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fillStyle = `rgba(255,255,255,${.35 + p.r / 5})`; ctx.fill(); return p.y < h + 6; });
  }
  function garland(host, h, n, cls) {
    const W = 400, s = svgEl("svg", { class: "jd-decor jd-garland jd-anim " + cls, viewBox: `0 0 ${W} ${h}`, preserveAspectRatio: "none", "aria-hidden": "true" });
    const sag = h * .55, cols = ["#ff5b4f", "#f3c34f", "#5fd38a", "#6fb6ff", "#ff8fd0"];
    const yAt = t => 4 + sag * 4 * t * (1 - t);
    let d = "M0 4"; for (let i = 1; i <= 40; i++) { const t = i / 40; d += ` L${t * W} ${yAt(t)}`; }
    s.append(svgEl("path", { d, fill: "none", stroke: "#0a1a12", "stroke-width": 1.6, "vector-effect": "non-scaling-stroke" }));
    for (let i = 1; i < n; i++) {
      const t = i / n, x = t * W, y = yAt(t), col = cols[i % cols.length];
      const g = svgEl("g", { class: "jd-bulb", style: `animation-delay:${(i * 0.37 % 2.6).toFixed(2)}s` });
      g.append(svgEl("ellipse", { cx: x, cy: y + 9, rx: 9, ry: 11, fill: col, opacity: .22 }), svgEl("rect", { x: x - 2.2, y: y - 1, width: 4.4, height: 4, fill: "#2d3b33" }), svgEl("ellipse", { cx: x, cy: y + 8, rx: 3.6, ry: 5.4, fill: col }));
      s.append(g);
    }
    host.prepend(s);
  }

  const DECOR = {
    peis(top) {
      const box = Object.assign(document.createElement("div"), { className: "jd-decor jd-hero" }); box.style.height = top.offsetHeight + 28 + "px";
      const c = Object.assign(document.createElement("canvas"), { className: "jd-embers" }); box.appendChild(c); top.prepend(box);
      particles(c, { count: (w) => Math.round(w / 9), one: (w, h, init) => ({ x: rnd(0, w), y: init ? rnd(0, h) : h + 4, r: rnd(.6, 2.2), vy: rnd(.25, .8), sway: rnd(0, 6.28), life: rnd(.5, 1) }) },
        (p, w, h, ctx) => { p.y -= p.vy; p.sway += .03; p.x += Math.sin(p.sway) * .35; const a = Math.max(0, Math.min(1, p.y / h)) * p.life;
          ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fillStyle = `rgba(255,${140 + p.r * 40 | 0},60,${a})`; ctx.shadowColor = "#ff7a1a"; ctx.shadowBlur = 8; ctx.fill(); return p.y > -5; });
    },
    sno(top) { skyline(top, "#0a1330", false); snowfall(); },
    lys(top) {
      garland(top, 70, 18, "");
      const jc = document.getElementById("julcard"); if (jc) garland(jc, 34, 12, "small");
    },
    kofte(top) {
      // Strikkemønster (selburose og bord) tegnet piksel for piksel og brukt som bakgrunn
      const band = (rows, color, bg) => { const c = document.createElement("canvas"); c.width = rows[0].length; c.height = rows.length; const x = c.getContext("2d");
        x.fillStyle = bg; x.fillRect(0, 0, c.width, c.height); x.fillStyle = color; rows.forEach((r, j) => [...r].forEach((ch, i) => { if (ch === "#") x.fillRect(i, j, 1, 1); })); return c.toDataURL(); };
      const rose = [
        "..............", "#.#.#.#.#.#.#.", "..............", "......#.......", ".....###......", "..#..###..#...", "..##..#..##...", "..###...###...",
        "...###.###....", "#...#####...#.", "##...###...##.", "#...#####...#.", "...###.###....", "..###...###...", "..##..#..##...", "..#..###..#...",
        ".....###......", "......#.......", "..............", "#.#.#.#.#.#.#.", ".............."];
      const thin = ["........", "#..##..#", ".##..##.", "#..##..#", "........"];
      const red = "#b3242c", wool = "#f5efe4";
      const hero = Object.assign(document.createElement("div"), { className: "jd-decor jd-knit" }); hero.style.backgroundImage = `url(${band(rose, red, wool)})`; top.prepend(hero);
      const jc = document.getElementById("julcard"); if (jc) { const k = Object.assign(document.createElement("div"), { className: "jd-decor jd-knit" }); k.style.backgroundImage = `url(${band(rose, "#fff", "#b3242c")})`; jc.prepend(k); }
      const sep = band(thin, red, wool), paint = () => document.querySelectorAll(".day").forEach(d => d.style.backgroundImage = `url(${sep})`);
      paint(); const mo = new MutationObserver(paint); mo.observe(document.getElementById("list"), { childList: true }); stops.push(() => mo.disconnect());
    },
    pepperkake(top) {
      const W = 760, H = 110, s = svgEl("svg", { class: "jd-decor jd-houses", viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "xMidYMax slice", "aria-hidden": "true" });
      let x = 0, seed = 3; const r = () => (seed = (seed * 9301 + 49297) % 233280) / 233280; const ice = "#fffaf2";
      while (x < W) {
        const bw = 58 + r() * 36, bh = 40 + r() * 30, y = H - bh, mid = x + bw / 2, peak = y - 22 - r() * 12, g = svgEl("g", {});
        g.append(svgEl("path", { d: `M${x} ${y} L${mid} ${peak} L${x + bw} ${y} Z`, fill: "#8d4f27" }), svgEl("rect", { x: x + 4, y, width: bw - 8, height: bh, rx: 3, fill: "#a6623a" }));
        let sc = `M${x} ${y}`; const n = 5; for (let i = 0; i < n; i++) { const x0 = x + (i / n) * bw, x1 = x + ((i + 1) / n) * bw; sc += ` Q${(x0 + x1) / 2} ${y + 9} ${x1} ${y}`; }
        g.append(svgEl("path", { d: `M${x} ${y} L${mid} ${peak} L${x + bw} ${y}`, fill: "none", stroke: ice, "stroke-width": 3.5, "stroke-linecap": "round", "stroke-linejoin": "round" }), svgEl("path", { d: sc, fill: "none", stroke: ice, "stroke-width": 2.5, "stroke-linecap": "round" }));
        const dw = 12, dx = mid - dw / 2; g.append(svgEl("path", { d: `M${dx} ${H} V${H - 18} a${dw / 2} ${dw / 2} 0 0 1 ${dw} 0 V${H}`, fill: "#6e3a18", stroke: ice, "stroke-width": 2 }));
        [[x + 10, y + 12], [x + bw - 24, y + 12]].forEach(([wx, wy]) => { g.append(svgEl("rect", { x: wx, y: wy, width: 14, height: 12, rx: 2, fill: "#ffd77a", stroke: ice, "stroke-width": 2 }), svgEl("path", { d: `M${wx + 7} ${wy} V${wy + 12} M${wx} ${wy + 6} H${wx + 14}`, stroke: ice, "stroke-width": 1.5 })); });
        [[mid - 4, peak + 12, "#c8312f"], [mid + 5, peak + 18, "#2f6b4f"], [x + bw - 10, y + bh - 10, "#c8312f"]].forEach(([cx, cy, f]) => g.append(svgEl("circle", { cx, cy, r: 2.8, fill: f })));
        s.append(g); x += bw + 6 + r() * 10;
      }
      top.appendChild(s);
    },
    advent(top) {
      // Adventskrans: lysene tennes søndagene i advent (1. søndag i advent er fire søndager før juledag)
      const now = new Date(), y = now.getFullYear(), xmas = new Date(y, 11, 25), first = new Date(xmas); first.setDate(25 - (xmas.getDay() || 7) - 21);
      const lit = now < first ? 0 : Math.min(4, 1 + Math.floor((now - first) / 6048e5));
      const s = svgEl("svg", { class: "jd-decor jd-wreath jd-anim", viewBox: "0 0 150 150", role: "img", "aria-label": `Adventskrans med ${lit} av 4 lys tent` });
      for (let i = 0; i < 46; i++) { const a = i / 46 * 6.283, rr = 52 + (i % 3) * 5; s.append(svgEl("ellipse", { cx: 75 + Math.cos(a) * rr, cy: 104 + Math.sin(a) * rr * .32, rx: 10, ry: 4.5, transform: `rotate(${a * 57.3 + 30} ${75 + Math.cos(a) * rr} ${104 + Math.sin(a) * rr * .32})`, fill: i % 2 ? "#1f5a3c" : "#2d7a4f" })); }
      const pos = [[34, 102], [62, 92], [90, 92], [118, 102]];
      pos.forEach(([cx, base], i) => {
        const h = 46, ty = base - h;
        s.append(svgEl("rect", { x: cx - 7, y: ty, width: 14, height: h, rx: 2, fill: "#f6ead6" }), svgEl("rect", { x: cx - 7, y: ty, width: 4, height: h, fill: "#fff8ec" }), svgEl("line", { x1: cx, y1: ty, x2: cx, y2: ty - 5, stroke: "#3a2a20", "stroke-width": 1.4 }));
        if (i < lit) s.append(svgEl("ellipse", { cx, cy: ty - 12, rx: 12, ry: 16, fill: "#ffcf6a", opacity: .25 }), svgEl("path", { class: "jd-flame", d: `M${cx} ${ty - 22} C${cx + 6} ${ty - 13} ${cx + 4} ${ty - 5} ${cx} ${ty - 5} C${cx - 4} ${ty - 5} ${cx - 6} ${ty - 13} ${cx} ${ty - 22} Z`, fill: "#ffcf6a" }));
      });
      for (let i = 0; i < 9; i++) { const a = i / 9 * 6.283 + .3; s.append(svgEl("circle", { cx: 75 + Math.cos(a) * 58, cy: 106 + Math.sin(a) * 18, r: 3.4, fill: "#c8202f" })); }
      const note = Object.assign(document.createElement("div"), { className: "jd-decor jd-wreath-note" });
      const fmt = d => `${d.getDate()}. ${["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"][d.getMonth()]}`;
      note.textContent = lit === 0 ? `Første lys tennes søndag ${fmt(first)}` : lit < 4 ? `${lit}. søndag i advent` : "God jul!";
      const brand = top.querySelector(".brand"); brand.after(s); s.after(note);
    },
    vinterkveld(top) {
      garland(top, 62, 16, "");
      skyline(top, "#120f2a", true); snowfall(12000);
      const jc = document.getElementById("julcard"); if (jc) garland(jc, 34, 12, "small");
    },
    juletre(top) {
      // Grantre i lag med pynt, lys som blinker og stjerne på toppen
      const s = svgEl("svg", { class: "jd-decor jd-tree jd-anim", viewBox: "0 0 132 200", "aria-hidden": "true" });
      s.append(svgEl("rect", { x: 58, y: 172, width: 16, height: 20, fill: "#5a3a22" }));
      [[66, 40, 26, 62], [66, 70, 40, 100], [66, 104, 54, 140], [66, 138, 64, 178]].forEach(([cx, ty, half, by], i) =>
        s.append(svgEl("path", { d: `M${cx} ${ty} Q${cx - half * .4} ${by - 14} ${cx - half} ${by} Q${cx} ${by - 8} ${cx + half} ${by} Q${cx + half * .4} ${by - 14} ${cx} ${ty} Z`, fill: i % 2 ? "#1f6b46" : "#246f4a" })));
      s.append(svgEl("path", { d: "M46 86 Q66 96 88 84 M36 120 Q66 134 98 118 M28 156 Q66 170 106 152", fill: "none", stroke: "#f2c55c", "stroke-width": 1.4, opacity: .8 }));
      const balls = [[56, 78, "#d8343a"], [80, 92, "#f2c55c"], [46, 112, "#6fb6ff"], [86, 124, "#d8343a"], [64, 116, "#f2c55c"], [38, 150, "#f2c55c"], [72, 152, "#d8343a"], [98, 160, "#6fb6ff"], [56, 164, "#f8f1e4"]];
      balls.forEach(([cx, cy, f], i) => { const g = svgEl("g", { class: i % 2 ? "jd-bulb" : "", style: `animation-delay:${(i * .5).toFixed(1)}s` }); g.append(svgEl("circle", { cx, cy, r: 9, fill: f, opacity: .18 }), svgEl("circle", { cx, cy, r: 4.2, fill: f })); s.append(g); });
      s.append(svgEl("path", { d: "M66 18 L70 30 L83 30 L72.5 37.5 L76.5 50 L66 42.5 L55.5 50 L59.5 37.5 L49 30 L62 30 Z", fill: "#f2c55c" }), svgEl("circle", { cx: 66, cy: 34, r: 22, fill: "#f2c55c", opacity: .15 }));
      top.appendChild(s); snowfall(22000);
    },
    frost(top) {
      // Rimkrystaller som vokser inn fra hjørnene, tegnet én gang på et lerret over siden
      const c = Object.assign(document.createElement("canvas"), { className: "jd-decor jd-frost" }); document.body.appendChild(c);
      const draw = () => { const dpr = devicePixelRatio || 1, w = innerWidth, h = innerHeight; c.width = w * dpr; c.height = h * dpr; const x = c.getContext("2d"); x.setTransform(dpr, 0, 0, dpr, 0, 0);
        let seed = 11; const r = () => (seed = (seed * 9301 + 49297) % 233280) / 233280;
        const branch = (px, py, ang, len, depth) => { if (depth > 5 || len < 4) return; const ex = px + Math.cos(ang) * len, ey = py + Math.sin(ang) * len;
          x.strokeStyle = `rgba(220,240,255,${.5 - depth * .07})`; x.lineWidth = Math.max(.5, 2 - depth * .35); x.beginPath(); x.moveTo(px, py); x.lineTo(ex, ey); x.stroke();
          for (let k = 1; k <= 3; k++) { const t = k / 4, bx = px + (ex - px) * t, by = py + (ey - py) * t; branch(bx, by, ang + .9 + r() * .3, len * .42, depth + 1); branch(bx, by, ang - .9 - r() * .3, len * .42, depth + 1); }
          branch(ex, ey, ang + (r() - .5) * .6, len * .7, depth + 1); };
        const size = Math.min(w, h) * .16;
        [[0, 0, .3, 1.3], [w, 0, 1.8, 2.9], [0, h, -1.3, -.3], [w, h, -2.9, -1.8]].forEach(([cx, cy, a0, a1]) => { for (let i = 0; i < 7; i++) branch(cx, cy, a0 + (a1 - a0) * (i / 6), size * (.55 + r() * .5), 0); });
        const g = x.createRadialGradient(w / 2, h / 2, Math.min(w, h) * .35, w / 2, h / 2, Math.max(w, h) * .75); g.addColorStop(0, "rgba(200,230,255,0)"); g.addColorStop(1, "rgba(200,230,255,.16)"); x.fillStyle = g; x.fillRect(0, 0, w, h); };
      draw(); addEventListener("resize", draw); stops.push(() => removeEventListener("resize", draw));
      const s = svgEl("svg", { class: "jd-decor jd-candle jd-anim", viewBox: "0 0 64 84", "aria-hidden": "true" });
      s.append(svgEl("ellipse", { cx: 32, cy: 22, rx: 26, ry: 26, fill: "#ffb562", opacity: .16 }), svgEl("rect", { x: 22, y: 34, width: 20, height: 44, rx: 2, fill: "#f6ead6" }), svgEl("rect", { x: 22, y: 34, width: 6, height: 44, fill: "#fff8ec" }),
        svgEl("line", { x1: 32, y1: 34, x2: 32, y2: 28, stroke: "#3a2a20", "stroke-width": 1.4 }), svgEl("path", { class: "jd-flame", d: "M32 10 C39 20 37 28 32 28 C27 28 25 20 32 10 Z", fill: "#ffcf6a" }), svgEl("rect", { x: 12, y: 76, width: 40, height: 6, rx: 3, fill: "#6e4a30" }));
      top.querySelector(".topbar").after(s);
    },
    hvit(top) {
      // En kvist kristtorn etter «Ålesund»
      const span = top.querySelector("h1 span"); if (!span) return;
      const s = svgEl("svg", { class: "jd-decor jd-holly", viewBox: "0 0 40 40", "aria-hidden": "true" });
      const leaf = "M0 0 C6 -4 8 -2 12 -6 C12 -2 16 0 20 -2 C18 2 20 6 24 8 C18 8 16 10 12 14 C10 10 6 10 2 10 C4 6 2 4 0 0 Z";
      s.append(svgEl("path", { d: leaf, fill: "#1f5c3a", transform: "translate(4 20) rotate(-20)" }), svgEl("path", { d: leaf, fill: "#2f7a50", transform: "translate(36 22) scale(-1 1) rotate(-20)" }),
        svgEl("circle", { cx: 17, cy: 21, r: 4.2, fill: "#c4161c" }), svgEl("circle", { cx: 24, cy: 19, r: 3.8, fill: "#e0262c" }), svgEl("circle", { cx: 20, cy: 27, r: 3.6, fill: "#b01218" }));
      span.after(s);
    },
    gran() {},
    rodtrad() {
      const jc = document.getElementById("julcard"); if (!jc) return;
      const s = svgEl("svg", { class: "jd-decor jd-bow", viewBox: "0 0 56 44", "aria-hidden": "true" });
      s.append(svgEl("path", { d: "M28 18 C18 4 4 6 6 16 C8 26 20 24 28 18 Z", fill: "#e5484d" }), svgEl("path", { d: "M28 18 C38 4 52 6 50 16 C48 26 36 24 28 18 Z", fill: "#c4161c" }),
        svgEl("path", { d: "M26 20 L18 42 L24 38 L27 44 Z M30 20 L38 42 L32 38 L29 44 Z", fill: "#a8121a" }), svgEl("circle", { cx: 28, cy: 18, r: 5, fill: "#ff6a6e" }));
      jc.appendChild(s);
    },
  };

  // Nissen som lurer over kanten: «meny» (over filtermenyen, følger med når den står fast), «kort» (over julekortet) eller «side» (inn fra høyre)
  function nisseSvg() {
    const s = svgEl("svg", { viewBox: "0 0 120 100", role: "img", "aria-label": "Nisse som titter fram" });
    s.append(svgEl("path", { d: "M30 54 Q40 10 92 18 Q108 22 106 40 Q92 30 86 54 Z", fill: "#d42a2f" }), svgEl("path", { d: "M44 30 Q60 18 82 22", fill: "none", stroke: "#ffffff33", "stroke-width": 3, "stroke-linecap": "round" }),
      svgEl("circle", { cx: 105, cy: 43, r: 7.5, fill: "#fff" }),
      svgEl("ellipse", { cx: 60, cy: 72, rx: 25, ry: 21, fill: "#f6c9a4" }),
      svgEl("rect", { x: 26, y: 47, width: 70, height: 13, rx: 6.5, fill: "#fff" }));
    const eyes = svgEl("g", { class: "jd-eyes" }); eyes.append(svgEl("circle", { cx: 51, cy: 68, r: 2.8, fill: "#2a1a14" }), svgEl("circle", { cx: 69, cy: 68, r: 2.8, fill: "#2a1a14" })); s.append(eyes);
    s.append(svgEl("circle", { cx: 44, cy: 76, r: 4.5, fill: "#f29a94", opacity: .6 }), svgEl("circle", { cx: 76, cy: 76, r: 4.5, fill: "#f29a94", opacity: .6 }),
      svgEl("path", { d: "M34 78 Q38 100 60 100 Q82 100 86 78 Q76 88 60 86 Q44 88 34 78 Z", fill: "#fff" }),
      svgEl("ellipse", { cx: 53, cy: 82, rx: 8, ry: 4, fill: "#f4f4f4" }), svgEl("ellipse", { cx: 67, cy: 82, rx: 8, ry: 4, fill: "#f4f4f4" }),
      svgEl("circle", { cx: 60, cy: 76, r: 4.2, fill: "#e88f7c" }),
      svgEl("ellipse", { cx: 24, cy: 94, rx: 11, ry: 8, fill: "#2f7a50" }), svgEl("rect", { x: 14, y: 96, width: 20, height: 5, rx: 2.5, fill: "#fff" }),
      svgEl("ellipse", { cx: 96, cy: 94, rx: 11, ry: 8, fill: "#2f7a50" }), svgEl("rect", { x: 86, y: 96, width: 20, height: 5, rx: 2.5, fill: "#fff" }));
    return s;
  }
  function nisse(place) {
    document.querySelectorAll(".jd-nisse").forEach(e => e.remove());
    if (!place) return;
    const box = Object.assign(document.createElement("div"), { className: "jd-nisse jd-peek" + (reduce ? "" : " anim") + (place === "side" ? " side" : "") });
    box.appendChild(nisseSvg());
    if (place === "meny") { const c = document.querySelector(".controls"); box.style.right = "18px"; c.appendChild(box); }
    else if (place === "kort") { const jc = document.getElementById("julcard"); if (!jc || jc.hidden) return; const w = Object.assign(document.createElement("div"), { className: "jd-nisse jd-peek-wrap" }); box.style.left = "22px"; w.appendChild(box); jc.before(w); }
    else document.body.appendChild(box);
  }

  function apply(name) {
    clear();
    if (!name || !DECOR[name]) { delete root.dataset.jul; startTema ? root.dataset.tema = startTema : delete root.dataset.tema; startTheme ? root.setAttribute("data-theme", startTheme) : root.removeAttribute("data-theme"); return; }
    font(name);
    root.dataset.jul = name;
    root.dataset.tema = "jul";                        // kveldstemaet (tema-kveld.css) av mens forslaget vises
    root.setAttribute("data-theme", DARK[name] ? "dark" : "light");
    DECOR[name](document.querySelector(".top"));
  }
  window.JULDESIGN = { apply, nisse, names: Object.keys(DECOR) };
})();
