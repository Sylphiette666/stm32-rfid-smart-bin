# -*- coding: utf-8 -*-
"""Build a Bambu Studio project with ONLY the 31 module accessories
(9 lids + 9 detents + 9 keepers + BAT_L/R detent+keeper) on the P2S at 0.16 mm.

The 31 parts are lifted out of the existing print plate
mounted-20261031/projects/P2S_MOUNTED_PLATE_1.3mf (44 objects) by byte-level
editing (ElementTree re-serialisation breaks BambuStudio's p: prefix lookup).
Obsolete bodies / P01 / P04 / P05 / P06 are dropped.
"""
from pathlib import Path
import json, re, shutil, subprocess, zipfile
import xml.etree.ElementTree as ET

W = Path(r'D:\Work\嵌入式课设\.p2s-accessory-plate-20261105')
OUT = W / 'checks'
PROJ = W / 'project'
for d in (OUT, PROJ, W / 'preview', W / 'slice'):
    d.mkdir(parents=True, exist_ok=True)

REPO = Path(r'D:\Work\嵌入式课设\stm32-rfid-smart-bin\hardware\mechanical\print-backup')
SRC_3MF = REPO / 'mounted-20261031' / 'projects' / 'P2S_MOUNTED_PLATE_1.3mf'
CLI = Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
PROFILES = CLI.parent / 'resources' / 'profiles' / 'BBL'
NS_P = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
NS_M = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'

KEEP = []
for m in range(1, 10):
    KEEP += ['M%02d_lid' % m, 'M%02d_detent' % m, 'M%02d_keeper' % m]
KEEP += ['BAT_L_detent', 'BAT_L_keeper', 'BAT_R_detent', 'BAT_R_keeper']
assert len(KEEP) == 31


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def save(p, d):
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')


# ------------------------------------------------------- 1) filter the plate
zin = zipfile.ZipFile(SRC_3MF)
entries = {n: zin.read(n) for n in zin.namelist()}

ms_txt = entries['Metadata/model_settings.config'].decode('utf-8')
names = dict(re.findall(r'<object id="(\d+)">\s*<metadata key="name" value="([^"]*)"', ms_txt))
assert len(names) == 44, len(names)
drop = {oid for oid, nm in names.items() if nm not in KEEP}
toks = '|'.join(sorted(drop))
assert len(drop) == 13

mx = entries['3D/3dmodel.model'].decode('utf-8')
mx = re.sub(r'\s*<item objectid="(?:%s)"[^>]*/>' % toks, '', mx)
mx = re.sub(r'\s*<object id="(?:%s)"[^>]*>.*?</object>' % toks, '', mx, flags=re.S)
ms_txt = re.sub(r'\s*<object id="(?:%s)">.*?</object>' % toks, '', ms_txt, flags=re.S)
entries['3D/3dmodel.model'] = mx.encode('utf-8')
entries['Metadata/model_settings.config'] = ms_txt.encode('utf-8')

# keep only mesh files still referenced by a component
refs = set(p.lstrip('/') for p in re.findall(r'<component[^>]*p:path="([^"]+)"', mx))
stale = [n for n in entries if n.startswith('3D/Objects/') and n not in refs]
for n in stale:
    entries.pop(n)
rels_n = '3D/_rels/3dmodel.model.rels'
rels = entries[rels_n].decode('utf-8')
for n in stale:
    rels = re.sub(r'\s*<Relationship[^>]*Target="/%s"[^>]*/>' % re.escape(n), '', rels)
entries[rels_n] = rels.encode('utf-8')

