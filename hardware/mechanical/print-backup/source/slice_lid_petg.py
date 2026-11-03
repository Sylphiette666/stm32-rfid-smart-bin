"""Six-piece lid plus a separate two-piece hinge trial, native P2S projects."""
from pathlib import Path
import json,zipfile,subprocess,hashlib,xml.etree.ElementTree as E
import trimesh
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'lid-petg-final-20261103';W=R.parent/'.p2s-lid-petg-final-20261103';W.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
layouts={'LID':[('L01_LIGHT_LID',1,20,20),('L02_HINGE_SHOE',1,210,35),('L02_HINGE_SHOE',2,210,75),('L03_LINK_ARM',1,205,120),('L04_SWITCH_FOOT',1,35,210),('L05_SWITCH_TONGUE',1,80,210)],
         'HINGE_TRIAL':[('T01_HINGE_FIT_COUPON',1,50,50),('L02_HINGE_SHOE',1,100,50)]}
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);tag=lambda n:'{'+ns+'}'+n
cfg=R.parent/'.p2s-pack-20261030/slicer-validation';cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
process=load(B/'wall-clamps-fine-20261103/checks/slicing.json')['process']
process.update({'name':'P2S Lightweight closed skin lid FINE 012 PLA','enable_support':'0','brim_width':'5','wall_loops':'4','sparse_infill_density':'20%',
 'top_shell_layers':'6','bottom_shell_layers':'6','outer_wall_speed':'35','top_surface_speed':'35'})

profiles=cli.parent/'resources/profiles/BBL'
index={q.stem:q for q in profiles.rglob('*.json')}
def resolve(name):
    x=load(index[name]); parent=x.pop('inherits',None); y=resolve(parent) if parent else {};y.update(x);return y
petg=resolve('Generic PETG @BBL P2S')
petg['filament_max_volumetric_speed']=['8','8','8']
process.update(resolve('0.08mm High Quality @BBL P2S'))
process.update({'name':'SmartBin P2S PETG FINAL 008','layer_height':'0.08','initial_layer_print_height':'0.16','wall_loops':'4','sparse_infill_density':'20%','enable_support':'0','brim_width':'5','outer_wall_speed':'25','inner_wall_speed':'50','top_surface_speed':'25','initial_layer_speed':'20','default_acceleration':'1500','outer_wall_acceleration':'1000','top_surface_acceleration':'1000','resolution':'0.01','top_shell_layers':'8','bottom_shell_layers':'8'})

allrecords={}
for key,layout in layouts.items():
    work=W/key;work.mkdir(exist_ok=True)
    root=E.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'});resources=E.SubElement(root,tag('resources'));build=E.SubElement(root,tag('build'));records=[]
    for i,(n,copy,x,y) in enumerate(layout,1):
        m=trimesh.load_mesh(O/'parts'/f'{n}_PRINT.stl');m.apply_translation([x,y,0]);records.append({'name':n,'copy':copy,'offset_xy':[x,y],'bounds':m.bounds.tolist()})
        ob=E.SubElement(resources,tag('object'),{'id':str(i),'name':f'{n}_{copy}','type':'model'});me=E.SubElement(ob,tag('mesh'));vs=E.SubElement(me,tag('vertices'));ts=E.SubElement(me,tag('triangles'))
        for v in m.vertices:E.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],map(str,v))))
        for f in m.faces:E.SubElement(ts,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,f))))
        E.SubElement(build,tag('item'),{'objectid':str(i)})
    geo=work/'geometry.3mf'
    with zipfile.ZipFile(B/'labeled-bases-20261101/geometry/PLATE_3_GEOMETRY.3mf') as template,zipfile.ZipFile(geo,'w',zipfile.ZIP_DEFLATED) as z:
        for n in ['[Content_Types].xml','_rels/.rels']:z.writestr(n,template.read(n))
        z.writestr('3D/3dmodel.model',E.tostring(root,encoding='utf-8',xml_declaration=True))
    for n,data in [('process',process),('machine',load(cfg/'machine.json')),('filament',petg)]:save(work/f'{n}.json',data)
    cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(work/'machine.json')+';'+str(work/'process.json'),'--load-filaments',str(work/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(work),'--debug','2',str(geo)]
    with (work/'slice.log').open('w') as log:r=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
    assert r.returncode==0,(key,r.returncode,(work/'slice.log').read_text(errors='replace')[-2000:])
    p=load(work/'result.json')['sliced_plates'][0];assert not p['warning_message'],p['warning_message']
    i=cmd.index('--slice');del cmd[i:i+2];project=f'P2S_{key}_PETG_FINAL_008.3mf';cmd[cmd.index('--export-3mf')+1]=project;cmd[cmd.index('--outputdir')+1]=str(O)
    with (work/'export.log').open('w') as log:r=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
    assert r.returncode==0
    with zipfile.ZipFile(O/project) as z,zipfile.ZipFile(work/'sliced.3mf') as tested:
        assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
        for n in z.namelist():
            if n.endswith('.model'):assert z.read(n)==tested.read(n)
        c=json.loads(z.read('Metadata/project_settings.config'));assert c['layer_height']=='0.08' and c['enable_support']=='0'
    allrecords[key]={'status':'PASS','project':project,'object_count':len(layout),'objects':records,'printer':'Bambu Lab P2S 0.4 nozzle','material':'Generic PETG','estimated_seconds':p['total_predication'],'filament_g':sum(f['total_used_g'] for f in p['filaments']),
        'warning_message':p['warning_message'],'native_matches_tested':True,'process':process,'sha256':hashlib.sha256((O/project).read_bytes()).hexdigest(),'printer_jobs_sent':False}
    if (O/'result.json').exists():(O/'result.json').unlink()
    print(key,p['total_predication'],allrecords[key]['filament_g'],flush=True)
save(O/'source/layout.json',{k:{'objects':v['objects'],'keep_orientation':True,'scale':1} for k,v in allrecords.items()})
save(O/'checks/slicing.json',allrecords)
