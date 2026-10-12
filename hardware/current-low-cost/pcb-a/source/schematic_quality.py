"""Record upstream schematic inspect results, without altering any KiCad design."""
import json
import os
from pathlib import Path
import subprocess
import sys

here=Path(__file__).resolve().parent
out=here.parent/'review'/'schematic'
out.mkdir(parents=True,exist_ok=True)
summaries=[]
for name in ['SmartBin_A.kicad_sch']+[f'SmartBin_A_{i:02}_01.kicad_sch' for i in range(1,6)]:
    p=subprocess.run([sys.executable,str(here/'schematic_cli.py'),'sch','inspect',str(here.parent/'kicad'/name),'--format','json'],capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1','KICAD_CLI':os.environ.get('KICAD_CLI','D:/KiCad/bin/kicad-cli.exe')})
    if p.returncode:
        summaries.append({'sheet':name,'error':p.stderr,'returncode':p.returncode});continue
    d=json.loads(p.stdout)
    (out/(name+'.inspect.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    summaries.append({'sheet':name,**d['score']})
(out/'inspect-summary.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summaries,ensure_ascii=False,indent=2))
