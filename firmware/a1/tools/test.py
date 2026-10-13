"""Compile the actual portable C logic with MSVC and run fault-injection tests."""
from pathlib import Path
import subprocess
import sys
import json
ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
OUT=ROOT/'build/host';OUT.mkdir(parents=True,exist_ok=True)
vc=Path(r'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat')
if not vc.exists():
    raise SystemExit('Install MSVC C build tools or edit vcvars64 path in tools/test.py')
results=[]
for name,sources in [('storage',['tests/storage_test.c','src/storage.c']),
                     ('app',['tests/app_test.c','src/storage.c','src/app.c','src/console.c']),
                     ('rfid',['tests/rfid_test.c','src/rfid.c']),
                     ('sensors',['tests/sensors_test.c','src/devices.c'])]:
    # Fixed, trusted paths only; do not use this batch construction for user text.
    batch=OUT/(name+'.cmd')
    command=['cl','/nologo','/std:c11','/W3','/D_CRT_SECURE_NO_WARNINGS',
             '/Iinclude', *sources, '/Fo:build/host/', '/Fe:build/host/'+name+'.exe']
    batch.write_text('@echo off\ncall "'+str(vc)+'" >nul\n'+' '.join(command)+'\nif errorlevel 1 exit /b 1\nbuild\\host\\'+name+'.exe\n',encoding='ascii')
    r=subprocess.run(['cmd.exe','/c','build\\host\\'+name+'.cmd'],cwd=ROOT,capture_output=True)
    text=r.stdout.decode('utf-8',errors='replace')+r.stderr.decode('utf-8',errors='replace')
    print(text)
    (OUT/(name+'.log')).write_text(text,encoding='utf-8')
    results.append({'test':name,'passed':r.returncode==0,'output':text})
    if r.returncode:
        raise SystemExit(r.returncode)
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