geom = W / 'accessories_31.3mf'
with zipfile.ZipFile(geom, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, data in entries.items():
        zo.writestr(n, data)

with zipfile.ZipFile(geom) as z:
    assert z.testzip() is None
    mr = ET.fromstring(z.read('3D/3dmodel.model'))
    n_items = len(mr.findall('.//{%s}item' % NS_M))
    n_objs = len(mr.findall('.//{%s}object' % NS_M))
    mset = z.read('Metadata/model_settings.config').decode('utf-8')
kept_names = sorted(set(re.findall(r'key="name" value="([^"]*)"', mset)))
print('filtered: objects=%d items=%d dropped=%d stale_files_removed=%d size=%d'
      % (n_objs, n_items, len(drop), len(stale), geom.stat().st_size))
assert n_items == 31 and n_objs == 31
for k in KEEP:
    assert kept_names.count(k) >= 1, k

# ------------------------------------------------------------- 2) settings
index = {}
for f in PROFILES.rglob('*.json'):
    try:
        d = json.loads(f.read_text(encoding='utf-8-sig'))
        if isinstance(d, dict) and d.get('name'):
            index[d['name']] = d
    except (ValueError, UnicodeDecodeError):
        pass


def resolve(name, seen=()):
    if name in seen:
        raise ValueError(name)
    d = index[name]
    out = {}
    if d.get('inherits'):
        out.update(resolve(d['inherits'], seen + (name,)))
    for inc in d.get('include', []):
        out.update(resolve(inc, seen + (name,)))
    out.update(d)
    out.pop('inherits', None)
    out.pop('include', None)
    return out


machine = resolve('Bambu Lab P2S 0.4 nozzle')
proc = resolve('0.16mm Standard @BBL P2S')
fil = resolve('Generic PLA @BBL P2S')

machine['curr_bed_type'] = 'Textured PEI Plate'
proc.update({
    'name': 'SmartBin PLA Accessories 31pcs 0.16 P2S',
    'layer_height': '0.16',
    'initial_layer_print_height': '0.2',
    'print_sequence': 'by layer',
    'wall_loops': '4',
    'sparse_infill_density': '30%',
    'sparse_infill_pattern': 'gyroid',
    'top_shell_layers': '6',
    'bottom_shell_layers': '4',
    'top_shell_thickness': '0.8',
    'bottom_shell_thickness': '0.64',
    'enable_support': '0',
    'brim_type': 'outer_only',
    'brim_width': '4',
    'brim_object_gap': '0.1',
    'skirt_loops': '0',
    'outer_wall_speed': ['60', '60', '60'],
    'inner_wall_speed': ['120', '120', '120'],
    'default_acceleration': ['3000', '3000', '3000'],
    'outer_wall_acceleration': ['1500', '1500', '1500'],
    'travel_speed': ['500', '500', '500'],
})
work = W / 'slice'
for d in (work / 'isolated-data',):
    d.mkdir(parents=True, exist_ok=True)
save(work / 'machine.json', machine)
save(work / 'process.json', proc)
save(work / 'filament.json', fil)
shutil.copy2(geom, work / 'geometry.3mf')

# ---------------------------------------------------------------- 3) slice
cmd = [str(CLI), '--datadir', str(work / 'isolated-data'),
       '--load-settings', str(work / 'machine.json') + ';' + str(work / 'process.json'),
       '--load-filaments', str(work / 'filament.json'),
       '--arrange', '1', '--orient', '0', '--slice', '0',
       '--export-3mf', 'sliced.3mf', '--outputdir', str(work),
       '--debug', '2', str(work / 'geometry.3mf')]
save(W / 'slice_command.json', cmd)
print('slice start', flush=True)
with (work / 'slice.log').open('w', encoding='utf-8', errors='replace') as log:
    rc = subprocess.run(cmd, cwd=str(CLI.parent), stdout=log, stderr=subprocess.STDOUT).returncode
log_txt = (work / 'slice.log').read_text(encoding='utf-8', errors='replace')
print('slice rc=%s' % rc, flush=True)
if rc != 0:
    print(log_txt[-4000:])
    raise SystemExit(1)

rec = {'date': '2026-11-05', 'returncode': rc, 'layer_height': 0.16, 'filament': 'PLA',
       'parts': 31, 'physical_print_tested': False,
       'process_base': '0.16mm Standard @BBL P2S, walls 4, 30% gyroid, top6/bottom4, no support, 4mm brim'}
res = load(work / 'result.json')
plate = res['sliced_plates'][0]
rec['total_predication_s'] = plate['total_predication']
rec['grams'] = sum(f['total_used_g'] for f in plate['filaments'])
rec['warning_message'] = plate['warning_message']
rec['result'] = res

with zipfile.ZipFile(work / 'sliced.3mf') as z:
    zn = z.namelist()
    png = [n for n in zn if n.endswith('plate_1.png')]
    if png:
        (W / 'preview' / 'accessories_31_plate.png').write_bytes(z.read(png[0]))
    cfg = z.read('Metadata/project_settings.config').decode('utf-8', 'replace')
    rec['config_ok'] = all(s in cfg for s in ('"filament_type": ["PLA"', '"layer_height": "0.16"',
                                              'Bambu Lab P2S', 'Textured PEI Plate',
                                              '"wall_loops": "4"', '"enable_support": "0"'))
    rec['sliced_has_gcode'] = any(n.endswith('.gcode') for n in zn)
print('time=%.4f h (%.0f s)  grams=%.3f  warn=%r  config_ok=%s  has_gcode=%s'
      % (rec['total_predication_s'] / 3600, rec['total_predication_s'], rec['grams'],
         rec['warning_message'], rec['config_ok'], rec['sliced_has_gcode']), flush=True)
save(OUT / 'accessories_plate_slicing.json', rec)

# ------------------------------------------------- 4) export project 3mf
cmd2 = [str(CLI), '--datadir', str(work / 'isolated-data'),
        '--load-settings', str(work / 'machine.json') + ';' + str(work / 'process.json'),
        '--load-filaments', str(work / 'filament.json'),
        '--export-3mf', 'project.3mf', '--outputdir', str(work),
        '--debug', '2', str(work / 'geometry.3mf')]
save(W / 'export_command.json', cmd2)
with (work / 'export.log').open('w', encoding='utf-8', errors='replace') as log:
    rc2 = subprocess.run(cmd2, cwd=str(CLI.parent), stdout=log, stderr=subprocess.STDOUT).returncode
print('export rc=%s' % rc2, flush=True)
if rc2 != 0:
    print((work / 'export.log').read_text(encoding='utf-8', errors='replace')[-3000:])
    raise SystemExit(1)

dst = PROJ / 'P2S_MODULE_ACCESSORIES_31PCS_PLA_20261105.3mf'
shutil.copy2(work / 'project.3mf', dst)
with zipfile.ZipFile(dst) as z:
    assert z.testzip() is None
    zn = z.namelist()
    cfg2 = z.read('Metadata/project_settings.config').decode('utf-8', 'replace')
    mr = ET.fromstring(z.read('3D/3dmodel.model'))
    n_items2 = len(mr.findall('.//{%s}item' % NS_M))
rec['project'] = {'path': str(dst), 'bytes': dst.stat().st_size, 'items': n_items2,
                  'has_gcode': any(n.endswith('.gcode') for n in zn),
                  'config_ok': all(s in cfg2 for s in ('"layer_height": "0.16"', '"filament_type": ["PLA"',
                                                        'Bambu Lab P2S', 'Textured PEI Plate'))}
print('project items=%d bytes=%d has_gcode=%s config_ok=%s'
      % (n_items2, dst.stat().st_size, rec['project']['has_gcode'], rec['project']['config_ok']))
save(OUT / 'accessories_plate_slicing.json', rec)
print('DONE')