from pathlib import Path
from collections import Counter
import json,re,zipfile,hashlib
import sys
from docx import Document
import pypdfium2 as pdf
O=Path(__file__).resolve().parents[1];R=O.parent.parents[2];W=R.parent/'codex_readback/integrated_pla_fast_manual_20261104'
if len(sys.argv)>1:W=Path(sys.argv[1])
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
old=Document(W/'before.docx');new=Document(W/NAME)
steps=lambda d:[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(old)==steps(new) and len(steps(new))==330
tables=lambda d:[[[c.text for c in row.cells] for row in t.rows] for t in d.tables]
expected=tables(old)
changes=json.loads((W/'edit-audit.json').read_text(encoding='utf8'))['table_changes']
for c in changes:
 assert expected[c['table']][c['row']][c['cell']]==c['before']
 expected[c['table']][c['row']][c['cell']]=c['after']
assert expected==tables(new)[:len(old.tables)]
def media(path):
 with zipfile.ZipFile(path) as z:return Counter(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
om=media(W/'before.docx');nm=media(W/NAME);assert all(nm[k]>=v for k,v in om.items())
d=pdf.PdfDocument(str(W/'manual.pdf'));bad=[]
for i,page in enumerate(d):
 t=page.get_textpage().get_text_range();nums=re.findall(r'第\s*(\d+)\s*页',t)
 if not nums or int(nums[-1])!=i+1:bad.append(i+1)
assert not bad,bad
selected=[1,5]+list(range(267,len(d)+1))
for n in selected:d[n-1].render(scale=1.3).to_pil().save(W/f'final-page-{n}.png')
text='\n'.join(d[i].get_textpage().get_text_range() for i in range(266,len(d)))
assert 'PLA' in text and '0.28' in text and '24' in text
report={'status':'STRUCTURAL_CHECKS_PASS','steps_preserved':330,'old_tables_preserved':len(old.tables),
 'explicit_table_changes':changes,'old_media_preserved':True,'pages':len(d),'page_numbers_verified':True,'visual_review_pages':selected,
 'docx_sha256':hashlib.sha256((W/NAME).read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256((W/'before.docx').read_bytes()).hexdigest(),
 'pdf_sha256':hashlib.sha256((W/'manual.pdf').read_bytes()).hexdigest()}
(W/'qa.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(report)
