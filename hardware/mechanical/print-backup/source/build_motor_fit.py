"""Small, non-load-bearing D06 fit coupons; no existing plate modifications."""
from pathlib import Path
import json,zipfile,hashlib,subprocess,xml.etree.ElementTree as E
import cadquery as cq
import trimesh
B=Path(__file__).resolve().parents[1]; R=B.parents[2]
O=B/'motor-fit-20261101';W=R.parent/'.p2s-motor-fit-20261101'
for p in [O,O/'parts',O/'step',O/'checks',W]:p.mkdir(parents=True,exist_ok=True)
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns)
tag=lambda n:'{'+ns+'}'+n
root=E.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'});res=E.SubElement(root,tag('resources'));build=E.SubElement(root,tag('build'))
records=[]
for i,(name,width) in enumerate([('A',2.2),('B',2.4),('C',2.6)],1):
 s=cq.Workplane('XY').box(28,36,5,centered=(True,True,False)).edges('|Z').fillet(1)
 s=s.cut(cq.Workplane('XY').box(14,12,7,centered=(True,True,False)).translate((0,0,-1)))
 for y in [-10.5,10.5]:
  cutter=cq.Workplane('XY').box(12,width,7,centered=(True,True,False)).translate((0,y,-1));s=s.cut(cutter)
 letters=cq.Workplane('XY').text(name,4,.4,font='Arial',kind='bold',halign='center',valign='center').translate((10,0,5))
 solid=s.union(letters).val();assert solid.isValid() and len(solid.Solids())==1
 cq.exporters.export(solid,str(O/'step'/f'FIT_{name}.step'))
 flat=solid.translate((14,18,0));path=O/'parts'/f'FIT_{name}.stl';cq.exporters.export(flat,str(path),tolerance=.02,angularTolerance=.05)
 m=trimesh.load_mesh(path);assert m.is_watertight and m.is_winding_consistent
 # Confirm slots are full-through and the simulated 11.5 x 2 mm necks fit.
 for y in [-10.5,10.5]:
  probe=cq.Workplane('XY').box(11.5,2,9,centered=(True,True,False)).translate((0,y,-2)).val()
  assert solid.intersect(probe).Volume()<1e-7
 m.apply_translation([68+(i-1)*42,110,0])
 obj=E.SubElement(res,tag('object'),{'id':str(i),'name':f'FIT_{name}_slot_12x{width}','type':'model'});mesh=E.SubElement(obj,tag('mesh'));vs=E.SubElement(mesh,tag('vertices'));ts=E.SubElement(mesh,tag('triangles'))
 for v in m.vertices:E.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],map(str,v))))
 for f in m.faces:E.SubElement(ts,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,f))))
 E.SubElement(build,tag('item'),{'objectid':str(i)})
 records.append({'id':name,'slot_mm':[12,width],'slot_centres_mm':[[0,-10.5],[0,10.5]],'nominal_inner_tab_gap_mm':19,'plate_thickness_mm':5,'size_mm':[28,36,5.4],'watertight':True,'neck_fit_digital':True})
geometry=W/'FIT_GEOMETRY.3mf'
with zipfile.ZipFile(B/'labeled-bases-20261101/geometry/PLATE_3_GEOMETRY.3mf') as template,zipfile.ZipFile(geometry,'w',zipfile.ZIP_DEFLATED) as z:
 for n in ['[Content_Types].xml','_rels/.rels']:z.writestr(n,template.read(n))
 z.writestr('3D/3dmodel.model',E.tostring(root,encoding='utf-8',xml_declaration=True))
config=R.parent/'.p2s-pack-20261030/slicer-validation'
process=json.loads((B/'labeled-bases-20261101/checks/slicing.json').read_text(encoding='utf-8'))['plates']['PLATE_3_GEOMETRY']['process'].copy()
process.update({'name':'D06 fit coupons 0.16','brim_type':'no_brim','brim_width':'0','xy_hole_compensation':'0','xy_contour_compensation':'0','elefant_foot_compensation':'0.15'})
process.update({'wall_loops':'3','top_shell_layers':'5','bottom_shell_layers':'5','top_shell_thickness':'0.8','bottom_shell_thickness':'0.8','sparse_infill_density':'15%'})
for name,data in [('process',process),('machine',json.loads((config/'machine.json').read_text(encoding='utf-8'))),('filament',json.loads((config/'filament.json').read_text(encoding='utf-8')))]:
 (W/f'{name}.json').write_text(json.dumps(data),encoding='utf-8')
cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(W/'machine.json')+';'+str(W/'process.json'),'--load-filaments',str(W/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(W),'--debug','2',str(geometry)]
with (W/'slice.log').open('w') as log:done=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert done.returncode==0,(W/'slice.log').read_text(errors='replace')[-2000:]
result=json.loads((W/'result.json').read_text(encoding='utf-8'));p=result['sliced_plates'][0];assert not p['warning_message']
n=cmd.index('--slice');del cmd[n:n+2];cmd[cmd.index('--export-3mf')+1]='P2S_D06_FIT_TEST_016.3mf';cmd[cmd.index('--outputdir')+1]=str(O)
with (W/'export.log').open('w') as log:done=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert done.returncode==0
native=O/'P2S_D06_FIT_TEST_016.3mf'
with zipfile.ZipFile(native) as z,zipfile.ZipFile(W/'sliced.3mf') as tested:
 assert not any(n.endswith('.gcode') for n in z.namelist())
 for n in z.namelist():
  if n.endswith('.model'):assert z.read(n)==tested.read(n)
 settings=json.loads(z.read('Metadata/project_settings.config'));assert settings['layer_height']=='0.16'
code=''
with zipfile.ZipFile(W/'sliced.3mf') as z:
 code='\n'.join(z.read(n).decode('utf-8',errors='replace') for n in z.namelist() if n.endswith('.gcode'))
assert code and 'G39' not in '\n'.join(l for l in code.splitlines() if not l.startswith(';'))
report={'status':'PASS','coupons':records,'estimated_seconds':p['total_predication'],'filament_g':sum(f['total_used_g'] for f in p['filaments']),'warning_message':p['warning_message'],'native_matches_tested_geometry':True,'physical_fit_verified':False,'load_bearing_part':False,'material_identity':'nonmetal per user; exact polymer unspecified','latest_user_measurements_mm':{'neck_width':11.5,'tab_thickness':2,'motor_width':18.5},'insertion':'downwards; T head above plate','slot_centre_distance_mm':21,'note':'19 mm is nominal inner gap for centred 2 mm tabs; slot clearance permits lateral movement. No forced clamping across excess gap.'}
(O/'checks/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if (O/'result.json').exists():(O/'result.json').unlink()
print(json.dumps(report,ensure_ascii=False))
