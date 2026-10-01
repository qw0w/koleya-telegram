from pathlib import Path

p = Path("index.html")
s = p.read_text(encoding="utf-8")

anchor = 'function setVol(){ if(!actx) return; setMusic(); if(sfxGain) sfxGain.gain.setTargetAtTime(0.95*prefs.vS,actx.currentTime,0.05); }'
insert = '''function setVol(){ if(!actx) return; setMusic(); if(sfxGain) sfxGain.gain.setTargetAtTime(0.95*prefs.vS,actx.currentTime,0.05); }
function duckMusic(depth=0.22,hold=0.10){
  if(!actx||!music.nodes||!prefs.music) return;
  try{
    const g=music.nodes.out.gain, t=actx.currentTime, base=0.55*prefs.vM;
    g.cancelScheduledValues(t);
    g.setValueAtTime(Math.max(0.0001,g.value),t);
    g.setTargetAtTime(Math.max(0.0001,base*depth),t,0.008);
    g.setTargetAtTime(base,t+hold,0.055);
  }catch(e){}
}'''
if 'function duckMusic(' not in s:
    if anchor not in s:
        raise SystemExit("setVol anchor not found")
    s = s.replace(anchor, insert, 1)

old_hit = '  hit:()=>{ noise(0.085,0.11,"highpass",1350,4300,0.7); tone("sine",165,48,0.14,0.14,0.015); tone("triangle",1550,900,0.075,0.045,0.015); },'
new_hit = '  hit:()=>{ duckMusic(0.16,0.11); noise(0.11,0.22,"highpass",1100,4800,0.75); noise(0.075,0.15,"bandpass",520,190,1.15,0.006); tone("sine",190,42,0.17,0.30,0.004); tone("triangle",1650,720,0.09,0.12,0.008); tone("square",92,48,0.07,0.10,0.012); },'
if old_hit not in s:
    raise SystemExit("current hit SFX not found")
s = s.replace(old_hit, new_hit, 1)

old_hurt = '  hurt:()=>{ tone("sine",125,42,0.2,0.15); noise(0.14,0.10,"lowpass",850,220,0.8); tone("sawtooth",185,95,0.12,0.045,0.015); },'
new_hurt = '  hurt:()=>{ duckMusic(0.12,0.15); tone("sine",145,38,0.24,0.32); noise(0.17,0.20,"lowpass",980,170,0.9); noise(0.09,0.12,"bandpass",1400,520,1.1,0.008); tone("sawtooth",210,82,0.14,0.11,0.012); },'
if old_hurt not in s:
    raise SystemExit("current hurt SFX not found")
s = s.replace(old_hurt, new_hurt, 1)

p.write_text(s, encoding="utf-8")
