from pathlib import Path

p=Path("index.html")
s=p.read_text(encoding="utf-8")

def must_replace(old,new,label):
    global s
    if old not in s:
        raise SystemExit(label+" not found")
    s=s.replace(old,new,1)

# Auto quality: react around 50 FPS, not only after dropping near 30.
must_replace("qT>=2.5","qT>=2.0","quality sample window")
must_replace("if(!lowQ&&avg>1/30)","if(!lowQ&&avg>1/52)","lowQ threshold")
must_replace("else if(lowQ&&avg>1/24)","else if(lowQ&&!vlowQ&&avg>1/40)","vlowQ threshold")

# Reduce fill-rate pressure on HiDPI displays while keeping the picture crisp.
must_replace(
'DPR=Math.min(vlowQ?1:(lowQ?1.25:2),window.devicePixelRatio||1);',
'DPR=Math.min(vlowQ?1:(lowQ?1.2:(pcMode()?1.75:1.5)),window.devicePixelRatio||1);',
"DPR")

must_replace(
'''  const placed=S.path.length, roadSet=new Set();
  for(let i=0;i<=placed;i++) roadSet.add(S.cells[i][0]+","+S.cells[i][1]);
  for(const b of (S.buildings||[])) roadSet.add(b.x+","+b.y);
  const x0=Math.floor((cam.x-W/2/z)/CELL)-1, x1=Math.ceil((cam.x+W/2/z)/CELL)+1, y0=Math.floor((cam.y-H/2/z)/CELL)-1, y1=Math.ceil((cam.y+H/2/z)/CELL)+1;
  const roadIdx=new Map(); for(let i=0;i<=placed;i++) roadIdx.set(S.cells[i][0]+","+S.cells[i][1],i);
  const cellRegion=(gx,gy)=>{ let best=-1; for(let dx=-2;dx<=2;dx++) for(let dy=-2;dy<=2;dy++){ const v=roadIdx.get((gx+dx)+","+(gy+dy)); if(v!=null&&v>best) best=v; } return best<0?curR:regionOf(Math.max(1,best)); };''',
'''  const placed=S.path.length, BL=S.buildings||[];
  const cacheKey=placed+"|"+BL.length+"|"+(run?1:0);
  if(frame._roadKey!==cacheKey||frame._roadS!==S){
    const rs=new Set(), ri=new Map();
    for(let i=0;i<=placed;i++){ const key=S.cells[i][0]+","+S.cells[i][1]; rs.add(key); ri.set(key,i); }
    for(const b of BL) rs.add(b.x+","+b.y);
    frame._roadKey=cacheKey; frame._roadS=S; frame._roadSet=rs; frame._roadIdx=ri; frame._regionCache=new Map();
  }
  const roadSet=frame._roadSet, roadIdx=frame._roadIdx, regionCache=frame._regionCache;
  const x0=Math.floor((cam.x-W/2/z)/CELL)-1, x1=Math.ceil((cam.x+W/2/z)/CELL)+1, y0=Math.floor((cam.y-H/2/z)/CELL)-1, y1=Math.ceil((cam.y+H/2/z)/CELL)+1;
  const visibleCell=(c,pad=1)=>c&&c[0]>=x0-pad&&c[0]<=x1+pad&&c[1]>=y0-pad&&c[1]<=y1+pad;
  const cellRegion=(gx,gy)=>{ const ck=gx+","+gy; const cv=regionCache.get(ck); if(cv!=null) return cv; let best=-1; for(let dx=-2;dx<=2;dx++) for(let dy=-2;dy<=2;dy++){ const v=roadIdx.get((gx+dx)+","+(gy+dy)); if(v!=null&&v>best) best=v; } const rg=best<0?curR:regionOf(Math.max(1,best)); regionCache.set(ck,rg); return rg; };''',
"road cache")

must_replace(
'''  for(let i=0;i<=placed;i++){ const c=S.cells[i], k=i===0?"camp":S.path[i-1].key, sc=pop[i]!=null?pop[i]:1; const sd=c[0]*7919+c[1]*104729, tn=i>0?REGIONS[regionOf(i)].tint:null, pc=patchSprite(k,sd,tn), E=CELL*0.8*sc; ctx.drawImage(pc,c[0]*CELL-E,c[1]*CELL-E,E*2,E*2); }
  ctx.lineCap="round"; ctx.lineJoin="round"; ctx.beginPath();
  for(let i=0;i<=placed;i++){ const c=S.cells[i]; if(i===0) ctx.moveTo(c[0]*CELL,c[1]*CELL); else ctx.lineTo(c[0]*CELL,c[1]*CELL); }
  if(placed>0) drawRoad(ctx,S,placed,curR);''',
'''  for(let i=0;i<=placed;i++){ const c=S.cells[i]; if(!visibleCell(c,2)) continue; const k=i===0?"camp":S.path[i-1].key, sc=pop[i]!=null?pop[i]:1; const sd=c[0]*7919+c[1]*104729, tn=i>0?REGIONS[regionOf(i)].tint:null, pc=patchSprite(k,sd,tn), E=CELL*0.8*sc; ctx.drawImage(pc,c[0]*CELL-E,c[1]*CELL-E,E*2,E*2); }
  ctx.lineCap="round"; ctx.lineJoin="round";
  if(placed>0) drawRoad(ctx,S,placed,curR);''',
"route sprites")

