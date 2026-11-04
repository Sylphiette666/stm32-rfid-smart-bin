"""Slice the three unchanged models with R3D PETG at several layer heights.

Filament preset: Bambu generic PETG base (Bambu Studio has no built-in R3D
profile) overridden with R3D's own published recommendations for PETG
(nozzle 230-260 C, bed 40-60 C, part fan 5-40 %, rated up to 300 mm/s,
0.4-0.8 mm nozzle, dry 60-65 C / 4-8 h).  A conservative 12 mm3/s volume-flow
cap is kept (same as the official BBL PETG preset for P2S) so the result stays
inside reliable PETG extrusion.

Only layer height / shell-layer count / support Z gap are varied; every other
process parameter is identical so the time + material comparison is fair.
"""
from pathlib import Path
import json, shutil, subprocess, traceback, zipfile

ROOT = Path(r'D:\Work\嵌入式课设')
PLA = ROOT / '.p2s-integrated-pla-fast-20261104'
W = ROOT / '.p2s-petg-fast-20261104'
CLI = Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
PROFILES = CLI.parent / 'resources' / 'profiles' / 'BBL'
OUT = W / 'results'


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def save(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


idx = {p.stem: p for p in PROFILES.rglob('*.json')}


def resolve(name):
    d = load(idx[name])
    parent = d.pop('inherits', None)
    base = resolve(parent) if parent else {}
    base.update(d)
    return base


def r3d_petg():
    """Bambu generic PETG base + R3D official PETG recommendations."""
    fil = resolve('Generic PETG @BBL P2S')
    fil.update({
        'name': 'R3D PETG @BBL P2S 0.4 nozzle',
        'filament_settings_id': 'R3D PETG @BBL P2S 0.4 nozzle',
        'filament_vendor': ['R3D'],
        'filament_type': ['PETG'],
        'filament_density': ['1.27'],
        'filament_flow_ratio': ['0.95', '0.95', '0.95'],
        # R3D PETG official: nozzle 230-260 C -> use 250 C (mid-high, better Z bond)
        'nozzle_temperature': ['250', '250', '250'],
        'nozzle_temperature_initial_layer': ['250', '250', '250'],
        # R3D PETG official: bed 40-60 C -> 60 C (top of range, textured PEI)
        'hot_plate_temp': ['60'], 'hot_plate_temp_initial_layer': ['60'],
        'textured_plate_temp': ['60'], 'textured_plate_temp_initial_layer': ['60'],
        'eng_plate_temp': ['60'], 'eng_plate_temp_initial_layer': ['60'],
        'supertack_plate_temp': ['60'], 'supertack_plate_temp_initial_layer': ['60'],
        # R3D PETG official: part cooling 5-40 % -> 10/40, overhang fan capped at 40
        'fan_min_speed': ['10'], 'fan_max_speed': ['40'], 'overhang_fan_speed': ['40'],
        # conservative flow cap equal to the official BBL PETG preset for P2S
        'filament_max_volumetric_speed': ['12', '12', '12'],
    })
    return fil


SOURCE = {
    'LOWER_H41_B1': 'r3',
    'UPPER_INTEGRATED': 'r4',
    'PANEL_COVER': 'r7',
}
# (layer_height, shell_layers) candidates; shells chosen to keep >=0.8 mm shells
CANDIDATES = {
    'LOWER_H41_B1': [(0.28, 3), (0.24, 4), (0.20, 4)],
    'UPPER_INTEGRATED': [(0.28, 3), (0.24, 4), (0.20, 4)],
    'PANEL_COVER': [(0.28, 3), (0.24, 4), (0.20, 4)],
}

filament = r3d_petg()
save(W / 'filament_r3d_petg.json', filament)
print('R3D PETG preset: type=%s nozzle=%s bed_textured=%s maxvol=%s density=%s fan=%s/%s overhang=%s retr_speed=%s'
      % (filament.get('filament_type'), filament.get('nozzle_temperature'),
         filament.get('textured_plate_temp'), filament.get('filament_max_volumetric_speed'),
         filament.get('filament_density'), filament.get('fan_min_speed'), filament.get('fan_max_speed'),
         filament.get('overhang_fan_speed'), filament.get('filament_retraction_speed')), flush=True)

summary = []
for name, cands in CANDIDATES.items():
    variant = SOURCE[name]
    base_dir = PLA / variant / name
    machine = load(base_dir / 'machine.json')
    base_process = load(base_dir / 'process.json')
    for layer_height, shells in cands:
        tag = '%s_L%02d' % (name, round(layer_height * 100))
        work = W / tag
        work.mkdir(parents=True, exist_ok=True)
        process = dict(base_process)
        process.update({
            'name': 'SmartBin R3D PETG Fast Tree ' + tag,
            'layer_height': str(layer_height),
            'initial_layer_print_height': '0.2',
            'top_shell_layers': str(shells),
            'bottom_shell_layers': str(shells),
            'top_shell_thickness': '0.8',
            'bottom_shell_thickness': '0.8',
            'support_top_z_distance': str(layer_height),
            'support_bottom_z_distance': str(layer_height),
        })
        save(work / 'machine.json', machine)
        save(work / 'process.json', process)
        save(work / 'filament.json', filament)
        shutil.copy2(base_dir / 'geometry.3mf', work / 'geometry.3mf')
        cmd = [
            str(CLI), '--datadir', str(work / 'isolated-data'),
            '--load-settings', str(work / 'machine.json') + ';' + str(work / 'process.json'),
            '--load-filaments', str(work / 'filament.json'),
            '--arrange', '0', '--orient', '0', '--slice', '0',
            '--export-3mf', 'sliced.3mf', '--outputdir', str(work),
            '--debug', '2', str(work / 'geometry.3mf'),
        ]
        print('slice start', tag, flush=True)
        try:
            with (work / 'slice.log').open('w', encoding='utf-8', errors='replace') as log:
                rc = subprocess.run(cmd, cwd=str(CLI.parent), stdout=log, stderr=subprocess.STDOUT).returncode
            rec = {'part': name, 'tag': tag, 'variant': variant, 'layer_height': layer_height,
                   'shell_layers': shells, 'filament': 'R3D PETG', 'returncode': rc,
                   'physical_print_tested': False}
            result_json = work / 'result.json'
            if result_json.exists():
                rec['result'] = load(result_json)
                plate = rec['result']['sliced_plates'][0]
                rec['total_predication_s'] = plate['total_predication']
                rec['grams'] = sum(f['total_used_g'] for f in plate['filaments'])
                rec['warning_message'] = plate['warning_message']
            if rc == 0 and not rec.get('warning_message'):
                with zipfile.ZipFile(work / 'sliced.3mf') as z:
                    names = z.namelist()
                    png = [n for n in names if n.endswith('plate_1.png')]
                    if png:
                        (W / 'preview' / (tag + '.png')).write_bytes(z.read(png[0]))
                    cfg = z.read('Metadata/project_settings.config').decode('utf-8', 'replace')
                    rec['config_ok'] = all(s in cfg for s in (
                        '"filament_type": ["PETG"', '"layer_height": "%s"' % layer_height,
                        'Bambu Lab P2S', 'Textured PEI Plate', '"nozzle_temperature": ["250"'))
            save(OUT / (tag + '.json'), rec)
            print('slice done', tag, 'rc=%s' % rc,
                  'hours=%.4f' % (rec.get('total_predication_s', 0) / 3600),
                  'grams=%.3f' % rec.get('grams', 0),
                  'warning=%r' % rec.get('warning_message', 'n/a'),
                  'config_ok=%s' % rec.get('config_ok'), flush=True)
            summary.append(rec)
        except Exception:
            print('FAILED', tag, flush=True)
            traceback.print_exc()
            raise

save(OUT / 'candidates.json', {
    'date': '2026-11-04', 'filament': 'R3D PETG',
    'filament_basis': 'Bambu generic PETG base + R3D official PETG recommendations (250 C nozzle, 60 C textured PEI bed, fan 10/40 %, conservative 12 mm3/s)',
    'process_base': 'PLA fast r3/r4/r7 process (only layer height / shell layers / support Z gap changed)',
    'candidates': summary,
})
print('ALL CANDIDATE SLICES DONE', flush=True)
