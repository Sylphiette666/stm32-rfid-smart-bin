"""Structured mash kicad-tool extension for native DNP metadata consistency."""
import argparse,json
from pathlib import Path
import kicad_tool
from kiutils.schematic import Schematic

def run(a):
 root=a.root.resolve();parts={p['ref']:p for p in json.loads((root/'circuit.json').read_text(encoding='utf-8'))['parts']};changes=[]
 for path in (root/'kicad').glob('*.kicad_sch'):
  s=Schematic.from_file(str(path));dirty=False
  for sym in s.schematicSymbols:
   props={p.key:p.value for p in sym.properties};ref=props.get('Reference')
   if ref in parts:
    desired=bool(parts[ref]['dnp'])
    if bool(sym.dnp)!=desired:
     changes.append({'sheet':path.name,'ref':ref,'old_dnp':sym.dnp,'new_dnp':desired});sym.dnp=desired;dirty=True
  if dirty:s.to_file(str(path))
 out=root/'review/four-skills';out.mkdir(parents=True,exist_ok=True)
 (out/'native-dnp-fix.json').write_text(json.dumps(changes,indent=2));print(json.dumps(changes));return 0
p=kicad_tool.build_parser();sub=next(a for a in p._actions if isinstance(a,argparse._SubParsersAction));s=sub.add_parser('smartbin-dnp-metadata');s.add_argument('root',type=Path);s.set_defaults(func=run)
a=p.parse_args();raise SystemExit(a.func(a))
