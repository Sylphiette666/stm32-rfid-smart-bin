"""Place THT interfaces using native geometry; no PCB file access.
Power placement is fixed. Remaining parts are packed near functional anchors,
then iterated for collision-free bodies and shorter signal connections.
"""
from pathlib import Path
import json,math,random,time,sys
root=Path(__file__).resolve().parents[1]
cfg=json.loads((root/'circuit.json').read_text(encoding='utf-8'))
meta=json.loads((root/'checks'/'board-geometry.json').read_text(encoding='utf-8'))
parts={c['ref']:c for c in cfg['parts']};geo={c['ref']:c for c in meta['footprints']}
# Inputs from seed board are all zero-angle except fixed holes.
base={}
for r,g in geo.items():
    x,y=g['position'];a=math.radians(-g['angle']);cc=round(math.cos(a));ss=round(math.sin(a))
    points=[(cc*(xx-x)+ss*(yy-y),-ss*(xx-x)+cc*(yy-y)) for xx in (g['bbox'][0],g['bbox'][2]) for yy in (g['bbox'][1],g['bbox'][3])]
    base[r]=[min(z[0] for z in points),min(z[1] for z in points),max(z[0] for z in points),max(z[1] for z in points)]
fixed={'H1':(5,5,0),'H2':(95,5,0),'H3':(5,95,0),'H4':(95,95,0),
       'J1':(7,13,270),'J2':(7,27,270),'J3':(7,41,270),'J4':(7,55,270),'J5':(7,69,270),'J6':(7,83,270),
       'C1':(21,51,0),'C2':(21,69,0),'C3':(21,87,0),'C4':(18,60,0),'C5':(18,78,0),'C6':(18,96,0),
       'U1':(38,46,0),'C8':(49,42,0),'J8':(60,43,0),'J9':(71,43,0)}
anchors={'estop':(38,20),'i2c':(64,21),'mcp':(81,12),'spi':(85,40),'core':(60,65),'uart':(82,57),'motor':(89,79),'ahct':(43,40),'buzzer':(45,75),'ultrasonic':(50,87),'encoder':(84,91),'dht':(53,94),'voice':(77,91),'switches':(79,75),'adc':(25,28),'led':(24,12),'digital_inputs':(92,45),'power':(20,36)}
def rot(x,y,a):
    c=round(math.cos(math.radians(a)));s=round(math.sin(math.radians(a)));return c*x+s*y,-s*x+c*y
shapes={}
for r,v in base.items():
    for a in (0,90,180,270):
        corners=[rot(x,y,a) for x in (v[0],v[2]) for y in (v[1],v[3])]
        shapes[r,a]=[min(x for x,y in corners)-.3,min(y for x,y in corners)-.3,max(x for x,y in corners)+.3,max(y for x,y in corners)+.3]
def bbox(r,q):
    a=shapes[r,q[2]];return [a[0]+q[0],a[1]+q[1],a[2]+q[0],a[3]+q[1]]
def overlap(a,b):return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
def center(r,q):
    a=bbox(r,q);return ((a[0]+a[2])/2,(a[1]+a[3])/2)
nets={}
for r,c in parts.items():
    for n in set(c['pins'].values()):
        if n and n not in ['GND','5V_BUS','VBAT_SW','3V3_CORE','3V3_EXT']:nets.setdefault(n,[]).append(r)
edges={r:{} for r in parts}
for n,rs in nets.items():
    for r in rs:
        for s in rs:
            if s!=r:edges[r][s]=edges[r].get(s,0)+1/max(1,len(rs)-1)
def energy(r,q,poses,boxes):
    b=bbox(r,q);cx,cy=center(r,q)
    bad=max(0,1-b[0])+max(0,1-b[1])+max(0,b[2]-99)+max(0,b[3]-99)
    pen=bad*bad*10000
    for s,sb in boxes.items():
        if s!=r:pen+=overlap(b,sb)*10000
    ax,ay=anchors.get(parts[r]['group'],(50,50))
    pen+=.6*(abs(cx-ax)+abs(cy-ay))
    for s,w in edges[r].items():
        if s in poses:
            sx,sy=center(s,poses[s]);pen+=w*(abs(cx-sx)+abs(cy-sy))
    return pen
random.seed(10712);poses=dict(fixed);boxes={r:bbox(r,q) for r,q in poses.items()}
rest=sorted([r for r in parts if r not in fixed],key=lambda r:-(base[r][2]-base[r][0])*(base[r][3]-base[r][1]))
for r in rest:
    best=None
    for a in (0,90):
        bb=shapes[r,a]
        for x in range(3,98,2):
            for y in range(3,98,2):
                q=(x,y,a);en=energy(r,q,poses,boxes)
                if best is None or en<best[0]:best=(en,q)
    poses[r]=best[1];boxes[r]=bbox(r,best[1])
def conflicts():return [(r,s,round(overlap(boxes[r],boxes[s]),3)) for i,r in enumerate(poses) for s in list(poses)[i+1:] if overlap(boxes[r],boxes[s])>.0001]
print('greedy conflicts',len(conflicts()),flush=True)
start=time.monotonic()
for k in range(120000):
    r=random.choice(rest);old=poses[r]
    if random.random()<.22:q=(random.randrange(4,193)/2,random.randrange(4,193)/2,random.choice((0,90)))
    else:q=(round((old[0]+random.choice((-3,-2,-1,-.5,.5,1,2,3)))*2)/2,round((old[1]+random.choice((-3,-2,-1,-.5,.5,1,2,3)))*2)/2,old[2] if random.random()<.95 else 90-old[2])
    olde=energy(r,old,poses,boxes);ne=energy(r,q,poses,boxes)
    temp=25*(1-k/120000)**2+.04
    if ne<olde or random.random()<math.exp(min(0,(olde-ne)/temp)):
        poses[r]=q;boxes[r]=bbox(r,q)
    if k and k%30000==0:print(k,'conflicts',len(conflicts()),'sec',round(time.monotonic()-start),flush=True)
conf=conflicts()
out={'placements':poses,'tracks':[],'silk':[],'placement_conflicts':conf,'placement_method':'Fixed power path/decoupling + constrained packing/connection cost; needs visual review'}
(root/'layout.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
(root/'checks'/'placement-boxes.json').write_text(json.dumps({'boxes':boxes,'conflicts':conf},indent=2),encoding='utf-8')
print('done conflicts',conf,flush=True)
