"""Package only validated firmware, source and reproducible evidence (no local runtimes)."""
import argparse
import datetime
import hashlib
import json
import re
import shutil
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--archive',type=Path,required=True)
a=p.parse_args()
build=ROOT/'build'
tests=json.loads((build/'host/results.json').read_text(encoding='utf-8'))
assert len(tests)==4 and all(t['passed'] for t in tests)
keil_log=(build/'keil/rebuild.log').read_text(encoding='utf-8',errors='replace')
assert '0 Error(s), 0 Warning(s)' in keil_log
result=json.loads((build/'build_results.json').read_text(encoding='utf-8'))
release=ROOT/'release';release.mkdir(exist_ok=True)
for filename,sha in result['files'].items():
    src=build/filename
    assert hashlib.sha256(src.read_bytes()).hexdigest()==sha
    shutil.copyfile(src,release/filename)
maptext=(build/'SmartBin_A1.map').read_text(encoding='utf-8',errors='replace')
ram=int(re.search(r'Total RW\s+Size.*?\s(\d+)\s+\(',maptext).group(1))
assert ram<=20480
sources={}
for folder in ('src','include','vendor','MDK','tools','tests'):
    for f in sorted((ROOT/folder).rglob('*')):
        if not f.is_file() or any(part in ('RTE','DebugConfig','__pycache__') for part in f.parts):continue
        if f.suffix not in ('.c','.h','.s','.py','.sct','.uvprojx','.txt'):continue
        sources[str(f.relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(f.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
validation={**result,'ram_bytes_including_reserved_stack':ram,
            'verified_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
            'keil_rebuild':{'errors':0,'warnings':0,'log':keil_log},
            'host_tests':tests,'source_sha256':sources,'source_hash_normalization':'CRLF to LF; UTF-8 bytes otherwise unchanged',
            'limitations':['No target hardware attached or flashed','Physical calibration and acceptance remain pending',
                           'Command-line legacy assembler reports a deprecation warning; uVision build reports 0 warnings']}
(release/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
(release/'SHA256SUMS.txt').write_text(''.join(sha+'  '+name+'\n' for name,sha in result['files'].items()),encoding='ascii')
with zipfile.ZipFile(a.archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for f in sorted(ROOT.rglob('*')):
        if not f.is_file():continue
        rel=f.relative_to(ROOT)
        if any(x in ('build','RTE','DebugConfig','__pycache__') for x in rel.parts):continue
        if f.suffix in ('.uvoptx','.bak') or '.uvguix.' in f.name:continue
        z.write(f,'SmartBin_A1/firmware/a1/'+str(rel).replace('\\','/'))
    for name in ('stm32f10x.h','system_stm32f10x.h'):
        f=ROOT.parent/'legacy/SmartBin_F103/CMSIS/Device'/name
        z.write(f,'SmartBin_A1/firmware/legacy/SmartBin_F103/CMSIS/Device/'+name)
    z.writestr('SmartBin_A1/00_README.txt','打开 firmware/a1/README.md 阅读说明。\nKeil工程：firmware/a1/MDK/SmartBin_A1.uvprojx\n烧录文件：firmware/a1/release/SmartBin_A1.hex\n首次调试：firmware/a1/LAB_CHECKLIST.md\n已完成代码编译和模拟测试，未进行实物烧录或验收。\n')
print(json.dumps({'archive':str(a.archive),'bytes':a.archive.stat().st_size,
                  'flash':result['flash_image_bytes'],'ram_including_stack':ram},ensure_ascii=True))
