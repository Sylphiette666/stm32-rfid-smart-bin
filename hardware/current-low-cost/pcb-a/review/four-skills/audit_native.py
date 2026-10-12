from pathlib import Path
import json,math,sys,hashlib
import pcbnew as k
root=Path(sys.argv[1]); variant=sys.argv[2] if len(sys.argv)>2 else 'baseline'; pcb=root/variant/'kicad/SmartBin_A.kicad_pcb'
b=k.LoadBoard(str(pcb)); fps={f.GetReference():f for f in b.GetFootprints()}
xy=lambda v:[k.ToMM(v.x),k.ToMM(v.y)]
gndzones=[z for z in b.Zones() if z.GetNetname()=='GND']
fills={layer:[z.GetFilledPolysList(layer) for z in gndzones if z.IsOnLayer(layer)] for layer in (k.F_Cu,k.B_Cu)}
def covers(x,y,layer):
 for poly in fills[layer]:
  for dx,dy in [(0,0)]+[(.5*math.cos(j*math.pi/4),.5*math.sin(j*math.pi/4)) for j in range(8)]:
   if poly.Contains(k.VECTOR2I(k.FromMM(x+dx),k.FromMM(y+dy))):return True
 return False
coverage={};vias=[]
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):
  vias.append({'net':t.GetNetname(),'xy':xy(t.GetPosition()),'diameter':k.ToMM(t.GetWidth(k.F_Cu)),'drill':k.ToMM(t.GetDrill())});continue
 net=t.GetNetname()
 if net in ('GND','5V_BUS','VBAT_SW','3V3_CORE','3V3_EXT'):continue
 p1=xy(t.GetStart());p2=xy(t.GetEnd());length=math.dist(p1,p2)
 if length<.1:continue
 n=max(2,int(length/2)+1);layer=k.B_Cu if t.GetLayer()==k.F_Cu else k.F_Cu
 d=coverage.setdefault(net,{'samples':0,'gnd_near':0,'trace_mm':0,'misses':[]})
 d['trace_mm']+=length
 for j in range(n):
  x=p1[0]+(p2[0]-p1[0])*j/(n-1);y=p1[1]+(p2[1]-p1[1])*j/(n-1)
  hit=covers(x,y,layer); d['samples']+=1;d['gnd_near']+=int(hit)
  if not hit and len(d['misses'])<8:d['misses'].append([round(x,3),round(y,3),b.GetLayerName(layer)])
for v in coverage.values(): v['coverage_pct']=round(v['gnd_near']/v['samples']*100,1);v['trace_mm']=round(v['trace_mm'],3)
pads={r:{p.GetNumber():{'net':p.GetNetname(),'xy':xy(p.GetPosition()),'drill':xy(p.GetDrillSize())} for p in f.Pads()} for r,f in fps.items()}
u=pads['U1']; c=pads['C8']
out={'pcb_sha256':hashlib.sha256(pcb.read_bytes()).hexdigest(),'footprint_count':len(fps),'pads':pads,'via_count':len(vias),'gnd_via_count':sum(v['net']=='GND' for v in vias),'gnd_pth_count':sum(p['net']=='GND' and p['drill'][0]>0 for f in pads.values() for p in f.values()),'coverage_method':'Native KiCad filled polygons; center and 8 points at 0.5 mm radius; 2 mm trace sampling; GND only; no antipad credit. Heuristic geometry, not EMC certification.','native_gnd_coverage':coverage,'C8_distances_mm':{'VCC_to_C8':math.dist(u['14']['xy'],c['1']['xy']),'GND_to_C8':math.dist(u['7']['xy'],c['2']['xy'])}}
(root/f'analysis/native-audit-{variant}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:out[key] for key in ('footprint_count','via_count','gnd_via_count','gnd_pth_count','C8_distances_mm')}))
print(json.dumps({n:coverage[n] for n in ('PA5','PA6','PA7','I2C_SCL','I2C_SDA','PB8') if n in coverage},ensure_ascii=False))
