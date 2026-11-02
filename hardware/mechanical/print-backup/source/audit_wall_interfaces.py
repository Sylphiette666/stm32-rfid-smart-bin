"""Exact BRep intersection audit and true-mesh assembly previews (no physical fit claim)."""
from pathlib import Path
import json, itertools
import cadquery as cq
import numpy as np
import trimesh, vtk

B=Path(__file__).resolve().parents[1];O=B/'wall-panels-20261102'
d=json.loads((O/'checks/design.json').read_text(encoding='utf-8'))
walls={
 'W01_FRONT':[[0,0,1,157],[1,0,0,3],[0,1,0,0],[0,0,0,1]],
 'W02_REAR':[[0,0,-1,3],[-1,0,0,147],[0,1,0,0],[0,0,0,1]],
 'W03_LEFT':[[1,0,0,0],[0,0,-1,3],[0,1,0,0],[0,0,0,1]],
 'W04_RIGHT':[[-1,0,0,160],[0,0,1,147],[0,1,0,0],[0,0,0,1]]}
shapes={};meshes={};assembly=[]
for name in d['parts']:
 s=cq.importers.importStep(str(O/'step'/f'{name}.step')).val();shapes[name]=s
 bb=s.BoundingBox();m=trimesh.load_mesh(O/'parts'/f'{name}.stl');m.apply_translation([bb.xmin,bb.ymin,bb.zmin]);meshes[name]=m

def put(name,mat,label=None):
 mat=np.array(mat,dtype=float)
 s=shapes[name].transformGeometry(cq.Matrix(mat.tolist()))
 m=meshes[name].copy();m.apply_transform(mat)
 assembly.append((label or name,s,m,mat))
for n,m in walls.items():put(n,m)
covermat=np.array([[0,0,-1,219.4],[-1,0,0,147],[0,1,0,45],[0,0,0,1]])
put('PANEL_COVER',covermat)
def coverpart(name,origin,flip=(1,1,1),label=None):
 m=np.eye(4);m[:3,:3]=np.diag(flip);m[:3,3]=origin;put(name,covermat@m,label)
coverpart('ENCODER_PIN_HOOD',[40,46,-25])
for i,cx in enumerate([96,122]):
 coverpart('BUTTON_CARRIER',[cx-12,44.5,16.6],(1,1,-1),f'BUTTON_CARRIER_{i}')
 coverpart('BUTTON_RETAINER',[cx-12,44.5,12.6],(1,1,-1),f'BUTTON_RETAINER_{i}')
 for xx in [cx-10,cx+10]:coverpart('BUTTON_SPACER',[xx-3,54,2.4],label=f'BUTTON_SPACER_{xx}')
for x,flip in [(7,(1,1,1)),(82,(-1,1,1))]:
 coverpart('RFID_EDGE_RAIL',[x,7,2.4],flip,f'RFID_EDGE_RAIL_{x}')
 coverpart('RFID_RETAINER',[x,7,8.4],flip,f'RFID_RETAINER_{x}')
for i,r in enumerate(d['sensor_instances']):
 mat=np.eye(4)
 if 'world_origin'in r:
  mat[:3,:3]=r['world_matrix'];mat[:3,3]=r['world_origin']
 else:
  mat[:3,:3]=r.get('matrix',np.eye(3));mat[:3,3]=r['origin'];mat=np.array(walls[r['wall']])@mat
 put(r['name'],mat,f"{r['name']}_{i}")
for z in [16,152]:
 for x,sx in [(148,1),(12,-1)]:
  for y,sy in [(-3,1),(153,-1)]:put('CORNER_ANGLE',[[sx,0,0,x],[0,sy,0,y],[0,0,1,z],[0,0,0,1]],f'CORNER_{x}_{y}_{z}')

collisions=[];checked=0
for a,b in itertools.combinations(assembly,2):
 ba,bb=a[1].BoundingBox(),b[1].BoundingBox()
 if any(min(getattr(ba,k+'max'),getattr(bb,k+'max'))-max(getattr(ba,k+'min'),getattr(bb,k+'min'))<1e-5 for k in 'xyz'):continue
 checked+=1;v=a[1].intersect(b[1]).Volume()
 if v>.05:collisions.append(dict(a=a[0],b=b[0],intersection_mm3=v))

def render(items,path,camera):
 r=vtk.vtkRenderer();r.SetBackground(1,1,1)
 for name,s,m,mat in items:
  pts=vtk.vtkPoints();polys=vtk.vtkCellArray()
  for v in m.vertices:pts.InsertNextPoint(*v)
  for f in m.faces:
   t=vtk.vtkTriangle()
   for j,k in enumerate(f):t.GetPointIds().SetId(j,int(k))
   polys.InsertNextCell(t)
  pd=vtk.vtkPolyData();pd.SetPoints(pts);pd.SetPolys(polys);mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(pd)
  actor=vtk.vtkActor();actor.SetMapper(mapper)
  actor.GetProperty().SetColor(*((.28,.57,.67) if name.startswith('W0') else (.88,.63,.30)))
  actor.GetProperty().SetAmbient(.3);r.AddActor(actor)
 c=r.GetActiveCamera();c.SetPosition(*camera);c.SetFocalPoint(95,75,90);c.SetViewUp(0,0,1);c.ParallelProjectionOn();r.ResetCamera()
 w=vtk.vtkRenderWindow();w.SetOffScreenRendering(1);w.SetSize(1500,1150);w.AddRenderer(r);w.Render()
 im=vtk.vtkWindowToImageFilter();im.SetInput(w);im.Update();wr=vtk.vtkPNGWriter();wr.SetFileName(str(path));wr.SetInputConnection(im.GetOutputPort());wr.Write();w.Finalize()
render(assembly,O/'preview/complete_assembly_front.png',(480,-420,330))
render(assembly,O/'preview/complete_assembly_rear.png',(-300,-380,360))
render([a for a in assembly if a[0] not in ['W01_FRONT','PANEL_COVER','W03_LEFT']],O/'preview/interior_cutaway.png',(470,-450,380))

# Existing upper platform, correct face UP. Verify footprint of bare-bin floor.
upper=cq.importers.importStep(str(B/'step/P02_light.step')).val()
floor=cq.Workplane('XY').box(154,144,.1,centered=False).translate((53,23,4.9)).val()
void=floor.cut(upper).Volume()
out=dict(status='PASS_GEOMETRY_ONLY' if not collisions and void<1e-5 else 'FAIL',
 intersection_pairs_evaluated=checked,collisions=collisions,
 assembly_instances=len(assembly),bare_floor_void_mm3=void,
 caveats=['No screws or real electronic components included in exact collision test.',
 'Moving lid and servo swept envelope still require physical dry fit.',
 'Print and sensor performance are not certified by this digital audit.'])
(O/'checks/assembly_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
