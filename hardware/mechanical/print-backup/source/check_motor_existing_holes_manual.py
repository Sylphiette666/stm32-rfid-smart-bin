"""Rasterize every page; unchanged page bodies inherit visually reviewed baseline evidence."""
from pathlib import Path
import hashlib,json,re
import pypdfium2 as pdfium
from docx import Document
R=Path(__file__).resolve().parents[4];O=R/'hardware/mechanical/print-backup/motor-existing-holes-20261102'
W=R.parent/'.p2s-motor-existing-holes-20261102/manual';OLD=R.parent/'.p2s-wall-panels-20261102/manual'
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
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
    else:
        changed.append(i+1);raster(new,i,1.65).save(W/f'page-{i+1}.png')
    p=new[i];t=p.get_textpage();texts.append(t.get_text_range());t.close();p.close()
before=Document(W/'before.docx');after=Document(W/N)
steps=lambda d:[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
tables=lambda d:[[[c.text for c in r.cells] for r in t.rows] for t in d.tables]
assert steps(before)==steps(after) and len(steps(after))==330
assert tables(after)[:78]==tables(before)[:78]
assert '66.12' in '\n'.join(texts[-10:])
assert all(re.search(r'图解\s*'+str(n), '\n'.join(texts[-10:])) for n in [71,72,73,74,75])
assert any('旧版另钻孔' in t for t in texts)
audit={'status':'VISUAL_REVIEW_PENDING','old_pages':len(old),'new_pages':len(new),'same_page_bodies':len(same),'unchanged_mapping':same,'changed_pages':changed,'all_pages_rasterized':True,'original_steps_preserved':330,'original_tables_preserved':78,'new_figures':[71,72,73,74,75],'baseline_sha256':sha(W/'before.docx'),'docx_sha256':sha(W/N),'renderer':'Independent owned Word instance; PDF rasterized with pypdfium2 after packaged renderer found no LibreOffice','user_word_instances_touched':False}
(W/'raster_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='unchanged_mapping'},ensure_ascii=False))
for i in changed:print('PAGE',i,texts[i-1][:90].replace('\n',' | '),'END',texts[i-1][-90:].replace('\n',' | '))
