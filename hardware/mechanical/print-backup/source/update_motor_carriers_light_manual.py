"""Append the conservative lightening revision without changing original numbered steps."""
from pathlib import Path
import json,hashlib,shutil,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.section import WD_SECTION_START,WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT,WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'motor-existing-holes-light-20261103';W=R.parent/'.p2s-motor-existing-holes-light-20261103/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';src=R/'docs/manual'/N
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert src.read_bytes()==(R.parent/N).read_bytes()
if not (W/'before.docx').exists():shutil.copy2(src,W/'before.docx')
assert sha(src)==sha(W/'before.docx')
before=Document(W/'before.docx');d=Document(W/'before.docx');assert not any(p.text.startswith('66.13') for p in d.paragraphs)
def para(t,size=10):
    p=d.add_paragraph(t);p.paragraph_format.space_after=Pt(5);p.paragraph_format.line_spacing=1.15
    for r in p.runs:r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
    return p
def picture(name,caption,width=16):
    p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(0);p.add_run().add_picture(str(O/'preview'/name),width=Cm(width));para(caption,9)
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7);s.left_margin=Cm(2);s.right_margin=Cm(2);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.8)
p=d.add_paragraph('66.13 电机转接板保守轻量化',style='Heading 2')
for r in p.runs:r.font.color.rgb=RGBColor(0,0,0)
para('本节提供66.12节转接板的轻量化替换版。保留16mm总厚度、9个底板共孔、8个原座连接孔、金属锁母、原穿槽座和安装位置，五金及装配顺序继续按66.12节执行；底板仍不新增孔。')
picture('01_lightweight_assembly.png','图解76  左板3处、右板4处轻量化浅腔；蓝色为新板，橙色为继续复用的原座。')
para('采用向上开口的圆角浅腔，深11mm，轻量化区域保留5mm底层；孔周和直接承力连接筋按16mm全高保留。主筋以11mm宽保护带布置，右板另保留8mm宽斜向保护带，孔周保护半径8mm、外缘4mm；原有五金避空处按原形保留，原最薄4mm处不再减薄。')
para('相同打印参数下，耗材146.97g降至135.93g，减少7.5%；切片时间11小时10分降至9小时41分，缩短约89分钟。CAD实体体积减少17.2%，不把这个比例当成实际耗材节省。')
para('打印文件为motor-existing-holes-light-20261103/P2S_D06_EXISTING_HOLES_LIGHT_016.3mf，只含两块新板。保留0.16mm层高、6墙、60%螺旋体填充、顶底各8层、100%比例，连续平底面贴床、所有凹位朝上，无支撑。不要再次掏薄主筋、孔台和底层。')
para('已核对保护区材料未被移除、下部原材料保持、孔位及包络不变、STEP重读、封闭网格和所有切片路径。轻量化会改变整体刚度；本轮未证明与原厚板等强，也没有额定载重。仍须按计划实际载荷逐步加载，检查发白、裂纹、松动及永久变形，合格后再低速试车。',9.5)
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.LANDSCAPE;s.page_width=Cm(29.7);s.page_height=Cm(21);s.left_margin=Cm(1.5);s.right_margin=Cm(1.5);s.top_margin=Cm(1.5);s.bottom_margin=Cm(1.5)
for i,name in enumerate(['LEFT','RIGHT']):
    p=d.add_paragraph();p.paragraph_format.page_break_before=(i>0);p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1;p.add_run().add_picture(str(O/'preview'/f'{name}_pocket_dimensions.png'),width=Cm(24))
    p=para(f'图解{77+i}  {name}轻量化浅腔定位；原孔位参见图解74—75，实际轮廓按模型和点表。',9);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1
steps=lambda x:[p.text for p in x.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(d)==steps(before) and len(steps(d))==330 and len(d.tables)==len(before.tables)
d.save(W/N);print(str(W/N))
