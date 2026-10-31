"""Replace chapter 65 with the measured one-piece module-mounting design.

This authoring script only reads the published manual and writes a staging copy.
It never starts Word, updates a live document, publishes, commits, or renders.
Run it with the bundled document Python after the artifact-operation marker;
then render, inspect, update fields, and publish through the separate QA flow.

Read-only entry points:
    python update_mounted_manual.py --schema
    python update_mounted_manual.py --check-inputs

Default inputs under print-backup/mounted-20261031:
    source/design.json
    checks/final_printing.json
    preview/01_layout.png ... preview/08_plate2_bed.png

Missing numeric results are printed as pending, never copied from an old run.
Use --allow-incomplete only for an explicitly marked draft; the default requires
the manufacturing figures and any listed 3MF projects to exist.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import zipfile

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image


NAME = 'STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
FIGURES = [
    ('01_layout.png', '底板上的模块位置和接线操作空间',
     '整片底板上的模块布置图，标明模块编号、位置和接口方向。'),
    ('02_base_3d.png', '整片底板的安装座和局部加强',
     '带模块安装座、安装孔和局部加强区的一体化底板。'),
    ('03_clamp_open_closed.png', '方案A压框与九十度旋转拨片的开闭位置',
     '金属销铰链压框、旋转拨片、硬止挡和独立低挠度定位簧片的开闭状态。'),
    ('04_battery_speaker.png', '电池限位和喇叭的可调固定',
     '电池挡边及固定通道、喇叭两耳安装孔和可调螺母垫柱。'),
    ('05_plate1.png', '第一项打印任务的完整摆放',
     '第一项打印任务内的完整板件、辅助结构和独立打印小件。'),
    ('06_plate2.png', '第二项打印任务的完整摆放',
     '第二项打印任务内的完整板件与独立打印小件。'),
    ('07_plate1_bed.png', '第一项打印任务的热床边界',
     '第一项打印任务的热床俯视图，展示各件位置及边界预留。'),
    ('08_plate2_bed.png', '第二项打印任务的热床边界',
     '第二项打印任务的热床俯视图，展示各件位置及边界预留。'),
]
REQUIRED_FIGURES = {item[0] for item in FIGURES} - {'04_battery_speaker.png'}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_number(value):
    """Accept a real measurement, not booleans or a string containing units."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def number(value, suffix='') -> str:
    result = finite_number(value)
    return '待确认' if result is None else f'{result:g}{suffix}'


