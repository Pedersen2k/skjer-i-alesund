"""Bygger ferdig.html (karusell A med 5 bilder og reel 1) av stilene og tegningene i index.html.

python3 docs/putti-instagram/lag_ferdig.py   # lager docs/putti-instagram/ferdig.html
node docs/putti-instagram/render.js <ut-mappe> # lager PNG-er og bilder til filmen
"""
import re
from pathlib import Path

HER = Path(__file__).parent
src = (HER / "index.html").read_text()

style = re.search(r"<style>.*?</style>", src, re.S).group(0)
defs = "\n".join(re.findall(r'<svg width="0" height="0" style="position:absolute" aria-hidden="true">.*?</svg>\n', src, re.S))
# tyv-scenen med nissen (forslag B)
i = src.index('<div class="thief ">', src.index('<section id="tyv">'))
starts = [m.start() for m in re.finditer(r'<div class="thief', src[i:])]
thiefB = src[i + starts[1]: i + starts[2]]
thiefB = thiefB[: thiefB.rindex('<div class="cap">')]
nisse = re.search(r'<g class="nisse".*?</g></g>', thiefB, re.S).group(0)
nisse_still = (nisse.replace('class="nisse" transform="translate(135,452) scale(1.3)"', 'class="nisse" transform="translate(70,190) scale(1.15)"')
               .replace('<g class="nB">', '<g>').replace('class="armsDown"', 'class="armsDown" display="none"')
               .replace('class="armsUp"', 'class="armsUpS"').replace('class="eyes"', 'class="eyesS"'))

EXTRA = """
<style>
body{background:#222;margin:0}
.slides{display:flex;flex-wrap:wrap;gap:20px;padding:20px}
.post{border-radius:0!important}
#reel{width:270px;height:480px;position:relative;overflow:hidden;background:var(--night)}
#reel .scn{position:absolute;inset:0;opacity:0}
#reel .scn>.reel,#reel .scn>.thief{width:100%;height:100%;border-radius:0}
#reel .thief .lbl{font-size:19px}
.still *{animation:none!important}
.big2{font-weight:800;font-size:27px;line-height:1.02;text-wrap:balance}
/* reel-scener */
.rin{animation:rin .5s cubic-bezier(.3,1.5,.5,1) both}
.rin2{animation:rin .5s .45s cubic-bezier(.3,1.5,.5,1) both}
.rin3{animation:rin .5s .9s cubic-bezier(.3,1.5,.5,1) both}
@keyframes rin{from{transform:scale(.6);opacity:0}to{transform:none;opacity:1}}
.rise{animation:rise .7s cubic-bezier(.2,1.3,.5,1) both}
@keyframes rise{from{transform:translateY(160px)}to{transform:none}}
.bob{animation:bob .8s .7s ease-in-out infinite alternate}
@keyframes bob{from{transform:translateY(0)}to{transform:translateY(-6px)}}
.sq span{background:var(--gold);animation:sq .2s both}
""" + "".join(f".sq span:nth-child({k+1}){{animation-delay:{0.35 + k*0.14:.2f}s}}" for k in range(11)) + """
@keyframes sq{to{background:var(--red)}}
</style>
"""

def beard_ghost():
    return """<svg viewBox="0 0 240 150" style="width:82%;height:auto;display:block;margin:0 auto 4px">
  <path d="M-10,22 Q120,46 250,18" fill="none" stroke="#c9cfdb" stroke-width="1.4" opacity=".8"/>
  <rect x="82" y="22" width="7" height="22" rx="2" fill="#b98a55" transform="rotate(-8 85 22)"/>
  <rect x="150" y="22" width="7" height="22" rx="2" fill="#b98a55" transform="rotate(10 153 22)"/>
  <use href="#beard" x="64" y="30" width="112" height="122" opacity=".16"/>
  <use href="#beard" x="64" y="30" width="112" height="122" fill="none" opacity="0"/>
</svg>"""

def nisse_med_skjegg(cls="", w=150):
    return f"""<svg viewBox="0 0 140 200" style="width:{w}px;height:auto;display:block;margin:0 auto" class="{cls}">
  <use href="#beard" x="28" y="0" width="84" height="92"/>
  {nisse_still}
</svg>"""

chips = "".join(f'<div class="chip"><i>{d}</i>{t}</div>' for d, t in [
    ("Fre 27.11", "18:00"), ("Lør 28.11", "13:00 · 16:00"), ("Søn 29.11", "13:00 · 16:00"), ("Tor 3.12", "18:00"),
    ("Fre 4.12", "18:00"), ("Lør 5.12", "13:00 · 16:00"), ("Søn 6.12", "13:00 · 16:00"), ("Pris", "350 kr")])

