"""Measured sensor interfaces for the four wall jobs, mm.

All fits are provisional until real components are fitted. No waterproof rating.
Wall coordinates u across, v up, z out; all new pieces have a flat printing face.
"""
import cadquery as cq


def extend(parts, save, box, cyl, hole, slot, union):
    instances = []
    features = []
    extra = []

    def add(name, shape, count=1):
        save(name, shape)
        extra.extend([name] * count)

    def install(name, wall, origin, rotation=None):
        instances.append(dict(name=name, wall=wall, origin=origin,
                              rotation=rotation or [0, 0, 0]))

    def pad_holes(wallname, origin, size, centres, diameter=3.4, slots=False):
        u, v = origin
        w, h = size
        s = parts[wallname].fuse(box(u, v, 1.6, w, h, 3.9))
        for x, y in centres:
            if slots:
                s = slot(s, u+x, v+y, 9, diameter, h=10, angle=90)
            else:
                s = hole(s, u+x, v+y, r=diameter/2, h=10, csk=True)
        save(wallname, s)
        features.append(dict(wall=wallname, origin_uv=[u, v], pad_size=[w, h],
                             hole_centres_uv=[[u+x, v+y] for x, y in centres],
                             diameter=diameter, vertical_slot_length=9 if slots else None))

    # Beam break: two external identical seats. Optical axes at the same world X=100,
    # Z=150, 30mm below rim; right wall's u axis is reversed in the assembly.
    seat = box(0, 0, 0, 30, 28, 3)
    seat = slot(seat, 15, 19.2, 14, 8, h=20, angle=90)
    for x in [7.4, 20.3]:
        seat = seat.fuse(box(x, 3.7, 3, 2.3, 20.6, 9.3))
    seat = seat.fuse(box(7.4, 24.3, 3, 15.2, 2, 9.3))
    for x in [4, 26]:
        seat = seat.fuse(cyl(x, 8.7, 0, 3.6, 12.3))
        seat = hole(seat, x, 8.7, r=1.7, h=16)
    # Bottom exit is open; shell is captured by the side walls and rear bar.
    seat = seat.cut(box(11, -1, -1, 8, 5, 16))
    add('BEAM_SEAT', seat, 2)
    bar = box(0, 0, 0, 30, 5, 2.4)
    for x in [4, 26]:
        bar = hole(bar, x, 2.5, r=1.7, h=6)
    add('BEAM_RETAINER', bar, 2)
    for wallname, centre in [('W03_LEFT', 100), ('W04_RIGHT', 60)]:
        origin = (centre-15, 130.8)
        pad_holes(wallname, origin, (30, 28), [(4, 8.7), (26, 8.7)], slots=True)
        s = slot(parts[wallname], centre, 150, 17, 9, h=12, angle=90)
        save(wallname, s)
        install('BEAM_SEAT', wallname, [origin[0], origin[1], 5.5])
        install('BEAM_RETAINER', wallname, [origin[0], origin[1]+6.2, 17.8])
        features.append(dict(wall=wallname, function='beam optical window', centre_uv=[centre,150],
                             slot_width=9, slot_length=17, adjustment_each_direction_mm=2.8))

    # Generic PCB cradles clamp only the long edges. Left/right are open for pins,
    # probes and trimmer access. Screw spacing is outside the measured PCB outline.
    def pcb_cradle(prefix, length, width, wallname, origin):
        w, h = length+16, width+10
        base = box(0, 0, 0, w, h, 2)
        base = base.cut(box(9, 6, -1, length-2, width-2, 5))
        for y in [3, width+4.4]:
            base = base.fuse(box(7.5, y, 2, length+1, 2.6, 3))
        centres = [(4,3.5),(w-4,3.5),(4,h-3.5),(w-4,h-3.5)]
        for x,y in centres:
            base = base.fuse(cyl(x,y,0,3.3,7.3))
            base = hole(base,x,y,r=1.7,h=12)
        add(prefix+'_CRADLE', base)
        strip = box(0,0,0,w,5.6,2.4)
        for x in [4,w-4]:strip=hole(strip,x,2.8,r=1.7,h=6)
        add(prefix+'_EDGE_BAR',strip,2)
        pad_holes(wallname,origin,(w,h),centres)
        install(prefix+'_CRADLE',wallname,[*origin,5.5])
        install(prefix+'_EDGE_BAR',wallname,[origin[0],origin[1]+.7,12.8])
        install(prefix+'_EDGE_BAR',wallname,[origin[0],origin[1]+h-6.3,12.8])
        features.append(dict(wall=wallname,function=prefix+' PCB seat',origin_uv=list(origin),
                             pcb_outline=[length,width],pcb_lower_left_local=[8,5],
                             pcb_support_z=10.5,clamp_gap_mm=2.3,
                             note='Open header side. Thin insulating shim if needed; do not bend PCB.'))
    # Front approach module on a horizontal shelf: a side-looking probe points
    # towards the user rather than sideways along the front wall.
    # Board cradle is built separately, then mounted to an L shelf through four bolts.
    pcb_cradle('LIGHT',28,20,'W03_LEFT',(75,78))

    # DHT bare body12x16x6: open lower lead exit, edge ledges, perforated removable guard.
    base=box(0,0,0,28,30,2)
    for x in [5.4,20.3]:base=base.fuse(box(x,5,2,2.3,18,7.5))
    base=base.fuse(box(5.4,22,2,17.2,2,7.5))
    for x in [3,25]:
        base=base.fuse(cyl(x,15,0,3,9.5));base=hole(base,x,15,r=1.7,h=13)
    base=base.cut(box(9,0,-1,10,6,5))
    add('DHT_SEAT',base)
    guard=box(0,0,0,28,30,1.6)
    for x in [8,12,16,20]:guard=guard.cut(box(x,7,-1,2,14,5))
    guard=guard.cut(box(9,-1,-1,10,7,5))
    for x in [3,25]:guard=hole(guard,x,15,r=1.7,h=5)
    add('DHT_GUARD',guard)
    pad_holes('W03_LEFT',(28,78),(28,30),[(3,15),(25,15)])
    install('DHT_SEAT','W03_LEFT',[28,78,5.5])
    install('DHT_GUARD','W03_LEFT',[28,78,15])

    # Removable approach sensor shelf. Print on the broad flange, turn90deg to install.
    # Cradle31x20 at local x=8..39, y=5..25; probe extension beyond x=39 to49.
    s=box(0,0,0,47,30,2.4)
    for y in [3,24.4]:s=s.fuse(box(7.5,y,2.4,32,2.6,3))
    for x in [4,43]:
        for y in [3.5,26.5]:s=s.fuse(cyl(x,y,0,3.3,7.7));s=hole(s,x,y,r=1.7,h=12)
    s=s.fuse(box(0,0,0,3,30,24))
    for y in [6,24]:s=s.cut(cyl(-1,y,17,1.7,6,(1,0,0)))
    # Side triangles brace the cantilever, without enclosing the adjustment pot.
    for y in [0,27.6]:
        tri=cq.Workplane('XZ',origin=(0,y+2.4,0)).polyline([(0,0),(25,0),(0,7)]).close().extrude(2.4).val()
        s=s.fuse(tri)
    for y in [.5,23.5]:s=s.cut(box(-1,y,7.7,4.2,6,2.6))
    add('APPROACH_SHELF',s)
    strip=box(0,0,0,47,5.6,2.4)
    for x in [4,43]:strip=hole(strip,x,2.8,r=1.7,h=6)
    add('APPROACH_EDGE_BAR',strip,2)
    # Shelf fastening wall coordinates. Mounted above control pod, left rear pins open.
    pad_holes('W01_FRONT',(56,140),(32,28),[(7,17),(25,17)])
    # Map shelf x out, y across, z up. Rotation supplied as a full mapping below.
    instances.append(dict(name='APPROACH_SHELF',wall='W01_FRONT',origin=[57,140,5.5],
                          matrix=[[0,1,0],[0,0,1],[1,0,0]]))
    for yy in [.7,23.7]:
        instances.append(dict(name='APPROACH_EDGE_BAR',wall='W01_FRONT',origin=[57+yy,147.7,5.5],
                              matrix=[[0,1,0],[0,0,1],[1,0,0]]))

    # KCD1 on external left lower wall, local electrical cavity stays outside waste.
    power=box(0,0,0,42,34,2)
    for x in [0,39.6]:power=power.fuse(box(x,0,2,2.4,34,32))
    for y in [0,31.6]:power=power.fuse(box(0,y,2,42,2.4,32))
    for x in [5,37]:
        for y in [5,29]:power=power.fuse(cyl(x,y,0,3.4,34));power=hole(power,x,y,r=1.7,h=38)
    power=power.cut(box(16,-1,7,10,5,12))
    add('POWER_POD',power)
    cover=box(0,0,0,42,34,2)
    cover=cover.cut(box(11.3,10.8,-1,19.4,12.4,5))
    for x in [5,37]:
        for y in [5,29]:cover=hole(cover,x,y,r=1.7,h=5)
    add('POWER_INSERT',cover)
    pad_holes('W03_LEFT',(75,25),(42,34),[(5,5),(37,5),(5,29),(37,29)])
    install('POWER_POD','W03_LEFT',[75,25,5.5]);install('POWER_INSERT','W03_LEFT',[75,25,39.5])

    # Fixed ultrasonic beam, supported by two independent interior shelf brackets.
    bracket=box(0,0,0,30,26,3)
    bracket=bracket.fuse(box(0,14,0,30,3,15))
    for x in [0,27]:bracket=bracket.fuse(box(x,5,3,3,9,10))
    for x in [6,24]:bracket=hole(bracket,x,5,r=1.7,h=8)
    bracket=bracket.cut(cyl(15,13,9,1.7,6,(0,1,0)))
    add('BEAM_LEDGE',bracket,2)
    for wallname,centre in [('W03_LEFT',35),('W04_RIGHT',125)]:
        pad_holes(wallname,(centre-15,145),(30,26),[(6,5),(24,5)])
        instances.append(dict(name='BEAM_LEDGE',wall=wallname,origin=[centre+15,145,0],
                              matrix=[[-1,0,0],[0,1,0],[0,0,-1]]))
    beam=box(0,0,0,144,35,3)
    # Near-full PCB aperture leaves0.8mm peripheral bearing. No M2 screws inØ1.5 PCB holes.
    beam=beam.cut(box(50.3,8.05,-1,43.4,18.9,7))
    for x in [9,135]:beam=hole(beam,x,17.5,r=1.7,h=8)
    for x in [47,97]:
        for y in [5,30]:beam=hole(beam,x,y,r=1.4,h=8)
    for y in [0,32.6]:beam=beam.fuse(box(15,y,3,114,2.4,3))
    # Clear the vertical faces of the two independent ledges, retain bolt lands.
    for x in [0,140.8]:beam=beam.cut(box(x,-1,-1,3.2,37,10))
    # Pin-bank access notch at the front long edge of the sensor window.
    beam=beam.cut(box(65,26.9,-1,14,5,9))
    add('ULTRASONIC_BEAM',beam)
    # Small corner retainers grip the board back edges; central board/pins remain open.
    ret=box(0,0,0,8,30,2)
    for y in [2.5,27.5]:ret=hole(ret,3,y,r=1.4,h=6)
    add('ULTRASONIC_RETAINER',ret,2)
    instances.append(dict(name='ULTRASONIC_BEAM',world_origin=[17.5,3,162],
                          world_matrix=[[0,1,0],[1,0,0],[0,0,1]]))
    # Note world_matrix has a reflection for beam x; this is only mesh placement of a symmetric part.
    for x in [44,94]:
        instances.append(dict(name='ULTRASONIC_RETAINER',world_origin=[20,3+x,166.6],
                              world_matrix=[[0,1,0],[1,0,0],[0,0,1]]))

    # Microswitch adjustable plate uses M2 (fits nominalØ2.35), not M2.5.
    # Thickness is unconstrained: bolts can be chosen after fitting the actual switch.
    s=box(0,0,0,34,28,3)
    for x in [5,29]:s=slot(s,x,8,10,3.4,h=8,angle=90)
    for x in [12,21.5]:s=slot(s,x,20,8,2.2,h=8,angle=90)
    add('LID_SWITCH_PLATE',s)
    pad_holes('W01_FRONT',(100,149),(34,28),[(5,8),(29,8)])
    install('LID_SWITCH_PLATE','W01_FRONT',[100,149,5.5])
    # Flat lid touch tab (new holes in lid after dry fit); independent soft stops below.
    tab=box(0,0,0,30,12,3)
    for x in [5,13]:tab=slot(tab,x,6,7,3.4,h=8,angle=90)
    add('LID_TOUCH_TAB',tab)
    stop=box(0,0,0,16,20,3)
    stop=stop.fuse(box(0,16,0,16,4,12))
    for y in [5,11]:stop=hole(stop,8,y,r=1.7,h=8)
    add('LID_SOFTSTOP_SEAT',stop,2)
    for wallname,uu in [('W03_LEFT',70),('W04_RIGHT',90)]:
        pad_holes(wallname,(uu-8,158),(16,20),[(8,5),(8,11)])
        instances.append(dict(name='LID_SOFTSTOP_SEAT',wall=wallname,origin=[uu+8,158,0],
                              matrix=[[-1,0,0],[0,1,0],[0,0,-1]]))

    # 5mm LED at fixed front rim, shines inward; lead access outside with strain relief.
    led=box(0,0,0,22,18,3)
    led=hole(led,11,9,r=2.65,h=8)
    for x in [4,18]:led=hole(led,x,9,r=1.4,h=8)
    add('LED_INSERT',led)
    pad_holes('W01_FRONT',(18,158),(22,18),[(4,9),(18,9)],diameter=2.8)
    save('W01_FRONT',hole(parts['W01_FRONT'],29,167,r=3,h=10))
    install('LED_INSERT','W01_FRONT',[18,158,5.5])

    # External cable clamps: open saddle, screw-on bridge; all edges kept off moving linkage.
    saddle=box(0,0,0,24,10,2)
    for x in [0,18]:saddle=saddle.fuse(box(x,0,2,6,10,5))
    for x in [3,21]:saddle=hole(saddle,x,5,r=1.7,h=12)
    cap=box(0,0,0,24,10,2)
    for x in [3,21]:cap=hole(cap,x,5,r=1.7,h=8)
    add('CABLE_SADDLE',saddle,4);add('CABLE_CAP',cap,4)
    for wallname,u,v in [('W03_LEFT',24,46),('W03_LEFT',118,46),('W04_RIGHT',50,82),('W02_REAR',60,24)]:
        pad_holes(wallname,(u,v),(24,10),[(3,5),(21,5)])
        install('CABLE_SADDLE',wallname,[u,v,5.5]);install('CABLE_CAP',wallname,[u,v,12.5])
    return extra, instances, features
