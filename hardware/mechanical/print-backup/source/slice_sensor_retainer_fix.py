"""Slice only the four replacement retainers, keeping previously printed seats and walls."""
from pathlib import Path
import json,zipfile,subprocess,hashlib,xml.etree.ElementTree as E
import trimesh
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'sensor-retainers-fix-20261103';W=R.parent/'.p2s-sensor-retainers-fix-20261103';W.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
layout=[('LIGHT_BAR_V2',1,30,35),('LIGHT_BAR_V2',2,30,60),('BEAM_CUP_V2',1,110,35),('BEAM_CUP_V2',2,160,35)]
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);tag=lambda n:'{'+ns+'}'+n
root=E.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'});resources=E.SubElement(root,tag('resources'));build=E.SubElement(root,tag('build'));records=[]
for i,(n,copy,x,y) in enumerate(layout,1):
    mesh=trimesh.load_mesh(O/'parts'/f'{n}_PRINT.stl');mesh.apply_translation([x,y,0]);records.append({'name':n,'copy':copy,'offset_xy':[x,y],'bounds':mesh.bounds.tolist()})
    ob=E.SubElement(resources,tag('object'),{'id':str(i),'name':f'{n}_{copy}','type':'model'});me=E.SubElement(ob,tag('mesh'));vs=E.SubElement(me,tag('vertices'));ts=E.SubElement(me,tag('triangles'))
    for v in mesh.vertices:E.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],map(str,v))))
    for f in mesh.faces:E.SubElement(ts,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,f))))
    E.SubElement(build,tag('item'),{'objectid':str(i)})
geometry=W/'REPLACEMENT_RETAINERS.3mf'
with zipfile.ZipFile(B/'labeled-bases-20261101/geometry/PLATE_3_GEOMETRY.3mf') as template,zipfile.ZipFile(geometry,'w',zipfile.ZIP_DEFLATED) as z:
    for n in ['[Content_Types].xml','_rels/.rels']:z.writestr(n,template.read(n))
    z.writestr('3D/3dmodel.model',E.tostring(root,encoding='utf-8',xml_declaration=True))
process=load(B/'wall-clamps-fine-20261103/checks/slicing.json')['process'];process.update({'name':'P2S Light bars and IR lower cups repair FINE 012 PLA','enable_support':'0','brim_width':'3'})
cfg=R.parent/'.p2s-pack-20261030/slicer-validation'
for n,data in [('process',process),('machine',load(cfg/'machine.json')),('filament',load(cfg/'filament.json'))]:save(W/f'{n}.json',data)
cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(W/'machine.json')+';'+str(W/'process.json'),'--load-filaments',str(W/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(W),'--debug','2',str(geometry)]
with (W/'slice.log').open('w') as log:r=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0,(r.returncode,(W/'slice.log').read_text(errors='replace')[-2000:])
result=load(W/'result.json');p=result['sliced_plates'][0];assert not p['warning_message'],p['warning_message']
i=cmd.index('--slice');del cmd[i:i+2];project='P2S_LIGHT_BARS_IR_CUPS_FIX_FINE_012.3mf';cmd[cmd.index('--export-3mf')+1]=project;cmd[cmd.index('--outputdir')+1]=str(O)
with (W/'export.log').open('w') as log:r=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0
with zipfile.ZipFile(O/project) as z,zipfile.ZipFile(W/'sliced.3mf') as tested:
    assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
    for n in z.namelist():
        if n.endswith('.model'):assert z.read(n)==tested.read(n)
    c=json.loads(z.read('Metadata/project_settings.config'));assert c['layer_height']=='0.12' and c['enable_support']=='0'
save(O/'source/layout.json',{'objects':records,'keep_orientation':True,'scale':1,'old_seats_included':False})
save(O/'checks/slicing.json',{'status':'PASS','project':project,'object_count':4,'printer':'Bambu Lab P2S 0.4 nozzle','material':'Generic PLA','estimated_seconds':p['total_predication'],'filament_g':sum(f['total_used_g'] for f in p['filaments']),'warning_message':p['warning_message'],'native_matches_tested':True,'process':process,'sha256':hashlib.sha256((O/project).read_bytes()).hexdigest(),'physical_trial_fit':False,'printer_jobs_sent':False})
if (O/'result.json').exists():(O/'result.json').unlink()
print(json.dumps({k:v for k,v in load(O/'checks/slicing.json').items() if k!='process'},ensure_ascii=False),flush=True)
