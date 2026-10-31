"""Separate, reusable hinged holders for the SmartBin measured modules.

All dimensions are millimetres.  The PCB is centred in XY, its long side is X,
and its underside is at ``seat_height`` above the holder's mounting face Z=0.
The output contains no fastener or electronics geometry.  A metal M3 hinge
pin and a separate metal M3 latch screw carry the opening and clamp loads.
The independent flat-printed spring only indexes the rotary latch.

Only constructors are run on import.  ``self_check`` is an explicit, read-only
CAD check; it neither exports files nor changes the parent mechanical model.
"""
from __future__ import annotations

import math
from typing import Any

import cadquery as cq


def _box(x: float, y: float, z: float,
         dx: float, dy: float, dz: float) -> cq.Shape:
    return cq.Workplane("XY").box(dx, dy, dz, centered=False).translate((x, y, z)).val()


def _cyl(radius: float, height: float, x: float, y: float, z: float,
         direction=(0, 0, 1)) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, height, cq.Vector(x, y, z), cq.Vector(*direction))


def _union(parts: list[cq.Shape]) -> cq.Shape:
    assert parts
    return parts[0].fuse(*parts[1:]).clean()


def _bounds(shape: cq.Shape) -> list[list[float]]:
    b = shape.BoundingBox()
    return [[b.xmin, b.ymin, b.zmin], [b.xmax, b.ymax, b.zmax]]


def _valid_single(shape: cq.Shape, name: str) -> None:
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise ValueError(f"{name} must be one valid solid")


def _nut_trap(x: float, y: float, z: float) -> cq.Shape:
    """Bottom-loaded M3 nut, 5.7-mm across flats and 2.6-mm depth."""
    return cq.Workplane("XY").polygon(6, 5.7/math.cos(math.pi/6)).extrude(2.7).translate((x,y,z-.1)).val()


def _flat_print(shape: cq.Shape) -> dict[str, Any]:
    """Translation-only print transform: all four parts have flat lower faces."""
    b = shape.BoundingBox()
    return {"rotation_degrees_xyz": [0, 0, 0],
            "translation_mm": [-b.xmin, -b.ymin, -b.zmin],
            "print_extents_mm": [b.xlen, b.ylen, b.zlen],
            "support": "none; 3.4-mm horizontal hinge bore uses short bridging"}


