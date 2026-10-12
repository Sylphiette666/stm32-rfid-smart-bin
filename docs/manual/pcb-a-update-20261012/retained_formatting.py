"""Formatting helpers retained from the previous illustrated manual update."""

def format_run(r, size=None, bold=None):
    r.font.name = '微软雅黑'
    r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), '微软雅黑')
    if size is not None: r.font.size = Pt(size)
    if bold is not None: r.bold = bold
    r.font.color.rgb = RGBColor(0, 0, 0)

def replace_text(p, text):
    saved = deepcopy(p.runs[0]._r.rPr) if p.runs and p.runs[0]._r.rPr is not None else None
    p.clear()
    r = p.add_run(text)
    if saved is not None: r._r.insert(0, saved)

def para(text, size=10.5, keep=False):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = keep
    p.paragraph_format.widow_control = True
    format_run(p.add_run(text), size)
    return p

def heading(text, level=2, newpage=False):
    p = doc.add_paragraph(text, style=f'Heading {level}')
    if newpage: p.paragraph_format.page_break_before = True
    p.paragraph_format.keep_with_next = True
    for r in p.runs: r.font.color.rgb = RGBColor(0, 0, 0)
    return p

def figure(path, caption, alt, width):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.keep_together = True
    run = p.add_run(); run.add_picture(str(path), width=Cm(width))
    for pr in run._r.xpath('.//wp:docPr'): pr.set('descr', alt)
    c = para(caption, 9.5)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.keep_together = True
    c.paragraph_format.space_after = Pt(5)
    audit.setdefault('figures', []).append({'caption': caption, 'file': path.name, 'width_cm': width})

def table(headers, rows, widths, size=9.5, center=()):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for col, width in zip(t.columns, widths): col.width = Cm(width)
    for cell, width in zip(t.rows[0].cells, widths): cell.width = Cm(width)
    for cell, value in zip(t.rows[0].cells, headers): cell.text = str(value)
    for vals in rows:
        row = t.add_row()
        for cell, width, value in zip(row.cells, widths, vals):
            cell.width = Cm(width); cell.text = str(value)
    pr = t._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        e = OxmlElement('w:'+edge); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'4'); e.set(qn('w:color'),'D9D9D9'); borders.append(e)
    pr.append(borders)
    for i, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr(); trPr.append(OxmlElement('w:cantSplit'))
        if i == 0: trPr.append(OxmlElement('w:tblHeader'))
        for j, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp = cell._tc.get_or_add_tcPr()
            margins = OxmlElement('w:tcMar')
            for side, value in [('top',65),('bottom',65),('left',80),('right',80)]:
                m = OxmlElement('w:'+side); m.set(qn('w:w'),str(value)); m.set(qn('w:type'),'dxa'); margins.append(m)
            cp.append(margins)
            if i == 0:
                shade = OxmlElement('w:shd'); shade.set(qn('w:fill'),'E9EFF5'); cp.append(shade)
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.05
                p.paragraph_format.keep_with_next = i == 0
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 or j in center else WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs: format_run(r, size, i == 0)
    return t