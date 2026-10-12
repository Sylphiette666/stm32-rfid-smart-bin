"""Native KiCad object-model backend; invoked by pcb_cli.py only."""
from pathlib import Path
import argparse, json, uuid, subprocess, math, shutil, xml.etree.ElementTree as ET
import pcbnew as p

CLI=Path(r'D:\KiCad\bin\kicad-cli.exe')
LIB=Path(r'D:\KiCad\share\kicad\footprints')
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'smartbin-a-20261012/'+s))
def readj(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def outj(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def box(item):
    b=item.GetBoundingBox()
    return [p.ToMM(b.GetX()),p.ToMM(b.GetY()),p.ToMM(b.GetRight()),p.ToMM(b.GetBottom())]
def line(b,a,c,layer=p.Edge_Cuts,width=.1):
    s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(vec(*a));s.SetEnd(vec(*c));s.SetWidth(p.FromMM(width));s.SetLayer(layer);b.Add(s)
def text(b,txt,x,y,size=1,layer=p.F_SilkS,angle=0):
    t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(vec(x,y));t.SetTextSize(vec(size,size));t.SetTextThickness(p.FromMM(.15));t.SetLayer(layer);t.SetMirrored(layer==p.B_SilkS);t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));b.Add(t);return t
def track(b,net,points,width,layer='F.Cu',locked=True):
    for a,c in zip(points,points[1:]):
        if a==c:continue
        t=p.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*c));t.SetWidth(p.FromMM(width));t.SetLayer(b.GetLayerID(layer));t.SetNet(b.FindNet(net));t.SetLocked(locked);b.Add(t)
def zone(b,net,layer,points,priority=0,spoke=.5):
    z=p.ZONE(b);z.SetLayer(b.GetLayerID(layer));z.SetNet(b.FindNet(net));z.SetLocalClearance(p.FromMM(.3));z.SetMinThickness(p.FromMM(.25));z.SetThermalReliefGap(p.FromMM(.3));z.SetThermalReliefSpokeWidth(p.FromMM(spoke));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetAssignedPriority(priority)
    o=z.Outline();o.NewOutline()
    for x,y in points:o.Append(p.FromMM(x),p.FromMM(y))
    b.Add(z)
def setup(b):
    b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
    ns=b.GetDesignSettings().m_NetSettings
    d=ns.GetDefaultNetclass();d.SetClearance(p.FromMM(.20));d.SetTrackWidth(p.FromMM(.3));d.SetViaDiameter(p.FromMM(.8));d.SetViaDrill(p.FromMM(.4))
    for name,width,pats in [('LogicPower',.8,['5V_LOGIC','3V3_*','5V_BUS','VBAT_SW']),('Ground',.5,['GND'])]:
        n=p.NETCLASS(name);n.SetClearance(p.FromMM(.20));n.SetTrackWidth(p.FromMM(width));n.SetViaDiameter(p.FromMM(.8));n.SetViaDrill(p.FromMM(.4));ns.SetNetclass(name,n)
        for pat in pats:ns.SetNetclassPatternAssignment(pat,name)
def project(root):
    (root/'kicad').mkdir(parents=True,exist_ok=True)
    classes=[{'name':'Default','clearance':.20,'track_width':.3,'via_diameter':.8,'via_drill':.4},{'name':'LogicPower','clearance':.20,'track_width':.8,'via_diameter':.8,'via_drill':.4},{'name':'Supply','clearance':.20,'track_width':3,'via_diameter':1,'via_drill':.5},{'name':'Ground','clearance':.20,'track_width':.5,'via_diameter':.8,'via_drill':.4}]
    rules={'min_clearance':.20,'min_track_width':.25,'min_via_diameter':.8,'min_through_hole_diameter':.4,'min_hole_clearance':.25,'min_copper_edge_clearance':.5,'min_silk_clearance':.15,'min_text_height':1,'min_text_thickness':.15}
    data={'meta':{'filename':'SmartBin_A.kicad_pro','version':1},'board':{'design_settings':{'rules':rules,'rule_severities':{}}},'net_settings':{'classes':classes,'netclass_patterns':[{'netclass':'LogicPower','pattern':'3V3_*'},{'netclass':'LogicPower','pattern':'5V_LOGIC'},{'netclass':'LogicPower','pattern':'VBAT_SW'},{'netclass':'LogicPower','pattern':'5V_BUS'},{'netclass':'Ground','pattern':'GND'}]}}
    outj(root/'kicad'/'SmartBin_A.kicad_pro',data)
