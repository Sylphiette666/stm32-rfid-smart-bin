"""Reconstruct native 3MF component transforms; compare all four meshes to checked STL."""
from pathlib import Path
import json,posixpath,zipfile,xml.etree.ElementTree as E
import numpy as np
import trimesh
from scipy.spatial import cKDTree
B=Path(__file__).resolve().parents[1];O=B/'sensor-retainers-fix-20261103';load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));s=load(O/'checks/slicing.json');layout=load(O/'source/layout.json')['objects'];ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
def matrix(value):
    if not value:return np.eye(4)
    nums=np.array(list(map(float,value.split()))).reshape(4,3);out=np.eye(4);out[:3,:3]=nums[:3,:].T;out[:3,3]=nums[3,:];return out
with zipfile.ZipFile(O/s['project']) as z:
    cache={}
    def root(path):
        if path not in cache:cache[path]=E.fromstring(z.read(path))
        return cache[path]
    def vertices(path,oid,t):
        ob=next(o for o in root(path).findall('m:resources/m:object',ns) if o.attrib['id']==oid);mesh=ob.find('m:mesh',ns)
        if mesh is not None:
            vs=np.array([[float(v.attrib[k]) for k in ['x','y','z']] for v in mesh.findall('m:vertices/m:vertex',ns)]);return [vs@t[:3,:3].T+t[:3,3]]
        out=[]
        for c in ob.findall('m:components/m:component',ns):
            cp=next((v for k,v in c.attrib.items() if k.endswith('}path')),path);cp=cp.lstrip('/') if cp.startswith('/') else (path if cp==path else posixpath.normpath(posixpath.join(posixpath.dirname(path),cp)));out+=vertices(cp,c.attrib['objectid'],t@matrix(c.attrib.get('transform')))
        return out
    items=root('3D/3dmodel.model').findall('m:build/m:item',ns);assert len(items)==len(layout)==4;report=[]
    for item,v in zip(items,layout):
        actual=np.vstack(vertices('3D/3dmodel.model',item.attrib['objectid'],matrix(item.attrib.get('transform'))));n=v['name'];expected=trimesh.load_mesh(O/'parts'/(n+'_PRINT.stl')).vertices+[*v['offset_xy'],0]
        distance=max(cKDTree(actual).query(expected)[0].max(),cKDTree(expected).query(actual)[0].max());assert distance<5e-5,(n,distance)
        assert abs(actual[:,2].min())<1e-5,(n,'not on bed');report.append({'name':n,'bidirectional_vertex_error_mm':float(distance),'on_bed':True,'scale_and_orientation_match':True})
result={'status':'PASS_NATIVE_ROUNDTRIP','objects':report,'max_allowed_roundtrip_error_mm':5e-5,'all_objects_verified':4,'not_a_physical_tolerance_claim':True};(O/'checks/native_geometry.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(result))
