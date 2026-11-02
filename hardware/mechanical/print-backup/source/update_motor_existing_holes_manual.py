"""Append checked current-hole motor mounting instructions; preserve original 330 steps."""
from pathlib import Path
import json,re,shutil,hashlib
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.section import WD_SECTION_START,WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'motor-existing-holes-20261102'
W=R.parent/'.p2s-motor-existing-holes-20261102/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
src=R/'docs/manual'/N
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)==sha(R.parent/N),'Published copies diverged'
if not (W/'before.docx').exists():shutil.copy2(src,W/'before.docx')
assert sha(src)==sha(W/'before.docx'),'Source changed since snapshot'
before=Document(W/'before.docx');d=Document(W/'before.docx')
assert not any('66.12' in p.text for p in d.paragraphs),'Already appended'
for p in d.paragraphs:
    if p.text.strip()=='66.10  电机穿槽转接座':p.text='66.10  旧版另钻孔电机穿槽转接座'

def para(t,size=10,keep=False):
    p=d.add_paragraph(t);p.paragraph_format.space_after=Pt(5);p.paragraph_format.line_spacing=1.15;p.paragraph_format.keep_with_next=keep
    for r in p.runs:r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
    return p
def heading(t,newpage=False):
    p=d.add_paragraph(t,style='Heading 2');p.paragraph_format.page_break_before=newpage
    for r in p.runs:r.font.color.rgb=RGBColor(0,0,0)
    return p
def picture(name,caption,width=15.5):
    p=d.add_paragraph();p.paragraph_format.space_after=Pt(1);p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(O/'preview'/name),width=Cm(width));para(caption,9)
def table(headers,rows,widths):
    t=d.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    for c,w in zip(t.columns,widths):c.width=Cm(w)
    for c,s in zip(t.rows[0].cells,headers):c.text=s
    for row in rows:
        for c,s in zip(t.add_row().cells,row):c.text=str(s)
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
    t._tbl.tblPr.append(borders)
    for i,row in enumerate(t.rows):
        for c,width in zip(row.cells,widths):
            c.width=Cm(width)
            c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if i==0:
                s=OxmlElement('w:shd');s.set(qn('w:fill'),'DCE8EF');c._tc.get_or_add_tcPr().append(s)
            for p in c.paragraphs:
                p.paragraph_format.space_after=Pt(4);p.paragraph_format.space_before=Pt(4)
                for r in p.runs:r.font.size=Pt(9.5)
    return t

s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7)
s.left_margin=Cm(2);s.right_margin=Cm(2);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.8)
heading('66.12 电机转接板复用底板现有孔')
para('本节取代66.10节中需要另钻底板孔的电机座固定方案。新增左右两块16mm厚转接板，原已试配合适的穿槽座继续使用；底板、模块底座位置和原穿槽基准均不改，不新增底板孔。')
para('从底板上方向下看，X从车尾起算，yb从非舵机侧边起算。蓝色LEFT板共用5个模块座脚孔；棕色RIGHT板共用2个拼接孔、1个MPU6050座脚孔和1个降压托架孔。不是把新孔图当作底板钻孔模板。')
picture('01_existing_hole_layout.png','图解71  现有孔与新增转接板对应；十字为原穿槽基准，不是实测轮轴中心。')

heading('66.12.1 转接层与紧固件',True)
picture('02_stack_assembly.png','图解72  蓝色为新增厚转接板，橙色为原穿槽座；电子模块及完整轮组未画出。')
para('两块新增板采用16mm连续承力板、圆角外缘和五点或四点贯穿锁紧。贴底板面留有原螺母避空；右板另有拼接片凹位。使用金属螺母，不把机螺丝直接拧进PLA。')
table(['紧固件','数量','用途'],[
 ['M3×30 ISO7380低圆头','9颗','5个LEFT共孔＋4个RIGHT共孔'],
 ['M3×25 ISO7380低圆头','8颗','原穿槽座各4孔连接新板'],
 ['M3尼龙防松螺母 约4mm高','17颗','8颗预放六角窝，9颗在共孔底部'],
 ['M3平垫 OD≤6 厚0.5mm','34片','上述每颗螺丝配2片，现有合格件可复用']], [6.2,2,7.3])
