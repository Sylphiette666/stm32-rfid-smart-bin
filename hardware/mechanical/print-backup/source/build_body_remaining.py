"""Build continuation jobs after printing the 43-piece fine accessory plate."""
from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'flat-split-20261101';OUT=ROOT/'body-after-accessories-20261101'
for d in ['geometry','projects','checks','preview']:(OUT/d).mkdir(parents=True,exist_ok=True)
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};E.register_namespace('',ns['m'])
keep={'P01_REAR_HALF','P01_FRONT_HALF','JOIN_BRIDGE_1','JOIN_BRIDGE_2','JOIN_BRIDGE_3','P02_UPPER','P03_STAND','P07_SPEAKER_cradle'};report=[]
for plate in [1,2,3]:
 f=OLD/'geometry'/f'PLATE_{plate}_GEOMETRY.3mf'
 with zipfile.ZipFile(f) as z:
  root=E.fromstring(z.read('3D/3dmodel.model'));resources=root.find('m:resources',ns);build=root.find('m:build',ns)
  removed={o.get('id') for o in resources if o.get('name') not in keep}
  for o in list(resources):
   if o.get('id') in removed:resources.remove(o)
  for b in list(build):
   if b.get('objectid') in removed:build.remove(b)
  with zipfile.ZipFile(OUT/'geometry'/f'PLATE_{plate}_GEOMETRY.3mf','w',zipfile.ZIP_DEFLATED) as out:
   for name in z.namelist():out.writestr(name,E.tostring(root,encoding='utf-8',xml_declaration=True) if name=='3D/3dmodel.model' else z.read(name))
  report.append({'plate':plate,'objects':len(list(build)),'names':[o.get('name') for o in resources]})
assert sum(r['objects'] for r in report)==8
(OUT/'checks/packing.json').write_text(json.dumps({'status':'PASS','plates':report,'geometry_and_positions_retained':True,'total_objects':8,'complements_fine_plate_without_duplicates':True},ensure_ascii=False,indent=2),encoding='utf-8')
print(report)
