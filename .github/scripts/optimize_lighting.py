from pathlib import Path

p=Path("index.html")
s=p.read_text(encoding="utf-8")

anchor='let dayK=0;'
insert=r'''let lightMaskCache=null, warmLightCache=null;
function lightMaskSprite(){
  if(lightMaskCache) return lightMaskCache;
  const cv=document.createElement("canvas"); cv.width=cv.height=128;
  const g=cv.getContext("2d"), r=64, gr=g.createRadialGradient(r,r,r*0.15,r,r,r);
  gr.addColorStop(0,"rgba(0,0,0,1)"); gr.addColorStop(1,"rgba(0,0,0,0)");
  g.fillStyle=gr; g.fillRect(0,0,128,128); lightMaskCache=cv; return cv;
}
function warmLightSprite(){
  if(warmLightCache) return warmLightCache;
  const cv=document.createElement("canvas"); cv.width=cv.height=128;
  const g=cv.getContext("2d"), r=64, gr=g.createRadialGradient(r,r,0,r,r,r);
  gr.addColorStop(0,"rgba(255,190,110,.10)"); gr.addColorStop(1,"rgba(255,190,110,0)");
  g.fillStyle=gr; g.fillRect(0,0,128,128); warmLightCache=cv; return cv;
}
let dayK=0;'''
if anchor not in s: raise SystemExit("dayK anchor not found")
s=s.replace(anchor,insert,1)

old='''  const light=(wx,wy,rad)=>{ const [px,py]=toS(wx,wy), g=dctx.createRadialGradient(px,py,rad*0.15,px,py,rad); g.addColorStop(0,"rgba(0,0,0,1)"); g.addColorStop(1,"rgba(0,0,0,0)"); dctx.fillStyle=g; dctx.fillRect(px-rad,py-rad,rad*2,rad*2); };'''
new='''  const light=(wx,wy,rad)=>{ const [px,py]=toS(wx,wy), sp=lightMaskSprite(); dctx.drawImage(sp,px-rad,py-rad,rad*2,rad*2); };'''
if old not in s: raise SystemExit("light gradient block not found")
s=s.replace(old,new,1)

old='''  drawWeather(ctx,dt,curR);
  const [hx,hy]=toS(heroPx.x,heroPx.y), warm=ctx.createRadialGradient(hx,hy,0,hx,hy,CELL*z*2);
  warm.addColorStop(0,"rgba(255,190,110,.10)"); warm.addColorStop(1,"rgba(255,190,110,0)"); ctx.fillStyle=warm; ctx.fillRect(0,0,W,H);'''
new='''  drawWeather(ctx,dt,curR);
  const [hx,hy]=toS(heroPx.x,heroPx.y), warmR=CELL*z*2, warm=warmLightSprite();
  ctx.drawImage(warm,hx-warmR,hy-warmR,warmR*2,warmR*2);'''
if old not in s: raise SystemExit("warm light block not found")
s=s.replace(old,new,1)

p.write_text(s,encoding="utf-8")
