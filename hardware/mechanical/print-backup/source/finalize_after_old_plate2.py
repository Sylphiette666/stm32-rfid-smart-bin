"""Publish the four-machine continuation after slice and document review."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile

REPO = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'parallel-after-old-plate2-20261101'
WORK = REPO.parent / '.p2s-after-old-plate2-20261101/manual'
NAME = 'STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8'))


def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


parser = argparse.ArgumentParser()
parser.add_argument('--checked-pages', required=True)
args = parser.parse_args()
checked = sorted(set(int(p) for p in args.checked_pages.split(',')))
audit = load(WORK / 'raster_audit.json')
assert checked == sorted(audit['changed_pages'])
assert audit['original_steps_preserved'] == 330 and audit['original_tables_preserved'] == 77
assert sha(WORK / NAME) == audit['docx_sha256']
targets = [REPO / 'docs/manual' / NAME, REPO.parent / NAME]
for p in targets:
    assert sha(p) in [audit['baseline_sha256'], audit['docx_sha256']], p

sliced = load(OUT / 'checks/slicing.json')
printing = load(OUT / 'checks/final_printing.json')
first = load(OUT / 'checks/first_layers.json')
coverage = load(OUT / 'checks/route_coverage.json')
assert sliced['status'] == printing['status'] == coverage['status'] == 'PASS'
assert coverage['total'] == 51 and not coverage['duplicates']
assert coverage['running_objects']==3 and set(coverage['running_names'])=={'P02_UPPER','P03_STAND','P07_SPEAKER_cradle'}
assert sum(p['objects'] for p in printing['plates']) == 48
assert [p['objects_with_first_layer_id'] for p in first.values()] == [1, 1, 23, 23]
assert all(p['all_model_extrusions_within_bed'] and p['G39_absent'] for p in first.values())
assert len(sliced['plates']) == 4
for p in sliced['plates'].values():
    assert p['return_code'] == 0 and not p['warning_message']
    assert p['native_geometry_and_positions_match_tested'] and not p['native_contains_gcode']
    assert sha(OUT / 'projects' / p['native_project']) == p['sha256']
    with zipfile.ZipFile(OUT / 'projects' / p['native_project']) as z:
        assert z.testzip() is None
        cfg = json.loads(z.read('Metadata/project_settings.config'))
        assert cfg['brim_width'] == p['process']['brim_width'] and cfg['layer_height'] == p['process']['layer_height']
        assert cfg['print_sequence'] == 'by layer'
assert sha(BASE / 'accessories-fine-20261101/projects/P2S_ORIGINAL_PLATE1_NO_BASE_FINE_016.3mf') == 'b68ae78857eb53375def3193316f376a38225e9bbc34faa74f90c1322a617560'

for p in targets:
    shutil.copy2(WORK / NAME, p)
assert sha(targets[0]) == sha(targets[1]) == audit['docx_sha256']
audit.update({'visual_qa_pending': False, 'visually_checked_pages': checked,
              'published_copies_match': True, 'status': 'PASS'})
save(OUT / 'checks/manual_qa.json', audit)
save(OUT / 'checks/visual_review.json', {'status': 'PASS', 'reviewed_actual_first_layers': [2, 3, 4, 5],
     'print_files_unchanged_after_review': True, 'rendered_preview_images_are_internal_QA': True})

attrs = REPO / '.gitattributes'
text = attrs.read_text(encoding='utf-8')
prefix = OUT.relative_to(REPO).as_posix()
if prefix + '/** -text' not in text:
    text += '\n# Preserve four-machine continuation export bytes.\n'
    text += prefix + '/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'
    text += prefix + '/geometry/** binary\n' + prefix + '/projects/*.3mf binary\n'
attrs.write_text(text, encoding='utf-8', newline='\n')
sources = ['build_after_old_plate2.py', 'slice_after_old_plate2.py', 'check_after_old_plate2_layers.py',
           'update_after_old_plate2_manual.py', 'check_after_old_plate2_manual.py', 'finalize_after_old_plate2.py']
normal = [attrs, REPO / 'README.md', REPO / 'docs/manual/ASSEMBLY.md', BASE / 'README.md']
normal += [BASE / 'source' / p for p in sources]
archive = BASE / 'parallel-four-p2s-20261101'
normal.append(archive / 'README.md')
for p in normal:
    p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
archive_hashes=load(archive/'checks/SHA256.json')
archive_hashes['README.md']=sha(archive/'README.md')
save(archive/'checks/SHA256.json',archive_hashes)
normal.append(archive/'checks/SHA256.json')
files = [p for p in OUT.rglob('*') if p.is_file() and p.name not in ['SHA256.json', 'release.json']]
assert not (OUT / 'projects/result.json').exists()
assert all(p.suffix.lower() not in ['.pyc', '.log'] for p in files)
save(OUT / 'checks/SHA256.json', {p.relative_to(OUT).as_posix(): sha(p) for p in sorted(files)})
package = REPO.parent / '昨天第二盘继续_四台补打底板及精细附件_20261101.zip'
with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name != 'release.json':
            z.write(p, p.relative_to(OUT).as_posix())
    z.write(targets[0], '手册/' + NAME)
    for name in sources:
        z.write(BASE / 'source' / name, '构建源/' + name)
    z.writestr('先读我.txt', '1号机继续昨天第二盘的上平台、舵机支架和喇叭圈，不用停止。\n'
               'projects内四个文件分别交给其余四台P2S，每份打印一次。按README清单区分。\n'
               '作为项目打开，保持参数、尺寸和排布，重新切片后选择对应空闲设备发送。\n'
               '四台同时启动约5小时20分完成；整套仍取决于1号机昨天第二盘剩余时间。\n'
               '不要再打印43件附件合盘、旧主体三盘或此前误按附件盘已开打安排的四台文件。底板拼接按手册66.1、66.2。\n'
               '完整源及输入：https://github.com/Sylphiette666/stm32-rfid-smart-bin\n')
with zipfile.ZipFile(package) as z:
    assert z.testzip() is None
release = {'status': 'PASS', 'new_concurrent_jobs': 4, 'remaining_objects': 48,
           'running_old_plate2_objects_excluded': 3, 'parallel_seconds': printing['parallel_elapsed_seconds_if_started_together'],
           'filament_g': printing['total_filament_g'], 'package_filename': package.name,
           'package_sha256': sha(package), 'package_bytes': package.stat().st_size,
           'manual_sha256': sha(targets[0]), 'manual_updated_and_visually_checked': True,
           'physical_print_test': False, 'load_tested': False, 'printer_jobs_sent': False}
save(OUT / 'checks/release.json', release)
manifest = REPO / 'MANIFEST.sha256'
entries = {l.split('  ', 1)[1]: l.split('  ', 1)[0]
           for l in manifest.read_text(encoding='utf-8').splitlines() if '  ' in l}
entries = {k: v for k, v in entries.items() if not k.startswith(prefix + '/') or (REPO / k).is_file()}
for p in normal + [targets[0]] + [p for p in OUT.rglob('*') if p.is_file()]:
    entries[p.relative_to(REPO).as_posix()] = sha(p)
manifest.write_bytes(''.join(f'{v}  {k}\n' for k, v in sorted(entries.items())).encode('utf-8'))
print(json.dumps(release, ensure_ascii=False))
