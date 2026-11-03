from pathlib import Path
import cadquery as cq,vtk
O=Path(__file__).resolve().parents[1]
for name in ['LOWER_H41_B1','UPPER_INTEGRATED']:
 s=cq.importers.importStep(str(O/'step'/f'{name}.step')).val();v,f=s.tessellate(.12,.12)
 pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
 for p in v:pts.InsertNextPoint(p.x,p.y,p.z)
 for face in f:
  t=vtk.vtkTriangle()
  for j,n in enumerate(face):t.GetPointIds().SetId(j,n)
  cells.InsertNextCell(t)
 data=vtk.vtkPolyData();data.SetPoints(pts);data.SetPolys(cells)
 normals=vtk.vtkPolyDataNormals();normals.SetInputData(data);normals.SetFeatureAngle(35)
 mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort());actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(.46,.66,.75)
 b=s.BoundingBox();c=((b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2)
 for label,pos in [('iso',(430,-390,380)),('bottom',(400,-390,-350))]:
  ren=vtk.vtkRenderer();ren.SetBackground(1,1,1);ren.AddActor(actor);cam=ren.GetActiveCamera();cam.SetPosition(*pos);cam.SetFocalPoint(*c);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(190)
  win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1200,950);win.AddRenderer(ren);win.Render()
  flt=vtk.vtkWindowToImageFilter();flt.SetInput(win);flt.Update();w=vtk.vtkPNGWriter();w.SetFileName(str(O/'preview'/f'{name}_{label}.png'));w.SetInputConnection(flt.GetOutputPort());w.Write();win.Finalize()
print('rendered')
