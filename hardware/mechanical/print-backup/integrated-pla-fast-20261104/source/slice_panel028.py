"""Re-slice PANEL_COVER at 0.28 mm layer height and export the project 3MF.

Provenance script for the all-0.28 mm package. Requires the local Bambu CLI
portable install and the .p2s-integrated-pla-fast-20261104 work directory
(r1/PANEL_COVER process/machine/filament/geometry from the previous round).
Run from this delivery folder: python source/slice_panel028.py
"""
from pathlib import Path
import json, shutil, subprocess, zipfile

O = Path(__file__).resolve().parents[1]      # delivery folder
R = O.parent                                 # workspace root
FAST = R / '.p2s-integrated-pla-fast-20261104'
CLI = Path('C:/Users/35462/AppData/Local/Temp/smartbin-bambu-cli-20261030/portable/BambuCliHost.exe')
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
save = lambda p, d: p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')

name = 'PANEL_COVER'
src = FAST / 'r1' / name
work = FAST / 'r7' / name
work.mkdir(parents=True, exist_ok=True)
for f in ('machine.json', 'filament.json', 'geometry.3mf'):
    shutil.copy2(src / f, work / f)

process = load(src / 'process.json')
process.update({
    'name': 'SmartBin PLA Fast Tree r7 PANEL 0.28',
    'layer_height': '0.28',
    'top_shell_layers': '3',
    'bottom_shell_layers': '3',
})
save(work / 'process.json', process)

cmd = [str(CLI), '--datadir', str(work / 'isolated-data'),
       '--load-settings', str(work / 'machine.json') + ';' + str(work / 'process.json'),
       '--load-filaments', str(work / 'filament.json'),
       '--arrange', '0', '--orient', '0', '--slice', '0',
       '--export-3mf', 'sliced.3mf', '--outputdir', str(work), '--debug', '2',
       str(work / 'geometry.3mf')]
with (work / 'slice.log').open('w') as log:
    r = subprocess.run(cmd, cwd=CLI.parent, stdout=log, stderr=subprocess.STDOUT)
assert r.returncode == 0, (work / 'slice.log').read_text(errors='replace')[-3000:]

res = load(work / 'result.json')
save(work / 'slice_result.json', res)
p = res['sliced_plates'][0]
assert not p['warning_message'], p['warning_message']
print('PANEL 0.28 hours = %.4f grams = %.3f' % (p['total_predication'] / 3600,
                                                sum(x['total_used_g'] for x in p['filaments'])))

cmd2 = [c for c in cmd]
i = cmd2.index('--slice')
del cmd2[i:i + 2]
cmd2[cmd2.index('--export-3mf') + 1] = 'project.3mf'
with (work / 'export.log').open('w') as log:
    r2 = subprocess.run(cmd2, cwd=CLI.parent, stdout=log, stderr=subprocess.STDOUT)
assert r2.returncode == 0, (work / 'export.log').read_text(errors='replace')[-3000:]

with zipfile.ZipFile(work / 'project.3mf') as z, zipfile.ZipFile(work / 'sliced.3mf') as tested:
    assert z.testzip() is None
    assert not any(n.endswith('.gcode') for n in z.namelist())
    assert all(z.read(n) == tested.read(n) for n in z.namelist() if n.endswith('.model'))
print('export checked; copy project.3mf over projects/P2S_PANEL_COVER_PLA_FAST_CANDIDATE.3mf')
