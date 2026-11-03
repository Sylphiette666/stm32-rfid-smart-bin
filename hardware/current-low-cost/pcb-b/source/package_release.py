from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1]
for report,keys in [('checks/pcb-drc.json',['violations','unconnected_items','schematic_parity'])]:
 d=json.loads((R/report).read_text(encoding='utf-8'));assert all(not d[k] for k in keys)
for name in ['checks/netlist-verified.json','review/design-audit.json','review/cam-audit.json']:
 assert json.loads((R/name).read_text(encoding='utf-8'))['pass']
files={}
for p in sorted(R.rglob('*')):
 if not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.pyc','.kicad_prl','.lck'] or p.name=='RELEASE_FILES.sha256':continue
 files[p.relative_to(R).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(R/'RELEASE_FILES.sha256').write_text(''.join(v+'  '+k+'\n' for k,v in files.items()),encoding='utf-8')
archive=R.parents[3]/'SmartBin_B1_PCB_设计与打板资料_20261103.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for name in list(files)+['RELEASE_FILES.sha256']:z.write(R/name,'SmartBin_B1/'+name)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name,digest in files.items():assert hashlib.sha256(z.read('SmartBin_B1/'+name)).hexdigest()==digest
print(json.dumps({'archive':str(archive),'files':len(files)+1,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},ensure_ascii=False))