def schematic_sync(b,root):
    f=root/'kicad'/'schematic_paths.json'
    if f.exists():
        paths=readj(f);paths=paths.get('components',paths)
        for fp in b.GetFootprints():
            r=fp.GetReference()
            if r in paths:
                d=paths[r];fp.SetPath(p.KIID_PATH(d['path'] if isinstance(d,dict) else d))
    for netf in [root/'kicad'/'SmartBin_A.net.xml',root/'checks'/'SmartBin_A.net.xml',root/'kicad'/'SmartBin_A.xml']:
        if netf.exists():
            fps={f.GetReference():f for f in b.GetFootprints()}
            xml=ET.parse(netf).getroot()
            for comp in xml.findall('./components/comp'):
                fp=fps.get(comp.attrib['ref'])
                if not fp:continue
                for field in comp.findall('./fields/field'):
                    name=field.attrib['name']
                    if name not in ('Footprint',):
                        fp.SetField(name,field.text or '');fp.GetField(name).SetVisible(False)
            for n in xml.findall('./nets/net'):
                name=n.attrib['name'];ni=b.FindNet(name)
                if not ni or ni.GetNetCode()<0:ni=p.NETINFO_ITEM(b,name);b.Add(ni)
                for nd in n.findall('node'):
                    if nd.attrib['ref'] in fps:
                        for pad in fps[nd.attrib['ref']].Pads():
                            if pad.GetNumber()==nd.attrib['pin']:pad.SetNet(ni)
            break
def build(root):
    cfg=readj(root/'circuit.json');layout=readj(root/'layout.json');kdir=root/'kicad';kdir.mkdir(exist_ok=True)
    b=p.BOARD();setup(b)
    tb=p.TITLE_BLOCK();tb.SetTitle('SmartBin A - THT cable interface and power distribution');tb.SetRevision('A1');tb.SetDate('2026-10-12');tb.SetComment(0,'External modules; hand assembly; no core sockets');b.SetTitleBlock(tb)
    names=sorted({n for c in cfg['parts'] for n in c['pins'].values() if n})
    nets={}
    for n in names:ni=p.NETINFO_ITEM(b,n);b.Add(ni);nets[n]=ni
    usedlibs=set()
    for c in cfg['parts']:
        if not c.get('footprint') or c.get('on_board') is False:continue
        lib,name=c['footprint'].split(':',1);libdir=LIB/(lib+'.pretty')
        if not libdir.exists():libdir=kdir/(lib+'.pretty')
        fp=p.FootprintLoad(str(libdir),name)
        if not fp:raise ValueError('Missing footprint '+c['footprint'])
        local=kdir/'footprints'/(lib+'.pretty');local.mkdir(parents=True,exist_ok=True)
        shutil.copy2(libdir/(name+'.kicad_mod'),local/(name+'.kicad_mod'));usedlibs.add(lib)
        r=c['ref'];fp.SetReference(r);fp.SetValue(c['value']);fp.SetFPIDAsString(c['footprint'])
        fp.SetDNP(bool(c.get('dnp',False)))
        x,y,a=layout['placements'][r];fp.SetPosition(vec(x+50,y+50));fp.SetOrientationDegrees(a)
        fp.SetPath(p.KIID_PATH('/'+uid('root')+'/'+uid(r)));fp.SetExcludedFromBOM(False)
        fp.Value().SetVisible(False);fp.Reference().SetTextSize(vec(1,1));fp.Reference().SetTextThickness(p.FromMM(.15));fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));fp.Reference().SetPosition(vec(x+50,y+47))
        for pad in fp.Pads():
            n=c['pins'].get(pad.GetNumber())
            if n:pad.SetNet(nets[n])
        b.Add(fp)
    (kdir/'fp-lib-table').write_text('(fp_lib_table\n'+''.join('  (lib (name "'+s+'") (type "KiCad") (uri "${KIPRJMOD}/footprints/'+s+'.pretty") (options "") (descr "Vendored KiCad 10 footprint"))\n' for s in sorted(usedlibs))+')\n',encoding='utf-8')
    for a,c in [((50,50),(150,50)),((150,50),(150,150)),((150,150),(50,150)),((50,150),(50,50))]:line(b,a,c)
    for t in layout.get('tracks',[]):track(b,t['net'],[(x+50,y+50) for x,y in t['points']],t['width'],t.get('layer','F.Cu'))
    schematic_sync(b,root);b.BuildConnectivity();p.SaveBoard(str(kdir/'SmartBin_A.kicad_pcb'),b);project(root)
    assert p.ExportSpecctraDSN(b,str(kdir/'SmartBin_A.dsn'))
    inspect(root,b)