SLIDES = f"""
<div class="slides">
<div class="post night" id="s1"><div class="kicker">Ålesund, november</div>{beard_ghost()}<div class="big2" style="font-size:25px;margin-bottom:22px">Noen har rappet julenissens skjegg.</div><div class="foot"><span>kaskjerda.no</span><span>sveip →</span></div></div>

<div class="post redbg" id="s2" style="justify-content:flex-start;padding-top:16px">{nisse_med_skjegg(w=118)}<div class="big2" style="margin-top:2px;font-size:25px">Det var Putti Plutti Pott. Igjen.</div><div class="small" style="margin-top:6px;margin-bottom:22px">Nå er han på vei hjem til Onkel Per, Pernille, Petter og Lille Caroline.</div><div class="foot"><span>kaskjerda.no</span><span>→</span></div></div>

<div class="post night" id="s3"><div class="kicker">Jugendteateret · Ålesund kulturskole</div><div class="big" style="font-size:64px;line-height:.95;color:var(--gold)">200</div><div class="mid" style="font-size:24px">elever på scenen</div><div class="small" style="margin-top:14px;font-size:13px">For 35. gang setter Jugendteateret opp Putti Plutti Pott. Ny scenografi. Anbefalt fra 3 år.</div><div class="foot"><span>Parken kulturhus</span><span>→</span></div></div>

<div class="post snowbg" id="s4"><span class="stamp">Få igjen</span><div class="kicker" style="color:var(--red);margin-top:18px">Alle 11 forestillinger</div><div class="mid">Få billetter igjen</div><div class="chips">{chips}</div><div class="foot"><span>Parken kulturhus</span><span>→</span></div></div>

<div class="post redbg" id="s5" style="text-align:center;align-items:center"><div class="big2">Rekk det før skjegget er borte.</div><div class="small" style="margin-top:14px;font-size:13px">Billetter hos Parken kulturhus<br>Alle tidene: kaskjerda.no</div><div class="foot" style="justify-content:center"><span>@parken_kulturhus</span></div></div>
</div>
"""

bars = "<span></span>" * 11
REEL = f"""
<div id="reel">
  <div class="scn" data-start="0" data-end="5.6">{thiefB.replace('class="thief "', 'class="thief"')}</div>
  <div class="scn" data-start="5.6" data-end="8.2"><div class="reel redbg" style="justify-content:flex-start;padding-top:70px"><div class="rise"><div class="bob">{nisse_med_skjegg()}</div></div><div class="t rin2" style="font-size:28px;margin-top:14px">Det var Putti Plutti Pott. Igjen.</div></div></div>
  <div class="scn" data-start="8.2" data-end="10.8"><div class="reel night"><div class="kicker rin">Jugendteateret · 200 elever</div><div class="t rin" style="font-size:36px">Putti Plutti Pott</div><div class="small rin2" style="margin-top:14px;font-size:15px;line-height:1.5">Parken kulturhus<br>27. nov – 6. des<br>Fra 3 år · 350 kr</div></div></div>
  <div class="scn" data-start="10.8" data-end="14"><div class="reel snowbg"><div class="mid rin" style="font-size:26px">11 forestillinger</div><div class="reelbar sq" style="margin-top:16px;gap:6px;max-width:190px">{bars.replace('<span>', '<span style="width:24px;height:24px;border-radius:5px">')}</div><div class="small rin3" style="margin-top:16px;font-size:16px;line-height:1.45">Få billetter igjen på alle.<br><b>kaskjerda.no</b></div></div></div>
</div>
<script>
const scn=[...document.querySelectorAll('#reel .scn')];
window.reelLength=14;
window.renderAt=function(t){{
  const F=.25;
  scn.forEach(s=>{{
    const a=+s.dataset.start,b=+s.dataset.end;
    let o=0; if(t>=a-F&&t<b){{o=Math.min(1,(t-a+F)/F); if(a===0)o=1; if(t>b-F&&b<window.reelLength)o=Math.min(o,(b-t)/F+0);}}
    s.style.opacity=o>0?Math.max(0,Math.min(1,o)):0;
    const lt=Math.max(0,t-a);
    s.getAnimations({{subtree:true}}).forEach(an=>{{an.pause();an.currentTime=lt*1000;}});
  }});
}};
renderAt(0);
</script>
"""

out = f"""<!doctype html><html lang="no"><head><meta charset="utf-8"><title>Putti Plutti Pott – ferdig</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,800&family=Inter:wght@400;600&display=swap">
{style}{EXTRA}</head><body>
{defs}
{SLIDES}
{REEL}
</body></html>"""
(HER / "ferdig.html").write_text(out)
print("skrev", HER / "ferdig.html")
