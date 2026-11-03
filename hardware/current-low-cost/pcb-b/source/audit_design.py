"""Independent JSON/XML/geometry checks; no KiCad file text parsing."""
from pathlib import Path
import json,csv,math,heapq
import xml.etree.ElementTree as ET
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
spec=read(R/'circuit.json');base=read(R.with_name('pcb-a')/'circuit.json');geo=read(R/'checks/board-geometry.json');layout=read(R/'layout.json')
parts={p['ref']:p for p in spec['parts']};fps={p['ref']:p for p in geo['footprints']}
expected={('J31','3'):'DF_BUSY_RAW',**{('J33',str(i+4)):f'IR{i}_RAW' for i in range(6)}}
diff=[]
for p in base['parts']:
 for pin,net in p['pins'].items():
  new=parts[p['ref']]['pins'][pin]
  if new!=net:diff.append({'ref':p['ref'],'pin':pin,'before':net,'after':new})
assert {(d['ref'],d['pin']):d['after'] for d in diff}==expected
assert len({p['ref'] for p in spec['parts']})==len(spec['parts'])==len(fps)
fail=[];power=[]
for t in layout['tracks']:
 for a,b in zip(t['points'],t['points'][1:]):
  candidates=[LineString([s['start'],s['end']]).buffer(.005) for s in geo['tracks'] if s['class']=='PCB_TRACK' and s['net']==t['net'] and s['layer']==t.get('layer','F.Cu') and s['width']>=t['width']-.001]
  line=LineString([a,b]);missing=line.difference(unary_union(candidates)).length
  power.append({'net':t['net'],'width_mm':t['width'],'start':a,'end':b,'missing_mm':missing})
  if missing>.02:fail.append(power[-1])
assert not fail,fail
holes={h:fps[h]['position'] for h in ['H1','H2','H3','H4']}
assert holes=={'H1':[5,5],'H2':[95,5],'H3':[5,95],'H4':[95,95]}
for i in range(7):
 u=parts[f'U{i+2}'];out=u['pins']['4'];rail='3V3_CORE' if out in ['PB8','PA12'] else '3V3_EXT'
 assert u['pins']=={'1':None,'2':f'BUF_IN_{i}','3':'GND','4':out,'5':rail}
 assert parts[f'C{i+9}']['pins']=={'1':rail,'2':'GND'}
 # Check footprint pad map independently of the schematic writer.
 assert {p['number']:p['net'] for p in fps[f'U{i+2}']['pads'] if p['number']!='1'}=={k:v for k,v in u['pins'].items() if k!='1'}
assert parts['J34']['pins']=={'1':'GND','2':'GND','3':'GND'}
assert parts['J6']['pins']=={'1':'5V_BUS','2':'GND'}
assert len(parts['J8']['pins'])==17 and len(parts['J9']['pins'])==16
assert parts['U1']['pins']==next(p for p in base['parts'] if p['ref']=='U1')['pins']

# Track-graph distances to local bypass capacitors. Include pad contact radius,
# and connect same-net track endpoints when they meet on a copper pad.
distances=[]
for i in range(7):
 u=fps[f'U{i+2}'];c=fps[f'C{i+9}'];up=next(x for x in u['pads'] if x['number']=='5');cp=next(x for x in c['pads'] if x['number']=='1')
 net=up['net'];edges={}
 def key(pos,layer):return (round(pos[0],4),round(pos[1],4),layer)
 def edge(a,b,w):edges.setdefault(a,[]).append((b,w));edges.setdefault(b,[]).append((a,w))
 for t in geo['tracks']:
  if t['net']!=net:continue
  if t['class']=='PCB_VIA':edge(key(t['start'],'F.Cu'),key(t['start'],'B.Cu'),1.6)
  else:edge(key(t['start'],t['layer']),key(t['end'],t['layer']),math.dist(t['start'],t['end']))
 for label,pad in [('source',up),('target',cp)]:
  pkey=(label,);edges[pkey]=[]
  for n in list(edges):
   if len(n)==3 and n[2]=='F.Cu' and math.dist(n[:2],pad['position'])<max(pad['size'])/2+.05:edge(pkey,n,math.dist(n[:2],pad['position']))
 heap=[(0,0,('source',))];ds={('source',):0};seq=0
 while heap:
  d,_,n=heapq.heappop(heap)
  if d>ds[n]:continue
  for nn,w in edges[n]:
   nd=d+w
   if nd<ds.get(nn,1e9):ds[nn]=nd;seq+=1;heapq.heappush(heap,(nd,seq,nn))
 distances.append({'buffer':u['ref'],'cap':c['ref'],'pad_distance_mm':math.dist(up['position'],cp['position']),'track_graph_length_mm':ds.get(('target',))})
assert all(x['track_graph_length_mm'] is not None and x['track_graph_length_mm']<3 for x in distances),distances

report={'pass':True,'parts':len(parts),'connected_pins_expected':sum(v is not None for p in parts.values() for v in p['pins'].values()),'changed_existing_pins':diff,'preserved_power_segments':power,'holes_from_top_left_mm':holes,'input_buffer_channels':7,'buffer_pinout_source':'TI SCES351Y page 3 DBV; 1 NC,2 A,3 GND,4 Y,5 VCC','bypass_geometry':distances,'pcb_drc':read(R/'checks/pcb-drc.json'),'limitations':['No physical assembly, load, thermal or EMC validation.','Original A1 two-layer return-path limitations retained.','125x100 outline requires mechanical clearance review; 90x90 mounting pitch retained.']}
(R/'review/design-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
oldbom={}
with (R.with_name('pcb-a')/'manufacturing/BOM.csv').open(encoding='utf-8-sig') as f:
 for row in csv.DictReader(f):oldbom[row['Designator']]=row
fields=['Designator','Quantity','Value','DNP','Footprint','MPN','Manufacturer','Notes']
with (R/'manufacturing/BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for p in parts.values():
  note=oldbom.get(p['ref'],{}).get('Notes',p.get('notes',''))
  if p['ref'] in ['J6','J31','J33'] or p['ref'] not in oldbom:note=p.get('notes','')
  w.writerow({'Designator':p['ref'],'Quantity':1,'Value':p['value'],'DNP':'YES' if p.get('dnp') else 'NO','Footprint':p['footprint'],'MPN':p.get('MPN',''),'Manufacturer':p.get('Manufacturer',''),'Notes':note})
print(json.dumps({k:report[k] for k in ['parts','connected_pins_expected','bypass_geometry']},ensure_ascii=False,indent=2))