def make_lock(*, origin=(0.0, 0.0, 0.0), base_z=0.0,
              catch_top_z=9.2, overlap=2.3,
              arm_reach=6.5) -> dict[str, Any]:
    """Return a complete, reusable 0/90-degree metal-axis rotary latch.

    ``origin`` is the vertical latch axis XY (Z is an optional global offset).
    The closed finger points -Y.  A matching catch ends at
    ``axis_y - arm_reach + overlap`` and has its top at ``catch_top_z``.
    Opening is +90 degrees about Z; the finger then points +X.  A metal M3
    screw with washers/locking nut is required; tighten it to retain the
    finger axially while permitting rotation.  Hard stops take rotation load.

    The removable detent has a 12-mm free beam, 2-mm width and 1.16-mm
    thickness.  Its 0.48-mm nib rises 0.25 mm into the keeper's underside;
    two 0.48-mm-deep blind pockets provide the 0/90 positions.  The spring is
    relieved underneath and carries no lid/battery clamping load.
    """
    ox, oy, oz = map(float, origin)
    base_z = float(base_z)
    catch_top_z = float(catch_top_z)
    keeper_bottom = catch_top_z + 0.2
    keeper_thickness = 3.2
    # The bearing must support the finger at its nominal height.  A nominal
    # air gap here would let the finger sag into the catch and load the detent.
    bearing_top = keeper_bottom
    spring_bottom = keeper_bottom - 1.39
    if spring_bottom <= base_z + 2.4:
        raise ValueError("raise catch_top_z: the detent needs room above the 2.4-mm foot")
    radius = 3.7

    # Metal screw bearing and rigid 0/90 stops, all joined at the mounting foot.
    body_parts = [
        _cyl(6.2, 2.4, 0, 0, base_z),
        _cyl(radius, bearing_top-base_z, 0, 0, base_z),
        _box(1.2, 3.8, base_z, 1.6, 2.0,
             keeper_bottom+keeper_thickness+.3-base_z),
        _box(-5.8, -2.8, base_z, 2.0, 1.6,
             keeper_bottom+keeper_thickness+.3-base_z),
        # The fixed spring head is mechanically captured by M3 + a second key.
        _box(-18.5, -.7, base_z, 7, 7, spring_bottom-.05-base_z),
        _box(-15, .8, base_z, 15, 4, 2.4),
    ]
    body = _union(body_parts)
    # M3 axis and independent spring anchor through holes.
    for x, y in [(0, 0), (-15, 2.8)]:
        body = body.cut(_cyl(1.7, keeper_bottom+8-base_z, x, y, base_z-1))
    # Relief under the free spring, preserving the central screw bearing.
    body = body.cut(_box(-12, 1.6, spring_bottom-.35,
                         13.3, 2.4, 2.0))
    body = body.fuse(_cyl(.55, 1.16, -17, .8, spring_bottom-.05)).clean()

    keeper = _union([
        _cyl(radius, keeper_thickness, 0, 0, keeper_bottom),
        _box(-3, -arm_reach, keeper_bottom, 6, arm_reach,
             keeper_thickness),
        # Indexing dog: separate from the load-carrying clamping finger.
        _box(-1, 3.5, keeper_bottom, 2, 2, keeper_thickness),
    ])
    keeper = keeper.cut(_cyl(1.7, keeper_thickness+2, 0, 0, keeper_bottom-1))
    for x, y in [(0, 2.8), (2.8, 0)]:
        keeper = keeper.cut(_cyl(.95, .49, x, y, keeper_bottom-.01))
    keeper = keeper.clean()

    # One-piece detachable planar spring; never printed at its assembled height.
    leaf_top = spring_bottom+1.16
    # A 0.40-mm flat tip removes the spherical-pole degenerate STL triangle.
    # Overall nib height remains 0.48 mm and working deflection remains 0.25.
    dome = cq.Solid.makeSphere(1.0,cq.Vector(0,2.8,leaf_top-.5))
    dome = dome.intersect(_box(-1,1.8,leaf_top-.1,2,2,.58))
    detent = _union([
        _box(-18, -.2, spring_bottom, 6, 6, 1.16),
        _box(-12, 1.8, spring_bottom, 12, 2, 1.16),
        _cyl(1, 1.16, 0, 2.8, spring_bottom),
        dome,
    ])
    for x, y, r in [(-15, 2.8, 1.7), (-17, .8, .70)]:
        detent = detent.cut(_cyl(r, 3.1, x, y, spring_bottom-1))
    detent = detent.clean()
    shift = (ox, oy, oz)
    body = body.translate(shift)
    keeper = keeper.translate(shift)
    detent = detent.translate(shift)
    for label, shape in [("lock body", body), ("keeper", keeper), ("detent", detent)]:
        _valid_single(shape, label)
    keeper_open = keeper.rotate((ox, oy, oz), (ox, oy, oz+1), 90)
    # Nominal operating clearance; the detent nib legitimately enters a pocket.
    if body.intersect(keeper).Volume() > 1e-6:
        raise ValueError("closed rotary latch collides with rigid lock body")
    if body.intersect(keeper_open).Volume() > 1e-6:
        raise ValueError("open rotary latch collides with rigid lock body")
    return {
        "body": body, "keeper": keeper, "keeper_open": keeper_open,
        "detent": detent,
        "axis_xy": [ox, oy], "axis_z": keeper_bottom+oz,
        "anchor_xy": [ox-15, oy+2.8],
        "body_mount_holes_xy": [[ox,oy],[ox-15,oy+2.8]],
        "catch_max_y": oy-arm_reach+overlap,
        "overlap_mm": overlap,
        "closed_degrees": 0, "open_degrees": 90,
        "spring": {"free_length_mm": 12, "width_mm": 2,
                   "thickness_mm": 1.16, "maximum_deflection_mm": .25,
                   "nib_height_mm":.48,"keeper_leaf_gap_mm":.23,
                   "pocket_depth_mm":.48,
                   "dome_flat_tip_diameter_mm":2*math.sqrt(1-.98**2),
                   "is_load_bearing": False},
        "print_transforms": {"body": _flat_print(body),
                             "keeper": _flat_print(keeper),
                             "detent": _flat_print(detent)},
    }


