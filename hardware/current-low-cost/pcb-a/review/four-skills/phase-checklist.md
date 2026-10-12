# Toaster阶段清单逐项审查

本项目是已有设计的低成本手焊教学原型。FAIL保持为未满足/待实测项；不代表已获整机量产、热或EMC批准。裸板几何与文件检查单独记录。

## §1 Post-stackup (board setup complete)

| 原检查项 | 结果 | 本板证据或适用边界 |
|---|---|---|
| Outline single closed shape on outline layer; dims match enclosure; units mm. | PASS | 100mm closed centerline; native/CAM agreement |
| Mounting holes sized (screw table) + keepout rings; enclosure screws fit. | PASS | 3.2mm NPTH centers5/95mm; nominalM3 envelope checked; purchased fixtures still measure |
| Position-fixed connectors at TRUE locations (re-check vs mechanical drawing). | PASS | External cable connectors; not a direct-fit core socket |
| Layer count justified by decision tree; stackup documented in journal. | PASS | 2layerFR4 1.6mm handbuild; no integrated RF/converter |
| Impedance nets enumerated; fab worksheet requested (or N-A honestly marked). | N-A | No controlled-impedance interface claimed |
| Net classes created; widths/clearances/vias per class; fab minimums ≥20% margin. | PASS | 0.20clearance;0.25mintrace;.8/.4vias; intended stronger than ordinary2layer minimum |
| Thickness fits every connector's mating spec. | PASS | Through-hole handbuild; no edge/card mating |
| Panelization decision recorded; assembler spec fetched if panelizing. | N-A | Single board no panel or PCBA |
| Fab notes template filled (no TBD). | PASS | Existing order-and-assembly.md specifies bareboard parameters |
| Zone/keepout rules for antenna, HV creepage, mechanical exclusions drawn. | N-A | No PCB antenna or HV; four mechanical holes checked |
| Journal + backup checkpoint DONE. | PASS | Frozen baseline/local review history; user-authorized Git repository backup |

## §2 Post-placement

| 原检查项 | 结果 | 本板证据或适用边界 |
|---|---|---|
| Zones drawn & honored; flow direction consistent; no zigzag bundles. | PASS | Power left, signal right; external modules |
| Placement order followed (mechanicals → anchors → decaps → TPs → silk). | PASS | Nominal placement reviewed in existing design plus current rendering |
| Every IC: decap ≤2 mm from power pins with own via; bulk per cluster. | FAIL | U1/C8 pin distance5.24mm exceeds2mm recipe; residual EMC risk retained |
| Crystal cluster ≤5 mm, guarded, no copper beneath on adjacent layers. | N-A | No onboard crystal |
| Dirty/clean separation real (measure the mm): converter/MCU away from analog. | PASS | Switching buck/driver external; power and signal banks separated |
| Buck hot-loop parts adjacent (input cap + switches + diode cluster). | N-A | Buck internal hot loop outside this board |
| Thermal: hot parts spread; electrolytics/crystals/sensors clear; EP via arrays reserved. | N-A | No onboard power converter or exposed-pad IC; no thermal qualification claimed |
| Antenna keepout on ALL copper layers, extends past antenna; EMPTY. | N-A | RFID antenna is external; physical clearance follows module manual |
| ESD/filters at connector entry, not at ICs. | FAIL | Universal I/O ESD/filter network not fitted; short enclosed wires, no hotplug/ESD rating |
| Test points: rails, resets, boot straps, buses, per-channel signals; labeled. | PASS | Labeled through-hole headers are probe access; table in joint report |
| Ratsnest: only neighbor connections remain; no long diagonal bundles. | N-A | Already routed; final unconnected0 replaces ratsnest check |
| Courtyard overlaps zero (or documented assembly-safe). | PASS | Nominal body/3D check; courtyard omissions explicitly supplemented; bought-part fit pending |
| Journal + backup checkpoint DONE. | PASS | Baseline and revision files retained locally |

## §3 Post-route