def inspect(root,b=None):
    if b is None:b=p.LoadBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'))
    d={'outline_bbox':box(b),'footprints':[],'tracks':[],'zones':len(b.Zones())}
    for f in b.GetFootprints():
        rect=f.GetBoundingBox(False,False)
        d['footprints'].append({'ref':f.GetReference(),'value':f.GetValue(),'footprint':f.GetFPID().GetLibItemName(),'position':[p.ToMM(f.GetPosition().x)-50,p.ToMM(f.GetPosition().y)-50],'angle':f.GetOrientationDegrees(),'bbox':[p.ToMM(rect.GetX())-50,p.ToMM(rect.GetY())-50,p.ToMM(rect.GetRight())-50,p.ToMM(rect.GetBottom())-50],'pads':[{'number':a.GetNumber(),'net':a.GetNetname(),'position':[p.ToMM(a.GetPosition().x)-50,p.ToMM(a.GetPosition().y)-50],'size':[p.ToMM(a.GetSize().x),p.ToMM(a.GetSize().y)],'drill':[p.ToMM(a.GetDrillSize().x),p.ToMM(a.GetDrillSize().y)]} for a in f.Pads()]})
    for t in b.GetTracks():d['tracks'].append({'class':t.GetClass(),'net':t.GetNetname(),'width':p.ToMM(t.GetWidth(p.F_Cu) if t.GetClass()=='PCB_VIA' else t.GetWidth()),'layer':b.GetLayerName(t.GetLayer()),'start':[p.ToMM(t.GetStart().x)-50,p.ToMM(t.GetStart().y)-50],'end':[p.ToMM(t.GetEnd().x)-50,p.ToMM(t.GetEnd().y)-50]})
    (root/'checks').mkdir(exist_ok=True);outj(root/'checks'/'board-geometry.json',d)
    print(json.dumps({'footprints':len(d['footprints']),'tracks':len(d['tracks']),'zones':d['zones']}))
def import_route(root,ses):
    b=p.LoadBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'));assert p.ImportSpecctraSES(b,str(ses));schematic_sync(b,root);b.BuildConnectivity();p.SaveBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'),b);inspect(root,b)
def finish(root):
    b=p.LoadBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'));layout=readj(root/'layout.json');schematic_sync(b,root)
    for z in list(b.Zones()):b.Remove(z)
    for layer in ['F.Cu','B.Cu']:zone(b,'GND',layer,[(50.7,50.7),(149.3,50.7),(149.3,149.3),(50.7,149.3)])
    for t in layout.get('silk',[]):text(b,t['text'],50+t['x'],50+t['y'],t.get('size',1),p.B_SilkS if t.get('back') else p.F_SilkS,t.get('angle',0))
    p.SaveBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'),b);inspect(root,b)

def repair(root):
    b=p.LoadBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'));schematic_sync(b,root)
    specs=readj(root/'checks'/'repair-routes.json') if (root/'checks'/'repair-routes.json').exists() else []
    for spec in specs:
        for seg in spec['segments']:track(b,spec['net'],seg['points'],spec.get('width',.3),seg['layer'])
        for x,y in spec['vias']:
            v=p.PCB_VIA(b);v.SetPosition(vec(x,y));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetWidth(p.FromMM(.8));v.SetDrill(p.FromMM(.4));v.SetNet(b.FindNet(spec['net']));b.Add(v)
    issues=readj(root/'checks'/'pcb-drc.json')
    thermal_ids={v['items'][1]['uuid'] for v in issues['violations'] if v['type']=='starved_thermal'}
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if str(pad.m_Uuid.AsString()) in thermal_ids:pad.SetLocalZoneConnection(p.ZONE_CONNECTION_NONE)
    p.SaveBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'),b);inspect(root,b)

def obstacles(root):
    b=p.LoadBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'));d={'pads':[],'tracks':[]}
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            d['pads'].append({'ref':fp.GetReference(),'pin':pad.GetNumber(),'net':pad.GetNetname(),'shape':int(pad.GetShape()),'angle':pad.GetOrientationDegrees(),'pos':[p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)],'size':[p.ToMM(pad.GetSize().x),p.ToMM(pad.GetSize().y)],'drill':[p.ToMM(pad.GetDrillSize().x),p.ToMM(pad.GetDrillSize().y)]})
    for t in b.GetTracks():
        via=t.GetClass()=='PCB_VIA'
        d['tracks'].append({'net':t.GetNetname(),'via':via,'width':p.ToMM(t.GetWidth(p.F_Cu) if via else t.GetWidth()),'layer':b.GetLayerName(t.GetLayer()),'start':[p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)],'end':[p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y)]})
    outj(root/'checks'/'routing-obstacles.json',d)

def rip(root):
    b=p.LoadBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'))
    nets=readj(root/'checks'/'rip-nets.json')
    for t in list(b.GetTracks()):
        if t.GetNetname() in nets:b.Remove(t)
    p.SaveBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'),b)

