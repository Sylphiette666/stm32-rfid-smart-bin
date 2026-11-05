"""Design, slice and package a PETG caster height spacer for the integrated lower body.

Measured basis (user, 2026-11-05): base-plate TOP plane -> wheel/ground contact ~70 mm.
Integrated H41 caster seat is at Z=-41; measured D05 caster total height 20 mm;
nominal top-plane -> ground = 5 (deck) + 41 + 20 = 66 mm (manual provenance 66.19).
=> required spacer H4 nominal; H3/H5 offered for measurement tolerance.
"""
from pathlib import Path
import json, zipfile, subprocess, hashlib, tempfile
import numpy as np
import trimesh
from shapely.geometry import box, Point
import xml.etree.ElementTree as E
from PIL import Image, ImageDraw

ROOT = Path(r'D:\Work\嵌入式课设')
W = ROOT / '.p2s-caster-spacer-petg-20261105'
CLI = Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
BASE = ROOT / '.p2s-petg-fast-20261104'
TEMPLATE = ROOT / 'stm32-rfid-smart-bin' / 'hardware' / 'mechanical' / 'print-backup' / 'labeled-bases-20261101' / 'geometry' / 'PLATE_3_GEOMETRY.3mf'
PKG = ROOT / '智能垃圾桶_万向轮增高垫块_PETG_20261105'
REPO = ROOT / 'stm32-rfid-smart-bin' / 'hardware' / 'mechanical' / 'print-backup' / 'caster-spacer-20261105'
VARIANTS = [('H3', 3.0), ('H4', 4.0), ('H5', 5.0)]

S = lambda p, d: p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))

machine = load(BASE / 'PANEL_COVER_L20' / 'machine.json')
filament = load(BASE / 'PANEL_COVER_L20' / 'filament.json')
process_base = load(BASE / 'PANEL_COVER_L20' / 'process.json')


def design_polygon():
    poly = box(-24, -8, 24, 8).buffer(4, resolution=32)
    # 40 mm hole pitch lies along the long (56 mm) axis: holes at x = -20 / +20, y = 0
    for x in (-20.0, 20.0):
        poly = poly.difference(Point(x, 0).buffer(1.7, resolution=32))
    return poly


def process_cfg(tag, t):
    p = dict(process_base)
    p.update({
        'name': f'SmartBin Caster Spacer R3D PETG {tag}',
        'layer_height': '0.2', 'initial_layer_print_height': '0.2',
        'wall_loops': '6',
        'sparse_infill_density': '45%', 'sparse_infill_pattern': 'gyroid',
        'top_shell_layers': '5', 'bottom_shell_layers': '5',
        'top_shell_thickness': '0.8', 'bottom_shell_thickness': '0.8',
        'enable_support': '0',
        'brim_type': 'outer_only', 'brim_width': '5', 'brim_object_gap': '0.1',
        'outer_wall_speed': '80', 'inner_wall_speed': '150',
        'sparse_infill_speed': '150', 'internal_solid_infill_speed': '150',
        'top_surface_speed': '80', 'initial_layer_speed': '25',
        'initial_layer_infill_speed': '40',
        'default_acceleration': '4000', 'outer_wall_acceleration': '1500',
        'top_surface_acceleration': '1500',
        'resolution': '0.01', 'enable_arc_fitting': '0',
    })
    return p


def write_geometry_3mf(mesh, name, path):
    ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    E.register_namespace('', ns)
    tag = lambda n: '{' + ns + '}' + n
    root = E.Element(tag('model'), {'unit': 'millimeter'})
    res = E.SubElement(root, tag('resources'))
    build = E.SubElement(root, tag('build'))
    ob = E.SubElement(res, tag('object'), {'id': '1', 'name': name, 'type': 'model'})
    me = E.SubElement(ob, tag('mesh'))
    vs = E.SubElement(me, tag('vertices'))
    ts = E.SubElement(me, tag('triangles'))
    for v in mesh.vertices:
        E.SubElement(vs, tag('vertex'), dict(zip(['x', 'y', 'z'], map(str, v))))
    for f in mesh.faces:
        E.SubElement(ts, tag('triangle'), dict(zip(['v1', 'v2', 'v3'], map(str, f))))
    E.SubElement(build, tag('item'), {'objectid': '1'})
    with zipfile.ZipFile(TEMPLATE) as tpl, zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in ['[Content_Types].xml', '_rels/.rels']:
            z.writestr(n, tpl.read(n))
        z.writestr('3D/3dmodel.model', E.tostring(root, encoding='utf-8', xml_declaration=True))


def run_cli(cmd, log_path):
    with log_path.open('w') as log:
        r = subprocess.run(cmd, cwd=str(CLI.parent), stdout=log, stderr=subprocess.STDOUT)
    return r.returncode, log_path.read_text(errors='replace')