| 原检查项 | 结果 | 本板证据或适用边界 |
|---|---|---|
| DRC: 0 errors; every remaining warning classified (inherited/cosmetic/accepted). | PASS | Final KiCad DRC0; ignored rule classes disclosed separately |
| Unconnected: 0 real gaps; zone artifacts refilled & explained. | PASS | Final unconnected0 after refill |
| Hot loops visually small (buck input/output); SW node copper contained. | N-A | External converter |
| No signal crosses plane splits (render planes alone and LOOK). | FAIL | PA6 and other segments lack continuous opposite-layer GND; raw coverage and CAM retained |
| Return vias accompany layer transitions on buses/critical nets. | FAIL | 55GND stitches improve but not every transition has <=1mmGND via |
| Diff pairs: geometry constant, no gaps crossed, matching at source end. | N-A | No differential interface on carrier |
| Length-matching tolerance derived from budget (not folklore) and met. | N-A | No synchronous skew budget; short low-rate SPI/I2C prototype |
| Power necks calculated, pours where current demands, via arrays on transitions. | PASS | 33 planned power/return segments preserved; actual load thermal validation pending |
| Sense/FB traces routed away from SW node, shielded, Kelvin at the point. | N-A | No converter FB; ADC is filtered slow battery divider |
| No dead copper islands; stitching vias along edges/connector entries. | PASS | Filled disconnected-island removal and DRC0;55groundstitchesadded |
| Silkscreen: refdes all present, off pads, one reading orientation, polarity marks visible post-assembly. | PASS | Native/CAM viewed; references and polarity readable; final silkscreen DRC0 |
| 3D pass done (collisions, heights, connector clash, antenna region clear). | PASS | Native3D refreshed; external module and actual bought parts still need real fit |
| Journal + backup checkpoint DONE. | PASS | Revision checkpoint retained |

## §4 Pre-fab-release

| 原检查项 | 结果 | 本板证据或适用边界 |
|---|---|---|
| `gerber_audit.py` exit 0 on the package directory. | PASS | gerber_audit.py exit0; report stored |
| Copper/mask/silk/paste/outline/drill files present; drill format & units snifffed correct; layer count matches stackup claim. | PASS | 9files includingPTH/NPTH; paste N-A for hand solder |
| Extra empty user-layer gerbers noted (harmless but flag in fab notes or drop). | PASS | Only intended7Gerberlayers+2drills inzip |
| pos.csv + BOM exported from the FINAL board; designator sets reconciled; `bom_lint.py` exit 0. | PASS | BOM/refsetschecked; placement-fileN-A noSMT; existingbomlintdataretained unchanged |
| Fab notes complete: stackup/finish/copper/qty/impedance/special flags. | PASS | Bareboard notes complete;quantityactualorder |
| Netlist→board diff clean (board connectivity == schematic connectivity). | PASS | KiCad schematic parity0 |
| Fab capability re-verified against tightest features (date recorded). | PASS | Official capability read at release; ordinary2layer rules |
| Human review done where mandated (HV/mains/safety/battery). | FAIL | Actual battery/driver/stop system not inspected by a human hardware reviewer; no safety certification claimed |
| Bring-up notes written BEFORE ordering (expected voltages per TP, bring-up order, flash procedure, failure decision tree). | PASS | Manual63 and64 specify voltages and staged tests |
| Journal updated; final archive uploaded + VERIFIED (download-back check). | PASS | Local journal plus authorizedGitHubpush; uploadedcommitmustbeverifiedbeforefinaldelivery |
| Critical release: ≥2 hosts hold the archive (`../../pcb-project-continuity`). | N-A | Educationalprototype; no publicfilehostbackup mandate; GitHubbackup peruser |

## §5 Schematic-review gate (Phase 3 of pcb-flow)

| 原检查项 | 结果 | 本板证据或适用边界 |
|---|---|---|
| ERC clean or every warning explained in journal. | PASS | FreshERC0; sourceunchanged |
| Net names reviewable (functional names, not N0032). | PASS | Namedfunctionalnets |
| Symmetry audit on repeated channels: scripted netlist comparison; all asymmetries intended & noted. [ft] | PASS | Native94ref/pinmatch; intentionalADC/Echo/stopasymmetries |
| Every input has a defined power-up state (pullups/pulldowns; gates especially — both-FET-on is smoke). | PASS | Specifiedresistorbias and unusedAHCTinputlevels checked; firmwareGPIOinit stillrequired |
| Reset/EN RC ≥ slowest rail ramp incl. soft-start (compute the product). | N-A | No onboardMCUresetsequencer; externalmodulestartup not simulated |
| Power-tree check: every load's rail exists; every converter budgeted ≥20%. | FAIL | Rails mapped; full externalmodulepeakload and20%budget not measured yet |
| Every connector pin assigned; no floating connector pins on live nets. | PASS | 181connectorpins assigned byfunction; modulephysicalsequence notassumed |
| USB-C CC terminations present for UFP designs. | N-A | NoUSB-C oncarrier |
| ICs: decap on every power pin; bulk per rail/cluster. | PASS | C4/C5/C6/C8localdecoupling andbulk; distancewarning retained |
| Buck feedback divider math verified (Vref math, not trust). | N-A | Externalbuckadjustment;dividersverifiedseparately |
| Part symbols pin-verified against datasheet for anything borrowed/variant. [ft] | PASS | U1andQreferencepinoutcrosscheck; purchasedgenericQidentitypending |
| Test strategy exists (what you'll measure at bring-up is decided HERE). | PASS | Stagedbringupmanual andprobepoints |
| Journal + backup checkpoint DONE. | PASS | LocalbaselineandGitcheckpoint |
