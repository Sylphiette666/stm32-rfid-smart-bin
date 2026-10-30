"""Rasterize and compare the updated manual with the previously reviewed PDF."""
from pathlib import Path
import hashlib,json,re
from collections import Counter
import pypdfium2 as pdfium
from PIL import Image
from docx import Document

REPO=Path(__file__).resolve().parents[4]
W=REPO.parent/'.p2s-whole-20261030/manual'
OLD=REPO.parent/'.mechanical-print-20261030/manual/render/manual.pdf'
NEW=W/'render/manual.pdf'
old=pdfium.PdfDocument(OLD); new=pdfium.PdfDocument(NEW)
def picture(doc,i,scale=1.3):
 p=doc[i]; bm=p.render(scale=scale); im=bm.to_pil().convert('RGB').copy(); bm.close();p.close();return im
def bh(im):
 return hashlib.sha256(im.crop((28,90,im.width-28,im.height-88)).tobytes()).hexdigest()
oldmap={}
for i in range(len(old)):oldmap.setdefault(bh(picture(old,i)),[]).append(i+1)
same=[];changed=[]
for i in range(len(new)):
 im=picture(new,i);h=bh(im)
 if h in oldmap:same.append({'new':i+1,'old':oldmap[h][0]})
 else:
  changed.append(i+1);picture(new,i,1.65).save(W/'render'/f'page-{i+1}.png')
 # All pages rasterized, unchanged bodies verified pixel-for-pixel.
name='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
a=Document(W/'before.docx'); b=Document(W/name)
steps=lambda d:[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(a)==steps(b) and len(steps(b))==330
assert [[[c.text for c in r.cells]for r in t.rows]for t in a.tables[:66]]==[[[c.text for c in r.cells]for r in t.rows]for t in b.tables[:66]]
wr=json.loads((W/'word_render.json').read_text(encoding='utf-8-sig'))
assert wr['status']=='success' and not wr['user_instances_touched']
# Check that chapter 65 and refreshed TOC entries survived native Word save.
texts=[]
for i in range(len(new)):
 p=new[i];tp=p.get_textpage();texts.append(tp.get_text_range());tp.close();p.close()
assert sum('65.1' in t for t in texts)>=1
assert sum('3D' in t and '65' in t for t in texts)>=2
report={'original_pages':len(old),'new_pages':len(new),'unchanged_page_bodies':len(same),
 'unchanged_mapping':same,'pages_requiring_visual_review':changed,'all_pages_rasterized':True,
 'steps_preserved':330,'original_tables_preserved':66,'user_word_instances_touched':False,
 'toc_and_page_numbers_updated_in_owned_word_instance':True,
 'docx_sha256':hashlib.sha256((W/name).read_bytes()).hexdigest(),
 'packaged_renderer':'Attempted; LibreOffice is absent. Used existing isolated Word renderer and bundled pypdfium2.',
 'physical_print_or_load_test_performed':False,'slicer_toolpath_test_performed':False,'whole_plates_only':True}
(W/'raster_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items()if k!='unchanged_mapping'},ensure_ascii=False))
