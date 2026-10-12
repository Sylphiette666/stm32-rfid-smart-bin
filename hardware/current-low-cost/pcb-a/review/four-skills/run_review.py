from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, time, urllib.request
ROOT=Path(__file__).resolve().parent
SKILLS=Path(r'C:\Users\35462\.codex\skills')
PY=Path(r'C:\Users\35462\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
BASE=ROOT/os.environ.get('REVIEW_VARIANT','baseline')
OUT=ROOT/('analysis-after' if os.environ.get('REVIEW_VARIANT')=='working' else 'analysis')
OUT.mkdir(exist_ok=True)
tasks={
 'schematic': ('kicad','analyze_schematic.py',[str(BASE/'kicad/SmartBin_A.kicad_sch'),'--output',str(OUT/'schematic.json')]),
 'pcb': ('kicad','analyze_pcb.py',[str(BASE/'kicad/SmartBin_A.kicad_pcb'),'--full','--output',str(OUT/'pcb.json')]),
 'gerber': ('kicad','analyze_gerbers.py',[str(BASE/'manufacturing'),'--output',str(OUT/'gerber.json')]),
 'cross': ('kicad','cross_analysis.py',['--schematic',str(OUT/'schematic.json'),'--pcb',str(OUT/'pcb.json'),'--output',str(OUT/'cross.json')]),
 'thermal': ('kicad','analyze_thermal.py',['--schematic',str(OUT/'schematic.json'),'--pcb',str(OUT/'pcb.json'),'--output',str(OUT/'thermal.json')]),
 'emc': ('emc','analyze_emc.py',['--schematic',str(OUT/'schematic.json'),'--pcb',str(OUT/'pcb.json'),'--output',str(OUT/'emc.json')]),
 'spice': ('spice','simulate_subcircuits.py',[str(OUT/'schematic.json'),'--output',str(OUT/'spice.json'),'--workdir',str(OUT/'spice_work')]),
 'lifecycle': ('kicad','lifecycle_audit.py',[str(OUT/'schematic.json'),'--output',str(OUT/'lifecycle.json')]),
}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('task',choices=list(tasks)+['datasheets']);args=a.parse_args()
 if args.task=='datasheets':
  links={
   'SN74AHCT125':'https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf',
   '2N3904':'https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf',
   'MCP23017':'https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf',
   'STM32F103C8':'https://www.st.com/resource/en/datasheet/stm32f103c8.pdf',
   'TB6612FNG':'https://toshiba.semicon-storage.com/info/TB6612FNG_datasheet_en_20141001.pdf?did=10660&prodName=TB6612FNG',
   'AO3400A':'https://www.aosmd.com/res/data_sheets/AO3400A.pdf'}
  results=[]
  for name,url in links.items():
   try:
    data=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read()
    assert data.startswith(b'%PDF'), 'not PDF'
    (ROOT/'datasheets'/f'{name}.pdf').write_bytes(data)
    results.append({'name':name,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
   except Exception as e:results.append({'name':name,'url':url,'error':str(e)})
  (ROOT/'datasheets/index.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
  print(json.dumps(results));sys.exit()
 suite,script,tail=tasks[args.task]
 cmd=[str(PY),str(SKILLS/suite/'scripts'/script),*tail]
 start=time.time()
 p=subprocess.run(cmd,cwd=ROOT,capture_output=True,env={**os.environ,'PYTHONUTF8':'1'},timeout=180)
 (OUT/f'{args.task}.log').write_bytes(p.stdout+b'\nSTDERR\n'+p.stderr)
 summary={'task':args.task,'exit':p.returncode,'seconds':round(time.time()-start,2),'script':str(SKILLS/suite/'scripts'/script),'script_sha256':hashlib.sha256((SKILLS/suite/'scripts'/script).read_bytes()).hexdigest(),'stderr':p.stderr.decode('utf-8','replace')[-1600:]}
 out=OUT/f'{args.task}.json'
 if out.exists():
  try:
   d=json.loads(out.read_text(encoding='utf-8'));summary.update({'summary':d.get('summary'),'keys':list(d)[:18]})
  except Exception as e:summary['output_error']=str(e)
 (OUT/f'{args.task}-run.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False))
