"""Reproducible local Arm Compiler 6 build. Never flashes connected hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
LEGACY = ROOT.parent / 'legacy/SmartBin_F103/CMSIS'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiler', default=r'D:\Keil5\ARM\ARMCLANG\bin')
args = parser.parse_args()
compiler = Path(args.compiler)
out = ROOT / 'build'
out.mkdir(exist_ok=True)
logs = []

def run(cmd):
    result = subprocess.run([str(x) for x in cmd], cwd=ROOT, capture_output=True, text=True, errors='replace')
    logs.append(' '.join(str(x) for x in cmd) + '\n' + result.stdout + result.stderr)
    (out / 'build.log').write_text('\n'.join(logs), encoding='utf-8')
    if result.stdout or result.stderr:
        print(result.stdout + result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)

run([compiler/'armclang.exe', '--version'])
flags = ['--target=arm-arm-none-eabi', '-mcpu=cortex-m3', '-mfloat-abi=soft',
         '-std=c11', '-Oz', '-g', '-ffunction-sections', '-fdata-sections',
         '-Wall', '-Wextra', '-Werror', '-DSTM32F10X_MD', '-D__MICROLIB',
         '-I'+str(ROOT/'include'), '-I'+str(LEGACY/'Device'), '-I'+str(ROOT/'vendor/CMSIS5_Core')]
objects = []
for source in sorted((ROOT/'src').glob('*.c')):
    obj = out/(source.stem+'.o')
    run([compiler/'armclang.exe', *flags, '-c', source, '-o', obj])
    objects.append(obj)
run([compiler/'armasm.exe', '--cpu=Cortex-M3', '--apcs=interwork', '-g',
     '--pd', '__MICROLIB SETA 1', ROOT/'src/startup.s', '-o', out/'startup.o'])
objects.append(out/'startup.o')
run([compiler/'armlink.exe', '--cpu=Cortex-M3', '--library_type=microlib', '--strict',
     '--scatter='+str(ROOT/'MDK/flash.sct'), '--entry=Reset_Handler', '--map',
     '--info=sizes,totals,unused', '--list='+str(out/'SmartBin_A1.map'),
     '-o', out/'SmartBin_A1.axf', *objects])
run([compiler/'fromelf.exe', '--i32combined', '--output='+str(out/'SmartBin_A1.hex'), out/'SmartBin_A1.axf'])
run([compiler/'fromelf.exe', '--bin', '--output='+str(out/'SmartBin_A1.bin'), out/'SmartBin_A1.axf'])
size = (out/'SmartBin_A1.bin').stat().st_size
if size > 64*1024:
    raise SystemExit('F103C8 64 KiB flash limit exceeded')
results = {'flash_image_bytes':size, 'flash_limit_bytes':65536, 'ram_limit_bytes':20480,
           'stack_reserved_bytes':4096, 'hardware_tested':False,
           'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in out.glob('SmartBin_A1.*') if p.suffix in ('.axf','.hex','.bin')}}
(out/'build_results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results, indent=2))
