#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SCRIPT=ROOT/'script/ashe_narration_clean_v2.txt'
OUT=ROOT/'captions/captions_clean_v2.ass'
# Sentence timing measured from the clean, natural-speed VibeVoice take.
RANGES=[(0.00,4.70),(6.36,14.32),(15.50,25.20),(26.20,35.02),(36.58,45.08),(46.08,53.56),(54.38,59.50)]
lines=[x.split(': ',1)[1].strip() for x in SCRIPT.read_text().splitlines() if x.startswith('Speaker 1:')]
assert len(lines)==len(RANGES)==7

def ast(t):
    h=int(t//3600); m=int((t%3600)//60); s=t%60
    return f'{h}:{m:02d}:{s:05.2f}'
def esc(s): return s.replace('{',r'\{').replace('}',r'\}')
def chunks(words):
    out=[]; cur=[]
    for w in words:
        trial=cur+[w]
        if cur and (len(trial)>7 or len(' '.join(trial))>50): out.append(cur); cur=[w]
        else: cur=trial
    if cur: out.append(cur)
    return out
def split2(text):
    if len(text)<=30:return text
    ws=text.split(); i=min(range(1,len(ws)),key=lambda n:abs(len(' '.join(ws[:n]))-len(' '.join(ws[n:]))))
    return ' '.join(ws[:i])+r'\N'+' '.join(ws[i:])
header='''[Script Info]\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Caption,DejaVu Sans,34,&H00FFFFFF,&H00FFFFFF,&H00120F0B,&H90000000,-1,0,0,0,100,100,0,0,3,2,0,2,50,50,145,1\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'''
events=[]
for text,(start,end) in zip(lines,RANGES):
    cs=chunks(text.split()); total=sum(len(c) for c in cs); cursor=start
    for idx,c in enumerate(cs):
        dur=(end-start)*len(c)/total
        cend=end if idx==len(cs)-1 else cursor+dur
        events.append(f'Dialogue: 0,{ast(cursor)},{ast(cend)},Caption,,0,0,0,,{{\\an2\\pos(360,1170)}}{esc(split2(" ".join(c)))}')
        cursor=cend
OUT.write_text(header+'\n'.join(events)+'\n')
print(OUT, len(events), 'events')
