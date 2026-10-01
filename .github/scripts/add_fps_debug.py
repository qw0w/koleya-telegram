from pathlib import Path
p=Path("index.html")
s=p.read_text(encoding="utf-8")

anchor='let lastT=performance.now();'
insert=r'''const PERF_FPS_DEBUG=new URLSearchParams(location.search).get("fps")==="1";
let perfFpsEl=null, perfFpsT=performance.now(), perfFpsN=0, perfFpsVal=0;
function perfFpsTick(now){
  if(!PERF_FPS_DEBUG) return;
  perfFpsN++;
  const span=now-perfFpsT;
  if(span>=500){
    perfFpsVal=Math.round(perfFpsN*1000/span);
    perfFpsN=0; perfFpsT=now;
    if(!perfFpsEl){
      perfFpsEl=document.createElement("div");
      perfFpsEl.style.cssText="position:fixed;right:8px;top:8px;z-index:99999;padding:5px 7px;border-radius:6px;background:rgba(0,0,0,.72);color:#9cff9c;font:700 12px ui-monospace,monospace;pointer-events:none";
      document.body.appendChild(perfFpsEl);
    }
    perfFpsEl.textContent=perfFpsVal+" FPS";
  }
}
let lastT=performance.now();'''
if anchor not in s: raise SystemExit("lastT anchor not found")
s=s.replace(anchor,insert,1)

anchor='function frame(now){\n  const rawDt='
replace='function frame(now){\n  perfFpsTick(now);\n  const rawDt='
if anchor not in s: raise SystemExit("frame anchor not found")
s=s.replace(anchor,replace,1)

p.write_text(s,encoding="utf-8")
