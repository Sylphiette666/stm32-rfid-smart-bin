"""Conservative top-pocket lightening; retain interfaces and explicit full-height load paths."""
from pathlib import Path
import json,math,csv,hashlib
import cadquery as cq
import trimesh
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
B=Path(__file__).resolve().parents[1];R=B.parents[2]
BASE=B/'motor-existing-holes-20261102';O=B/'motor-existing-holes-light-20261103'
for p in ['parts','step','checks','preview','source']:(O/p).mkdir(parents=True,exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def prism(poly,z,height):
    work=cq.Workplane('XY').polyline(list(poly.exterior.coords)[:-1]).close()
    for ring in poly.interiors:work=work.polyline(list(ring.coords)[:-1]).close()
    return work.extrude(height).translate((0,0,z)).val()
d=load(BASE/'checks/design.json');new=json.loads(json.dumps(d));records=[];contours=[]
links={'LEFT':[(0,0),(1,0),(2,1),(3,3),(4,1)],'RIGHT':[(0,0),(1,2),(2,3),(3,2)]}
for name,v in d['variants'].items():
    original=cq.importers.importStep(str(BASE/'step'/f'D06_CARRIER_{name}_ASSEMBLY.step')).val().translate((0,0,16))
    outline=Polygon(v['outline']);anchors=[x['xy'] for x in v['anchors']];seat=v['seat_connection_holes']
    protected=[outline.boundary.buffer(4,resolution=12)]+[Point(*p).buffer(8,resolution=12) for p in anchors+seat]
    protected += [Point(*p['xy']).buffer(5.5,resolution=12) for p in v['top_reliefs']]
    protected += [LineString([anchors[i],seat[j]]).buffer(5.5,resolution=12) for i,j in links[name]]
    cx=sum(p[0] for p in seat)/4;cy=sum(p[1] for p in seat)/4
    ring=sorted(seat,key=lambda p:math.atan2(p[1]-cy,p[0]-cx))
    protected.append(LineString(ring+[ring[0]]).buffer(5,resolution=12))
    if name=='RIGHT':protected.append(LineString([anchors[1],anchors[3]]).buffer(4,resolution=12))
    for p in v['splice_clearance_recesses']:
        x,y=p['centre'];protected.append(Polygon([(x-21,y-13),(x+21,y-13),(x+21,y+13),(x-21,y+13)]))
    keep=unary_union(protected).intersection(outline)
    cut=outline.difference(keep).buffer(-2.1,resolution=8).buffer(2,resolution=8)
    pockets=[p for p in (list(cut.geoms) if hasattr(cut,'geoms') else [cut]) if p.area>=35]
    result=original;entries=[]
    for i,p in enumerate(pockets,1):
        result=result.cut(prism(p,5,12))
        x0,y0,x1,y1=p.bounds;entry={'id':f'{name[0]}P{i}','bounds_mm':[x0,y0,x1,y1],'depth_from_top_mm':11,'floor_z_mm':5,'area_mm2':p.area,'nominal_corner_round_mm':2,'outline_xy':[list(q) for q in list(p.exterior.coords)[:-1]],'protected_island_rings_xy':[[list(q) for q in list(r.coords)[:-1]] for r in p.interiors]};entries.append(entry)
        records.append({'part':name,'pocket':entry['id'],'X_min_mm':x0,'yb_min_mm':y0,'X_max_mm':x1,'yb_max_mm':y1,'depth_mm':11,'remaining_floor_mm':5,'corner_round_mm':2})
        for ring_id,ring in enumerate([entry['outline_xy']]+entry['protected_island_rings_xy']):
            for j,(x,y) in enumerate(ring):contours.append({'part':name,'pocket':entry['id'],'ring':ring_id,'vertex':j,'X_mm':x,'yb_mm':y})
    result=result.clean();assert result.isValid() and len(result.Solids())==1
    # No material has been added or removed from bolt pads, load ribs, original hardware recesses, or the lower 5mm layer.
    assert result.cut(original).Volume()<1e-5
    for p in protected:
        inside=p.intersection(outline)
        pieces=list(inside.geoms) if hasattr(inside,'geoms') else [inside]
        for q in pieces:
            if not isinstance(q,Polygon) or q.area<1e-6:continue
            zone=prism(q,0,16).intersect(original)
            missing=zone.cut(result).Volume()
            assert missing<1e-4,(name,'protected material removed',missing)
    bottom=cq.Workplane('XY').box(400,300,5,centered=False).val().intersect(original)
    assert bottom.cut(result).Volume()<1e-5
    assert all(p.distance(outline.boundary)>=4-1e-5 for p in pockets)
    for xy in anchors+seat:
        bore=cq.Solid.makeCylinder(1.6999,18,cq.Vector(*xy,-1));assert bore.intersect(result).Volume()<1e-6
    cq.exporters.export(result.translate((0,0,-16)),str(O/'step'/f'D06_CARRIER_{name}_ASSEMBLY.step'))
    oldseat=cq.importers.importStep(str(BASE/'step'/f'D06_SEAT_{name}_ASSEMBLY.step')).val()
    cq.exporters.export(cq.Compound.makeCompound([result.translate((0,0,-16)),oldseat]),str(O/'step'/f'D06_STACK_{name}_ASSEMBLY.step'))
    bb=result.BoundingBox();flat=result.translate((-bb.xmin,-bb.ymin,-bb.zmin));cq.exporters.export(flat,str(O/'parts'/f'D06_CARRIER_{name}_PRINT.stl'),tolerance=.025,angularTolerance=.05)
    m=trimesh.load_mesh(O/'parts'/f'D06_CARRIER_{name}_PRINT.stl');m.merge_vertices(digits_vertex=5)
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
    re=cq.importers.importStep(str(O/'step'/f'D06_CARRIER_{name}_ASSEMBLY.step')).val()
    assert re.isValid() and abs(re.Volume()-result.Volume())<1e-3
    for j,x in enumerate(m.extents):assert abs(x-v['print_extents'][j])<.05
    new['variants'][name].update(pockets=entries,baseline_volume_mm3=original.Volume(),volume_mm3=result.Volume(),removed_volume_mm3=original.Volume()-result.Volume(),volume_reduction_percent=100*(1-result.Volume()/original.Volume()),print_extents=m.extents.tolist(),protected_load_paths_preserved=True,lower_5mm_original_material_preserved=True)
    print(name,'pockets',len(pockets),'volume reduction',round(100*(1-result.Volume()/original.Volume()),2),'%',flush=True)
new.update(status='LIGHTENED_GEOMETRY_CHECKED_PHYSICAL_STRENGTH_PENDING',lightening_floor_mm=5,primary_rib_width_mm=11,secondary_rib_width_mm=8,perimeter_width_mm=4,bolt_pad_radius_mm=8,load_rib_height_mm=16,lightening_pocket_depth_mm=11,physical_load_tested=False,lightweight_equal_strength_claimed=False,baseline_directory=BASE.name)
new['total_volume_reduction_percent']=100*(1-sum(v['volume_mm3'] for v in new['variants'].values())/sum(v['volume_mm3'] for v in d['variants'].values()))
new['strength_basis']='Full 16mm bolt pads and direct load ribs retained; 5mm original lower material retained; no rated load or equal-to-solid strength claim without physical validation'
save(O/'checks/design.json',new)
save(O/'source/design_plan.json',{'requirement':'Lightweight existing-hole carriers while retaining load paths and all interfaces','strategy':'Top-open rounded blind pockets; retain 5mm lower layer and 16mm high ribs/pads','unchanged':['9 existing chassis anchors','8 seat attachment holes','16mm carrier height','all old hardware clearances','old motor seats','fasteners'],'validation':['Exact protected-material boolean difference','STEP reimport','closed mesh','actual slicing comparison','four-view visual review','same-name manual update'],'limitations':['No rated payload requested','No physical strength or durability test','Not certified equal strength to original solid plate']})
for filename,rows in [('pocket_bounds.csv',records),('pocket_contours.csv',contours)]:
    with (O/'source'/filename).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
print('Total CAD volume reduction',round(new['total_volume_reduction_percent'],2),'%',flush=True)
