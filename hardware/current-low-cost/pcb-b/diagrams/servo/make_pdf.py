# -*- coding: utf-8 -*-
"""把舵机接线示意图排成 A4 横向单页 PDF（200 dpi，整页留边），便于打印或入册。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

D = Path(r'D:\Work\嵌入式课设\.servo-diagram-20261105')
png = D / 'servo_wiring_B1.png'
pdf = D / 'servo_wiring_B1_A4.pdf'

DPI = 200
A4 = (int(297 / 25.4 * DPI), int(210 / 25.4 * DPI))   # 2339 x 1654
poster = Image.new('RGB', A4, 'white')
im = Image.open(png).convert('RGB')

margin = int(10 / 25.4 * DPI)
foot = int(8 / 25.4 * DPI)
avail_w, avail_h = A4[0] - 2 * margin, A4[1] - 2 * margin - foot
scale = min(avail_w / im.width, avail_h / im.height)
new = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
x = (A4[0] - new.width) // 2
y = margin + (avail_h - new.height) // 2
poster.paste(new, (x, y))

d = ImageDraw.Draw(poster)
f = ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', int(3.2 / 25.4 * DPI), index=0)
note = 'SG90 舵机接线示意图（B1 印制板 + A1 固件）· 设计检查通过，实物未通电验证 · 2026-11-05'
w = d.textlength(note, font=f)
d.text(((A4[0] - w) / 2, A4[1] - foot - int(1.6 / 25.4 * DPI)), note, font=f, fill='#455A64')

poster.save(pdf, 'PDF', resolution=float(DPI))
print('saved', pdf, pdf.stat().st_size, A4, 'scale %.3f' % scale)