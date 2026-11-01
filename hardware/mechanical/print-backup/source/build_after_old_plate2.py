"""Four free printers while yesterday's upper/stand/speaker plate is running."""
from pathlib import Path
import copy
import json
import shutil
import zipfile
import xml.etree.ElementTree as E
import numpy as np
import trimesh

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'parallel-after-old-plate2-20261101'
PREV = BASE / 'parallel-four-p2s-20261101'
for d in ['geometry', 'projects', 'checks']:
    (OUT / d).mkdir(parents=True, exist_ok=True)
NS = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
E.register_namespace('', NS['m'])
tag = lambda x: '{' + NS['m'] + '}' + x


def read(path):
    with zipfile.ZipFile(path) as z:
        root = E.fromstring(z.read('3D/3dmodel.model'))
    return {o.get('name'): o for o in root.findall('m:resources/m:object', NS)}


def mesh(obj):
    v = [[float(x.get(k)) for k in ['x', 'y', 'z']] for x in obj.findall('m:mesh/m:vertices/m:vertex', NS)]
    f = [[int(x.get(k)) for k in ['v1', 'v2', 'v3']] for x in obj.findall('m:mesh/m:triangles/m:triangle', NS)]
    m = trimesh.Trimesh(v, f, process=False)
    assert m.is_watertight and m.is_winding_consistent and m.volume > 0
    return m


running = read(BASE / 'mounted-20261031/geometry/PLATE_2_GEOMETRY.3mf')
assert set(running) == {'P02_UPPER', 'P03_STAND', 'P07_SPEAKER_cradle'}
fine = read(BASE / 'accessories-fine-20261101/geometry/PLATE_1_GEOMETRY.3mf')
assert len(fine) == 43 and not set(fine).intersection(running)
groups = {}
for name, obj in fine.items():
    group = name.split('_')[0] if name.startswith('M') else ('BAT' if name.startswith(('BAT', 'P05')) else name)
    g = groups.setdefault(group, {'names': [], 'volume_mm3': 0})
    g['names'].append(name)
    g['volume_mm3'] += mesh(obj).volume

# Three identical connection plates occupy an empty band of the original fine layout.
bridge = read(BASE / 'body-after-accessories-20261101/geometry/PLATE_2_GEOMETRY.3mf')['JOIN_BRIDGE_1']
for i, x in enumerate([48, 95, 142], 1):
    obj = copy.deepcopy(bridge)
    name = f'JOIN_BRIDGE_{i}'
    obj.set('name', name)
    m = mesh(obj)
    shift = np.array([x, 222, 0]) - m.bounds[0]
    for v in obj.findall('m:mesh/m:vertices/m:vertex', NS):
        for k, delta in zip(['x', 'y', 'z'], shift):
            v.set(k, f'{float(v.get(k))+delta:.8f}')
    candidate = mesh(obj)
    for old in fine.values():
        a, b = candidate.bounds, mesh(old).bounds
        assert any(a[1, k]+6 < b[0, k] or b[1, k]+6 < a[0, k] for k in [0, 1])
    fine[name] = obj
    groups[name] = {'names': [name], 'volume_mm3': candidate.volume}

# Keep each complete module clamp together and initially balance CAD volume.
allocation = {3: [], 4: []}
weights = {3: 0, 4: 0}
for group, data in sorted(groups.items(), key=lambda pair: -pair[1]['volume_mm3']):
    job = min(weights, key=weights.get)
    allocation[job].append(group)
    weights[job] += data['volume_mm3']

# Initial measured slicing was 4h25 vs 5h59. Move a complete clamp group to
# the faster job; volume alone underestimates thin-wall accessory print time.
allocation[4].remove('M07')
allocation[3].append('M07')
weights[4] -= groups['M07']['volume_mm3']
weights[3] += groups['M07']['volume_mm3']

reports = []
for job in [1, 2]:
    shutil.copy2(PREV / f'geometry/PLATE_{job}_GEOMETRY.3mf', OUT / f'geometry/PLATE_{job}_GEOMETRY.3mf')
    names = list(read(OUT / f'geometry/PLATE_{job}_GEOMETRY.3mf'))
    reports.append({'plate': job, 'printer_label': job+1, 'objects': 1, 'names': names,
                    'geometry_unchanged_from_checked_flat_half': True, 'layer_height': .24, 'brim_mm': 5})
for job, group_names in allocation.items():
    names = [n for g in group_names for n in groups[g]['names']]
    root = E.Element(tag('model'), {'unit': 'millimeter'})
    resources = E.SubElement(root, tag('resources'))
    build = E.SubElement(root, tag('build'))
    for i, name in enumerate(names, 1):
        obj = copy.deepcopy(fine[name]); obj.set('id', str(i))
        m = mesh(obj)
        assert abs(m.bounds[0, 2]) < 1e-5
        assert m.bounds[0, :2].min() >= 3.79 and m.bounds[1, :2].max() <= 252.11
        resources.append(obj)
        E.SubElement(build, tag('item'), {'objectid': str(i)})
    with zipfile.ZipFile(OUT / 'geometry/PLATE_1_GEOMETRY.3mf') as template:
        with zipfile.ZipFile(OUT / f'geometry/PLATE_{job}_GEOMETRY.3mf', 'w', zipfile.ZIP_DEFLATED) as z:
            for p in ['[Content_Types].xml', '_rels/.rels']:
                z.writestr(p, template.read(p))
            z.writestr('3D/3dmodel.model', E.tostring(root, encoding='utf-8', xml_declaration=True))
    reports.append({'plate': job, 'printer_label': job+1, 'objects': len(names), 'names': names,
                    'module_groups': group_names, 'volume_mm3': weights[job],
                    'old_accessory_geometry_and_positions_unchanged': True, 'layer_height': .16, 'brim_mm': 3})

all_names = [n for p in reports for n in p['names']]
assert len(all_names) == len(set(all_names)) == 48
assert not set(all_names).intersection(running)
full = set()
for i in [1, 2, 3]:
    full.update(read(BASE / f'flat-split-20261101/geometry/PLATE_{i}_GEOMETRY.3mf'))
assert set(all_names) | set(running) == full and len(full) == 51
for name, payload in [
    ('packing.json', {'status': 'PASS', 'plates': reports, 'total_objects': 48, 'print_jobs': 4,
                      'running_old_plate2_excluded': sorted(running), 'physical_print_test': False}),
    ('route_coverage.json', {'status': 'PASS', 'running_project': 'mounted-20261031/projects/P2S_MOUNTED_PLATE_2.3mf',
                            'running_names': sorted(running), 'running_objects': 3, 'remaining_objects': 48,
                            'total': 51, 'duplicates': [], 'matches_full_flat_release': True})]:
    (OUT / 'checks' / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': 'PASS', 'running': sorted(running), 'remaining':48, 'allocation':allocation, 'volumes':weights}, ensure_ascii=False))
