from pathlib import Path
from collections import Counter
import json,hashlib
R=Path(__file__).resolve().parent;W=R/'working';O=W/'review/four-skills'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
a=load(R/'baseline/checks/board-geometry.json');b=load(W/'checks/board-geometry.json')
canon=lambda items:Counter(json.dumps(i,sort_keys=True) for i in items)
oldtracks=canon(t for t in a['tracks'] if t['class']=='PCB_TRACK');newtracks=canon(t for t in b['tracks'] if t['class']=='PCB_TRACK')
oldvias=canon(t for t in a['tracks'] if t['class']=='PCB_VIA');newvias=canon(t for t in b['tracks'] if t['class']=='PCB_VIA')
delta=list((newvias-oldvias).elements())
assert oldtracks==newtracks and sum(newtracks.values())==1117
assert not (oldvias-newvias) and len(delta)==55 and all(json.loads(t)['net']=='GND' for t in delta)
assert canon(a['footprints'])==canon(b['footprints'])
same={p.name:p.read_bytes()==(W/'kicad'/p.name).read_bytes() for p in (R/'baseline/kicad').glob('*.kicad_sch')}
for n in ['circuit.json','connector-map.csv','manufacturing/bom.csv']:same[n]=(R/'baseline'/n).read_bytes()==(W/n).read_bytes()
assert all(same.values())
out={'all_original_track_geometries_identical':True,'original_tracks':1117,'all_original_vias_retained':True,'added_ground_vias':55,'all_footprints_pads_and_positions_identical':True,'unchanged_sources':same,'board_sha256':hashlib.sha256((W/'kicad/SmartBin_A.kicad_pcb').read_bytes()).hexdigest()}
(O/'design-delta.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
