# -*- coding: utf-8 -*-
"""对渲染出的 PNG 做像素级抽查：导线是否真的落在应到的坐标、色块是否正确、页边是否干净。"""
from PIL import Image

P = r'D:\Work\嵌入式课设\.servo-diagram-20261105\servo_wiring_B1.png'
im = Image.open(P).convert('RGB')
pv = im.load()


def near(c, target, tol=60):
    return all(abs(a - b) <= tol for a, b in zip(c, target))


RED, BRN, ORG, GRY, BLU = (198, 40, 40), (109, 76, 65), (239, 108, 0), (55, 71, 79), (21, 101, 192)
checks = [
    ('5V rail at x=1300,y=234', (1300, 234), RED),
    ('5V rail at x=1560,y=234', (1560, 234), RED),
    ('GND vertical x=1490,y=400', (1490, 400), BRN),
    ('GND vertical x=1490,y=620', (1490, 620), BRN),
    ('GND run x=1550,y=636', (1550, 636), BRN),
    ('PWM vertical x=1000,y=650', (1000, 650), ORG),
    ('PWM run x=1300,y=690', (1300, 690), ORG),
    ('R6 tap x=330,y=600', (330, 600), GRY),
    ('VCC chip centre', (1625, 234), RED),
    ('GND chip centre', (1625, 636), BRN),
    ('SIG chip centre', (1625, 690), ORG),
]
bad = 0
for name, (x, y), col in checks:
    c = pv[x, y]
    ok = near(c, col)
    if not ok:
        # 允许 ±1px 抖动
        ok = any(near(pv[x + dx, y + dy], col) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    print(('OK  ' if ok else 'FAIL'), name, c, 'expect~', col)
    bad += 0 if ok else 1

# 底色带
print('band1 fill', pv[150, 160], 'expect pinkish')
print('band2 fill', pv[150, 470], 'expect bluish')
print('servo fill', pv[1900, 200], 'expect cream')

# 页边洁净度
margin_ink = []
for x in range(im.width):
    for y in list(range(0, 20)) + list(range(im.height - 20, im.height)):
        if pv[x, y] != (255, 255, 255):
            margin_ink.append((x, y))
for y in range(im.height):
    for x in list(range(0, 20)) + list(range(im.width - 20, im.width)):
        if pv[x, y] != (255, 255, 255):
            margin_ink.append((x, y))
print('margin ink pixels:', len(margin_ink))

# 统计彩色像素占比，确认有实际内容
import collections
cnt = collections.Counter()
for y in range(0, im.height, 2):
    for x in range(0, im.width, 2):
        r, g, b = pv[x, y]
        if r > 245 and g > 245 and b > 245:
            cnt['white'] += 1
        elif abs(r - g) < 12 and abs(g - b) < 12:
            cnt['gray'] += 1
        else:
            cnt['color'] += 1
tot = sum(cnt.values())
print({k: f'{v / tot:.1%}' for k, v in cnt.items()})
print('RESULT', 'PASS' if bad == 0 and len(margin_ink) == 0 else 'CHECK')