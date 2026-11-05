# -*- coding: utf-8 -*-
"""SG90 舵机接线示意图（B1 印制板 + A1 固件）—— PIL 绘制 + 自动排版自检。

数据来源（均已在仓库中核对）：
- PA0 = TIM2_CH1；firmware/a1/src/platform.c: servo_output() 写 TIM2->CCR1，
  PSC=1us、ARR=19999（50 Hz），脉宽 900-2100us，超出输出 0。
- J8 CORE_PA 第 4 脚 = PA0；R6 10k 下拉到 GND。
- U1 SN74AHCT125N：1A=PA0(pin2) -> 1Y=SERVO_SIG_5V(pin3)，VCC=5V_BUS(13/14)，1OE=GND。
- J20 SERVO_SIG：1=SERVO_SIG_5V，2=GND（仅信号参考）。
- J5 SERVO_PWR：1=5V_BUS，2=GND（2P 5.08 螺钉端子），C2 1000uF/16V 就近。
- J1 BAT_SW(VBAT_SW/GND) -> J2 BUCK_IN -> 5V 降压 -> J3 BUCK_OUT 5V_BUS（星形中心）。
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(r'D:\Work\嵌入式课设\.servo-diagram-20261105')
OUT.mkdir(parents=True, exist_ok=True)
SS = 2
W, H = 2000, 1400
FR = r'C:\Windows\Fonts\msyh.ttc'
FB = r'C:\Windows\Fonts\msyhbd.ttc'

img = Image.new('RGB', (W * SS, H * SS), 'white')
d = ImageDraw.Draw(img)
_cache = {}
TEXTS, SEGS, BOXES, WARN = [], [], [], []


def font(size, bold=False):
    k = (size, bold)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(FB if bold else FR, size * SS, index=0)
    return _cache[k]


def tw(s, size, bold=False):
    return d.textlength(s, font=font(size, bold)) / SS


def text(x, y, s, size=18, color='#1a1a1a', bold=False, anchor='la', tag=''):
    f = font(size, bold)
    d.text((x * SS, y * SS), s, font=f, fill=color, anchor=anchor)
    bb = d.textbbox((x * SS, y * SS), s, font=f, anchor=anchor)
    TEXTS.append(([v / SS for v in bb], s, size, tag))
    return bb


def rrect(x, y, w, h, r, fill=None, outline='#444444', width=1.5):
    d.rounded_rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS],
                        radius=r * SS, fill=fill, outline=outline, width=int(width * SS))
    BOXES.append((x, y, w, h))


def line(pts, color='#333333', width=2.5):
    d.line([(x * SS, y * SS) for x, y in pts], fill=color, width=int(width * SS), joint='curve')
    for i in range(len(pts) - 1):
        SEGS.append((pts[i], pts[i + 1], color))


def arrow(x1, y1, x2, y2, color='#333333', width=2.5, head=9):
    line([(x1, y1), (x2, y2)], color, width)
    ang = math.atan2(y2 - y1, x2 - x1)
    for s in (+1, -1):
        a = ang + s * 0.42
        d.line([(x2 * SS, y2 * SS),
                ((x2 - head * math.cos(a)) * SS, (y2 - head * math.sin(a)) * SS)],
               fill=color, width=int(width * SS))


def fit(s, max_w, size, bold=False, tag=''):
    while size > 9 and tw(s, size, bold) > max_w:
        size -= 1
    if tw(s, size, bold) > max_w:
        WARN.append(f'overflow-tight {tag}: {s!r}')
    return size


def label_box(x, y, w, h, title, lines, title_color='#111111', fill='white',
              edge='#4a5568', tsize=20, lsize=15):
    rrect(x, y, w, h, 8, fill=fill, outline=edge, width=1.8)
    s = fit(title, w - 12, tsize, True, f'title/{title}')
    text(x + w / 2, y + 10, title, s, title_color, True, anchor='ma')
    yy = y + 10 + s + 7
    for ln in lines:
        s2 = fit(ln, w - 10, lsize, False, f'line/{ln}')
        text(x + w / 2, yy, ln, s2, '#333333', anchor='ma')
        yy += s2 + 3
    if yy > y + h - 2:
        WARN.append(f'box-overflow {title!r}: content {yy - (y + h):.0f}px 超出')


def gnd(x, y, color='#37474F'):
    """接地符号：顶端在 (x,y)，向下。"""
    line([(x, y), (x, y + 12)], color, 2.5)
    for i, half in enumerate((12, 8, 4)):
        yy = y + 12 + i * 5
        line([(x - half, yy), (x + half, yy)], color, 2.5)


RED, GRN, BLU, ORG, GRY, BRN, PUR = '#C62828', '#2E7D32', '#1565C0', '#EF6C00', '#37474F', '#6D4C41', '#6A1B9A'

# ------------------------------------------------------------------ header
text(60, 30, 'SG90 舵机接线示意图（B1 印制板 + A1 固件）', 40, '#0D47A1', True, tag='title')
text(62, 86, '只画电气连接；机械数据见装配指南。数据源：pcb-b/connector-map.csv、board-geometry.json、firmware/a1/src/platform.c（2026-11-05）',
     15, GRY, tag='subtitle')
line([(60, 122), (1940, 122)], '#B0BEC5', 2)

# ------------------------------------------------------------------- bands
rrect(52, 140, 1896, 292, 12, fill='#FFF5F5', outline='#E57373', width=2)
text(68, 146, '① 5 V 主电流支路 —— 主电流只走螺钉端子，不进排针', 19, RED, True, tag='band1')
rrect(52, 448, 1896, 324, 12, fill='#F3F8FF', outline='#64B5F6', width=2)
text(68, 454, '② 3.3 V 逻辑信号支路 —— 只走排针，不承担舵机电流', 19, BLU, True, tag='band2')

# ------------------------------------------------------------- power chain
PY, PH = 206, 96
label_box(70, PY, 148, PH, '2S 18650 电池包', ['7.4 V 标称', '8.4 V 满电'], tsize=16, lsize=14)
label_box(236, PY, 152, PH, '外置保险座', ['+ 总开关', '裸电池不得直连'], tsize=16, lsize=14)
label_box(406, PY, 176, PH, 'J1 BAT_SW', ['1 = VBAT_SW', '2 = GND'], tsize=16, lsize=14)
label_box(600, PY, 184, PH, 'J2 BUCK_IN', ['→ 外置 5 V 降压', '20 AWG 短线'], tsize=16, lsize=14)
label_box(802, PY, 196, PH, 'J3 BUCK_OUT', ['1 = 5V_BUS 星形中心', '2 = GND'], tsize=16, lsize=14)
label_box(1016, PY, 212, PH, 'J5 SERVO_PWR', ['1 = 5V_BUS   2 = GND', '2P 5.08 mm 螺钉端子'],
          title_color=RED, edge=RED, tsize=16, lsize=14)

for x1, x2 in ((218, 236), (388, 406), (582, 600), (784, 802), (998, 1016)):
    arrow(x1 + 2, PY + PH / 2, x2 - 3, PY + PH / 2, GRY, 2.5)

# 5V rail + GND rail + C2
line([(1228, 234), (1600, 234)], RED, 3.2)
line([(1228, 261), (1490, 261), (1490, 636), (1600, 636)], BRN, 3.2)
# C2 between rails
line([(1400, 234), (1400, 243)], RED, 3)
line([(1372, 243), (1428, 243)], RED, 4)          # 上极板
line([(1372, 255), (1428, 255)], GRY, 4)          # 下极板
line([(1400, 255), (1400, 261)], GRY, 3)
for p in ((1400, 234), (1400, 261)):
    d.ellipse([(p[0] - 4) * SS, (p[1] - 4) * SS, (p[0] + 4) * SS, (p[1] + 4) * SS], fill=RED if p[1] == 234 else BRN)
text(1436, 174, 'C2 1000 µF/16 V', 13, PUR, True, tag='c2a')
text(1436, 192, '就近（板载）', 12, GRY, tag='c2b')
text(1240, 204, '5V_BUS 红色主线 22 AWG', 13, RED, tag='rail5v')
text(1398, 470, 'GND 公共回流', 13, BRN, tag='gndlab')

# ------------------------------------------------------------ signal chain
SY, SH = 500, 100
label_box(70, SY, 200, SH, 'STM32 核心板 PA0', ['J8 CORE_PA 第 4 脚', 'TIM2_CH1 · 50 Hz PWM'],
          title_color=BLU, edge=BLU, tsize=16, lsize=14)
label_box(300, SY + 122, 168, 62, 'R6 10 kΩ', ['PA0 下拉到 GND'], tsize=15, lsize=13)
label_box(410, SY, 256, SH, 'U1 SN74AHCT125N', ['1A = PA0（3.3 V 输入）', '1Y = SERVO_SIG_5V（5 V 输出）',
                                               'VCC = 5V_BUS，1OE = GND 常使能'],
          title_color=PUR, edge=PUR, tsize=16, lsize=13)
label_box(700, SY, 200, SH, 'J20 SERVO_SIG', ['1 = SERVO_SIG_5V', '2 = GND 仅信号参考'],
          title_color=ORG, edge=ORG, tsize=16, lsize=13)

arrow(270, SY + SH / 2, 408, SY + SH / 2, BLU, 2.5)
arrow(666, SY + SH / 2, 698, SY + SH / 2, PUR, 2.5)
text(280, 516, 'PA0', 14, BLU, True, tag='pa0lab')
# R6 tap
line([(330, SY + SH / 2), (330, SY + 122)], GRY, 2.5)
line([(330, SY + 184), (330, SY + 200)], GRY, 2.5)
gnd(330, SY + 200)
# J20.2 reference ground
line([(900, 585), (940, 585), (940, 622)], GRY, 2.5)
gnd(940, 622)
text(820, 640, 'J20.2 参考地', 13, GRY, tag='j20gnd')
# PWM signal to servo (below the brown ground drop)
line([(900, 550), (1000, 550), (1000, 690), (1600, 690)], ORG, 3.2)
text(1200, 662, 'PWM 信号 → 橙线', 13, ORG, tag='siglab')

# ------------------------------------------------------------------ servo
SX, S0, SW_, SH0 = 1600, 176, 340, 540
rrect(SX, S0, SW_, SH0, 12, fill='#FFFDE7', outline='#F9A825', width=2.2)
text(SX + SW_ / 2, 188, 'SG90 位置舵机（H12）', 21, '#E65100', True, anchor='ma', tag='servo-title')

# body
bx, by, bw, bh = SX + 68, 264, 200, 138
rrect(bx, by, bw, bh, 6, fill='#ECEFF1', outline='#546E7A', width=2)
text(bx + bw / 2, by + 14, 'SG90 本体', 16, '#263238', True, anchor='ma', tag='servo-body')
rrect(bx + 78, by - 14, 44, 22, 3, fill='#B0BEC5', outline='#546E7A', width=1.6)
text(bx + bw / 2, by + 44, '舵盘 / 摇臂', 14, GRY, anchor='ma', tag='servo-horn')
text(bx + bw / 2, by + 68, '非 360° 连续旋转', 13, GRY, anchor='ma', tag='servo-nc')
text(bx + bw / 2, by + 90, '保留原舵盘与中心螺钉', 12, GRY, anchor='ma', tag='servo-keep')
text(bx + bw / 2, by + 112, '扭矩≈1.8 kg·cm @4.8 V', 12, GRY, anchor='ma', tag='servo-tq')

text(SX + 32, 428, '轴在盖铰链轴后方 50 mm', 13, '#4E342E', tag='servo-a1')
text(SX + 32, 450, '摇臂与舵盘等高、平行', 13, '#4E342E', tag='servo-a2')
text(SX + 32, 472, '开盖约 70°；维护约 120°', 13, '#4E342E', tag='servo-a3')
text(SX + 32, 494, '维护位须断电并拆下拉杆', 13, '#4E342E', tag='servo-a4')

# terminals
for yy, col, t1, t2 in ((234, RED, '① 红线  VCC 5 V', '来自 J5.1'),
                        (636, BRN, '② 棕/黑线  GND', '回到 J5.2'),
                        (690, ORG, '③ 橙线  PWM 信号', '来自 J20.1')):
    rrect(SX + 14, yy - 15, 22, 30, 4, fill=col, outline=col, width=1)
    text(SX + 46, yy - 20, t1, 15, col, True, tag=f'term/{t1}')
    text(SX + 46, yy + 2, t2, 12, GRY, tag=f'term2/{t2}')

# warning inside servo block
rrect(SX + 16, 546, SW_ - 32, 52, 8, fill='#FFEBEE', outline=RED, width=1.8)
text(SX + SW_ / 2, 552, '禁止整根 3 芯线直接插 J20', 14, RED, True, anchor='ma', tag='warn1')
text(SX + SW_ / 2, 572, '配电处先拆成 电源 / 信号 两路', 13, '#333333', anchor='ma', tag='warn2')

# ------------------------------------------------------------------ notes
NY = 796
rrect(52, NY, 1896, 556, 12, fill='#FAFAFA', outline='#90A4AE', width=2)
text(68, NY + 12, '③ 固件参数 / 接线要点 / 机械与调试', 19, '#263238', True, tag='notes-title')

def note_box(x, w, title, lines, color):
    rrect(x, NY + 50, w, 240, 8, fill='white', outline='#B0BEC5', width=1.6)
    text(x + 14, NY + 60, title, 17, color, True, tag=f'nt/{title}')
    yy = NY + 88
    for ln in lines:
        s = fit(ln, w - 30, 14, False, f'note/{ln}')
        text(x + 15, yy, ln, s, '#333333', tag=f'note/{ln[:8]}')
        yy += s + 6
    if yy > NY + 288:
        WARN.append(f'note-overflow {title!r}: +{yy - (NY + 290):.0f}px')

note_box(70, 580, '固件侧（firmware/a1）', [
    '· PWM：TIM2_CH1 / PA0；PSC=1 µs、ARR=19999 → 50 Hz（20 ms）',
    '· 有效脉宽 900–2100 µs；越界一律输出 0（关断，不给力矩）',
    '· 默认 close_us = open_us = 1500，需先标定开/关两点',
    '· 单步测试：串口发  SERVO 1500 （取值 900–2100）',
    '· 复位先 servo_output(0)，上电桶盖不会自己抽动',
    '· 电平转换在板上 U1 完成，核心板只出 3.3 V',
], '#0D47A1')

note_box(676, 580, '接线要点（三根线怎么分）', [
    '· 5 V 主电源：J5.1 → 红线，22 AWG，主电流只走这里',
    '· 主地回流：J5.2 → 棕/黑线；不要从 J20.2 借道',
    '· PWM 信号：J20.1 → 橙线，逻辑电流（毫安级）',
    '· J20.2 只作信号参考地，板上已与 5V_BUS 地共点',
    '· 延长线在配电处剪开：红+棕 → J5，橙 → J20',
    '· C2 1000 µF/16 V 就近并在 J5 两端，抑制开盖压降',
], RED)

note_box(1282, 560, '机械与调试顺序', [
    '· 舵机轴在盖铰链轴后方 50 mm，摇臂与舵盘等高平行',
    '· 正常开盖约 70°；维护约 120°，须断电拆拉杆',
    '· 上电前架空舵机试转，确认方向与限位再装拉杆',
    '· 持续嗡嗡声/发热 = 行程顶死，立刻断电放宽 us',
    '· 舵机架 60×190 立架 + 约 80×40×5 托片定位',
], GRN)

text(70, NY + 306, '本图为设计/接线图，取自仓库现有连接表与固件；J5 极性、C2 位置为板载设计位号，通电前请用万用表复核。',
     14, GRY, tag='foot1')
text(70, NY + 330, '整机尚未做实物通电验收：以下仅为设计检查结论，不代表已装配实测。',
     14, GRY, tag='foot2')
rrect(70, NY + 366, 430, 40, 8, fill='#FFF3E0', outline=ORG, width=1.8)
text(84, NY + 376, '状态：设计检查通过 · 实物未通电验证', 16, '#E65100', True, tag='status')
rrect(520, NY + 366, 600, 40, 8, fill='#E8F5E9', outline=GRN, width=1.8)
text(534, NY + 376, '标定：SERVO 1500 → 装摇臂 → 找开/关点 → 写入设置', 15, '#1B5E20', tag='calib')

# legend
rrect(70, NY + 428, 1772, 72, 8, fill='white', outline='#B0BEC5', width=1.6)
lx = 88
for col, s in ((RED, '5 V 主电源（J5.1，22 AWG）'), (BRN, 'GND 回流（J5.2）'),
               (ORG, 'PWM 信号（J20.1，5 V）'), (BLU, '3.3 V 逻辑侧（PA0）'),
               (PUR, '电平转换 U1')):
    rrect(lx, NY + 440, 20, 20, 3, fill=col, outline=col, width=1)
    text(lx + 28, NY + 442, s, 14, '#263238', tag=f'legend/{s[:4]}')
    lx += 28 + tw(s, 14) + 34
text(88, NY + 470, '① ② ③ 为支路编号；同一网络使用同一颜色；本图导线零交叉（交叉处不画点即表示不相连）。',
     13, GRY, tag='legend-note')

# ------------------------------------------------------------------ checks
def seg_hits_rect(p, q, r, pad=1.0):
    x1, y1 = p; x2, y2 = q
    rx, ry, rw, rh = r
    rx, ry, rw, rh = rx - pad, ry - pad, rw + 2 * pad, rh + 2 * pad
    n = max(2, int(math.dist(p, q) / 3) + 1)
    for i in range(n + 1):
        t = i / n
        x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        if rx <= x <= rx + rw and ry <= y <= ry + rh:
            return True
    return False


def overlaps(a, b, pad=0.5):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


for i in range(len(TEXTS)):
    a = TEXTS[i][0]
    if a[0] < 0 or a[1] < 0 or a[2] > W or a[3] > H:
        WARN.append(f'out-of-canvas {TEXTS[i][1]!r} {a}')
    for j in range(i + 1, len(TEXTS)):
        b = TEXTS[j][0]
        if overlaps(a, b):
            WARN.append(f'text-overlap {TEXTS[i][1]!r} <> {TEXTS[j][1]!r}')

for p, q, col in SEGS:
    for bb, s, size, tag in TEXTS:
        if tag.startswith('term') or tag.startswith('note') or tag.startswith('nt'):
            if seg_hits_rect(p, q, bb):
                WARN.append(f'wire-crosses-text {s!r} seg {p}->{q}')


def _cross(a, b, c, e):
    """两线段是否在内部相交（端点相接不算）。"""
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)
    o1, o2 = orient(a, b, c), orient(a, b, e)
    o3, o4 = orient(c, e, a), orient(c, e, b)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    return False


crossings = 0
for i in range(len(SEGS)):
    for j in range(i + 1, len(SEGS)):
        if _cross(SEGS[i][0], SEGS[i][1], SEGS[j][0], SEGS[j][1]):
            crossings += 1
            WARN.append(f'wire-crossing {SEGS[i][0]}->{SEGS[i][1]} X {SEGS[j][0]}->{SEGS[j][1]}')

img = img.resize((W, H), Image.LANCZOS)
png = OUT / 'servo_wiring_B1.png'
img.save(png, optimize=True)
stats = {
    'canvas': [W, H], 'supersample': SS,
    'text_blocks': len(TEXTS), 'wire_segments': len(SEGS), 'boxes': len(BOXES),
    'warnings': sorted(set(WARN)), 'wire_crossings': crossings,
}
(OUT / 'layout-stats.json').write_text(__import__('json').dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
print('saved', png, png.stat().st_size, img.size)
print('texts', len(TEXTS), 'segs', len(SEGS), 'boxes', len(BOXES), 'crossings', crossings)
if WARN:
    print('--- WARNINGS', len(WARN))
    seen = set()
    for w in WARN:
        if w not in seen:
            print('  ', w)
            seen.add(w)
else:
    print('layout self-check: OK')