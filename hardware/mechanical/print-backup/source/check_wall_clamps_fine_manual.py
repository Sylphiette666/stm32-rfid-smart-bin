"""Rasterize the complete manual and identify new print-release pages."""
from pathlib import Path
import json,re,hashlib
from docx import Document
import pypdfium2 as pdfium
R=Path(__file__).resolve().parents[4];W=R.parent/'.p2s-wall-clamps-fine-20261103/manual';OLD=R.parent/'.p2s-wall-clamp-preview-20261103/manual';N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(W/'before.docx')==sha(OLD/N)
old=pdfium.PdfDocument(OLD/'manual.pdf');new=pdfium.PdfDocument(W/'manual.pdf')
def raster(doc,i,scale):
    p=doc[i];bm=p.render(scale=scale);im=bm.to_pil().convert('RGB').copy();bm.close();p.close();return im
def bodyhash(im):return hashlib.sha256(im.crop((28,90,im.width-28,im.height-88)).tobytes()).hexdigest()
oldmap={}
for i in range(len(old)):oldmap.setdefault(bodyhash(raster(old,i,1.3)),[]).append(i+1)
same=[];changed=[];texts=[]
for i in range(len(new)):
    im=raster(new,i,1.3);h=bodyhash(im)
    if h in oldmap:same.append({'new':i+1,'old':oldmap[h][0]})
    else:changed.append(i+1);raster(new,i,1.65).save(W/f'page-{i+1}.png')
    p=new[i];t=p.get_textpage();texts.append(t.get_text_range());t.close();p.close()
before=Document(W/'before.docx');after=Document(W/N);steps=lambda doc:[p.text for p in doc.paragraphs if re.match(r'步骤 \d{3}',p.text)];tables=lambda doc:[[[c.text for c in r.cells] for r in t.rows] for t in doc.tables]
assert steps(before)==steps(after) and len(steps(after))==330 and tables(before)==tables(after)
assert '66.15' in '\n'.join(texts[-8:]) and all(re.search(r'图解\s*'+str(n),'\n'.join(texts[-8:])) for n in [83,84])
audit={'status':'VISUAL_REVIEW_PENDING','old_pages':len(old),'new_pages':len(new),'same_page_bodies':len(same),'unchanged_mapping':same,'changed_pages':changed,'all_pages_rasterized':True,'original_steps_preserved':330,'all_baseline_tables_preserved':len(before.tables),'new_figures':[83,84],'baseline_sha256':sha(W/'before.docx'),'docx_sha256':sha(W/N),'renderer':'Independent owned Word, then pypdfium2 rasterization; packaged LibreOffice unavailable','user_word_instances_touched':False}
(W/'raster_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in audit.items() if k!='unchanged_mapping'},ensure_ascii=False))