def plan_preview(poly, path, t):
    sc = 12
    Wpx = int((56 + 16) * sc)
    Hpx = int((24 + 18) * sc)
    img = Image.new('RGB', (Wpx, Hpx), (245, 245, 245))
    d = ImageDraw.Draw(img)
    def pts(coords):
        return [(Wpx / 2 + (x - 0) * sc, Hpx / 2 - (y - 0) * sc) for x, y in coords]
    d.polygon(pts(poly.exterior.coords), fill=(200, 170, 255), outline=(60, 20, 140))
    for interior in poly.interiors:
        d.polygon(pts(interior.coords), fill=(245, 245, 245), outline=(60, 20, 140))
    d.text((8, 6), f'CASTER SPACER {t:g} mm  (56 x 24, holes d3.4 @ 40)', fill=(30, 30, 30))
    d.text((8, Hpx - 18), 'PETG / P2S 0.4 / 0.2 mm layers / 6 walls / 45% gyroid', fill=(30, 30, 30))
    img.save(path)


for tag, t in VARIANTS:
    work = W / tag
    work.mkdir(parents=True, exist_ok=True)
    poly = design_polygon()
    mesh = trimesh.creation.extrude_polygon(poly, t)
    mesh.apply_translation((128.0, 128.0, 0.0))
    assert mesh.is_watertight and mesh.is_winding_consistent
    vol, ext = mesh.volume, mesh.extents
    write_geometry_3mf(mesh, f'CASTER_SPACER_{tag}', work / 'geometry.3mf')
    cfg = process_cfg(tag, t)
    S(work / 'process.json', cfg)
    S(work / 'machine.json', machine)
    S(work / 'filament.json', filament)
    base_cmd = [str(CLI), '--datadir', str(work / 'isolated-data'),
                '--load-settings', str(work / 'machine.json') + ';' + str(work / 'process.json'),
                '--load-filaments', str(work / 'filament.json'),
                '--arrange', '0', '--orient', '0']
    cmd = base_cmd + ['--slice', '0', '--export-3mf', 'sliced.3mf', '--outputdir', str(work), '--debug', '2', str(work / 'geometry.3mf')]
    rc, log = run_cli(cmd, work / 'slice.log')
    assert rc == 0, log[-3000:]
    import shutil
    shutil.copyfile(work / 'result.json', work / 'slice_result.json')
    result = load(work / 'slice_result.json')
    plate = result['sliced_plates'][0]
    assert not plate['warning_message'], plate['warning_message']
    rec = {
        'tag': tag, 'thickness_mm': t,
        'design': {'length_mm': 56, 'width_mm': 24, 'corner_r_mm': 4,
                   'hole_d_mm': 3.4, 'hole_pitch_mm': 40,
                   'mount_pads_d_mm': 15, 'caster_seat_z_mm': -41},
        'mesh': {'watertight': True, 'winding_consistent': True,
                 'volume_mm3': round(vol, 2), 'bbox_mm': [round(float(x), 3) for x in ext],
                 'faces': int(len(mesh.faces))},
        'returncode': rc, 'process': cfg, 'filament': filament,
        'machine': machine.get('name'), 'result': plate,
        'physical_print_tested': False,
    }
    S(work / f'{tag}_slice.json', rec)

    # export native project (no gcode) exactly like the accepted pipeline
    cmd2 = list(base_cmd) + ['--export-3mf', 'project.3mf', '--outputdir', str(work), '--debug', '2', str(work / 'geometry.3mf')]
    rc2, log2 = run_cli(cmd2, work / 'export.log')
    assert rc2 == 0, log2[-3000:]
    proj = work / 'project.3mf'
    with zipfile.ZipFile(proj) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert not any(n.endswith('.gcode') for n in names), names
        embedded = json.loads(z.read('Metadata/project_settings.config').decode('utf-8'))
    assert embedded['layer_height'] == '0.2', embedded['layer_height']
    assert embedded['wall_loops'] == '6', embedded['wall_loops']
    assert embedded['sparse_infill_density'] == '45%', embedded['sparse_infill_density']
    assert embedded['top_shell_layers'] == '5'
    assert embedded['bottom_shell_layers'] == '5'
    assert embedded['enable_support'] == '0'
    assert embedded['filament_type'] == ['PETG'], embedded['filament_type']
    assert embedded['filament_vendor'] == ['R3D']
    assert embedded['nozzle_temperature'] == ['250']
    assert embedded['textured_plate_temp'] == ['60']
    assert embedded['filament_max_volumetric_speed'] == ['12']
    assert 'P2S' in embedded['printer_model']
    assert embedded['curr_bed_type'] == 'Textured PEI Plate', embedded.get('curr_bed_type')
    assert embedded['nozzle_diameter'] == ['0.4']
    rec['exported_project'] = {'file': f'P2S_CASTER_SPACER_{tag}_PETG.3mf',
                               'entries': len(names), 'embedded_layer_height': embedded['layer_height'],
                               'embedded_wall_loops': embedded['wall_loops'],
                               'embedded_infill': embedded['sparse_infill_density'],
                               'embedded_filament': embedded['filament_type'],
                               'no_gcode': True}
    S(work / f'{tag}_slice.json', rec)
    px = float(plate['total_predication']); pg = float(plate['filaments'][0]['total_used_g'])
    print(f'{tag} t={t:g}mm  {px/3600:.3f} h  {pg:.2f} g  layers? rc={rc}', flush=True)

print('ALL DESIGN/SLICE/EXPORT DONE', flush=True)
