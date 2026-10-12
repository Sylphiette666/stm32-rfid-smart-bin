"""Read-only release evidence reconciliation. No KiCad mutation or auto-approval.
Run after final exports; explicit paths may override the expected file names.
Python standard library only. Exit 0 digital/manual release checks pass,
1 a check failed, 2 evidence remains pending. Hardware tests are never implied.
"""
import argparse, csv, hashlib, json, math, re, zipfile
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
ap=argparse.ArgumentParser()
ap.add_argument('--geometry', type=Path, default=ROOT/'checks/board-geometry.json')
ap.add_argument('--drc', type=Path, default=ROOT/'checks/pcb-drc.json')
ap.add_argument('--gerber', type=Path, default=ROOT/'manufacturing/Gerber_RS274X.zip')
ap.add_argument('--manual', type=Path, default=HERE/'release-manual.json')
ap.add_argument('--out', type=Path, default=HERE/'release-evidence.json')
args=ap.parse_args()
checks=[]
def add(name,status,detail=''):
    checks.append({'name':name,'status':status,'detail':detail})
def test(name,condition,detail=''):
    add(name,'PASS' if condition else 'FAIL',detail)
def readjson(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

d=readjson(ROOT/'circuit.json')
parts={p['ref']:p for p in d['parts']}
native_path=HERE/'04-native-final-audit.json'
drill_path=HERE/'05-drill-alignment.json'
if native_path.exists():
    native=readjson(native_path)
    test('Native audit matches current PCB',native.get('board_sha256')==sha(ROOT/'kicad/SmartBin_A.kicad_pcb'))
    test('Native 94 references / exact electrical definition',native.get('native_definition_match',{}).get('pass') is True,native.get('native_definition_match',{}))
    test('All 33 planned copper segments preserved',native.get('power_segments_pass')==native.get('power_segments_expected')==33)
    test('Copper to routed board edge >=0.50mm',native.get('conservative_copper_edge_clearance_mm',[0])[0]>=.5,native.get('conservative_copper_edge_clearance_mm'))
else:add('Native final PCB audit','PENDING',str(native_path))
if drill_path.exists():
    drill_audit=readjson(drill_path)
    test('Excellon holes match PCB positions / diameter / plating',drill_audit.get('status')=='PASS' and drill_audit.get('board_sha256')==sha(ROOT/'kicad/SmartBin_A.kicad_pcb'),drill_audit.get('drill_matches'))
else:add('Drill coordinate audit','PENDING',str(drill_path))
with (ROOT/'manufacturing/bom.csv').open(encoding='utf-8-sig',newline='') as f:
    bom=list(csv.DictReader(f))
br={r['Designator']:r for r in bom if r['ItemType']!='accessory'}
access=[r for r in bom if r['ItemType']=='accessory']
test('BOM unique rows',len(bom)==len({r['Designator'] for r in bom}))
test('BOM PCB reference set',set(br)==set(parts),{'board':len(parts),'bom_board':len(br)})
test('BOM values and footprints',all(br[r]['Value']==p['value'] and br[r]['Footprint']==p['footprint'] for r,p in parts.items()))
test('BOM defaults',all((br[r]['DNP']=='YES')==(p['dnp'] or p['kind']=='mounting_hole') for r,p in parts.items()))
test('U1 socket separate accessory only',len(access)==1 and access[0]['Designator']=='U1_SOCKET' and access[0]['Quantity']=='1' and br['U1']['Quantity']=='1')
test('AHCT third input biased',not parts['R36']['dnp'] and parts['R37']['dnp'])
test('two 3V3 rails distinct',not any(set(p['pins'].values())=={'3V3_EXT','3V3_CORE'} for p in parts.values()))
if args.geometry.exists():
    geo=readjson(args.geometry)
    fps={f['ref']:f for f in geo['footprints']}
    test('Geometry footprint reference set',set(fps)==set(parts),{'geometry':len(fps),'definition':len(parts)})
    test('Geometry library footprint names',all(fps[r]['footprint']==p['footprint'].split(':',1)[-1] for r,p in parts.items()))
    pin_mismatch=[]
    for ref,p in parts.items():
        if p['kind']=='mounting_hole':continue
        actual={str(x['number']):x.get('net','') for x in fps[ref]['pads']}
        if set(actual)!=set(p['pins']):pin_mismatch.append([ref,'pin set'])
        for pin,net in p['pins'].items():
            v=actual.get(pin)
            okay=v==net if net else v in ('',None) or str(v).startswith('unconnected-')
            if not okay:pin_mismatch.append([ref,pin,net,v])
    test('Geometry pad-to-net exact match',not pin_mismatch,pin_mismatch)
    bounds=geo['outline_bbox']
    wh=[bounds[2]-bounds[0],bounds[3]-bounds[1]]
    test('Outline approximately 100mm including stroke',all(abs(v-100)<=.2 for v in wh),{'bbox_mm':wh,'note':'Final centerline outline must also be visually verified.'})
    holes=[fps[f'H{i}']['pads'][0] for i in range(1,5)]
    test('Four 3.2mm mounting holes',all(abs(x['drill'][0]-3.2)<1e-6 for x in holes))
    pos={tuple(round(v,3) for v in x['position']) for x in holes}
    test('Mounting centers at 5/95mm relative board',pos=={(5.,5.),(95.,5.),(5.,95.),(95.,95.)},sorted(pos))
    terminals=[]
    for i in range(1,7):
        pads=sorted(fps[f'J{i}']['pads'],key=lambda x:x['number'])
        pitch=math.dist(pads[0]['position'],pads[1]['position'])
        terminals.append({'ref':f'J{i}','pitch':pitch,'drills':[p['drill'][0] for p in pads]})
    test('Power connector 5.08 pitch / 1.3 drill',all(abs(x['pitch']-5.08)<.001 and all(abs(v-1.3)<.001 for v in x['drills']) for x in terminals),terminals)
    rings=[]
    for ref,f in fps.items():
        if ref.startswith('H'):continue
        for pad in f['pads']:
            rings.append((min(pad['size'])-max(pad['drill']))/2)
    test('THT pad annular rings >=0.15mm',min(rings)>=.149,{'minimum_ring_mm':min(rings)})
    add('Power widths informational','INFO',{'widths_mm':sorted({t['width'] for t in geo.get('tracks',[]) if t['net'] in ('VBAT_SW','5V_BUS','GND')}),'note':'Full net minimum is not a power-path rating. Verify J3 trunk/branches and return paths manually.'})
else:add('Final geometry','PENDING',str(args.geometry))

manual=readjson(args.manual) if args.manual.exists() else {}
allowed=set(manual.get('accepted_warning_types',[]))
if args.drc.exists():
    drc=readjson(args.drc)
    test('DRC unconnected items zero',len(drc.get('unconnected_items',[]))==0,{'count':len(drc.get('unconnected_items',[]))})
    for key in ('violations','schematic_parity'):
        entries=drc.get(key,[])
        failed=[x for x in entries if x.get('severity')=='error' or x.get('type') not in allowed]
        test('DRC '+key+' zero or explicitly classified',not failed,{'count':len(entries),'unaccepted':len(failed),'types':dict(Counter(x.get('type','unknown') for x in entries))})
    add('DRC source','INFO',{'path':str(args.drc),'sha256':sha(args.drc),'date':drc.get('date'),'version':drc.get('kicad_version'),'ignored_checks':drc.get('ignored_checks',[])})
else:add('Final DRC report','PENDING',str(args.drc))

if args.gerber.exists():
    with zipfile.ZipFile(args.gerber) as z:
        files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    names=list(files)
    patterns={'F.Cu':r'F[_\.]Cu.*\.gbr$|\.gtl$','B.Cu':r'B[_\.]Cu.*\.gbr$|\.gbl$','F.Mask':r'F[_\.]Mask.*\.gbr$|\.gts$','B.Mask':r'B[_\.]Mask.*\.gbr$|\.gbs$','F.Silkscreen':r'F[_\.](?:Silkscreen|SilkS).*\.gbr$|\.gto$','Edge.Cuts':r'Edge[_\.]Cuts.*\.gbr$|\.gko$|\.gm1$'}
    matches={k:[n for n in names if re.search(v,n,re.I)] for k,v in patterns.items()}
    test('Gerber required layer set',all(len(v)==1 for v in matches.values()),matches)
    gerber_names=[n for n in names if n.lower().endswith(('.gbr','.gtl','.gbl','.gts','.gbs','.gto','.gbo','.gko','.gm1'))]
    format_errors=[]
    for n in gerber_names:
        txt=files[n].decode('ascii',errors='replace')
        if '%FS' not in txt or '%MO' not in txt or '%ADD' not in txt:format_errors.append([n,'missing RS274X declarations'])
        if re.search(r'%T[FADO]',txt):format_errors.append([n,'X2 attribute present'])
    test('RS274X declarations and no X2 attributes',not format_errors,format_errors)
    drills=[n for n in names if n.lower().endswith(('.drl','.xln'))]
    drill_ok=bool(drills) and all(b'M48' in files[n] and (b'METRIC' in files[n] or b'INCH' in files[n]) for n in drills)
    test('Excellon drill headers and units',drill_ok,drills)
    test('Bare-board archive has no project or credentials',not any(n.lower().endswith(('.kicad_pcb','.kicad_sch','.prl','.toml','.pem','.key')) for n in names))
    add('Gerber archive','INFO',{'path':str(args.gerber),'sha256':sha(args.gerber),'files':names})
else:add('Final Gerber archive','PENDING',str(args.gerber))

for key in ('placement_and_hand_solder_access','power_trunks_and_returns','decoupling_and_analog_separation','silkscreen_and_pin1','gerber_visual_and_drill_alignment'):
    item=manual.get('reviews',{}).get(key,{})
    state=item.get('status','PENDING')
    add('Manual review: '+key,state if state in ('PASS','FAIL') else 'PENDING',item.get('evidence','Not yet reviewed'))
hasfail=any(x['status']=='FAIL' for x in checks)
pending=any(x['status']=='PENDING' for x in checks)
status='NOT_RELEASED' if hasfail or pending else 'DIGITAL_FAB_CHECKS_PASSED'
report={'status':status,'circuit_sha256':sha(ROOT/'circuit.json'),'bom_sha256':sha(ROOT/'manufacturing/bom.csv'),'checks':checks,'scope':'Manufacturing/digital review only; no physical fit, actual welding, powered function, load/temperature or firmware completion implied.'}
args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':status,'pass':sum(x['status']=='PASS' for x in checks),'fail':[x['name'] for x in checks if x['status']=='FAIL'],'pending':[x['name'] for x in checks if x['status']=='PENDING'],'report':str(args.out)},ensure_ascii=False,indent=2))
raise SystemExit(1 if hasfail else 2 if pending else 0)
