"""Slice two new carrier plates only; retain the already-fitted motor seats."""
from pathlib import Path
import json,zipfile,subprocess,xml.etree.ElementTree as E
import trimesh
B=Path(__file__).resolve().parents[1];R=B.parents[2]
O=B/'motor-existing-holes-20261102';W=R.parent/'.p2s-motor-existing-holes-20261102';W.mkdir(exist_ok=True)
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);tag=lambda n:'{'+ns+'}'+n
root=E.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'});resources=E.SubElement(root,tag('resources'));build=E.SubElement(root,tag('build'))
for i,(name,xy) in enumerate([('LEFT',(12,30)),('RIGHT',(115,30))],1):
    m=trimesh.load_mesh(O/'parts'/f'D06_CARRIER_{name}_PRINT.stl');m.apply_translation([*xy,0])
    ob=E.SubElement(resources,tag('object'),{'id':str(i),'name':f'D06_CARRIER_{name}','type':'model'});me=E.SubElement(ob,tag('mesh'));vs=E.SubElement(me,tag('vertices'));ts=E.SubElement(me,tag('triangles'))
    for v in m.vertices:E.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],map(str,v))))
    for f in m.faces:E.SubElement(ts,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,f))))
    E.SubElement(build,tag('item'),{'objectid':str(i)})
geometry=W/'CARRIER_PAIR.3mf'
with zipfile.ZipFile(B/'labeled-bases-20261101/geometry/PLATE_3_GEOMETRY.3mf') as template,zipfile.ZipFile(geometry,'w',zipfile.ZIP_DEFLATED) as z:
    for n in ['[Content_Types].xml','_rels/.rels']:z.writestr(n,template.read(n))
    z.writestr('3D/3dmodel.model',E.tostring(root,encoding='utf-8',xml_declaration=True))
process=json.loads((B/'motor-adapter-clearance2-final-20261102/checks/slicing.json').read_text(encoding='utf-8'))['process']
process.update({'name':'D06 existing hole carriers 016 reinforced','layer_height':'0.16','wall_loops':'6','sparse_infill_density':'60%','sparse_infill_pattern':'gyroid','top_shell_layers':'8','bottom_shell_layers':'8','enable_support':'0','brim_type':'outer_only','brim_width':'3','brim_object_gap':'0.1'})
config=R.parent/'.p2s-pack-20261030/slicer-validation'
for name,data in [('process',process),('machine',json.loads((config/'machine.json').read_text(encoding='utf-8'))),('filament',json.loads((config/'filament.json').read_text(encoding='utf-8')))]:
    (W/f'{name}.json').write_text(json.dumps(data),encoding='utf-8')
cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(W/'machine.json')+';'+str(W/'process.json'),'--load-filaments',str(W/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(W),'--debug','2',str(geometry)]
with (W/'slice.log').open('w') as log:done=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert done.returncode==0,done.returncode
p=json.loads((W/'result.json').read_text(encoding='utf-8'))['sliced_plates'][0];assert not p['warning_message'],p['warning_message']
n=cmd.index('--slice');del cmd[n:n+2];project='P2S_D06_EXISTING_HOLES_CARRIERS_016.3mf'
cmd[cmd.index('--export-3mf')+1]=project;cmd[cmd.index('--outputdir')+1]=str(O)
with (W/'export.log').open('w') as log:done=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert done.returncode==0
with zipfile.ZipFile(O/project) as z,zipfile.ZipFile(W/'sliced.3mf') as tested:
    assert not any(n.endswith('.gcode') for n in z.namelist())
    for n in z.namelist():
        if n.endswith('.model'):assert z.read(n)==tested.read(n)
report={'status':'PASS','project':project,'new_objects':2,'retained_motor_seats_included':False,'estimated_seconds':p['total_predication'],'filament_g':sum(f['total_used_g'] for f in p['filaments']),'warning_message':p['warning_message'],'process':process,'native_matches_tested':True,'physical_test':False}
(O/'checks/slicing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
if (O/'result.json').exists():(O/'result.json').unlink()
print(json.dumps({k:v for k,v in report.items() if k!='process'},ensure_ascii=False))