must_replace(
'''  for(let i=0;i<=placed;i++){
    const c=S.cells[i], k=i===0?"camp":S.path[i-1].key, sc=pop[i]!=null?pop[i]:1;
    ctx.save(); ctx.translate(c[0]*CELL,c[1]*CELL); ctx.scale(sc,sc); drawProps(ctx,k,0,0,CELL,t,i*31+7); ctx.restore();''',
'''  for(let i=0;i<=placed;i++){
    const c=S.cells[i]; if(!visibleCell(c,2)) continue; const k=i===0?"camp":S.path[i-1].key, sc=pop[i]!=null?pop[i]:1;
    ctx.save(); ctx.translate(c[0]*CELL,c[1]*CELL); ctx.scale(sc,sc); drawProps(ctx,k,0,0,CELL,t,i*31+7); ctx.restore();''',
"props")

must_replace(
'''  const BL=S.buildings||[];
  for(const b of BL){ const sc=bpop[b.x+","+b.y]!=null?bpop[b.x+","+b.y]:1; ctx.save(); ctx.translate(b.x*CELL,b.y*CELL); ctx.scale(sc,sc); drawBuilding(ctx,b.k,0,0,CELL,t); ctx.restore(); }''',
'''  for(const b of BL){ if(b.x<x0-2||b.x>x1+2||b.y<y0-2||b.y>y1+2) continue; const sc=bpop[b.x+","+b.y]!=null?bpop[b.x+","+b.y]:1; ctx.save(); ctx.translate(b.x*CELL,b.y*CELL); ctx.scale(sc,sc); drawBuilding(ctx,b.k,0,0,CELL,t); ctx.restore(); }''',
"buildings")

must_replace(
'''    for(let i=1;i<=lim;i++){ const ks=[...new Set(bNear(i).map(b=>b.k))]; ks.forEach((k,j)=>bBadge(ctx,k,S.cells[i][0]*CELL+CELL*0.36-j*CELL*0.19,S.cells[i][1]*CELL-CELL*0.36,CELL*0.085)); }''',
'''    for(let i=1;i<=lim;i++){ if(!visibleCell(S.cells[i],1)) continue; const ks=[...new Set(bNear(i).map(b=>b.k))]; ks.forEach((k,j)=>bBadge(ctx,k,S.cells[i][0]*CELL+CELL*0.36-j*CELL*0.19,S.cells[i][1]*CELL-CELL*0.36,CELL*0.085)); }''',
"badges")

must_replace(
'''  for(const b of (S.buildings||[])){ if(b.k==="fire") light(b.x*CELL,b.y*CELL,CELL*z*(1.9+Math.sin(t*9)*0.08)); else if(b.k==="tower"||b.k==="mill") light(b.x*CELL,b.y*CELL,CELL*z*0.9); }
  for(let i=1;i<=placed;i++){ const k=S.path[i-1].key; if(k==="village") light(S.cells[i][0]*CELL,S.cells[i][1]*CELL,CELL*z*1.35); else if(k==="guard") light(S.cells[i][0]*CELL,S.cells[i][1]*CELL,CELL*z*(1.5+Math.sin(t*11)*0.05)); }''',
'''  for(const b of BL){ if(b.x<x0-3||b.x>x1+3||b.y<y0-3||b.y>y1+3) continue; if(b.k==="fire") light(b.x*CELL,b.y*CELL,CELL*z*(1.9+Math.sin(t*9)*0.08)); else if(b.k==="tower"||b.k==="mill") light(b.x*CELL,b.y*CELL,CELL*z*0.9); }
  for(let i=1;i<=placed;i++){ if(!visibleCell(S.cells[i],3)) continue; const k=S.path[i-1].key; if(k==="village") light(S.cells[i][0]*CELL,S.cells[i][1]*CELL,CELL*z*1.35); else if(k==="guard") light(S.cells[i][0]*CELL,S.cells[i][1]*CELL,CELL*z*(1.5+Math.sin(t*11)*0.05)); }''',
"lights")

p.write_text(s,encoding="utf-8")
