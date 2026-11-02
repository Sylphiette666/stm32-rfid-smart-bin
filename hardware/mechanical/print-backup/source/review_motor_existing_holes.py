"""Review actual sliced extrusion extents and reimported STEP/mesh evidence."""
from pathlib import Path
import json,math,re,zipfile,hashlib
import cadquery as cq
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'motor-existing-holes-20261102';W=R.parent/'.p2s-motor-existing-holes-20261102'
d=json.loads((O/'checks/design.json').read_text(encoding='utf-8'))
geocheck={}
for name,v in d['variants'].items():
    s=cq.importers.importStep(str(O/'step'/f'D06_CARRIER_{name}_ASSEMBLY.step')).val()
    assert s.isValid() and len(s.Solids())==1 and abs(s.BoundingBox().zlen-16)<1e-6
    assert abs(s.BoundingBox().zmax)<1e-6 and abs(s.BoundingBox().zmin+16)<1e-6
    s=s.translate((0,0,16))
    assert abs(s.Volume()-v['volume_mm3'])<.001
    for p in [a['xy'] for a in v['anchors']]+v['seat_connection_holes']:
        tool=cq.Solid.makeCylinder(1.6999,18,cq.Vector(*p,-1))
        assert s.intersect(tool).Volume()<1e-6,(name,p,'hole obstructed')
    m=trimesh.load_mesh(O/'parts'/f'D06_CARRIER_{name}_PRINT.stl');m.merge_vertices(digits_vertex=5)
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
    assert abs(m.volume-s.Volume())/s.Volume()<.001
    geocheck[name]={'reimported_STEP_valid':True,'thickness_mm':s.BoundingBox().zlen,'volume_mm3':s.Volume(),'mesh_volume_relative_error':abs(m.volume-s.Volume())/s.Volume(),'all_through_holes_clear':True}
with zipfile.ZipFile(W/'sliced.3mf') as z:
    code=z.read(next(n for n in z.namelist() if n.endswith('.gcode'))).decode('utf-8',errors='replace')
layer=-1;x=y=0;relative=True;ep=0;feature='';segs=[];objs=set();support_total=0;count=0;mins=[1e10,1e10];maxs=[-1e10,-1e10]
for line in code.splitlines():
    if line.startswith('; CHANGE_LAYER'):layer+=1
    if line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
    if layer==0 and line.startswith('; OBJECT_ID:'):objs.add(line.strip())
    cmd=line.split(';')[0].strip()
    if cmd=='M83':relative=True
    if cmd=='M82':relative=False
    if cmd.startswith('G92 E'):ep=float(cmd[5:])
    if not re.match(r'^G[123] ',cmd):continue
    f={k:float(v) for k,v in re.findall(r'([XYEIJR])(-?\d*\.?\d+)',cmd)};nx=f.get('X',x);ny=f.get('Y',y);ex=f.get('E',0) if relative else f.get('E',ep)-ep
    if 'E' in f:ep=ep+f['E'] if relative else f['E']
    if ex>0 and ('X' in f or 'Y' in f) and feature!='Custom' and layer>=0:
        path=[(x,y),(nx,ny)];extrema=path
        if cmd.startswith(('G2 ','G3 ')):
            assert 'R' not in f
            cx=x+f.get('I',0);cy=y+f.get('J',0);radius=math.hypot(x-cx,y-cy)
            start=math.atan2(y-cy,x-cx);end=math.atan2(ny-cy,nx-cx);sweep=(end-start)%(2*math.pi)
            if cmd.startswith('G2 '):sweep-=2*math.pi
            elif abs(sweep)<1e-9:sweep=2*math.pi
            angles=[q*math.pi/2 for q in range(4)]
            extrema=path+[(cx+radius*math.cos(a),cy+radius*math.sin(a)) for a in angles if ((a-start)%(2*math.pi)<=sweep+1e-8 if sweep>0 else (start-a)%(2*math.pi)<=-sweep+1e-8)]
            if layer==0:
                steps=max(8,math.ceil(abs(sweep)*radius/.05));path=[(cx+radius*math.cos(start+sweep*i/steps),cy+radius*math.sin(start+sweep*i/steps)) for i in range(steps+1)];path[0]=(x,y);path[-1]=(nx,ny)
        assert all(min(p)>=-.001 and max(p)<=256.001 for p in extrema),(layer,extrema)
        for p in extrema:
            for i in range(2):mins[i]=min(mins[i],p[i]);maxs[i]=max(maxs[i],p[i])
        count+=1
        if 'Support' in feature:support_total+=1
        if layer==0:segs.extend(zip(path,path[1:]))
    x,y=nx,ny
assert len(objs)==2 and support_total==0
plt.rcParams['font.family']='Microsoft YaHei'
fig,ax=plt.subplots(figsize=(9,8));ax.add_collection(LineCollection(segs,colors='#235d7b',linewidths=.55));ax.set(xlim=(0,256),ylim=(0,256));ax.set_aspect('equal');ax.set_title('两块新增厚转接板  实际切片首层');fig.tight_layout();fig.savefig(O/'preview/04_actual_first_layer.png',dpi=160);plt.close(fig)
with zipfile.ZipFile(O/'P2S_D06_EXISTING_HOLES_CARRIERS_016.3mf') as z:
    cfg=json.loads(z.read('Metadata/project_settings.config'))
    assert cfg['wall_loops']=='6' and cfg['sparse_infill_density']=='60%' and cfg['layer_height']=='0.16'
    assert not any(n.endswith('.gcode') for n in z.namelist())
r={'status':'PASS','geometry':geocheck,'first_layer_object_count':2,'all_extrusions_checked':count,'all_layers':layer+1,'all_extrusion_bounds':[mins,maxs],'support_moves':support_total,'all_paths_in_bed':True,'G39_absent':not bool(re.search(r'^\s*G39(?:\s|;|$)',code,re.M)),'physical_load_or_wheel_fit_tested':False}
(O/'checks/geometry_and_path_review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(r))
