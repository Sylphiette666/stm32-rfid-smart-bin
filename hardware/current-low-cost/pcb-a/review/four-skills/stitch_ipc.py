"""Hubert kicad-pcb workflow: verify document, one undo transaction, save."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tooling/kipy'))
from kipy import KiCad
from kipy.board_types import Via
from kipy.geometry import Vector2
from kipy.util.units import from_mm
from kipy.proto.common.types import DocumentType
k=KiCad();k.ping();b=k.get_board()
docs=k.get_open_documents(DocumentType.DOCTYPE_PCB)
assert 'working' in str(docs),str(docs)
plan=json.loads((R/'analysis/stitch-plan.json').read_text())
net=next(n for n in b.get_nets() if n.name=='GND')
assert not any(v.net.name=='GND' for v in b.get_vias()),'Stitches already present; refusing duplicate application'
commit=b.begin_commit()
try:
 items=[]
 for x,y in plan['points']:
  v=Via();v.position=Vector2.from_xy(from_mm(x),from_mm(y));v.diameter=from_mm(.8);v.drill_diameter=from_mm(.4);v.net=net;items.append(v)
 created=b.create_items(items);assert len(created)==len(items)
 b.push_commit(commit,'A1 review: GND stitching, no pinout or BOM change')
except Exception:
 b.drop_commit(commit);raise
b.refill_zones();b.save()
out={'version':str(k.get_version()),'board':b.name,'added_gnd_vias':len(created),'saved':True,'created_ids':[str(v.id) for v in created]}
(R/'analysis/hubert-ipc-edit.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
