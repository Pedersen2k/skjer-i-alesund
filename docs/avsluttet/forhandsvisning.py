"""Forslag til «Tips oss» på sider for arrangementer som er over.
Kjør etter scripts/pages.py. Skriver preview/avsluttet/index.html (én fil, bytter forslag med #a, #b, #c, #n)."""
import pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
site = ROOT / "_site"
page = (site / "arrangement/golf-terminalen-byscene/index.html").read_text()
css = (site / "stil.css").read_text() + (site / "tema-kveld.css").read_text()
page = re.sub(r'<link rel="stylesheet" href="[^"]*(stil|tema-kveld)\.css[^"]*">', "", page)
EXTRA = """
.tips-a{margin:14px 0 0;font-size:14px;color:var(--muted)}.tips-a a{color:var(--fg)}
.tips-b{margin:28px 0 0;padding:18px;border:1px dashed var(--line);border-radius:14px;background:var(--surface)}
.tips-b h2{font:700 18px/1.2 var(--font-display);margin:0 0 6px}.tips-b p{margin:0 0 12px;font-size:15px;color:var(--muted)}
.tips-c{margin-top:10px;font-size:14px}.tips-c a{font-weight:600}
.pick{position:fixed;left:0;right:0;bottom:0;z-index:50;background:#111c;backdrop-filter:blur(6px);display:flex;gap:6px;flex-wrap:wrap;justify-content:center;padding:8px;font:600 13px system-ui}
.pick a{color:#fff;text-decoration:none;padding:6px 10px;border-radius:99px;border:1px solid #fff5}.pick a.on{background:#fff;color:#000}
body{padding-bottom:70px}
"""
V = {
 "a": ('Etter knappene', 'Én diskret linje under knappene', '<p class="tips-a">Savner du et arrangement? <a href="../../kontakt/">Tips oss →</a></p>', ".cta"),
 "b": ('Eget kort nederst', 'Kort under listene', '<section class="tips-b"><h2>Ser du noe vi ikke har med?</h2><p>Vi samler det som skjer i Ålesund. Sender du oss et tips, legger vi det inn med lenke til arrangøren.</p><a class="btn" href="../../kontakt/">Foreslå et arrangement</a></section>', "main"),
 "c": ('I stripen øverst', 'Inni «er over»-stripen', '<div class="tips-c">Savner du noe på programmet? <a href="../../kontakt/">Tips oss</a></div>', ".overbar"),
}
tabs = "".join(f'<a href="#{k}" data-k="{k}">{k.upper()} · {v[0]}</a>' for k, v in V.items()) + '<a href="#n" data-k="n">Ingen</a>'
js = """const V=%s;
function go(){const k=(location.hash||'#a').slice(1);
 document.querySelectorAll('.inj').forEach(x=>x.remove());
 const v=V[k];
 if(v){const t=document.querySelector(v[1]);const d=document.createElement('div');d.className='inj';d.innerHTML=v[0];
  if(v[2]==='in')t.appendChild(d);else t.after(d);}
 document.querySelectorAll('.pick a').forEach(a=>a.classList.toggle('on',a.dataset.k===k));}
addEventListener('hashchange',go);go();""" % __import__("json").dumps({k: [v[2], v[3], "in" if k in "bc" else "after"] for k, v in V.items()})
out = page.replace("</head>", f"<style>{css}</style><style>{EXTRA}</style></head>").replace("</body>", f'<div class="pick">{tabs}</div><script>{js}</script></body>')
out = out.replace("../../", "https://kaskjerda.no/")
d = ROOT / "preview/avsluttet"; d.mkdir(parents=True, exist_ok=True); (d / "index.html").write_text(out)
print(d / "index.html", len(out) // 1024, "kB")
