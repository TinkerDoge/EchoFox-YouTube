#!/usr/bin/env python3
"""Generate an original minimal electronic editorial bed for Weekly In Tech."""
from pathlib import Path
import wave
import numpy as np

SR=48000
DURATION=59.667
BPM=100.0
BEAT=60.0/BPM
N=int(SR*DURATION)
rng=np.random.default_rng(20260810)
out=np.zeros((N,2),dtype=np.float32)

def hz(midi): return 440.0*2**((midi-69)/12)
def add(buf,start,sig,pan=0.0,gain=1.0):
    i=max(0,int(start*SR)); n=min(len(sig),N-i)
    if n<=0:return
    # equal-power panning
    l=np.cos((pan+1)*np.pi/4); r=np.sin((pan+1)*np.pi/4)
    buf[i:i+n,0]+=sig[:n]*l*gain
    buf[i:i+n,1]+=sig[:n]*r*gain

def tone(freq,dur,amp=1.0,phase=0.0):
    t=np.arange(int(dur*SR),dtype=np.float32)/SR
    return (np.sin(2*np.pi*freq*t+phase)+0.24*np.sin(2*np.pi*freq*2*t+phase*.7)+0.08*np.sin(2*np.pi*freq*3*t))*amp

def adsr(n,a=.3,d=.5,s=.7,r=.5):
    env=np.ones(n,dtype=np.float32)*s
    ia=min(n,int(a*SR)); idd=min(max(0,n-ia),int(d*SR)); ir=min(n,int(r*SR))
    if ia:env[:ia]=np.linspace(0,1,ia,dtype=np.float32)
    if idd:env[ia:ia+idd]=np.linspace(1,s,idd,dtype=np.float32)
    if ir:env[-ir:]*=np.linspace(1,0,ir,dtype=np.float32)
    return env

# Cm9 -> Abmaj7 -> Ebmaj7 -> Bbadd9, four beats each.
chords=[([48,51,55,58,62],48),([44,48,51,55],44),([51,55,58,62],51),([46,50,53,60],46)]
progression=16*BEAT
for cycle_start in np.arange(0,DURATION,progression):
    for ci,(notes,root) in enumerate(chords):
        st=cycle_start+ci*4*BEAT
        dur=4*BEAT+0.35
        if st>=DURATION:continue
        for j,m in enumerate(notes):
            sig=tone(hz(m),dur,amp=0.055,phase=j*.31)*adsr(int(dur*SR),a=.45,d=.55,s=.72,r=.65)
            # tiny detuned counterpart and broad stereo placement
            add(out,st,sig,pan=-.55+j*(1.1/max(1,len(notes)-1)))
            det=tone(hz(m)*1.003,dur,amp=0.018,phase=.7)*adsr(int(dur*SR),a=.6,d=.4,s=.65,r=.7)
            add(out,st,det,pan=.5-j*(1.0/max(1,len(notes)-1)))
        # warm bass pulse on each beat
        for b in range(4):
            bst=st+b*BEAT
            durb=.48
            t=np.arange(int(durb*SR),dtype=np.float32)/SR
            sig=(np.sin(2*np.pi*hz(root-12)*t)+.18*np.sin(2*np.pi*hz(root)*t))*np.exp(-t*3.8)*.12
            add(out,bst,sig,pan=0)

# Muted eighth-note arpeggio, kept sparse in intro/outro.
arp=[60,67,70,74,67,63,70,67]
for k,st in enumerate(np.arange(2.4,DURATION-4.2,BEAT/2)):
    m=arp[k%len(arp)]
    dur=.38
    t=np.arange(int(dur*SR),dtype=np.float32)/SR
    env=np.exp(-t*8.0)*(1-np.exp(-t*90))
    sig=(np.sin(2*np.pi*hz(m)*t)+.28*np.sin(2*np.pi*hz(m)*2*t))*env*.065
    add(out,st,sig,pan=(-.5 if k%2==0 else .5))

# Soft editorial pulse: kick each beat, brushed hat on eighth notes.
for k,st in enumerate(np.arange(3.6,DURATION-5.0,BEAT)):
    dur=.24;t=np.arange(int(dur*SR),dtype=np.float32)/SR
    phase=2*np.pi*(78*t-(34/(2*dur))*t*t)
    kick=np.sin(phase)*np.exp(-t*20)*.18
    add(out,st,kick,pan=0)
for k,st in enumerate(np.arange(4.2,DURATION-5.0,BEAT/2)):
    dur=.075;t=np.arange(int(dur*SR),dtype=np.float32)/SR
    noise=rng.normal(0,1,len(t)).astype(np.float32)
    hp=np.concatenate(([0],np.diff(noise))).astype(np.float32)
    hat=hp*np.exp(-t*(62 if k%2 else 46))*(.017 if k%2 else .013)
    add(out,st,hat,pan=(-.42 if k%2 else .42))

# Subtle transition bells at the locked scene boundaries.
for i,st in enumerate([2.4,12.5,23.2,33.7,44.5,55.5]):
    for offset,m,g in [(0,72,.034),(.08,79,.022),(.17,75,.018)]:
        dur=1.15;t=np.arange(int(dur*SR),dtype=np.float32)/SR
        sig=(np.sin(2*np.pi*hz(m)*t)+.32*np.sin(2*np.pi*hz(m)*2.01*t))*np.exp(-t*3.4)*g
        add(out,st+offset,sig,pan=(-.35+i*.14)%1-.5)

# Gentle stereo delay/reverb; no external samples.
dry=out.copy()
for delay,gain,cross in [(0.145,.13,False),(0.287,.085,True),(0.413,.045,False)]:
    d=int(delay*SR)
    if cross:
        out[d:,0]+=dry[:-d,1]*gain;out[d:,1]+=dry[:-d,0]*gain
    else:
        out[d:]+=dry[:-d]*gain

# Intro/outro fades and slight story-safe contour.
t=np.arange(N,dtype=np.float32)/SR
env=np.ones(N,dtype=np.float32)
env*=np.minimum(1,t/1.1)
env*=np.minimum(1,(DURATION-t)/2.8)
# Leave breathing space around the opening identity cue.
env*=0.82+0.18*np.minimum(1,t/5.0)
out*=env[:,None]
# Soft saturation and deterministic peak normalization.
out=np.tanh(out*1.35)
peak=float(np.max(np.abs(out)))
out*=0.891/max(peak,1e-9)  # -1 dBFS
pcm=np.clip(out*32767,-32768,32767).astype('<i2')
path=Path(__file__).with_name('weekly_in_tech_editorial_bed_v1.wav')
with wave.open(str(path),'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
print(path)
print('duration',N/SR,'peak',float(np.max(np.abs(out))))
