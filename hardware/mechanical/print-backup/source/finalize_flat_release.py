"""Publish checked flat-base / fine-accessory releases without unrelated changes."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile

REPO = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parents[1]
ROOTS = [BASE / n for n in ['flat-split-20261101', 'accessories-fine-20261101',
                           'body-after-accessories-20261101']]
W = REPO.parent / '.p2s-flat-split-20261101/manual'
NAME = 'STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(p.read_text(encoding='utf-8'))


def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


parser = argparse.ArgumentParser()
parser.add_argument('--checked-pages', required=True)
args = parser.parse_args()
audit = load(W / 'raster_audit.json')
checked = sorted(set(int(v) for v in args.checked_pages.split(',')))
assert checked == sorted(audit['changed_pages'])
assert audit['original_steps_preserved'] == 330 and audit['original_tables_preserved'] == 66
assert sha(W / NAME) == audit['docx_sha256']
targets = [REPO / 'docs/manual' / NAME, REPO.parent / NAME]
for target in targets:
    assert sha(target) in [audit['baseline_sha256'], audit['docx_sha256']], target

for root, count in zip(ROOTS, [51, 43, 8]):
    sliced = load(root / 'checks/slicing.json')
    assert sliced['status'] == 'PASS'
    for plate in sliced['plates'].values():
        assert plate['return_code'] == 0 and not plate['warning_message']
        assert plate['native_geometry_and_positions_match_tested']
        assert not plate['native_contains_gcode']
        assert sha(root / 'projects' / plate['native_project']) == plate['sha256']
    printing = load(root / 'checks/final_printing.json')
    assert printing['status'] == 'PASS'
    assert sum(p['objects'] for p in printing['plates']) == count
    first = load(root / 'checks/first_layers.json')
    assert sum(p['objects_with_first_layer_comment'] for p in first.values()) == count
    assert all(p['all_model_extrusions_within_bed'] and p['G39_absent'] for p in first.values())
    assert not (root / 'projects/result.json').exists()
coverage = load(ROOTS[2] / 'checks/route_coverage.json')
assert coverage['status'] == 'PASS' and coverage['duplicates'] == []
assert coverage['matches_full_flat_release'] and coverage['total'] == 51
assert sha(ROOTS[1] / 'projects/P2S_ORIGINAL_PLATE1_NO_BASE_FINE_016.3mf') == 'b68ae78857eb53375def3193316f376a38225e9bbc34faa74f90c1322a617560'

audit.update({'visual_qa_pending': False, 'visually_checked_pages': checked,
              'published_copies_match': True, 'status': 'PASS'})
for target in targets:
    shutil.copy2(W / NAME, target)
assert sha(targets[0]) == sha(targets[1]) == audit['docx_sha256']
save(ROOTS[0] / 'checks/manual_qa.json', audit)

sources = ['build_flat_split.py', 'pack_flat_split.py', 'slice_flat_split.py',
           'render_flat_split.py', 'render_flat_joint.py', 'update_flat_split_manual.py',
           'check_flat_split_manual.py', 'build_accessories_fine.py',
           'slice_accessories_fine.py', 'check_accessories_first_layer.py',
           'build_body_remaining.py', 'slice_body_remaining.py', 'check_body_first_layers.py',
           'finalize_flat_release.py']
attrs = REPO / '.gitattributes'
text = attrs.read_text(encoding='utf-8')
for root in ROOTS:
    prefix = root.relative_to(REPO).as_posix()
    if prefix + '/** -text' not in text:
        text += '\n# Preserve checked print export bytes.\n'
        text += prefix + '/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'
        for suffix in ['step/**', 'parts/**', 'geometry/**', 'projects/*.3mf', 'source/*.stl']:
            text += prefix + '/' + suffix + ' binary\n'
attrs.write_text(text, encoding='utf-8', newline='\n')
normal = [attrs, REPO / 'README.md', REPO / 'docs/manual/ASSEMBLY.md', BASE / 'README.md']
normal += [BASE / 'source' / s for s in sources]
for p in normal:
    p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
for root in ROOTS:
    files = [p for p in root.rglob('*') if p.is_file() and p.name not in ['SHA256.json', 'release.json']]
    assert all(p.suffix.lower() not in ['.pyc', '.log'] for p in files)
    save(root / 'checks/SHA256.json', {p.relative_to(root).as_posix(): sha(p) for p in sorted(files)})

package = REPO.parent / '附件精细打印及底板平放拼接_20261101.zip'
with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for root in ROOTS:
        for p in sorted(root.rglob('*')):
            if p.is_file() and p.name != 'release.json':
                z.write(p, p.relative_to(BASE).as_posix())
    z.write(targets[0], '手册/' + NAME)
    for name in sources:
        z.write(BASE / 'source' / name, '构建源/' + name)
    z.writestr('先读我.txt', '现在打印：accessories-fine-20261101/projects/P2S_ORIGINAL_PLATE1_NO_BASE_FINE_016.3mf\n'
               '作为项目打开，保留参数与排布，重新切片。43件，0.16 mm，约9小时18分、84g PLA。\n'
               '完成后只用body-after-accessories-20261101的三份工程补打主体，避免重复附件。\n'
               'flat-split-20261101为全套三盘替代路线，仅用于还未打印附件时。\n'
               '完整源目录和原始输入见 https://github.com/Sylphiette666/stm32-rfid-smart-bin\n'
               '工程已切片检查，尚未实物打印、承重或寿命验证。\n')
with zipfile.ZipFile(package) as z:
    assert z.testzip() is None
release = {'status': 'PASS', 'package_filename': package.name, 'package_sha256': sha(package),
           'package_bytes': package.stat().st_size, 'manual_sha256': sha(targets[0]),
           'manual_updated_and_visually_checked': True, 'original_steps': 330,
           'immediate_route': {'fine_accessory_jobs': 1, 'remaining_body_jobs': 3, 'objects': 51},
           'alternative_full_route': {'jobs': 3, 'objects': 51},
           'base_original_envelope_mm': [280, 220], 'base_halves': 2, 'upper_whole': True,
           'physical_print_test': False, 'load_tested': False, 'unrelated_firmware_changes_included': False}
save(ROOTS[0] / 'checks/release.json', release)
manifest = REPO / 'MANIFEST.sha256'
entries = {line.split('  ', 1)[1]: line.split('  ', 1)[0]
           for line in manifest.read_text(encoding='utf-8').splitlines() if '  ' in line}
prefixes = tuple(root.relative_to(REPO).as_posix() + '/' for root in ROOTS)
entries = {k: v for k, v in entries.items() if not k.startswith(prefixes) or (REPO / k).is_file()}
ours = normal + [targets[0]] + [p for root in ROOTS for p in root.rglob('*') if p.is_file()]
for p in ours:
    entries[p.relative_to(REPO).as_posix()] = sha(p)
manifest.write_bytes(''.join(f'{v}  {k}\n' for k, v in sorted(entries.items())).encode('utf-8'))
print(json.dumps(release, ensure_ascii=False))
