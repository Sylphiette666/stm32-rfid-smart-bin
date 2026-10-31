"""Publish only after the changed Word pages have actually been reviewed."""
from pathlib import Path
import argparse,hashlib,json,shutil,zipfile

REPO=Path(__file__).resolve().parents[4]
ROOT=Path(__file__).resolve().parents[1]/'mounted-20261031'
W=REPO.parent/'.p2s-mounted-20261031/manual'
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
parser=argparse.ArgumentParser()
parser.add_argument('--checked-pages',required=True,help='Comma-separated page numbers actually inspected in page PNGs.')
args=parser.parse_args()
audit=load(W/'raster_audit.json')
checked=sorted(set(int(v) for v in args.checked_pages.split(',')))
assert checked==sorted(audit['changed_pages']),'Every changed page needs visual review.'
assert audit['original_steps_preserved']==330 and audit['original_tables_preserved']==66
assert sha(W/NAME)==audit['docx_sha256']
for target in [REPO/'docs/manual'/NAME,REPO.parent/NAME]:
    assert sha(target) in [audit['baseline_sha256'],audit['docx_sha256']],f'Published source changed while staging: {target}'
for file in ['assembly.json','packing.json','slicing.json']:
    data=load(ROOT/'checks'/file)
    assert data.get('status',data.get('digital_geometry_status'))=='PASS',file
hardware=load(ROOT/'checks/hardware_review.json')
assert hardware['status'].startswith('PASS')
for key in ['static_errors','metal_pair_errors','lid_motion_errors','keeper_motion_errors','lid_own_body_errors']:
    assert not hardware[key],key
printing=load(ROOT/'checks/final_printing.json')
assert len(printing['plates'])==2 and sum(p['objects'] for p in printing['plates'])==47
first=load(ROOT/'checks/first_layers.json')
assert sum(p['objects_with_first_layer_comment'] for p in first.values())==47

audit.update({'visual_qa_pending':False,'visually_checked_pages':checked,
              'published_copies_match':True,'status':'PASS'})
for target in [REPO/'docs/manual'/NAME,REPO.parent/NAME]:shutil.copy2(W/NAME,target)
(ROOT/'checks/manual_qa.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for original,alias in [('P02_light.step','P02_UPPER_DESIGN.step'),
                       ('P03_servo_adjustable_stand.step','P03_STAND_DESIGN.step'),
                       ('P04_servo_adjustable_tray.step','P04_TRAY_DESIGN.step')]:
    shutil.copy2(ROOT.parent/'step'/original,ROOT/'step'/alias)

sources=['module_measurements_20261031.json','module_clamps_a.py','build_mounted_design.py',
         'pack_mounted_plates.py','slice_mounted_plates.py','review_mounted_hardware.py',
         'render_mounted_design.py','render_mounted_plates.py','write_mounted_readme.py',
         'update_mounted_manual.py','check_mounted_manual.py','finalize_mounted_release.py']
# Canonical LF for normal repository text. The generated release directory is
# byte-preserved by .gitattributes, including CAD exporter formatting.
normal_text=[REPO/'.gitattributes',REPO/'README.md',REPO/'docs/manual/ASSEMBLY.md',ROOT.parent/'README.md']
normal_text += [ROOT.parent/'source'/s for s in sources]
for p in normal_text:p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
(ROOT/'projects/result.json').unlink(missing_ok=True)
files=[p for p in ROOT.rglob('*') if p.is_file() and p.name not in ['SHA256.json','release.json']]
hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}
(ROOT/'checks/SHA256.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

package=REPO.parent/'一体底板上平台_方案A夹具_两盘打印_20261031.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and p.name!='release.json':z.write(p,p.relative_to(ROOT).as_posix())
    z.write(REPO/'docs/manual'/NAME,'手册/'+NAME)
    for name in sources:z.write(ROOT.parent/'source'/name,'构建源/'+name)
    z.writestr('构建源/说明.txt','完整可复现目录和原始STEP输入见GitHub仓库 hardware/mechanical/print-backup/source；本压缩包以两份打印工程和最终可编辑STEP为入口。\nhttps://github.com/Sylphiette666/stm32-rfid-smart-bin\n')
with zipfile.ZipFile(package) as z:assert z.testzip() is None
release={'status':'PASS','whole_main_plates':True,'print_jobs':2,'printed_objects':47,
    'package_filename':package.name,'package_sha256':sha(package),'package_bytes':package.stat().st_size,
    'manual_sha256':sha(REPO/'docs/manual'/NAME),'manual_updated_and_visually_checked':True,
    'physical_print_test':False,'load_tested':False,'unrelated_firmware_changes_included':False}
(ROOT/'checks/release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Update only this release's entries; unrelated dirty firmware keeps its HEAD
# manifest hashes rather than silently changing the scope of this commit.
manifest=REPO/'MANIFEST.sha256'
entries={line.split('  ',1)[1]:line.split('  ',1)[0] for line in manifest.read_text(encoding='utf-8').splitlines() if '  ' in line}
release_prefix=ROOT.relative_to(REPO).as_posix()+'/'
entries={k:v for k,v in entries.items() if not k.startswith(release_prefix) or (REPO/k).is_file()}
ours=[REPO/'.gitattributes',REPO/'README.md',REPO/'docs/manual/ASSEMBLY.md',REPO/'docs/manual'/NAME,ROOT.parent/'README.md']
ours += [ROOT.parent/'source'/s for s in sources]
ours += [p for p in ROOT.rglob('*') if p.is_file()]
for file in ours:entries[file.relative_to(REPO).as_posix()]=sha(file)
manifest.write_bytes(''.join(f'{value}  {key}\n' for key,value in sorted(entries.items())).encode('utf-8'))
print(json.dumps(release,ensure_ascii=False))