def silk(root):
    from pcb_silk import finalize
    b=p.LoadBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'));schematic_sync(b,root);finalize(b,root)
    p.SaveBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'),b)

def thermals(root):
    b=p.LoadBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'))
    d=readj(root/'checks'/'pcb-drc.json');ids={v['items'][1]['uuid'] for v in d['violations'] if v['type']=='starved_thermal'}
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if str(pad.m_Uuid.AsString()) in ids:pad.SetLocalZoneConnection(p.ZONE_CONNECTION_NONE)
    p.SaveBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'),b)

def assemblyplot(root):
    b=p.LoadBoard(str(root/'kicad'/'SmartBin_A.kicad_pcb'))
    for fp in b.GetFootprints():
        for g in fp.GraphicalItems():
            if g.GetClass()=='PCB_TEXT' and g.GetLayer()==p.F_Fab:g.SetText('')
    temp=root/'renders'/'assembly-plot.kicad_pcb';p.SaveBoard(str(temp),b)
    subprocess.run([str(CLI),'pcb','export','svg','--output',str(root/'renders'/'board-assembly-top.svg'),'--mode-single','--exclude-drawing-sheet','--layers','F.Fab,F.SilkS,Edge.Cuts','--sketch-pads-on-fab-layers','--crossout-DNP-footprints-on-fab-layers','--page-size-mode','2',str(temp)],check=True)
def preview(root):
    rend=root/'renders';rend.mkdir(exist_ok=True);board=root/'kicad'/'SmartBin_A.kicad_pcb'
    commands=[['pcb','export','svg','--output',str(rend/'board-front.svg'),'--mode-single','--exclude-drawing-sheet','--layers','F.Cu,F.SilkS,F.Fab,Edge.Cuts','--page-size-mode','2',str(board)],['pcb','render','--output',str(rend/'board-3d.png'),'--width','1800','--height','1800','--side','top','--quality','basic','--background','opaque',str(board)]]
    for cmd in commands:
        r=subprocess.run([str(CLI),*cmd],capture_output=True,text=True,encoding='utf-8',errors='replace');print(r.stdout,r.stderr)
        if r.returncode:raise RuntimeError(str(cmd))
def export(root):
    bpath=root/'kicad'/'SmartBin_A.kicad_pcb';fab=root/'manufacturing';fab.mkdir(exist_ok=True);checks=root/'checks';checks.mkdir(exist_ok=True)
    commands=[['pcb','drc','--format','json','--schematic-parity','--refill-zones','--save-board','--output',str(checks/'pcb-drc.json'),str(bpath)],['pcb','export','gerbers','--no-x2','--no-netlist','--output',str(fab)+'\\','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts',str(bpath)],['pcb','export','drill','--output',str(fab)+'\\','--format','excellon','--excellon-units','mm','--excellon-separate-th','--generate-map','--generate-report','--report-path',str(fab/'drill-report.txt'),str(bpath)],['pcb','export','svg','--output',str(root/'renders'/'board-top-copper.svg'),'--mode-single','--exclude-drawing-sheet','--layers','F.Cu,F.SilkS,Edge.Cuts','--page-size-mode','2',str(bpath)],['pcb','export','svg','--output',str(root/'renders'/'board-bottom-solder.svg'),'--mode-single','--exclude-drawing-sheet','--layers','B.Cu,B.SilkS,Edge.Cuts','--mirror','--page-size-mode','2',str(bpath)]]
    (root/'renders').mkdir(exist_ok=True)
    for cmd in commands:
        r=subprocess.run([str(CLI),*cmd],capture_output=True,text=True,encoding='utf-8',errors='replace');print(r.stdout,r.stderr)
        if r.returncode:raise RuntimeError('KiCad failed '+str(cmd))
def drc(root):
    f=root/'checks'/'pcb-drc.json'
    r=subprocess.run([str(CLI),'pcb','drc','--format','json','--schematic-parity','--refill-zones','--save-board','--output',str(f),str(root/'kicad'/'SmartBin_A.kicad_pcb')],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if not f.exists():raise RuntimeError(r.stderr+r.stdout)
    data=readj(f)
    from collections import Counter
    print(json.dumps({'exit':r.returncode,'violations':dict(Counter(v['type'] for v in data.get('violations',[]))),'unconnected':len(data.get('unconnected_items',[])),'parity':dict(Counter(v['type'] for v in data.get('schematic_parity',[])))}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action');a.add_argument('root',type=Path);a.add_argument('--ses',type=Path);v=a.parse_args()
    if v.action=='import':import_route(v.root,v.ses)
    else:globals()[v.action](v.root)
