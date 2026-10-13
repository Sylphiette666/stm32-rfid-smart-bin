"""Rebuild the supplied uVision project without opening an interactive window."""
import argparse
from pathlib import Path
import subprocess
import sys
import re
ROOT=Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--keil',default=r'D:\Keil5\UV4\UV4.exe')
a=p.parse_args()
out=ROOT/'build/keil';out.mkdir(parents=True,exist_ok=True)
log=out/'rebuild.log'
log.unlink(missing_ok=True)
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
r=subprocess.run([a.keil,'-r',str(ROOT/'MDK/SmartBin_A1.uvprojx'),'-t','SmartBin_A1','-o',str(log),'-j0'],cwd=ROOT/'MDK',startupinfo=si)
text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
print(text)
if r.returncode>1 or not re.search(r'\b0 Error\(s\)',text) or not (out/'SmartBin_A1.hex').exists():
    raise SystemExit('Keil rebuild failed')
print('PASS uVision rebuild (compile only, no flashing)')
