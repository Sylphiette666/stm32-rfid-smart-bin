from pathlib import Path
import json,hashlib,zipfile
root=Path(__file__).resolve().parents[1];fab=root/'manufacturing'
names=['SmartBin_B-F_Cu.gtl','SmartBin_B-B_Cu.gbl','SmartBin_B-F_Mask.gts','SmartBin_B-B_Mask.gbs','SmartBin_B-F_Silkscreen.gto','SmartBin_B-B_Silkscreen.gbo','SmartBin_B-Edge_Cuts.gm1','SmartBin_B-PTH.drl','SmartBin_B-NPTH.drl']
d=json.loads((root/'checks/pcb-drc.json').read_text(encoding='utf-8'))
assert not d['violations'] and not d['unconnected_items'] and not d['schematic_parity']
with zipfile.ZipFile(fab/'Gerber_RS274X.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in names:
  data=(fab/n).read_bytes();assert data
  if not n.endswith('.drl'):assert b'%TF.' not in data and b'%TO.' not in data
  z.writestr(n,data)
with zipfile.ZipFile(fab/'Gerber_RS274X.zip') as z:assert z.testzip() is None and sorted(z.namelist())==sorted(names)
out={n:hashlib.sha256((fab/n).read_bytes()).hexdigest() for n in names+['Gerber_RS274X.zip']}
(fab/'fabrication-sha256.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'gerber_zip_files':len(names),'zip_sha256':out['Gerber_RS274X.zip']}))