def _open_edges(interfaces: dict[str, Any]) -> set[str]:
    aliases = {"left": "x-", "right": "x+", "bottom": "y-", "top": "y+",
               "upper": "y+", "lower": "y-", "x-": "x-", "x+": "x+",
               "y-": "y-", "y+": "y+"}
    result: set[str] = set()
    for value in interfaces.values():
        edge = value.get("edge") if isinstance(value, dict) else value
        if isinstance(edge, str) and edge.lower() in aliases:
            result.add(aliases[edge.lower()])
    return result


def build_holder(spec: dict[str, Any]) -> dict[str, Any]:
    """Build one hinged, pin-clear holder in closed assembly coordinates.

    Required spec keys: id, l, w, seat_height, component_height,
    headers_face and interfaces.  ``interfaces`` maps names to normalized
    edge strings (x-/x+/y-/y+, or left/right/bottom/top), or to dictionaries
    containing ``edge``.  Edges with an interface have their corner end
    guide omitted.  The end crossbars are below USB/SWD body height and
    above the back-facing header zone; no high wall spans either short end.

    Only 0.8 mm of PCB corner edge is overlapped by the lid pads.  The rest
    of the component area and the entire lower central pin zone are open.
    For an exceptionally edge-packed module, inspect its actual copper /
    components before adding any optional shim to the corner pads.
    """
    ident = str(spec["id"])
    length = float(spec["l"])
    width = float(spec["w"])
    seat = float(spec["seat_height"])
    if length < width or width <= 0 or seat < 4:
        raise ValueError("require l >= w > 0 and seat_height >= 4 mm")
    mech_l = max(length, 24.0)
    pcb_t = float(spec.get("pcb_thickness", 2.0))
    pcb_top = seat+pcb_t
    pcb_gap = float(spec.get("vertical_clearance", .15))
    hinge_y = -width/2-5.5
    base_t = 2.4
    guide_t = .8
    guide_clearance = .25
    guides_top = pcb_top-.2
    open_edges = _open_edges(spec.get("interfaces", {}))
    critical_end_edges=set()
    lowered_end_edges=set()
    usb_edges=set()
    for name,value in spec.get("interfaces",{}).items():
        edge_values=_open_edges({name:value})
        name_l=str(name).lower()
        if any(k in name_l for k in ["tf","sd","antenna","天线"]):
            critical_end_edges.update(edge_values & {"x-","x+"})
        if "usb" in name_l:usb_edges.update(edge_values & {"x-","x+"})
        if "header" in name_l or "排针" in name_l:
            if isinstance(value,dict) and value.get("face", "front") == "front":
                lowered_end_edges.update(edge_values & {"x-","x+"})
    if len(critical_end_edges)>1:
        raise ValueError("two fully open short ends require a different connecting frame")
    floor = max(2.8,seat-2) if lowered_end_edges else pcb_top-1.2
    hinge_z = floor+3.2
    low_floor = floor<seat

    outer_l, outer_w = mech_l+6.4, width+6.4
    body = _box(-outer_l/2, -outer_w/2, 0, outer_l, outer_w, base_t)
    body = body.cut(_box(-mech_l/2-.6, -width/2-.6, -1,
                         mech_l+1.2, width+1.2, base_t+2))
    additions: list[cq.Shape] = []
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            # Tiny corner ledges, not a floor beneath the pins or solder tails.
            px = sx*(length/2+.2)
            py = sy*(width/2+.2)
            if low_floor and sy<0:
                additions.append(_box(px-1.2,py-1.2,0,2.4,2.4,base_t))
                additions.append(_box(px-1.2,-width/2-.2,base_t-.1,
                                      2.4,1.2,seat-base_t+.1))
                continue
            additions.append(_box(px-1.2, py-1.2, 0, 2.4, 2.4, seat))
            if ("x+" if sx>0 else "x-") not in open_edges:
                gx = length/2+guide_clearance if sx>0 else -length/2-guide_clearance-guide_t
                gy0=py-1.0 if sy>0 else -width/2-.8
                additions.append(_box(gx, gy0, seat,
                                      guide_t, 2.0 if sy>0 else 1.6, guides_top-seat))
            if ("y+" if sy>0 else "y-") not in open_edges:
                gy = width/2+guide_clearance if sy>0 else -width/2-.8
                additions.append(_box(px-1.2, gy, seat,
                                      2.4, guide_t if sy>0 else .55, guides_top-seat))
    # Two independent M3 fasteners attach the holder to the whole base plate.
    mount_y=width/2+(7 if floor<4.6 else 5)
    mounts = [[-(mech_l/2-1), mount_y], [mech_l/2-1, mount_y]]
    if floor < 4.6:
        # The low HC-05 bridge needs outboard screw heads; its spring anchor
        # is also close to the left foot. Keep two 6-mm washers separated.
        mounts[0][0] = min(mounts[0][0], -20.5)
    for x, y in mounts:
        additions.append(_cyl(3.5, base_t, x, y, 0))
        if floor<4.6:
            additions.append(_box(x-3.5,width/2+2.4,0,7,4.6,base_t))

    # Three central hinge knuckles use one common M3 x 30 fastener.
    ear_xs = [-9.0,9.0]
    for x in ear_xs:
        additions.extend([
            _box(x-2.5, hinge_y-1.7, 0, 5.0, 3.4, hinge_z-1.3),
            _box(x-2.8, hinge_y-5.4, 0, 5.6,
                 -width/2+1.3-(hinge_y-5.4), base_t),
            _cyl(2.8, 5.0, x-2.5, hinge_y, hinge_z, (1,0,0)),
        ])
    # Positive 105-degree lid travel stop, behind and outboard of the hinge.
    stop_sx=-1 if "x+" in critical_end_edges else 1
    stop_x = stop_sx*(mech_l/2+2.25)
    cap_lead=pcb_top+3.2-hinge_z+.15
    a105=math.radians(105)
    stop_post_y=hinge_y+7*math.cos(a105)-(cap_lead+1.2)*math.sin(a105)
    stop_post_top=hinge_z+7*math.sin(a105)+(cap_lead+1.2)*math.cos(a105)+.5
    additions.append(_box(stop_x-1.2, stop_post_y-.45, 0,
                          2.4, .9, stop_post_top))
    cap = _box(stop_x-.8, hinge_y+6, hinge_z+cap_lead, 1.6, 2, 1.55)
    cap = cap.rotate((0,hinge_y,hinge_z), (1,hinge_y,hinge_z), 105)
    additions.append(cap)
    # Connect the end-corner travel stop independently of the central bearings.
    additions.append(_box(stop_x-1.2,stop_post_y-.45,0,
                          2.4,-width/2+1.3-(stop_post_y-.45),base_t))

    lock = make_lock(origin=(0, width/2+8.5, 0),
                     base_z=0, catch_top_z=pcb_top+3.2)
    additions.append(lock["body"])
    body = body.fuse(*additions).clean()
    for x,y in mounts:
        body = body.cut(_cyl(1.7, base_t+2, x, y, -1))
        # ISO7380 head plus OD6 washer must clear the nearby spring tower.
        # Keep the complete mounting foot; relieve only above its top face.
        body = body.cut(_cyl(3.2, 2.35, x, y, base_t))
    pin_tool = _cyl(1.7, mech_l+12, -mech_l/2-6,
                    hinge_y, hinge_z, (1,0,0))
    body = body.cut(pin_tool).clean()

    # Flat-bottom frame: high side rails and lower short-end crossbars.
    lid_parts: list[cq.Shape] = []
    for sy in [-1,1]:
        y = width/2+1.6 if sy>0 else -width/2-3.4
        if sy>0:
            lid_parts.append(_box(-mech_l/2-3.15, y, floor,
                                  mech_l+6.3, 1.8, pcb_top+3.2-floor))
        else:
            # Flat 1.1-mm bridges pass below the two fixed central ears.
            lid_parts.append(_box(-mech_l/2-3.15, y, floor,
                                  mech_l+6.3, 1.8, 1.1))
            upper_rail=_box(-mech_l/2-3.15,y,floor+1.1,
                            mech_l+6.3,1.8,pcb_top+3.2-floor-1.1)
            for ex in ear_xs:
                upper_rail=upper_rail.cut(_box(ex-2.7,y-.1,floor+1,
                                               5.4,2,pcb_top+8-floor))
            lid_parts.extend(upper_rail.Solids())
    for sx in [-1,1]:
        edge="x+" if sx>0 else "x-"
        if edge in critical_end_edges:continue
        x = mech_l/2+1.6 if sx>0 else -mech_l/2-3.2
        end_top=seat if edge in lowered_end_edges else pcb_top+.5
        beam=_box(x,-width/2-3.4,floor,1.6,width+6.8,end_top-floor)
        if edge in usb_edges:
            beam=beam.cut(_box(x-.1,-6,floor-1,1.8,12,end_top-floor+2))
        # The USB notch may divide this beam; the other end connects the frame.
        lid_parts.extend(beam.Solids())
    for sx in [-1,1]:
        for sy in [-1,1]:
            x0=length/2-3 if sx>0 else -mech_l/2-3.2
            tab_length=mech_l/2+3.2-(length/2-3)
            y=width/2-.8 if sy>0 else -width/2-2.4
            tab_width=4.2 if sy>0 else 3.2
            lid_parts.append(_box(x0, y, pcb_top+pcb_gap,
                                  tab_length, tab_width, 3.2-pcb_gap))
            if low_floor and sy<0:
                # The lid supplies the rear locating wall; the body leaves this
                # low swept zone clear so the lowered HC-05 frame can open.
                lid_parts.append(_box(x0,-width/2-1.05,seat,
                                      tab_length,.8,pcb_t+.3))
                # Support that raised wall as it is printed: its original
                # bottom at `seat` was an island until the corner pad above.
                # This short ~40-degree web grows from the flat rear rail,
                # stays .25mm outside the PCB edge and preserves the end ports.
                wall_inner_y=-width/2-.25
                ramp_start_y=wall_inner_y-(seat-floor)-.4
                web=cq.Workplane("YZ").polyline([
                    (ramp_start_y,floor),(wall_inner_y,seat),
                    (wall_inner_y,seat+.1),(ramp_start_y,seat+.1)
                ]).close().extrude(tab_length).translate((x0,0,0)).val()
                lid_parts.append(web)
    # One D-section knuckle: the whole lid and knuckle share the same flat bed.
    lid_parts.extend([
        _cyl(3, 12, -6, hinge_y, hinge_z, (1,0,0)),
        _box(-6, hinge_y-3, floor, 12, 6, hinge_z-floor),
        _box(-5, width/2+1.6, floor, 10, 2.7, pcb_top+3.2-floor),
        _box(stop_x-.8, hinge_y+3.2, hinge_z-.8,
             1.6, 4.8, pcb_top+3.2-hinge_z+.8),
        _box(stop_x-.8, hinge_y+6.4, floor,
             1.6, 1.6, hinge_z+.8-floor),
    ])
    lid = _union(lid_parts).cut(pin_tool).clean()
    # Central M3x30 hinge hardware lies beyond the 23-mm ear span. The head,
    # two OD6 washers and DIN985 nut need rotationally invariant clearance.
    # A 0.7-mm extension of the rear rail leaves a >=1-mm outer spine beside
    # the R3.4 tool, with the original coplanar print floor retained.
    hinge_hardware_clearances = [(-14.2, -11.4), (11.4, 16.5)]
    for x0, x1 in hinge_hardware_clearances:
        lid = lid.fuse(_box(x0, hinge_y+3.7, floor, x1-x0, .7,
                             pcb_top+3.2-floor))
        lid = lid.cut(_cyl(3.4, x1-x0, x0, hinge_y, hinge_z,
                            (1,0,0))).clean()
    keeper = lock["keeper"]
    detent = lock["detent"]
    for label,shape in [("body",body),("lid",lid),("keeper",keeper),("detent",detent)]:
        _valid_single(shape, ident+" "+label)
    lid_open = lid.rotate((0,hinge_y,hinge_z),(1,hinge_y,hinge_z),105)
    # Deliberate contacts (PCB support faces, screw-bearing faces) use clearances.
    closed_collision = body.intersect(lid).Volume()
    open_collision = body.intersect(lid_open).Volume()
    if closed_collision > 1e-5:
        raise ValueError(f"{ident}: closed lid/body collision {closed_collision:.6f} mm3")
    if open_collision > 1e-5:
        raise ValueError(f"{ident}: open lid/body collision {open_collision:.6f} mm3")

    all_parts = [body,lid,keeper,detent]
    bounds = [_bounds(s) for s in all_parts]
    lo=[min(b[0][i] for b in bounds) for i in range(3)]
    hi=[max(b[1][i] for b in bounds) for i in range(3)]
    dimensions={
        "closed_bounds_mm":[lo,hi],
        "closed_extents_mm":[hi[i]-lo[i] for i in range(3)],
        "part_bounds_mm":dict(zip(["body","lid","keeper","detent"],bounds)),
        "mechanism_length_mm":mech_l,
        "seat_height_mm":seat,"pcb_thickness_mm":pcb_t,
        "pcb_vertical_clearance_mm":pcb_gap,
        "hinge_axis":{"point":[0,hinge_y,hinge_z],"direction":[1,0,0],
                      "hole_diameter_mm":3.4,"nominal_open_degrees":105,
                      "suggested_pin_length_mm":30,
                      "fixed_ear_x_intervals_mm":[[-11.5,-6.5],[6.5,11.5]],
                      "lid_knuckle_x_interval_mm":[-6,6],
                      "total_bearing_span_mm":23},
        "lock_axis_xy":lock["axis_xy"],"lock_anchor_xy":lock["anchor_xy"],
        "keeper_rigid_overlap_mm":2.3,
        "fully_open_end_edges":sorted(critical_end_edges),
        "lowered_end_edges":sorted(lowered_end_edges),
        "usb_clear_window_width_mm":12 if usb_edges else 0,
        "lid_flat_floor_z":floor,
        "detent":lock["spring"],
        "mount_screw_note":"2 x M3 through holder foot and 5-mm main plate; nuts below main plate; use low-profile heads <=2 mm above the holder foot",
        "hinge_hardware_clearance_radius_mm":3.4,
        "hinge_hardware_clearance_x_intervals_mm":hinge_hardware_clearances,
        "lock_screw_note":"Latch axis and detent anchor also pass through 5-mm main plate; low round heads below that plate, locking nuts above. Adjust latch axial play to 0.1-0.2 mm while allowing rotation; no printed thread carries the hinge or latch load.",
        "interface_note":"TF/antenna short-end crossbar omitted completely. USB short-end crossbar has a >=12-mm central through-window. A front bent-header end uses a crossbar no higher than the PCB underside. Other end beams top out 0.5 mm above the PCB upper face. Inspect actual connector shell and corner pad clearance.",
    }
    return {
        "body":body,"lid":lid,"keeper":keeper,"detent":detent,
        "lid_open":lid_open,"keeper_open":lock["keeper_open"],
        "mount_holes_xy":mounts,
        "fastener_points_xy":{"foot":mounts,
                              "axis":[lock["axis_xy"]],
                              "anchor":[lock["anchor_xy"]]},
        "board_bounds_local":[[-length/2,-width/2,seat],[length/2,width/2,pcb_top]],
        "dimensions":dimensions,
        "assembly_parts":[(ident+"_body",body),(ident+"_lid",lid),
                          (ident+"_keeper",keeper),(ident+"_detent",detent)],
        "assembly_parts_open":[(ident+"_body",body),(ident+"_lid_open",lid_open),
                               (ident+"_keeper_open",lock["keeper_open"]),
                               (ident+"_detent",detent)],
        "colors":{"body":"#8d969e","lid":"#e39b43","keeper":"#4c81ba","detent":"#64a793"},
        "print_transforms":{name:_flat_print(shape) for name,shape in
                            [("body",body),("lid",lid),("keeper",keeper),("detent",detent)]},
        "lock":lock,
        "digital_checks":{"closed_lid_body_intersection_mm3":closed_collision,
                          "open_lid_body_intersection_mm3":open_collision,
                          "each_part_single_valid_solid":True},
    }


def self_check() -> list[dict[str,Any]]:
    """Construct the three mandatory examples without writing files."""
    examples=[
        dict(id="MCU",l=53,w=22,seat_height=20,component_height=9,
             headers_face="back",interfaces={"USB":"right","SWD":"left"}),
        dict(id="MCP",l=26,w=21,seat_height=20,component_height=5,
             headers_face="back",interfaces={}),
        dict(id="FLASH",l=23,w=19,seat_height=4,component_height=9,
             headers_face="front",interfaces={}),
    ]
    results=[]
    for example in examples:
        holder=build_holder(example)
        results.append({"id":example["id"],"dimensions":holder["dimensions"],
                        "mount_holes_xy":holder["mount_holes_xy"],
                        "digital_checks":holder["digital_checks"]})
    return results
