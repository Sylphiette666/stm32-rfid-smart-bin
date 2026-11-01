"""Remove only the original first plate's base+cradle, preserving all 43 accessories."""
from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'mounted-20261031';OUT=ROOT/'accessories-fine-20261101'
for d in ['geometry','projects','checks','preview']:(OUT/d).mkdir(parents=True,exist_ok=True)
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
E.register_namespace('',ns['m'])
f=OLD/'geometry/PLATE_1_GEOMETRY.3mf'
with zipfile.ZipFile(f) as z:
 root=E.fromstring(z.read('3D/3dmodel.model'));resources=root.find('m:resources',ns);build=root.find('m:build',ns)
 objects=resources.findall('m:object',ns);remove=[o for o in objects if o.get('name')=='P01_BASE_WITH_CRADLE'];assert len(objects)==44 and len(remove)==1
 ident=remove[0].get('id');before={o.get('id'):E.tostring(o) for o in objects if o.get('id')!=ident};resources.remove(remove[0])
 for b in list(build):
  if b.get('objectid')==ident:build.remove(b)
 assert len(list(build))==43 and len(list(resources))==43
 for o in resources:assert E.tostring(o)==before[o.get('id')]
 with zipfile.ZipFile(OUT/'geometry/PLATE_1_GEOMETRY.3mf','w',zipfile.ZIP_DEFLATED) as out:
  for name in z.namelist():out.writestr(name,E.tostring(root,encoding='utf-8',xml_declaration=True) if name=='3D/3dmodel.model' else z.read(name))
report={'status':'PASS','source_file':'mounted-20261031/geometry/PLATE_1_GEOMETRY.3mf','removed':['P01_BASE_WITH_CRADLE'],'objects_before':44,'objects_after':43,'remaining_object_xml_unchanged':True,'positions_and_scale_unchanged':True,'remaining_names':[o.get('name') for o in resources],'physical_print_test':False}
(OUT/'checks/removal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'checks/packing.json').write_text(json.dumps({'status':'PASS','plates':[{'plate':1,'objects':43}],'original_accessory_placement_retained':True,'physical_print_test':False}),encoding='utf-8')
print('Original plate 1: 44 objects -> 43; only the base+cradle removed.')
