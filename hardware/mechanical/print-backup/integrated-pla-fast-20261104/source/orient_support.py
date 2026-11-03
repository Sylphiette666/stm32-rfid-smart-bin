"""Search rigid poses by estimated unsupported projected area and height."""
from pathlib import Path
import numpy as np,trimesh,json,zipfile,xml.etree.ElementTree as E
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from scipy.optimize import differential_evolution
E.register_namespace('', 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02')
O=Path(__file__).resolve().parents[1];R=O.parent.parents[2];OLD=R.parent/'.p2s-integrated-pla-20261104';name='UPPER_INTEGRATED'
with zipfile.ZipFile(OLD/name/'geometry.3mf') as z:root=E.fromstring(z.read('3D/3dmodel.model'))
v=np.array([[float(x.attrib[k]) for k in ['x','y','z']] for x in root.findall('.//{*}vertex')]);f=np.array([[int(x.attrib[k]) for k in ['v1','v2','v3']] for x in root.findall('.//{*}triangle')])
oldmat=np.array(json.loads((O.parent/'integrated-pla-20261104/checks/UPPER_INTEGRATED_orientation.json').read_text())['matrix_design_to_print'])
m=trimesh.Trimesh(v,f,process=False);m.apply_transform(np.linalg.inv(oldmat));v=m.vertices
hull=v[ConvexHull(v).vertices];rng=np.random.default_rng(513)
ix=rng.choice(len(f),3000,p=m.area_faces/m.area);norm=m.face_normals[ix];cent=m.triangles_center[ix];lim=np.array([240,240,250])
def evaluate(x):
 rot=Rotation.from_euler('xyz',x,degrees=True).as_matrix();h=hull@rot.T;ext=np.ptp(h,axis=0)
 excess=np.maximum(ext/lim-1,0)
 nz=(norm@rot[2]);height=cent@rot[2]-h[:,2].min()
 score=np.mean(np.where(nz<-.574,-nz*height,0))
 return score+1e5*np.sum(excess)+1e5*np.sum(excess**2)
best=[]
for seed in [4,19,37]:
 res=differential_evolution(evaluate,[(0,360)]*3,seed=seed,popsize=14,maxiter=150,tol=1e-5)
 mat=Rotation.from_euler('xyz',res.x,degrees=True).as_matrix();ext=np.ptp(hull@mat.T,axis=0)
 if np.all(ext<=lim+.001):best.append((res.fun,res.x.tolist(),ext.tolist()))
 print(seed,res.fun,ext,flush=True)
assert best
best.sort();_,angles,ext=best[0];mat=np.eye(4);mat[:3,:3]=Rotation.from_euler('xyz',angles,degrees=True).as_matrix()
vv=v@mat[:3,:3].T;shift=np.r_[128,128,0]-np.r_[(vv.max(0)[:2]+vv.min(0)[:2])/2,vv[:,2].min()];vv+=shift;mat[:3,3]=shift
for node,xyz in zip(root.findall('.//{*}vertex'),vv):node.attrib.update(dict(zip(['x','y','z'],map(str,xyz))))
out=O/'source/r4_geometry';out.mkdir(exist_ok=True)
with zipfile.ZipFile(OLD/name/'geometry.3mf') as old,zipfile.ZipFile(out/f'{name}.3mf','w',zipfile.ZIP_DEFLATED) as z:
 for n in old.namelist():z.writestr(n,E.tostring(root,encoding='utf-8',xml_declaration=True) if n=='3D/3dmodel.model' else old.read(n))
(O/'checks/r4_orientation.json').write_text(json.dumps({'approximate_support_cost_candidates':best,'matrix_design_to_print':mat.tolist(),'mesh_extent_mm':ext,'scale':1,'geometry_change':'rigid rotation and translation only'},indent=2),encoding='utf8')
