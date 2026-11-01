"""Rasterize all pages, preserve baseline content, flag pages for visual QA."""
from pathlib import Path
import hashlib,json,re
import pypdfium2 as pdfium
from docx import Document

REPO=Path(__file__).resolve().parents[4]
W=REPO.parent/'.p2s-after-old-plate2-20261101/manual'
OLD=REPO.parent/'.p2s-parallel-20261101/manual'
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(W/'before.docx')==sha(OLD/N),'Baseline PDF and source DOCX must match.'
old=pdfium.PdfDocument(OLD/'render/manual.pdf');new=pdfium.PdfDocument(W/'render/manual.pdf')

def image(doc,i,scale):
    p=doc[i];bm=p.render(scale=scale);im=bm.to_pil().convert('RGB').copy();bm.close();p.close();return im

def bodyhash(im):
    return hashlib.sha256(im.crop((28,90,im.width-28,im.height-88)).tobytes()).hexdigest()

oldmap={}
for i in range(len(old)):oldmap.setdefault(bodyhash(image(old,i,1.3)),[]).append(i+1)
same=[];changed=[];texts=[]
for i in range(len(new)):
    im=image(new,i,1.3);h=bodyhash(im)
    if h in oldmap:same.append({'new':i+1,'old':oldmap[h][0]})
    else:
        changed.append(i+1);image(new,i,1.65).save(W/'render'/f'page-{i+1}.png')
    page=new[i];text=page.get_textpage();texts.append(text.get_text_range());text.close();page.close()
doc=Document(W/N);before=Document(W/'before.docx')
steps=lambda d:[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(doc)==steps(before) and len(steps(doc))==330
tables=lambda d:[[[c.text for c in r.cells] for r in t.rows] for t in d.tables]
assert tables(doc)[:77]==tables(before)[:77]
for label in ['66.1','66.6','66.7','66.8']:assert sum(label in t for t in texts)>=1,label
assert sum('原尺寸底板平放拼接' in t for t in texts)>=2,'Body and updated TOC must both contain chapter 66.'
assert not any('待最终切片' in t or '当前为待最终数据补齐的暂存稿' in t for t in texts[-25:])
result={'old_pages':len(old),'new_pages':len(new),'same_page_bodies':len(same),
    'unchanged_mapping':same,'changed_pages':changed,'all_pages_rasterized':True,
    'original_steps_preserved':330,'original_tables_preserved':77,'corrected_table':'66.8 current machine assignment',
    'docx_sha256':sha(W/N),'baseline_sha256':sha(W/'before.docx'),
    'new_figures':[],
    'renderer':'Independent owned Word instance and pypdfium2; packaged renderer fallback retained because LibreOffice is unavailable in this environment.',
    'user_word_instances_touched':False,'visual_qa_pending':True}
(W/'raster_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='unchanged_mapping'},ensure_ascii=False))
for i in changed:
    print('PAGE',i,texts[i-1][:110].replace('\r',' ').replace('\n',' | '),'END',texts[i-1][-70:].replace('\n',' | '))
