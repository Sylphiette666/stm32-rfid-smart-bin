"""Read-only KiCad native inspection; LoadBoard once, never save/refill."""
import hashlib,json,math
from collections import Counter
from pathlib import Path
import pcbnew as p
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PATH=ROOT/'kicad/SmartBin_A.kicad_pcb'
before=hashlib.sha256(PATH.read_bytes()).hexdigest()
b=p.LoadBoard(str(PATH))
def xy(v):return [p.ToMM(v.x)-50,p.ToMM(v.y)-50]
def box(v):return [p.ToMM(v.GetX())-50,p.ToMM(v.GetY())-50,p.ToMM(v.GetRight())-50,p.ToMM(v.GetBottom())-50]
tracks=[];vias=[];padrows=[];zones=[];edge=[];native_parts={}
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        vias.append({'net':t.GetNetname(),'position':xy(t.GetPosition()),'diameter':p.ToMM(t.GetWidth(p.F_Cu)),'drill':p.ToMM(t.GetDrill())})
    else:
        tracks.append({'net':t.GetNetname(),'start':xy(t.GetStart()),'end':xy(t.GetEnd()),'width':p.ToMM(t.GetWidth()),'layer':b.GetLayerName(t.GetLayer())})
for fp in b.GetFootprints():
    native_parts[fp.GetReference()]={'value':fp.GetValue(),'footprint':str(fp.GetFPID().GetLibItemName()),'pins':{pad.GetNumber():pad.GetNetname() for pad in fp.Pads()}}
    for pad in fp.Pads():
        padrows.append({'ref':fp.GetReference(),'pin':pad.GetNumber(),'net':pad.GetNetname(),'position':xy(pad.GetPosition()),'bbox':box(pad.GetBoundingBox()),'zone_connection':int(pad.GetLocalZoneConnection()),'drill':[p.ToMM(pad.GetDrillSize().x),p.ToMM(pad.GetDrillSize().y)]})
for z in b.Zones():
    zones.append({'net':z.GetNetname(),'layer':b.GetLayerName(z.GetLayer()),'bbox':box(z.GetBoundingBox()),'clearance':p.ToMM(z.GetLocalClearance()),'thermal_spoke':p.ToMM(z.GetThermalReliefSpokeWidth()),'filled_polygons':z.GetFilledPolysList(z.GetLayer()).OutlineCount()})
for s in b.GetDrawings():
    if s.GetLayer()==p.Edge_Cuts:
        edge.append({'class':s.GetClass(),'start':xy(s.GetStart()),'end':xy(s.GetEnd()),'width':p.ToMM(s.GetWidth())})
layout=json.loads((ROOT/'layout.json').read_text(encoding='utf-8-sig'))
preserved=[]
for plan in layout['tracks']:
    for a,c in zip(plan['points'],plan['points'][1:]):
        if a==c:continue
        dx,dy=c[0]-a[0],c[1]-a[1];ll=dx*dx+dy*dy
        segments=[]
        for t in tracks:
            if t['net']!=plan['net'] or t['layer']!=plan.get('layer','F.Cu') or t['width']+1e-6<plan['width']:continue
            points=t['start'],t['end']
            if any(abs((q[0]-a[0])*dy-(q[1]-a[1])*dx)>.002 for q in points):continue
            ts=sorted(((q[0]-a[0])*dx+(q[1]-a[1])*dy)/ll for q in points)
            lo,hi=max(0,ts[0]),min(1,ts[1])
            if hi>lo:segments.append((lo,hi))
        end=0
        for lo,hi in sorted(segments):
            if lo>end+1e-5:break
            end=max(end,hi)
        preserved.append({'net':plan['net'],'layer':plan.get('layer','F.Cu'),'width':plan['width'],'start':a,'end':c,'covered_fraction':min(end,1),'pass':end>=1-1e-5})
def copper_edge_box(bb):return min(bb[0],bb[1],100-bb[2],100-bb[3])
edge_candidates=[]
for t in tracks:
    r=t['width']/2
    bb=[min(t['start'][0],t['end'][0])-r,min(t['start'][1],t['end'][1])-r,max(t['start'][0],t['end'][0])+r,max(t['start'][1],t['end'][1])+r]
    edge_candidates.append((copper_edge_box(bb),'track '+t['net']))
for v in vias:
    x,y=v['position'];r=v['diameter']/2
    edge_candidates.append((copper_edge_box([x-r,y-r,x+r,y+r]),'via '+v['net']))
for pad in padrows:
    if pad['net']:edge_candidates.append((copper_edge_box(pad['bbox']),pad['ref']+'.'+pad['pin']))
for z in zones:edge_candidates.append((copper_edge_box(z['bbox']),'zone '+z['layer']))
after=hashlib.sha256(PATH.read_bytes()).hexdigest()
report={'board_sha256':after,'board_unchanged_during_read':before==after,'copper_layers':b.GetCopperLayerCount(),'thickness':p.ToMM(b.GetDesignSettings().GetBoardThickness()),'track_count':len(tracks),'via_count':len(vias),'width_counts':dict(Counter(str(t['width']) for t in tracks)),'vias':vias,'pad_count':len(padrows),'pads_no_zone':[x for x in padrows if x['net']=='GND' and x['zone_connection']==int(p.ZONE_CONNECTION_NONE)],'zones':zones,'edge_cuts':edge,'preserved_power_segments':preserved,'power_segments_expected':len(preserved),'power_segments_pass':sum(x['pass'] for x in preserved),'conservative_copper_edge_clearance_mm':min(edge_candidates),'drill_expected':dict(Counter(str(x['drill'][0]) for x in padrows if x['drill'][0]>0)),'terminal_orientation_degrees':{f.GetReference():f.GetOrientationDegrees() for f in b.GetFootprints() if f.GetReference() in {f'J{i}' for i in range(1,7)}}}
report['all_pad_drills']=[{'ref':x['ref'],'pin':x['pin'],'position':x['position'],'drill':x['drill'][0],'plated':not x['ref'].startswith('H')} for x in padrows]
definition=json.loads((ROOT/'circuit.json').read_text(encoding='utf-8-sig'))
expected_parts={x['ref']:x for x in definition['parts']}
part_issues=[]
if set(native_parts)!=set(expected_parts):part_issues.append('reference set differs')
for ref,x in expected_parts.items():
    if ref not in native_parts:continue
    n=native_parts[ref]
    if n['value']!=x['value']:part_issues.append([ref,'value',x['value'],n['value']])
    if n['footprint']!=x['footprint'].split(':',1)[-1]:part_issues.append([ref,'footprint',x['footprint'],n['footprint']])
    if x['kind']=='mounting_hole':continue
    if set(n['pins'])!=set(x['pins']):part_issues.append([ref,'pin set'])
    for pin,net in x['pins'].items():
        actual=n['pins'].get(pin)
        okay=actual==net if net else actual in ('',None) or str(actual).startswith('unconnected-')
        if not okay:part_issues.append([ref,pin,net,actual])
report['native_definition_match']={'pass':not part_issues,'references':len(native_parts),'expected_references':len(expected_parts),'issues':part_issues}
report['copper_geometry_sha256']=hashlib.sha256(json.dumps({'tracks':sorted(tracks,key=lambda x:json.dumps(x,sort_keys=True)),'vias':sorted(vias,key=lambda x:json.dumps(x,sort_keys=True)),'pads':sorted(padrows,key=lambda x:(x['ref'],x['pin'])),'zones':zones,'edges':edge},sort_keys=True).encode()).hexdigest()
(HERE/'04-native-final-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('vias','preserved_power_segments','all_pad_drills')},ensure_ascii=False,indent=2))