def prose(value, fallback='待确认') -> str:
    if isinstance(value, bool):
        return '是' if value else '否'
    if value is None or value == '' or value == [] or value == {}:
        return fallback
    if isinstance(value, dict):
        return '；'.join(f'{k}：{prose(v)}' for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return '；'.join(prose(v).rstrip('。；; ') for v in value)
    return str(value)


def notes(value) -> list[str]:
    if value is None or value == '' or value == []:
        return []
    if isinstance(value, (list, tuple)):
        return [prose(item) for item in value]
    return [prose(value)]


def dimensions(value) -> str:
    if isinstance(value, dict):
        value = [value.get('length', value.get('length_mm')),
                 value.get('width', value.get('width_mm')),
                 value.get('thickness', value.get('thickness_mm'))]
        while value and value[-1] is None:
            value.pop()
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return prose(value, '待测量')
    return '×'.join(number(v) for v in value) + ' mm'


def point(value) -> str:
    if isinstance(value, dict):
        value = [value.get('x'), value.get('y')]
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return '(' + ', '.join(number(v) for v in value) + ')'
    return prose(value)


def hole_description(value, diameter=None) -> str:
    if value is None or value == [] or value == {}:
        return '无独立安装孔或见固定方式'
    if isinstance(value, dict):
        if 'xy' in value:
            label={'foot':'座脚','axis':'锁片轴','anchor':'簧片锚钉'}.get(value.get('type'),value.get('type',''))
            dia=value.get('diameter',diameter)
            return (label+' '+point(value['xy'])+(f'，Ø{number(dia)}' if dia is not None else '')).strip()
        centres = value.get('centers', value.get('centres', value.get('points')))
        if centres is not None:
            diameter = value.get('diameter', value.get('diameter_mm', diameter))
            return hole_description(centres, diameter)
        if 'x' in value and 'y' in value:
            dia = value.get('diameter', value.get('d', diameter))
            return point(value) + (f'，Ø{number(dia)}' if dia is not None else '')
        return prose(value)
    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and all(finite_number(v) is not None for v in value[:2]):
            desc = point(value[:2])
            dia = value[2] if len(value) > 2 else diameter
            return desc + (f'，Ø{number(dia)}' if dia is not None else '')
        desc = ' / '.join(hole_description(v) for v in value)
        return desc + (f'；孔径Ø{number(diameter)}' if diameter is not None else '')
    return str(value)


def duration(seconds) -> str:
    seconds = finite_number(seconds)
    if seconds is None or seconds < 0:
        return '待最终切片'
    minutes = int(math.floor(seconds / 60 + .5))
    h, m = divmod(minutes, 60)
    return f'约{h}小时{m:02d}分'


def mass(grams) -> str:
    grams = finite_number(grams)
    return '待最终切片' if grams is None or grams < 0 else f'约{grams:.0f} g'


def schema_example() -> dict:
    return {
        'design.json': {
            'units': 'mm',
            'coordinate_notes': '说明layout_origin的具体基准及rotation正方向。',
            'seat_height_reference': '例如PCB底面相对底板安装面的架空高度，不能含糊。',
            'modules': [{
                'id': 'M01', 'name': '模块名称', 'board_size': [53, 22, 2],
                'layout_origin': [None, None], 'rotation': 0, 'seat_height': 20,
                'fixing': '方案A压框和90度拨片',
                'notes': ['反面出针', '右侧USB和左侧SWD开放'],
                'mount_holes': [],
                'header_side': 'back', 'header_protrusion': 9,
            }],
            'hardware': [{'name': 'M3金属轴', 'quantity': None,
                          'spec': '以最终五金统计为准',
                          'used_for': '铰链或拨片', 'notes': ''}],
            'plate_geometry': {
                'base_size': [280, 220, 5], 'upper_size': [240, 190, 5],
                'continuous_skin_mm': 3, 'local_mount_thickness_mm': 5,
            },
            'print_notes': ['填写最终打印方向、已有辅助结构及支撑设置。'],
            'assembly_notes': [],
            'unmeasured_features': [],
        },
        'final_printing.json': {
            'status': 'PASS或PENDING，不用历史切片结果替代',
            'plates': [{'file': 'projects/最终工程.3mf', 'objects': ['物体名'],
                        'estimated_seconds': None, 'filament_g': None}],
            'total_seconds': None, 'total_filament_g': None,
            'slicer_version': None, 'native_roundtrip_verified': None,
            'physical_print_test': False, 'load_tested': False,
            'settings': {'layer_height_mm': None, 'wall_loops': None,
                         'infill': None, 'brim_mm': None},
            'notes': [],
        },
        'notes': [
            '只读模式--schema或--check-inputs不会生成或修改Word。',
            '最终默认模式缺必需图片或已列出的工程文件会停止，--allow-incomplete仅生成标记草稿。',
            '座高和原点完全按数据描述，不自动推断为绝对Z或中心点。',
            '额外字段保留在源JSON；缺失数值在正文明确写待确认或待最终切片。',
        ],
    }


def load_json(path: Path, required=False) -> dict:
    if not path.exists():
        if required:
            raise FileNotFoundError(f'缺少设计元数据：{path}')
        return {}
    result = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(result, dict):
        raise ValueError(f'元数据根节点必须为对象：{path}')
    return result


def resolve_project(root: Path, value) -> Path | None:
    if not value:
        return None
    raw = Path(str(value))
    candidates = [raw] if raw.is_absolute() else [root/raw, root/'projects'/raw]
    for path in candidates:
        resolved = path.resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise ValueError(f'工程文件必须位于本轮模型目录内：{value}')
        if resolved.is_file():
            return resolved
    return None


def input_report(root: Path, design: dict, printing: dict) -> dict:
    if str(design.get('units', 'mm')).lower() not in {'mm', 'millimeter', 'millimetre', '毫米'}:
        raise ValueError('设计元数据必须统一为毫米，不能把厘米数值直接用于安装表。')
    modules = design.get('modules', [])
    if not isinstance(modules, list) or not modules:
        raise ValueError('design.json必须包含非空modules数组。')
    if any(not isinstance(item, dict) for item in modules):
        raise ValueError('modules中的每一项必须为对象。')
    ids = [prose(m.get('id'), '') for m in modules]
    present = [ident for ident in ids if ident]
    if len(set(present)) != len(present):
        raise ValueError('模块id重复，布局图与安装表将无法对应。')
    missing_images = [name for name in sorted(REQUIRED_FIGURES)
                      if not (root/'preview'/name).is_file()]
    plates = printing.get('plates', [])
    if not isinstance(plates, list):
        raise ValueError('final_printing.json的plates必须为数组。')
    missing_projects = []
    projects = []
    for index, plate in enumerate(plates, 1):
        if not isinstance(plate, dict):
            raise ValueError('plates中的每一项必须为对象。')
        file = plate.get('file')
        path = resolve_project(root, file)
        if path is None:
            missing_projects.append(str(file or f'第{index}盘未指定file'))
            continue
        if path.suffix.lower() != '.3mf':
            raise ValueError(f'打印项目应为待重切片的3MF：{path.name}')
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                raise ValueError(f'3MF压缩校验失败：{path.name}')
            if any(n.lower().endswith('.gcode') for n in z.namelist()):
                raise ValueError(f'文件含G-code，不能按待重切片工程交付：{path.name}')
        projects.append({'file': str(path.relative_to(root)), 'sha256': sha(path),
                         'contains_gcode': False})
    warnings = []
    if not printing:
        warnings.append('尚无final_printing.json，所有打印时间和用量保持待最终切片。')
    if not plates:
        warnings.append('尚无打印任务记录，不写成已实现两盘。')
    if not design.get('coordinate_notes'):
        warnings.append('缺coordinate_notes，原点及旋转基准必须在图和数据中明确。')
    if not design.get('seat_height_reference'):
        warnings.append('缺seat_height_reference，座高的Z基准尚未明确。')
    for item in modules:
        if not item.get('name') or not item.get('board_size'):
            warnings.append(f"模块{prose(item.get('id'))}缺名称或实测尺寸。")
        origin = item.get('layout_origin')
        if isinstance(origin, dict):
            origin = [origin.get('x'), origin.get('y')]
        if (not isinstance(origin, (list, tuple)) or len(origin) < 2 or
                any(finite_number(v) is None for v in origin[:2])):
            warnings.append(f"模块{prose(item.get('id'))}的布局原点待确认。")
        if finite_number(item.get('seat_height')) is None:
            warnings.append(f"模块{prose(item.get('id'))}的座高待确认。")
        if finite_number(item.get('rotation')) is None:
            warnings.append(f"模块{prose(item.get('id'))}的旋转角待确认。")
    if not design.get('hardware'):
        warnings.append('尚无最终五金统计，不猜数量或螺钉长度。')
    if plates and any(finite_number(p.get('estimated_seconds')) is None or
                      finite_number(p.get('filament_g')) is None for p in plates):
        warnings.append('部分任务缺最终时间或耗材数值，保留待最终切片。')
    return {'module_count': len(modules), 'plate_count': len(plates),
            'missing_required_figures': missing_images,
            'missing_projects': missing_projects, 'projects': projects,
            'warnings': warnings}


def module_rows(modules: list[dict]) -> list[tuple]:
    rows = []
    for item in modules:
        layout = (f"原点{point(item.get('layout_origin'))}\n"
                  f"旋转{number(item.get('rotation'), '°')}；座高{number(item.get('seat_height'), ' mm')}")
        fixed = prose(item.get('fixing'))
        side = item.get('header_side')
        if side:
            labels = {'front':'正面出针', 'back':'反面出针', 'side':'侧面出针'}
            header = labels.get(str(side).lower(), str(side))
            length = item.get('header_protrusion', item.get('header_protrusion_mm'))
            if length is not None:
                header += number(length, ' mm')
            fixed += '\n' + header
        note = prose(item.get('notes'), '')
        if note:
            fixed += '\n' + note
        rows.append((f"{prose(item.get('id'), '')} {prose(item.get('name'))}".strip(),
                     dimensions(item.get('board_size')), layout, fixed))
    return rows


def hardware_rows(value) -> list[tuple]:
    if isinstance(value, dict):
        value = [dict(item, name=item.get('name', name)) if isinstance(item, dict)
                 else {'name': name, 'quantity': item}
                 for name, item in value.items()]
    if not isinstance(value, list) or not value:
        return [('待最终五金统计', '不猜数量与长度', '待确认', '按实际装配检查')]
    rows = []
    for item in value:
        if not isinstance(item, dict):
            rows.append((str(item), '待确认', '待确认', '待确认'))
            continue
        usage = prose(item.get('used_for', item.get('purpose')), '')
        notes = prose(item.get('notes'), '')
        rows.append((prose(item.get('name')), prose(item.get('spec', item.get('size'))),
                     prose(item.get('quantity', item.get('qty'))),
                     '；'.join(v for v in [usage, notes] if v) or '见装配图'))
    return rows


def find_chapter_65(doc):
    for paragraph in doc.paragraphs:
        style = paragraph.style.name if paragraph.style else ''
        if style in {'Heading 1', '标题 1'} and re.match(r'^65(?:\s|\u3000)+', paragraph.text.strip()):
            return paragraph
    raise ValueError('已发布手册中未找到第65章，不自动删除其他章节。')


def steps(doc):
    return [p.text for p in doc.paragraphs if re.match(r'步骤\s+\d{3}', p.text)]


def table_texts(doc):
    return [[[(c.text) for c in row.cells] for row in table.rows] for table in doc.tables]


def author(args, root: Path, design: dict, printing: dict, inputs: dict) -> dict:
    source = args.published.resolve()
    work = args.work_dir.resolve()
    if source.is_relative_to(work):
        raise ValueError('已发布手册与暂存目录必须分开。')
    work.mkdir(parents=True, exist_ok=True)
    before = work/'before.docx'
    if not before.exists():
        shutil.copy2(source, before)
    if sha(source) != sha(before):
        raise ValueError('已发布手册自基线备份后已改变；停止，避免覆盖未合入的修改。')
    doc = Document(before)
    old = Document(before)
    if len(steps(old)) != 330:
        raise ValueError('原手册的步骤数不是330；须人工核对后再改章。')
    body = doc._element.body
    anchor = find_chapter_65(doc)
    children = list(body)
    start = children.index(anchor._p)
    prefix_table_count = sum(el.tag == qn('w:tbl') for el in children[:start])
    if prefix_table_count != 66:
        raise ValueError(f'第65章前表格数为{prefix_table_count}，与预期66不符。')
    # Preserve any later main chapter; only replace the chapter-65 block.
    paragraph_by_node = {p._p: p for p in doc.paragraphs}
    successor = None
    stop = len(children)
    for index in range(start+1, len(children)):
        paragraph = paragraph_by_node.get(children[index])
        if paragraph is None:
            continue
        match = re.match(r'^(\d+)(?:\s|\u3000)+', paragraph.text.strip())
        style = paragraph.style.name if paragraph.style else ''
        if match and int(match.group(1)) > 65 and style in {'Heading 1', '标题 1'}:
            stop = index; successor = children[index]; break
    for element in children[start:stop]:
        if element.tag != qn('w:sectPr'):
            body.remove(element)
    retained_nodes = set(body)
    audit = {'figures': [], 'chapter_replaced': 65, 'inputs': inputs,
             'source_design_sha256': sha(args.design),
             'source_printing_sha256': sha(args.printing) if args.printing.is_file() else None}
    # Retain the actual manual's formatting helpers, with a fresh document scope.
    namespace = dict(globals())
    namespace.update({'doc': doc, 'audit': audit})
    helper = args.repo/'docs/manual/pcb-a-update-20261012/retained_formatting.py'
    exec(compile(helper.read_text(encoding='utf-8'), str(helper), 'exec'), namespace)
    heading, para, figure, table = [namespace[k] for k in ['heading','para','figure','table']]
    figure_no = 50
    figure_numbers = {}

    def image(name, max_width=17.0, max_height=16.0, optional=False):
        nonlocal figure_no
        path = root/'preview'/name
        meta = next(item for item in FIGURES if item[0] == name)
        if not path.is_file():
            if optional:
                return False
            para(f'图件待完成：{name}。该页为草稿，不能作为最终制造说明。', 10)
            return False
        with Image.open(path) as im:
            width, height = im.size
        display_width = min(max_width, max_height*width/height)
        figure(path, f'图解 {figure_no}  {meta[1]}。', meta[2], display_width)
        figure_numbers[name] = figure_no
        figure_no += 1
        return True

    geometry = design.get('plate_geometry', {})
    modules = design['modules']
    plates = printing.get('plates', [])
    incomplete = bool(inputs['missing_required_figures'] or inputs['missing_projects'] or
                      inputs['warnings'] or not plates)

    heading('65  整片平台与模块安装位', 1, True)
    para('本章用于制作带模块安装位的一体化底板和上平台，并装配用户选择的方案A可开启压框。两块大板各自整片打印，不切块、不拼接；独立压框、拨片和定位环是活动五金配合件，不用于把板件拼成整片。')
    if incomplete:
        para('当前为待最终数据补齐的暂存稿。缺失图片、工程或切片数值会明确标记，不能按此稿开始打印。', 10)
    para('旧版细高侧立同盘曾发生底板倾倒并带倒上平台。本版按实际模块尺寸加入固定孔、架空座和开启机构，并重新检查辅助结构、热床边界及打印任务。数字检查与切片通过仍不等于已完成实物打印或承重验收。', 10)
    image('01_layout.png', max_height=14.2)
    table(['板件','完整外形与承载要求'], [
        ('P01底板', dimensions(geometry.get('base_size', [280,220,5])) + '；模块安装孔及固定座与板件对应，新增受力安装处保留局部5mm厚料。'),
        ('P02上平台', dimensions(geometry.get('upper_size', [240,190,5])) + '；保留四柱和舵机托片接口。'),
    ], [3.3,14.2], size=9.5)

    heading('65.1  模块位置和安装基准', 2, True)
    para(prose(design.get('coordinate_notes'), '原点和旋转方向按布局图与source/design.json的定义核对；不要把商品图片的上下左右直接当作车体坐标。'), 10)
    para(prose(design.get('seat_height_reference'), '表中座高直接引用设计源参数。安装前须核对其相对底板顶面或绝对Z的基准，不能把座高与元件总高混为一项。'), 10)
    table(['编号与模块','板体尺寸','布局参数','固定方式及接口避让'], module_rows(modules),
          [3.4,2.6,4.4,7.1], size=9.2)
    para('正面为主要元件面，反面为焊接面；同面的元件与排针高度取较大包络，不能重复相加。反面出针类别采用约20mm架空，正面出针类别一般采用约4mm架空；每个安装座最终值以表中和模型为准。插上实际杜邦接头后再次检查下方净空及线缆弯折。', 10)
    para('按模块旋转角检查STM32的USB与SWD、DFPlayer的TF卡口、HC-05天线端和电位器的可达性。MPU6050使用刚性承托，记录板上X向右、Y向上与车体轴向的换算关系。', 10)

    heading('65.2  安装孔和局部加强', 2, False)
    image('02_base_3d.png', max_height=14.6)
    hole_rows = [(prose(m.get('id'))+' '+prose(m.get('name')),
                  hole_description(m.get('mount_holes'), m.get('hole_diameter')))
                 for m in modules if m.get('mount_holes')]
    if hole_rows:
        table(['模块','对应底板安装孔（底板局部坐标）'], hole_rows, [5.2,12.3], size=9.5)
    para('A1主PCB保持100×100mm、四孔中心距90×90mm的矩形安装关系；安装柱与孔周有对应受力区。PCB下表面保持绝缘间距，螺钉不顶住焊点或铜箔。', 10)
    para('5V降压模块按实测43×21mm边界定位。以模块左下角为局部原点，两只安装孔为(7,19)、(36,2)，孔径3mm；它们不是四角接线焊盘。商品图中的39.5mm标注不得当作这两只大安装孔的横向孔距。', 10)
    para('无独立安装孔的小模块使用安装座和方案A压框，板边或角点由相应座面承托。卡持处避开元件、排针和焊点，不在电子PCB上另钻孔。', 10)

    heading('65.3  方案A压框和旋转拨片', 2, False)
    image('03_clamp_open_closed.png', max_height=14.0)
    para('压框通过金属销铰链开启；中心镂空，接口方向开放。合上后将刚性拨片转到闭合位置，使拨片与压框的承载面有明确重叠；0度和90度均有独立硬止挡。', 10)
    para('独立定位环中的低挠度簧片只提供防误转定位。压框向上受力时，载荷由刚性拨片、轴座和金属轴承担，不能靠弹舌充当承载钩或旋转止挡。簧片卡位属于防振定位，不能作为强防误触锁。', 10)
    latch = design.get('latch_parameters', design.get('latch'))
    if isinstance(latch, dict) and latch:
        labels={'type':'方案','closed_degrees':'闭合角度/度','open_degrees':'打开角度/度',
                'rigid_overlap_mm':'刚性搭接/mm','metal_hinge':'铰链轴',
                'spring_thickness_mm':'簧片厚度/mm','index_nib_mm':'定位凸点/mm',
                'nominal_deflection_mm':'旋转时簧片挠度/mm','spring_load_bearing':'簧片是否承载'}
        table(['锁扣设计参数','最终记录'],[(labels.get(k,str(k)),prose(v)) for k,v in latch.items()],
              [6.0,11.5],size=9.5)
    para('M3金属轴与螺母用于调整转动间隙，不能把拨片拧死后靠磨损获得松动，也不依赖PLA自攻螺纹反复开关。锁定调好的间隙后，确认转拨片不会带着螺钉松开，定位环不会随拨片一起旋转。', 10)
    para('先手动试开闭，不装电子板时确认止挡和卡位；再放入模块，确认板边承托到位、压框不压元件，最后检查翻盖完整运动轨迹。上平台装回后如遮挡开启路径，应先拆上平台检修，不强扭压框。', 10)

    heading('65.4  电池和喇叭的固定', 2, False)
    image('04_battery_speaker.png', max_height=13.4, optional=True)
    para('电池包按实测76×40×20mm布置，2S串联已由用户确认。挡边限制横向滑移，两端旋转压片提供竖向约束；支承条铺2mm EVA，压片只约束端部塑料外壳，不挤压电芯，出线口保留自然弯曲和检修空间。商品图中的两节并联电池盒不能替代已确认的2S接法。', 10)
    para('喇叭本体按Ø40mm、厚14mm，两耳孔心距48mm、孔径4mm布置。安装耳相对本体底面的高度尚未实测，因此用可调螺母垫柱与平垫调平；不能预设一个固定柱高后将安装耳强行压弯。固定时保留出声孔与引线出口。', 10)
    para('线束沿预留通道整理，避免经过拨片扫掠区、压框铰链或电机转动区域。电池、驱动和降压区的较粗导线不挤压信号排针；此处机械布置不改变原A1供电和接线要求。', 10)
    if design.get('unmeasured_features'):
        para('仍待实物核对：'+prose(design['unmeasured_features'])+'。', 10)

    heading('65.5  五金统计和装配顺序', 2, False)
    table(['五金','规格','数量','用途与注意事项'], hardware_rows(design.get('hardware')),
          [4.0,3.9,1.7,7.9], size=9.5)
    for text in [
        '1．先清理打印毛刺，空装金属轴、定位环、拨片和压框，检查环的防转与防脱以及两个旋转止挡。活动件需能顺畅转动，不能用硬拧螺钉消除打印干涉。',
        '2．先固定A1主PCB和有安装孔模块，再放入无孔模块，逐一核对座号与接口朝向。锁扣只需挡住压框开启，不把PCB压弯。',
        '3．插上实际杜邦线并模拟插拔USB、SWD和TF卡，检查背面针的架空间隙；再安装电池、喇叭和较粗导线。',
        '4．重新装上上平台，检查四柱、线束、桶壳和舵机机构互不挤压。断电手动检查盖框检修路径，再按原电气章节逐步通电。',
    ]:
        para(text, 10)
    for note in notes(design.get('assembly_notes')):
        para(note, 10)

    heading('65.6  打印项目和实际切片记录', 2, True)
    if plates:
        count_note = '最终记录为两项打印任务。' if len(plates)==2 else f'当前记录有{len(plates)}项打印任务，以本表为准；不把两盘目标写成已实现。'
    else:
        count_note = '打印任务以final_printing.json的最终记录为准，当前尚未填入。'
    para(count_note+'两片大板各自是一整片；压框、拨片、定位环等小件须一并核对，不能只确认两块板放得下。', 10)
    rows=[]
    for i, plate in enumerate(plates, 1):
        rows.append((f'第{i}项\n'+prose(plate.get('file')),
                     prose(plate.get('objects'), '物体清单待确认'),
                     duration(plate.get('estimated_seconds')), mass(plate.get('filament_g'))))
    if not rows:
        rows=[('待最终工程文件','待物体清单','待最终切片','待最终切片')]
    rows.append(('合计','各项目分别启动', duration(printing.get('total_seconds')),
                 mass(printing.get('total_filament_g'))))
    table(['工程文件','包含物体','切片时间','PLA用量'],rows,[6.2,5.3,3.2,2.8],size=9.3)
    status = str(printing.get('status','PENDING')).upper()
    if status in {'PASS','SUCCESS','OK'}:
        para('最终记录标记切片检查通过。'+('切片软件版本：'+prose(printing.get('slicer_version'))+'。' if printing.get('slicer_version') else '')+'本表仅是切片估算，不是实物计时；人工取件、清床和换盘时间另计。', 10)
    else:
        para('切片完成状态尚未明确标记通过；本表中缺失的时间和耗材保持待最终切片，不沿用旧原型数字。', 10)
    para('交付工程不含可直接运行的G-code。作为项目打开，选择实际P2S、喷嘴、热床和PLA重新切片；检查全部物体、朝向、辅助结构与热床边界后再发送。原生工程的几何重读检查与实物打印是不同验证。', 10)
    if isinstance(printing.get('settings'), dict) and printing['settings']:
        names={'printer':'打印机与喷嘴','material':'耗材','layer_height_mm':'层高/mm',
               'wall_loops':'墙层数','infill':'稀疏填充','auto_support':'全局自动支撑',
               'sequence':'打印顺序','brim_mm':'防翘边宽度/mm',
               'nozzle_wrapping_detection':'喷嘴缠料检测'}
        values=lambda v:('开启' if v else '关闭') if isinstance(v,bool) else ('逐层打印' if v=='by layer' else prose(v))
        table(['参数','最终记录'], [(names.get(k,str(k)),values(v)) for k,v in printing['settings'].items()],
              [6.0,11.5],size=9.5)
    elif printing.get('settings'):
        para('最终参数记录：'+prose(printing['settings']), 10)
    for note in notes(printing.get('notes')):
        para(note, 10)

    heading('65.7  第一项打印任务的摆放', 2, True)
    image('05_plate1.png', max_height=17.0)
    para('按最终工程的方向和位置打印，保持100%尺寸及逐层打印。不要用自动朝向、自动排布或逐件打印覆盖经过核对的排布。支撑设置与辅助结构按该工程保存的实际参数执行。', 10)
    heading('65.8  第一项打印任务的热床核对', 2, True)
    image('07_plate1_bed.png', max_height=18.3)
    para('切片后查看首层，确认刚性底脚、各独立小件和需要的附着边均有连续路径，未超出实际可打印区。不要把单层brim当作刚性承力底座。', 10)

    heading('65.9  第二项打印任务的摆放', 2, True)
    image('06_plate2.png', max_height=17.0)
    para('第一项完成后取下模型并清理热床，再启动第二项。用物体清单核对独立盖框、拨片、定位环和其他附件的数量，避免打印结束后才发现缺活动件。', 10)
    heading('65.10  第二项打印任务的热床核对', 2, True)
    image('08_plate2_bed.png', max_height=18.3)
    para('保持保存的模块座、接口与槽口方向；不要把上平台或底板切段来迁就排布。若实际设备、耗材或辅助选项改变可打印边界，应重新检查整盘再启动。', 10)

    heading('65.11  打印检查和拆除辅助结构', 2, True)
    for text in [
        '清理热床上的残料、手油和胶块，重新放正并按设备流程调平和校准；打印机用标准速度模式。按所用PLA与热床要求复核温度，不能只凭几何模型保证粘附。',
        '观察首层和中途板面稳定性。发现脱底、翘曲、明显晃动或喷头刮碰时停止处理，不让机器继续在空中挤料形成炒面。',
        '完全冷却后先取整件，再托住板面逐个处理辅助连接点；用斜口钳剪除专用辅助框架和起始边，修平残余小凸点。不抓板端扭折，不把底板或上平台切开、拼接。',
        '打印后先空装锁扣做开闭检查，再试装模块。检查簧片没有裂纹、拨片的刚性重叠和止挡有效；随后分阶段进行静态加载与机构调试。',
    ]:
        para(text,10)
    for note in notes(design.get('print_notes')):
        para(note,10)
    physical = printing.get('physical_print_test') is True or printing.get('printed') is True
    if printing.get('unprinted') is True:
        physical = False
    loaded = (printing.get('load_tested') is True or printing.get('loadtested') is True or
              printing.get('load_test') is True)
    para('本轮验证边界：'+('实物打印状态在最终记录中标为已执行；具体通过项目仍以实测记录为准。' if physical else '新版尚未完成实物打印验证。')+
         ('承重试验状态在最终记录中标为已执行；不能扩展到未测工况。' if loaded else '尚未完成承重试验，无额定承重值。')+
         '几何、封闭网格、切片及包络检查不能保证零失败或与原木板等强。原330步骤、电气路线和未改动的装车接口继续保留。',10)

    # Restore the authored block at the original chapter location if a later
    # user chapter exists; no later chapter or section is silently discarded.
    if successor is not None:
        created = [el for el in body if el not in retained_nodes and el.tag != qn('w:sectPr')]
        for element in created:
            body.remove(element)
            successor.addprevious(element)
    update = doc.settings._element.find(qn('w:updateFields'))
    if update is None:
        update=OxmlElement('w:updateFields');doc.settings._element.append(update)
    update.set(qn('w:val'),'true')
    target=work/NAME
    temporary=work/(NAME+'.writing.docx')
    doc.save(temporary)
    new=Document(temporary)
    if steps(old)!=steps(new):
        temporary.unlink();raise ValueError('原330步骤发生变化，停止发布暂存稿。')
    if table_texts(old)[:66]!=table_texts(new)[:66]:
        temporary.unlink();raise ValueError('前66表发生变化，停止发布暂存稿。')
    temporary.replace(target)
    audit.update({'baseline_sha256':sha(before),'output_sha256':sha(target),
                  'output':str(target),'steps_preserved':330,'original_tables_preserved':66,
                  'figure_numbers':figure_numbers,'draft_incomplete':incomplete,
                  'published_manual_modified':False,'word_process_started':False,
                  'fields_need_update':True,'render_and_visual_qa_pending':True})
    (work/'edit_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return audit


def main():
    repo=Path(__file__).resolve().parents[4]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=repo)
    parser.add_argument('--model-dir',type=Path)
    parser.add_argument('--work-dir',type=Path)
    parser.add_argument('--published',type=Path)
    parser.add_argument('--design',type=Path)
    parser.add_argument('--printing',type=Path)
    parser.add_argument('--schema',action='store_true',help='Print the metadata contract; write no files.')
    parser.add_argument('--check-inputs',action='store_true',help='Validate metadata and files; write no Word.')
    parser.add_argument('--allow-incomplete',action='store_true',help='Allow a visibly marked draft with missing files.')
    args=parser.parse_args()
    if args.schema:
        print(json.dumps(schema_example(),ensure_ascii=False,indent=2));return
    args.repo=args.repo.resolve()
    root=(args.model_dir or args.repo/'hardware/mechanical/print-backup/mounted-20261031').resolve()
    args.work_dir=(args.work_dir or args.repo.parent/'.p2s-mounted-20261031/manual').resolve()
    args.published=(args.published or args.repo/'docs/manual'/NAME).resolve()
    args.design=(args.design or root/'source/design.json').resolve()
    args.printing=(args.printing or root/'checks/final_printing.json').resolve()
    design=load_json(args.design,required=True)
    printing=load_json(args.printing)
    inputs=input_report(root,design,printing)
    if args.check_inputs:
        print(json.dumps(inputs,ensure_ascii=False,indent=2));return
    if not args.allow_incomplete and (inputs['missing_required_figures'] or inputs['missing_projects']):
        raise ValueError('缺少最终图片或已列出的工程文件。只读检查：\n'+json.dumps(inputs,ensure_ascii=False,indent=2))
    audit=author(args,root,design,printing,inputs)
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__=='__main__':
    try:
        main()
    except (OSError,ValueError,zipfile.BadZipFile) as error:
        print(f'ERROR: {error}',file=sys.stderr)
        raise SystemExit(1)