para('先把垫圈和锁母放入每板4个六角窝，T形固定片先穿入原穿槽座，再将原座用M3×25从下向上固定到转接板，最后装电机。按名义叠层，螺丝端低于贴底板面0.5mm、穿过锁母1mm。实际螺丝及锁母高度可能有差异，贴底板前用直尺确认无顶出；不能让螺丝顶进底板。')
para('原穿槽座3mm电机贴合面、12×2.4mm双槽、21mm槽距和6mm宽头腔保持。原穿槽基准为(96,14)与(96,206)mm；相对原直装方案，电机整体下移16mm，前后及左右基准不变。旧手册轮轴X≈90只是参考，轮轴与穿槽的实际偏移仍应以装配实物为准。')

heading('66.12.2 安装顺序与实物确认',True)
picture('03_fastener_sections.png','图解73  共孔螺丝与预埋锁母安装关系；拼接孔处不叠模块座脚。')
para('先断开电池、USB与所有供电，移开电子板和松散线束，只保留空模块底座。原T形固定片先穿入旧座，宽头留在腔内，再按图解64的方法装电机和轮子。')
para('逐个更换图解71的9个共孔螺丝为M3×30，拆掉这些孔原底面螺母；新板不能隔着原螺母悬空。右板坐入靠舵机侧的拼接片，其中心坐标为(138,138)mm；该片另外2颗原拼接螺丝保留，螺母和尾端进入已留避空。所有螺丝先轻带上，再交替轻紧。')
para('共孔对应：L1/L2为1117稳压座两脚，L3/L4为蜂鸣器座两脚，L5为STM32座靠前一脚。R1/R2为拼接片(126,144)/(150,144)两孔，R3为MPU6050座X=131.5的一脚，R4为降压托架X=189.5的一脚；不移动这些底座。')
para('装好后手转轮胎一整圈，确认与底板、转接板、螺丝及螺母的全周净隙目标至少3mm；两轮轴共线。量底板实际离地高度Hb，万向球原安装高度20mm，后续垫高件按Hb−20mm确定，不在本轮臆定高度。')
para('用户未指定额定载重。本轮只完成几何、五金、切片及图纸检查，不给出额定承重。先空载手推，再按计划实际载荷逐步加载并检查裂纹、发白、松动和永久变形，合格后才进行低速行驶；尺寸试配成功不等于承载验证通过。',9.5)

s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.LANDSCAPE;s.page_width=Cm(29.7);s.page_height=Cm(21)
s.left_margin=Cm(1.5);s.right_margin=Cm(1.5);s.top_margin=Cm(1.5);s.bottom_margin=Cm(1.5)
for i,name in enumerate(['LEFT','RIGHT']):
    p=d.add_paragraph();p.paragraph_format.page_break_before=(i>0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.keep_with_next=True;p.paragraph_format.line_spacing=1
    p.add_run().add_picture(str(O/'preview'/f'{name}_coordinates.png'),width=Cm(24))
    p=para(f'图解{74+i}  {name}转接板通孔、六角窝及避空坐标，单位mm。',9);p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(0)
steps=lambda doc:[p.text for p in doc.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(d)==steps(before) and len(steps(d))==330
assert len(d.tables)==len(before.tables)+1
d.save(W/N)
(W/'authoring.json').write_text(json.dumps({'baseline_sha256':sha(W/'before.docx'),'staged':str(W/N),'original_steps':330,'original_tables':len(before.tables),'new_figures':[71,72,73,74,75]},ensure_ascii=False,indent=2),encoding='utf-8')
print(str(W/N))
