from pathlib import Path

p = Path("index.html")
s = p.read_text(encoding="utf-8")

replacements = [
("""function ensureAudio(){
  if(!actx){ try{ actx=new (window.AudioContext||window.webkitAudioContext)(); }catch(e){ actx=null; } }
  applyAudio(); startMusic();
}""",
"""let audioUnlockPromise=null;
function ensureAudio(){
  if(!actx){ try{ actx=new (window.AudioContext||window.webkitAudioContext)(); }catch(e){ actx=null; } }
  if(!actx) return Promise.resolve(false);
  const finish=()=>{ applyAudio(); startMusic(); return actx.state==="running"; };
  if(actx.state==="running"){ finish(); return Promise.resolve(true); }
  try{
    const r=actx.resume();
    if(r&&typeof r.then==="function"){
      audioUnlockPromise=r.then(()=>{ finish(); return actx.state==="running"; }).catch(()=>false);
    }else{
      finish(); audioUnlockPromise=Promise.resolve(actx.state==="running");
    }
  }catch(e){
    finish(); audioUnlockPromise=Promise.resolve(false);
  }
  return audioUnlockPromise;
}"""),
("""["touchend","pointerup","keydown"].forEach(ev=>window.addEventListener(ev,()=>{ if(actx&&(actx.state==="suspended"||actx.state==="interrupted")) applyAudio(); },{passive:true}));""",
"""function primeAudioFromGesture(){
  try{
    const p=ensureAudio();
    if(p&&typeof p.then==="function") p.then(ok=>{
      if(!ok||!actx) return;
      try{
        const o=actx.createOscillator(), g=actx.createGain();
        g.gain.value=0.00001; o.connect(g); g.connect(actx.destination);
        o.start(); o.stop(actx.currentTime+0.01);
      }catch(e){}
    });
  }catch(e){}
}
["pointerdown","touchstart","keydown"].forEach(ev=>window.addEventListener(ev,primeAudioFromGesture,{passive:true}));"""),
("""  hit:()=>{ noise(0.07,0.07,"highpass",1500,4000,0.7); tone("sine",150,55,0.12,0.09,0.02); tone("triangle",1400,1100,0.06,0.02,0.02); },
  hurt:()=>{ tone("sine",110,45,0.18,0.11); noise(0.12,0.07,"lowpass",700,250,0.8); tone("sawtooth",160,110,0.1,0.025,0.02); },""",
"""  hit:()=>{ noise(0.085,0.11,"highpass",1350,4300,0.7); tone("sine",165,48,0.14,0.14,0.015); tone("triangle",1550,900,0.075,0.045,0.015); },
  hurt:()=>{ tone("sine",125,42,0.2,0.15); noise(0.14,0.10,"lowpass",850,220,0.8); tone("sawtooth",185,95,0.12,0.045,0.015); },"""),
("""function sfx(n){ try{ SFX[n]&&SFX[n](); }catch(e){} }""",
"""function sfx(n){
  const play=()=>{ try{ SFX[n]&&SFX[n](); }catch(e){} };
  try{
    if(!actx){
      const p=ensureAudio();
      if(p&&typeof p.then==="function") p.then(ok=>{ if(ok&&prefs.sound&&!paused) play(); });
      return;
    }
    if(actx.state==="running"){ play(); return; }
    if(!prefs.sound||paused) return;
    const p=ensureAudio();
    if(p&&typeof p.then==="function") p.then(ok=>{ if(ok&&prefs.sound&&!paused) play(); });
  }catch(e){}
}""")
]

for old, new in replacements:
    if old not in s:
        raise SystemExit("expected audio block not found")
    s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
