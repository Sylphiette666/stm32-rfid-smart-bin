"""One native P2S high-detail project: four keyed clamps plus four pressure pads."""
from pathlib import Path
import json,zipfile,subprocess,hashlib,xml.etree.ElementTree as E
import trimesh
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'wall-clamps-fine-20261103';W=R.parent/'.p2s-wall-clamps-fine-20261103';W.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
layout=[('C1_LEFT_REAR',25,25),('C2_LEFT_FRONT',25,70),('C3_RIGHT_FRONT',25,115),('C4_RIGHT_REAR',165,40)]+[(f'PRESSURE_PAD_{i+1}',162+20*i,105) for i in range(4)]
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);tag=lambda n:'{'+ns+'}'+n
root=E.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'});resources=E.SubElement(root,tag('resources'));build=E.SubElement(root,tag('build'));bounds=[]
for i,(n,x,y) in enumerate(layout,1):
    mesh=trimesh.load_mesh(O/'parts'/('PRESSURE_PAD_PRINT.stl' if n.startswith('PRESSURE_PAD') else n+'_PRINT.stl'));mesh.apply_translation([x,y,0])
    bb=mesh.bounds.tolist();assert all(0<=a<=256 for pair in bb for a in pair[:2]);bounds.append({'name':n,'offset_xy':[x,y],'bounds':bb})
    ob=E.SubElement(resources,tag('object'),{'id':str(i),'name':n,'type':'model'});me=E.SubElement(ob,tag('mesh'));vs=E.SubElement(me,tag('vertices'));ts=E.SubElement(me,tag('triangles'))
    for v in mesh.vertices:E.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],map(str,v))))
    for f in mesh.faces:E.SubElement(ts,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,f))))
    E.SubElement(build,tag('item'),{'objectid':str(i)})
geometry=W/'CLAMPS_AND_PADS.3mf'
with zipfile.ZipFile(B/'labeled-bases-20261101/geometry/PLATE_3_GEOMETRY.3mf') as template,zipfile.ZipFile(geometry,'w',zipfile.ZIP_DEFLATED) as z:
    for n in ['[Content_Types].xml','_rels/.rels']:z.writestr(n,template.read(n))
    z.writestr('3D/3dmodel.model',E.tostring(root,encoding='utf-8',xml_declaration=True))
process=load(B/'motor-existing-holes-light-20261103/checks/slicing.json')['process'];source=load(B/'wall-panels-20261102/source/github_support_source.json');s=source['profile']
keys=['support_type','support_style','support_threshold_angle','tree_support_branch_angle','tree_support_branch_diameter','tree_support_wall_count','support_interface_top_layers','support_interface_bottom_layers','support_interface_spacing','support_object_xy_distance','support_base_pattern_spacing','support_on_build_plate_only']
process.update({k:s[k] for k in keys})
process.update({'name':'P2S Wall clamps FINE 012 reinforced PLA','layer_height':'0.12','initial_layer_print_height':'0.2','wall_loops':'6','sparse_infill_density':'60%','sparse_infill_pattern':'gyroid','top_shell_layers':'12','bottom_shell_layers':'12','top_shell_thickness':'1.44','bottom_shell_thickness':'1.44','enable_support':'1','support_type':'tree(auto)','support_threshold_angle':'50','support_on_build_plate_only':'1','support_top_z_distance':'0.12','support_bottom_z_distance':'0.12','support_interface_top_layers':'3','support_interface_bottom_layers':'2','support_object_xy_distance':'0.35','brim_type':'outer_only','brim_width':'5','brim_object_gap':'0.1','enable_prime_tower':'0','print_sequence':'by layer','outer_wall_speed':['35']*3,'inner_wall_speed':['80']*3,'top_surface_speed':['35']*3,'initial_layer_speed':['25']*3,'initial_layer_infill_speed':['35']*3,'default_acceleration':['1800']*3,'outer_wall_acceleration':['700']*3,'bridge_speed':['25']*3,'resolution':'0.01','xy_hole_compensation':'0','xy_contour_compensation':'0','enable_wrapping_detection':'0'})
cfg=R.parent/'.p2s-pack-20261030/slicer-validation'
for n,data in [('process',process),('machine',load(cfg/'machine.json')),('filament',load(cfg/'filament.json'))]:save(W/f'{n}.json',data)
cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(W/'machine.json')+';'+str(W/'process.json'),'--load-filaments',str(W/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(W),'--debug','2',str(geometry)]
with (W/'slice.log').open('w') as log:r=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0,(r.returncode,(W/'slice.log').read_text(errors='replace')[-2000:])
result=load(W/'result.json');plate=result['sliced_plates'][0];assert not plate['warning_message'],plate['warning_message']
index=cmd.index('--slice');del cmd[index:index+2];project='P2S_WALL_CLAMPS_AND_PADS_FINE_012.3mf';cmd[cmd.index('--export-3mf')+1]=project;cmd[cmd.index('--outputdir')+1]=str(O)
with (W/'export.log').open('w') as log:r=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0
with zipfile.ZipFile(O/project) as z,zipfile.ZipFile(W/'sliced.3mf') as tested:
    assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
    for n in z.namelist():
        if n.endswith('.model'):assert z.read(n)==tested.read(n)
    c=json.loads(z.read('Metadata/project_settings.config'));assert c['layer_height']=='0.12' and c['enable_support']=='1' and c['wall_loops']=='6'
save(O/'source/layout.json',{'objects':bounds,'units':'mm','keep_saved_orientation':True,'auto_arrange':False,'scale':1})
report={'status':'PASS_SLICER','project':project,'printer':'Bambu Lab P2S 0.4 nozzle','material':'Generic PLA','object_count':8,'estimated_seconds':plate['total_predication'],'filament_g':sum(f['total_used_g'] for f in plate['filaments']),'warning_message':plate['warning_message'],'native_matches_tested':True,'native_contains_gcode':False,'support_type':'tree(auto)','feature_type_times':plate['feature_type_times'],'process':process,'support_profile_source_blob':source['blob_sha'],'sha256':hashlib.sha256((O/project).read_bytes()).hexdigest(),'physical_print_test':False,'printer_jobs_sent':False}
save(O/'checks/slicing.json',report)
if (O/'result.json').exists():(O/'result.json').unlink()
print(json.dumps({k:v for k,v in report.items() if k not in ['process','feature_type_times']},ensure_ascii=False),flush=True)
