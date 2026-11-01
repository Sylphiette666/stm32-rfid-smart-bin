"""Distribute eight unchanged remaining parts over four available P2S printers."""
from pathlib import Path
import copy
import hashlib
import json
import zipfile
import xml.etree.ElementTree as E
import numpy as np
import trimesh

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / 'body-after-accessories-20261101'
OUT = BASE / 'parallel-four-p2s-20261101'
for d in ['geometry', 'projects', 'checks']:
    (OUT / d).mkdir(parents=True, exist_ok=True)
NS = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
E.register_namespace('', NS['m'])
tag = lambda x: '{' + NS['m'] + '}' + x
objects = {}
for file in sorted((SOURCE / 'geometry').glob('*.3mf')):
    with zipfile.ZipFile(file) as z:
        root = E.fromstring(z.read('3D/3dmodel.model'))
        for obj in root.findall('m:resources/m:object', NS):
            assert obj.get('name') not in objects
            objects[obj.get('name')] = copy.deepcopy(obj)

# Print orientations, mesh topology and dimensions stay unchanged; XY only moves.
plans = {
    1: [('P01_REAR_HALF', None)],
    2: [('P01_FRONT_HALF', None)],
    3: [('P02_UPPER', None)],
    4: [('P03_STAND', (33, 35)), ('P07_SPEAKER_cradle', (35, 135)),
        ('JOIN_BRIDGE_1', (100, 130)), ('JOIN_BRIDGE_2', (160, 130)),
        ('JOIN_BRIDGE_3', (205, 130))],
}
assert sorted(n for plan in plans.values() for n, _ in plan) == sorted(objects)
reports = []
for job, items in plans.items():
    root = E.Element(tag('model'), {'unit': 'millimeter'})
    resources = E.SubElement(root, tag('resources'))
    build = E.SubElement(root, tag('build'))
    placements = []
    for ident, (name, xy) in enumerate(items, 1):
        obj = copy.deepcopy(objects[name])
        obj.set('id', str(ident))
        verts = obj.findall('m:mesh/m:vertices/m:vertex', NS)
        before = np.array([[float(v.get(k)) for k in ['x', 'y', 'z']] for v in verts])
        faces = np.array([[int(f.get(k)) for k in ['v1', 'v2', 'v3']]
                          for f in obj.findall('m:mesh/m:triangles/m:triangle', NS)])
        extent = np.ptp(before, axis=0)
        if xy is None:
            xy = (256 - extent[:2]) / 2
        shift = np.array([xy[0] - before[:, 0].min(), xy[1] - before[:, 1].min(), 0])
        after = before + shift
        assert np.allclose(np.ptp(after, axis=0), extent, atol=1e-7)
        assert abs(after[:, 2].min()) < 1e-7
        assert after[:, :2].min() >= 8 - 1e-6 and after[:, :2].max() <= 248 + 1e-6
        mesh = trimesh.Trimesh(vertices=after, faces=faces, process=False)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
        for element, point in zip(verts, after):
            for axis, value in zip(['x', 'y', 'z'], point):
                element.set(axis, f'{value:.8f}')
        resources.append(obj)
        E.SubElement(build, tag('item'), {'objectid': str(ident)})
        placements.append({'name': name, 'bounds_mm': [after.min(axis=0).tolist(), after.max(axis=0).tolist()],
                           'xy_translation_mm': shift[:2].tolist(), 'scale': 1,
                           'orientation_unchanged': True, 'faces_sha256': hashlib.sha256(faces.tobytes()).hexdigest()})
    for i, a in enumerate(placements):
        for b in placements[i+1:]:
            aa, bb = np.array(a['bounds_mm']), np.array(b['bounds_mm'])
            assert any(aa[1, k] + 10 < bb[0, k] or bb[1, k] + 10 < aa[0, k] for k in [0, 1]), (a, b)
    with zipfile.ZipFile(SOURCE / 'geometry/PLATE_1_GEOMETRY.3mf') as template:
        with zipfile.ZipFile(OUT / f'geometry/PLATE_{job}_GEOMETRY.3mf', 'w', zipfile.ZIP_DEFLATED) as z:
            for path in ['[Content_Types].xml', '_rels/.rels']:
                z.writestr(path, template.read(path))
            z.writestr('3D/3dmodel.model', E.tostring(root, encoding='utf-8', xml_declaration=True))
    reports.append({'plate': job, 'printer_label': job + 1, 'objects': len(items),
                    'names': [n for n, _ in items], 'placements': placements,
                    'all_objects_directly_on_bed': True, 'all_meshes_watertight': True,
                    'brim_mm': 5, 'aabb_separation_with_two_brims_checked': True})

fine = json.loads((BASE / 'accessories-fine-20261101/checks/removal.json').read_text(encoding='utf-8'))
fine_names = set(fine['remaining_names'])
assert not fine_names.intersection(objects) and len(fine_names | set(objects)) == 51
report = {'status': 'PASS', 'plates': reports, 'total_objects': 8, 'print_jobs': 4,
          'source': 'body-after-accessories-20261101/geometry',
          'only_xy_translation_and_redistribution': True, 'base_two_flat_halves': True,
          'upper_one_piece': True, 'fine_plate_43_parts_excluded': True, 'physical_print_test': False}
(OUT / 'checks/packing.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(OUT / 'checks/route_coverage.json').write_text(json.dumps({'status': 'PASS', 'running_fine_accessories': 43,
    'four_remaining_jobs': 8, 'total': 51, 'duplicates': [], 'all_remaining_parts_preserved': True}, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': 'PASS', 'jobs': 4, 'objects': 8, 'fine_plate_objects_excluded': 43}))
