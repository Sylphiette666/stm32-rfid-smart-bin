"""Native KiCad read-only geometry planner for Hubert IPC ground stitching."""
import pcbnew as k
import math,json
from pathlib import Path
R=Path(__file__).resolve().parent
b=k.LoadBoard(str(R/'baseline/kicad/SmartBin_A.kicad_pcb'))
xy=lambda p:(k.ToMM(p.x),k.ToMM(p.y))
tracks=[];pads=[];gnd=[];vias=[]
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):
  vias.append(xy(t.GetPosition()))
  if t.GetNetname()!='GND':tracks.append((xy(t.GetPosition()),xy(t.GetPosition()),k.ToMM(t.GetWidth(k.F_Cu))/2))
 elif t.GetNetname()!='GND':tracks.append((xy(t.GetStart()),xy(t.GetEnd()),k.ToMM(t.GetWidth())/2))
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetNetname()=='GND':gnd.append(xy(p.GetPosition()))
  q=p.GetBoundingBox();pads.append((k.ToMM(q.GetX())-.65,k.ToMM(q.GetY())-.65,k.ToMM(q.GetRight())+.65,k.ToMM(q.GetBottom())+.65))
fills=[z.GetFilledPolysList(z.GetLayer()) for z in b.Zones() if z.GetNetname()=='GND']
def dist(p,a,c):
 dx,dy=c[0]-a[0],c[1]-a[1];d=dx*dx+dy*dy
 t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/d)) if d else 0
 return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
def safe(p):
 x,y=p
 if not (51.5<x<148.5 and 51.5<y<148.5):return False
 if any(a<=x<=c and bb<=y<=d for a,bb,c,d in pads):return False
 if any(dist(p,a,c)<r+.65 for a,c,r in tracks):return False
 if any(math.dist(p,v)<1 for v in vias):return False
 return any(poly.Contains(k.VECTOR2I(k.FromMM(x),k.FromMM(y))) for poly in fills)
targets=[]
critical={'PA5','PA6','PA7','I2C_SCL','I2C_SDA','PB8','PB9','PA0','PB15'}
for t in b.GetTracks():
 if t.GetNetname() in critical:
  if isinstance(t,k.PCB_VIA):targets.append(xy(t.GetPosition()))
  else:
   a,c=xy(t.GetStart()),xy(t.GetEnd());n=max(1,int(math.dist(a,c)/5))
   targets.extend((a[0]+(c[0]-a[0])*i/n,a[1]+(c[1]-a[1])*i/n) for i in range(n+1))
targets.extend((x,y) for x in range(54,148,12) for y in range(54,148,12))
chosen=[]
for target in targets:
 if any(math.dist(target,p)<4 for p in chosen+gnd):continue
 candidates=[]
 for radius in (1,1.5,2,2.5,3,4):
  for j in range(16):
   p=tuple(round(target[i]+radius*(math.cos if i==0 else math.sin)(j*math.pi/8),2) for i in range(2))
   if safe(p) and all(math.dist(p,q)>4 for q in chosen+gnd):candidates.append(p)
  if candidates:break
 if candidates:chosen.append(min(candidates,key=lambda p:math.dist(p,target)))
out={'diameter_mm':.8,'drill_mm':.4,'net':'GND','points':chosen,'count':len(chosen),'method':'0.25mm conservative copper gap; pad bounding boxes excluded; at least one existing GND polygon; >=4mm from other GND anchors'}
(R/'analysis/stitch-plan.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
