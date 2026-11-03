from pathlib import Path
from collections import Counter
from docx import Document
import json,re,zipfile,hashlib
import pypdfium2 as pdf
REPO=Path(__file__).resolve().parents[3]
S=REPO.parent/'codex_readback/pcb_b_manual_release'
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
old=Document(S/'before.docx');new=Document(S/NAME)
a=json.loads((S/'edit-audit.json').read_text(encoding='utf-8'))
steps=lambda d:[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(old)==steps(new) and len(steps(new))==330
tables=[[[c.text for c in row.cells] for row in t.rows] for t in old.tables]
for c in a['table_changes']:
 assert tables[c['table']][c['row']][c['cell']]==c['before']
 tables[c['table']][c['row']][c['cell']]=c['after']
assert tables==[[[c.text for c in row.cells] for row in t.rows] for t in new.tables[:len(old.tables)]]
def media(p):
 with zipfile.ZipFile(p) as z:return Counter(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
om=media(S/'before.docx');nm=media(S/NAME);assert all(nm[k]>=v for k,v in om.items())
d=pdf.PdfDocument(S/'manual.pdf');bad=[]
for i,page in enumerate(d):
 text=page.get_textpage().get_text_range();nums=re.findall(r'第\s*(\d+)\s*页',text)
 if not nums or int(nums[-1])!=i+1:bad.append({'page':i+1,'footer_numbers':nums})
assert not bad,bad
assert 'PCB B1' in d[0].get_textpage().get_text_range()
selected=[1,2,5,6,7,177,258,259,260]
for n in selected:d[n-1].render(scale=1.5).to_pil().save(S/f'final-page-{n}.png')
report={'status':'structural and page-field checks passed','steps_preserved':330,'existing_tables_verified':len(old.tables),'explicit_table_cell_updates':a['table_changes'],'all_existing_media_preserved':True,'pages':len(d),'all_page_numbers_verified':True,'review_pages':selected,'docx_sha256':hashlib.sha256((S/NAME).read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256((S/'manual.pdf').read_bytes()).hexdigest(),'word_report':json.loads((S/'word-render.json').read_text(encoding='utf-8-sig'))}
(S/'FINAL_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
