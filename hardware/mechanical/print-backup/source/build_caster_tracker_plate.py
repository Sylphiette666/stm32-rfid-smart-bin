"""Pack the existing H41 caster and tracker printable meshes on one P2S plate."""
from pathlib import Path
import json
import zipfile
import xml.etree.ElementTree as ET

import trimesh

B = Path(__file__).resolve().parents[1]
O = B / 'caster-tracker-plate-20261103'
O.mkdir(exist_ok=True)
parts = [
    ('CASTER_FRAME', B/'caster-riser-20261103/parts/CASTER_FRAME_PRINT.stl', 20, 70),
    ('TRACKER_FRAME', B/'tracker-mount-20261103/parts/TRACKER_FRAME_PRINT.stl', 95, 70),
    ('CASTER_COLUMN_A_H41', B/'caster-riser-20261103/parts/CASTER_COLUMN_41_PRINT.stl', 165, 70),
    ('CASTER_COLUMN_B_H41', B/'caster-riser-20261103/parts/CASTER_COLUMN_41_PRINT.stl', 195, 70),
]
for j, h in enumerate((14, 18, 22)):
    for k, suffix in enumerate(('A', 'B')):
        parts.append((f'TRACKER_SPACER_{h}_{suffix}', B/f'tracker-mount-20261103/parts/SPACER_{h}_PRINT.stl', 165+30*j, 105+30*k))

meshes = []
boxes = []
for name, path, x, y in parts:
    mesh = trimesh.load_mesh(path)
    assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split()) == 1, name
    mesh.apply_translation((x-mesh.bounds[0, 0], y-mesh.bounds[0, 1], -mesh.bounds[0, 2]))
    box = [float(mesh.bounds[0, 0]), float(mesh.bounds[0, 1]), float(mesh.bounds[1, 0]), float(mesh.bounds[1, 1])]
    assert min(box[:2]) >= 10 and max(box[2:]) <= 246, (name, box)
    for other_name, other in boxes:
        dx = max(other[0]-box[2], box[0]-other[2], 0)
        dy = max(other[1]-box[3], box[1]-other[3], 0)
        assert (dx*dx+dy*dy)**0.5 >= 10.2, (name, other_name, box, other)
    boxes.append((name, box))
    meshes.append((name, mesh))

ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('', ns)
tag = lambda n: '{'+ns+'}'+n
root = ET.Element(tag('model'), {'unit': 'millimeter'})
resources = ET.SubElement(root, tag('resources'))
build = ET.SubElement(root, tag('build'))
for i, (name, mesh) in enumerate(meshes, 1):
    obj = ET.SubElement(resources, tag('object'), {'id': str(i), 'name': name, 'type': 'model'})
    shape = ET.SubElement(obj, tag('mesh'))
    verts = ET.SubElement(shape, tag('vertices'))
    tris = ET.SubElement(shape, tag('triangles'))
    for vertex in mesh.vertices:
        ET.SubElement(verts, tag('vertex'), dict(zip(('x', 'y', 'z'), map(str, vertex))))
    for face in mesh.faces:
        ET.SubElement(tris, tag('triangle'), dict(zip(('v1', 'v2', 'v3'), map(str, face))))
    ET.SubElement(build, tag('item'), {'objectid': str(i)})

out = O/'CASTER_H41_TRACKER_ALL_GEOMETRY.3mf'
template = B/'flat-split-20261101/geometry/PLATE_3_GEOMETRY.3mf'
with zipfile.ZipFile(template) as source, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as target:
    for member in ('[Content_Types].xml', '_rels/.rels'):
        target.writestr(member, source.read(member))
    target.writestr('3D/3dmodel.model', ET.tostring(root, encoding='utf-8', xml_declaration=True))

report = {'status': 'CAD_GEOMETRY_CHECKED', 'source_parts': [name for name, _ in meshes],
          'object_count': len(meshes), 'plate_size_mm': [256, 256], 'bounds_xy_mm': boxes,
          'minimum_clearance_mm': 10.2, 'print_orientations_preserved': True,
          'same_height_tracker_spacer_pairs_mm': [14, 18, 22], 'physical_print_tested': False}
(O/'geometry_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(out)
