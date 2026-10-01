from pathlib import Path

p=Path("index.html")
s=p.read_text(encoding="utf-8")

# Cache procedural background cells when quality has stepped down.
sig='function drawDecor(c,gx,gy,rg,t){'
if sig not in s:
    raise SystemExit("drawDecor signature not found")

wrapper=r'''const decorTileCache=new Map();
function drawDecor(c,gx,gy,rg,t){
  if(!lowQ){ drawDecorRaw(c,gx,gy,rg,t); return; }
  const q=vlowQ?0.85:1.05, size=CELL*2.5, pad=CELL*0.75;
  const phase=vlowQ?0:Math.floor((t+hash(gx,gy,991)*0.5)*2.2);
  const key=gx+","+gy+":"+rg+":"+(vlowQ?"v":"l");
  let e=decorTileCache.get(key);
  if(!e||e.phase!==phase){
    if(!e){
      const cv=document.createElement("canvas");
      e={cv,phase:-1};
      decorTileCache.set(key,e);
      if(decorTileCache.size>140) decorTileCache.delete(decorTileCache.keys().next().value);
    }
    const cv=e.cv;
    const pw=Math.ceil(size*q);
    if(cv.width!==pw||cv.height!==pw){ cv.width=pw; cv.height=pw; }
    const g=cv.getContext("2d",{alpha:true});
    g.setTransform(q,0,0,q,(pad-gx*CELL)*q,(pad-gy*CELL)*q);
    g.clearRect(gx*CELL-pad,gy*CELL-pad,size,size);
    drawDecorRaw(g,gx,gy,rg,t);
    e.phase=phase;
  }
  c.drawImage(e.cv,gx*CELL-pad,gy*CELL-pad,size,size);
}
function drawDecorRaw(c,gx,gy,rg,t){'''
s=s.replace(sig,wrapper,1)

# Weather: fewer particles at normal auto quality after lowQ engages; cache time per frame.
old='''function drawWeather(c,dt,rg){
  const want=Math.round(([14,60,6,55,34,0][rg]||0)*(lowQ?0.45:1));'''
new='''function drawWeather(c,dt,rg){
  const wxNow=performance.now(), wxSec=wxNow/1000;
  const want=Math.round(([12,48,6,44,28,0][rg]||0)*(lowQ?(vlowQ?0.28:0.42):1));'''
if old not in s:
    raise SystemExit("drawWeather header not found")
s=s.replace(old,new,1)
s=s.replace('Math.sin(performance.now()/1000*1.3+p.ph)','Math.sin(wxSec*1.3+p.ph)',1)
s=s.replace('Math.sin(performance.now()/1000*2+p.ph)','Math.sin(wxSec*2+p.ph)',1)
s=s.replace('Math.sin(performance.now()/700+p.ph)','Math.sin(wxNow/700+p.ph)',1)
s=s.replace('Math.sin(performance.now()/900+p.ph)','Math.sin(wxNow/900+p.ph)',1)
s=s.replace('Math.sin(performance.now()/400+p.ph)','Math.sin(wxNow/400+p.ph)',1)

# Motes: reduce only ambient density, never combat particles.
old='''const type=REGIONS[r].mote, want=Math.round((type==="fog"?9:(type==="ash"?34:24))*(lowQ?0.5:1)), vw=W/z, vh=H/z;'''
new='''const type=REGIONS[r].mote, want=Math.round((type==="fog"?8:(type==="ash"?28:20))*(lowQ?(vlowQ?0.32:0.48):1)), vw=W/z, vh=H/z;'''
if old not in s:
    raise SystemExit("mote density line not found")
s=s.replace(old,new,1)

# Mist density gets a second very-low tier instead of only on/off.
old='''const vw=W/z, vh=H/z, want=lowQ?4:(rg===1||rg===2||rg===NAV?11:7);'''
new='''const vw=W/z, vh=H/z, want=vlowQ?0:(lowQ?3:(rg===1||rg===2||rg===NAV?9:6));'''
if old not in s:
    raise SystemExit("mist density line not found")
s=s.replace(old,new,1)

p.write_text(s,encoding="utf-8")
