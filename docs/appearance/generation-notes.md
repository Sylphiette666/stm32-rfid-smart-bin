# 外观示意图生成说明

日期：2026-10-10

生成方式：内置 image_gen（imagegen 技能），先生成整体双视角，再修正连杆、探头朝向、按钮文字及核心板外观。未使用 CLI/API 回退。

图像是当前设计的外观概念渲染，不是实物照片、装配工程图或运动仿真；示意中的模块外形、固定件及连杆姿态不能代替手册尺寸和实测。最终采用第二次输出，保留了合盖与开盖两种状态。

## 初始提示词

```text
Use case: product-mockup.
Create one landscape presentation image with two consistent views of the SAME handmade university electronics coursework prototype: a small STM32 + RFID points-based mobile trash bin. Photorealistic concept rendering, visibly buildable using inexpensive purchased modules, plywood and flat white PVC foam sheets. It must look like a neat student-built working prototype, not a commercial appliance. Plain light grey studio background, soft realistic shadows and accurate relative proportions.

Composition: a large front-right three-quarter view on the left with the lid closed, and a slightly smaller front-right three-quarter view on the right with the same lid raised approximately 70 degrees. Entire robot visible in each view, including wheels and underside clearance. In both views the front of the bin faces the viewer; show the external servo linkage on the viewer-visible right/rear side. Consistent component locations and material colors between the two views. Both views are two states of one design.

Physical design, all sizes in millimeters:
- Lower plywood chassis plate 280 long x 220 wide x 5 thick, light natural wood grain and clearly cut square edges. Underside about 45 mm above floor. Two black rubber drive wheels with yellow plastic hubs, 65 mm diameter and 26 mm wide, mounted left and right near the rear third of the chassis. Wheel centers 252 mm apart, so the total outer wheel width is about 278 mm. Exactly TWO main drive wheels. One small metal ball caster below the front center, not another pair of large wheels.
- An upper plywood platform 240 x 190 x 5 is supported by FOUR slim white nylon hexagonal standoffs, 60 mm tall. Open electronics space between the two wooden platforms: one modest blue STM32 core board, brown perfboard carrying modules, tidy short color-coded wires, and a small two-cell 18650 battery pack strapped low on the lower platform. Some modules visible but no giant educational development board and no tall circuit tower.
- A single rectangular white bin shell 160 deep x 150 wide x 180 high sits on the upper platform. It is assembled from flat matte white 3 mm PVC foam panels, straight seams and small discrete external corner brackets. Its upper rim is approximately 295 mm above floor. This is a small roughly 30 cm tall model with a wide wheeled base, not a full-size household garbage bin.
- The lid is a thin flat white 160 x 150 x 2 mm PVC panel with a small rear hinge, almost flush with the square shell, NOT a molded domed lid. In the open view, show one shallow translucent PP liner and a neatly tucked lightweight garbage bag inside, not separate trash categories. Liner interior is about 140 x 130 x 121 mm.
- On the external right/rear side of the shell is a thin vertical light plywood servo support about 190 mm tall from the platform. A single small translucent blue SG90 servo is mounted near the lid's rear hinge height, not midway down the wall. Its output axis is about 50 mm behind the lid hinge axis at the same height. Show two SMALL 20 mm crank arms and a single short silver connecting rod with black M2 ball ends, approximately 50 mm center-to-center, making an exposed practical lid linkage outside the shell. In closed state both crank arms point forward-up about 20 degrees; in open state they turn upward. The rod must physically connect the servo horn and the small lid-hinge rocker, not attach randomly to the lid's front. No huge robotic arm, no second servo, no gas strut.
- Front panel: a small blue-lit 0.96 inch OLED near the upper center, with just simple tiny screen indicators, no large touchscreen; a marked card-tapping area below it with a small contactless icon and text "RFID"; one small black rotary knob and two small tactile buttons near the lower front. Keep realistic module scale compared to the 150 mm wide wall.
- A red mushroom stop button on the forward projecting edge of the upper platform, accessible without covering the bin opening. A small forward-facing infrared obstacle sensor near the front lower chassis, and a three-channel black line-following sensor tucked underneath the front chassis. The ultrasonic fill sensor is INSIDE near the upper rim pointing downward, visible subtly in open view; do not put two big ultrasonic 'eyes' on the front wall.
- Clean cable routing down the back/right side into the lower electronics bay; cables clear of wheels and linkage. Lightly visible screw heads, realistic cut-sheet edges and plywood texture. No branding or vendor logos.

Typography: clean legible Chinese labels only in the surrounding empty background, not over the product. Top title exactly "智能移动垃圾桶 成品外观示意". Left state label "合盖状态". Right state label "开盖状态". Bottom caption exactly "底板 28 × 22 cm   桶体 16 × 15 × 18 cm". Small bottom note "AI外观示意，具体孔位与接线以装配手册为准".
Style constraints: restrained technical visualization, realistic inexpensive materials, white box with natural wood and black/yellow wheels, not futuristic or a glossy industrial enclosure. No garbage-sorting compartments, no robotic grabber, no autonomous navigation lidar, no mobile phone props, no people, no dimension arrows pretending to be manufacturing drawings.
```

## 修订提示词

```text
Use case: precise-object-edit. Edit the supplied concept render of the SAME student-built smart trash bin. Preserve its exact two-view layout, white sheet-PVC shell, pale plywood double-deck chassis, two black/yellow driving wheels, one small ball caster, overall proportions, title, bottom dimensions, lighting and background.

Make only these technical corrections consistently in both robot views:
1. Correct the servo linkage. Remove the erroneous ball joint bolted onto the stationary right wall in the closed view. The cover is hinged at the REAR top edge. Put a small, clearly visible short crank on the SIDE of that rear lid hinge shaft, mechanically rigid with the moving lid, with its ball joint about 20 mm from that shaft. It must move with the lid, not be fixed to the stationary wall. The servo's shaft is 50 mm farther rearward and at the same height on the external plywood mast. Give the servo a second equal short crank. Connect the ends of the two cranks with one short straight silver ball-joint rod, making a tiny parallelogram linkage beside the REAR hinge. In the closed view both cranks are angled upward-forward about20degrees and the 50mm rod is roughly horizontal near the hinge. In the open view both equal cranks point nearly upward and the rod REMAINS roughly horizontal, joining them near the REAR hinge. Do NOT run a diagonal rod from the servo to the front edge of the open cover; the entire mechanism stays small and near its rear hinge. No rod attached to the fixed body side. One servo only.
2. In the open view, the ultrasonic fill sensor must be inside at the upper rim with its two silver circular transducers facing DOWN into the bin. Show its blue circuit board/support horizontally near the back rim, with transducer barrels pointing down, not facing toward the viewer like eyes.
3. Change the tiny front labels to match the real control functions. Under the black knob write "选择"; under the green button "模式"; under the red button "返回". Remove "清零" entirely. Do not change the red mushroom stop on the chassis.
4. Replace the oversized blue main board in each lower compartment with a narrow small STM32F103C8T6 core board having one central square microcontroller, two straight rows of header pins and a small USB connector. Keep the brown perfboard and bundled wiring beside it. Real inexpensive modules, no large Arduino-style motherboard.

Do not add new functions or elements. Keep the existing Chinese title and dimensional footer exactly unchanged. This remains an illustrative appearance concept, not an actual prototype photograph or construction drawing.
```
