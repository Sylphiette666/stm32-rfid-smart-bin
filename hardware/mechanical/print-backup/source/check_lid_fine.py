"""Roundtrip all native objects and audit every sliced extrusion, including arcs."""
from pathlib import Path
import json,posixpath,zipfile,xml.etree.ElementTree as E,re,math
import numpy as np
import trimesh
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'lid-fine-20261103';W=R.parent/'.p2s-lid-fine-20261103'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
def matrix(value):
    if not value:return np.eye(4)
    a=np.array(list(map(float,value.split()))).reshape(4,3);m=np.eye(4);m[:3,:3]=a[:3,:].T;m[:3,3]=a[3,:];return m
native={};paths={};plt.rcParams['font.family']='Microsoft YaHei';fig,axs=plt.subplots(1,2,figsize=(14,7))
for ax,(key,s) in zip(axs,load(O/'checks/slicing.json').items()):
    layout=s['objects']
    with zipfile.ZipFile(O/s['project']) as z:
        cache={}
        def root(path):
            if path not in cache:cache[path]=E.fromstring(z.read(path))
            return cache[path]
        def vertices(path,oid,t):
            ob=next(o for o in root(path).findall('m:resources/m:object',ns) if o.attrib['id']==oid);me=ob.find('m:mesh',ns)
            if me is not None:
                vs=np.array([[float(v.attrib[k]) for k in ['x','y','z']] for v in me.findall('m:vertices/m:vertex',ns)]);return [vs@t[:3,:3].T+t[:3,3]]
            out=[]
            for c in ob.findall('m:components/m:component',ns):
                cp=next((v for k,v in c.attrib.items() if k.endswith('}path')),path);cp=cp.lstrip('/') if cp.startswith('/') else (path if cp==path else posixpath.normpath(posixpath.join(posixpath.dirname(path),cp)))
                out+=vertices(cp,c.attrib['objectid'],t@matrix(c.attrib.get('transform')))
            return out
        items=root('3D/3dmodel.model').findall('m:build/m:item',ns);assert len(items)==len(layout);report=[]
        for item,v in zip(items,layout):
            actual=np.vstack(vertices('3D/3dmodel.model',item.attrib['objectid'],matrix(item.attrib.get('transform'))));n=v['name'];expected=trimesh.load_mesh(O/'parts'/(n+'_PRINT.stl')).vertices+[*v['offset_xy'],0]
            error=max(cKDTree(actual).query(expected)[0].max(),cKDTree(expected).query(actual)[0].max());assert error<5e-5,(key,n,error)
            assert abs(actual[:,2].min())<1e-5;report.append({'name':n,'bidirectional_vertex_error_mm':float(error),'on_bed':True})
        c=json.loads(z.read('Metadata/project_settings.config'));assert c['layer_height']=='0.12' and c['enable_support']=='0' and c['resolution']=='0.01'
        assert c['print_sequence']=='by layer' and c['xy_hole_compensation']=='0' and c['xy_contour_compensation']=='0'
        native[key]={'status':'PASS','objects_verified':len(report),'objects':report,'physical_tolerance_claim':False}
    with zipfile.ZipFile(W/key/'sliced.3mf') as z:code=z.read(next(n for n in z.namelist() if n.endswith('.gcode'))).decode('utf-8',errors='replace')
    layer=-1;x=y=ep=0.;relative=True;feature='';first=[];objs=set();count=support=0;mins=[1e9,1e9];maxs=[-1e9,-1e9];layer_z=[];zh=0
    skin_paths={}
    for line in code.splitlines():
        if line.startswith('; CHANGE_LAYER'):layer+=1
        if line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
        if layer==0 and line.startswith('; OBJECT_ID:'):objs.add(line.strip())
        cmd=line.split(';')[0].strip()
        if cmd=='M83':relative=True
        if cmd=='M82':relative=False
        if cmd.startswith('G92 E'):ep=float(cmd[5:])
        if not re.match(r'^G[123] ',cmd):continue
        f={k:float(v) for k,v in re.findall(r'([XYEIJRZ])(-?\d*\.?\d+)',cmd)};nx=f.get('X',x);ny=f.get('Y',y);zh=f.get('Z',zh);ex=f.get('E',0) if relative else f.get('E',ep)-ep
        if 'E'in f:ep=ep+f['E'] if relative else f['E']
        if ex>0 and ('X'in f or 'Y'in f) and feature!='Custom' and layer>=0:
            path=[(x,y),(nx,ny)];extrema=path
            if cmd.startswith(('G2 ','G3 ')):
                assert 'R' not in f;cx=x+f.get('I',0);cy=y+f.get('J',0);rad=math.hypot(x-cx,y-cy);start=math.atan2(y-cy,x-cx);end=math.atan2(ny-cy,nx-cx);sweep=(end-start)%(2*math.pi)
                if cmd.startswith('G2 '):sweep-=2*math.pi
                elif abs(sweep)<1e-9:sweep=2*math.pi
                extrema=path+[(cx+rad*math.cos(a),cy+rad*math.sin(a)) for a in [q*math.pi/2 for q in range(4)] if ((a-start)%(2*math.pi)<=sweep+1e-8 if sweep>0 else (start-a)%(2*math.pi)<=-sweep+1e-8)]
                if layer==0:
                    steps=max(3,math.ceil(abs(sweep)*rad/.15));path=[(cx+rad*math.cos(start+sweep*i/steps),cy+rad*math.sin(start+sweep*i/steps)) for i in range(steps+1)];path[0]=(x,y);path[-1]=(nx,ny)
            assert all(min(p)>=-.001 and max(p)<=256.001 for p in extrema),(key,layer,extrema)
            for p in extrema:
                for i in range(2):mins[i]=min(mins[i],p[i]);maxs[i]=max(maxs[i],p[i])
            count+=1
            if 'Support'in feature:support+=1
            if layer==0:first.extend(zip(path,path[1:]))
            if key=='LID' and x<195 and nx<195 and y<180 and ny<180 and layer<6:skin_paths.setdefault(round(zh,3),0);skin_paths[round(zh,3)]+=1
        x,y=nx,ny
    assert len(objs)==len(layout) and support==0 and not re.search(r'^\s*G39(?:\s|;|$)',code,re.M)
    # The closed skin must have actual toolpaths through the designed .56mm skin.
    if key=='LID':assert all(h in skin_paths for h in [.2,.32,.44,.56]),skin_paths
    paths[key]={'status':'PASS_ALL_LAYER_PATHS','first_layer_objects':len(objs),'layers':layer+1,'extrusions_checked':count,'bounds':[mins,maxs],'support_moves':support,'all_paths_in_bed':True,'G39_absent':True,'closed_skin_first_four_layers':skin_paths if key=='LID' else None}
    ax.add_collection(LineCollection(first,colors='#235d7b',linewidths=.3));ax.set_aspect('equal');ax.set(xlim=(0,256),ylim=(0,256));ax.set_title('整盖六件  首层' if key=='LID' else '合页试装小样两件  首层');ax.set_xlabel('X / mm');ax.set_ylabel('Y / mm')
fig.tight_layout();fig.savefig(O/'preview/05_actual_first_layers.png',dpi=140);plt.close(fig)
save(O/'checks/native_geometry.json',native);save(O/'checks/path_review.json',paths)
print(json.dumps(paths,ensure_ascii=False),flush=True)
