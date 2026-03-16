# Workflow Patterns Guide

These patterns explain common CAD workflows with the reasoning behind each step's ordering. Understanding the "why" lets you adapt these patterns to variations.

## Box / Enclosure Pattern

**Goal:** Create a hollow box with rounded edges (e.g., electronics enclosure).

**Steps:**
1. `create_sketch(plane="XY")` -- draw outer profile
2. `draw_rectangle(x1=0, y1=0, x2=10, y2=8)` -- outer dimensions
3. `finish_sketch()`
4. `extrude(distance=5)` -- create solid block
5. `shell(thickness=0.2, faces_to_remove=[top_face_index])` -- hollow it out, remove top
6. `fillet(radius=0.3)` -- round all edges

**Why this order matters:**
- **Shell before fillet.** Filleting changes edge topology -- edges split, merge, or shift indices. If you fillet first, the face you need to remove for shelling may have a different index or may no longer be a simple planar face. Shelling on the flat-faced solid is predictable. Filleting the already-shelled body rounds both inner and outer edges cleanly.
- **Extrude before shell.** You need a solid body to hollow out. Shell operates on existing solid geometry.

## Cylinder Pattern

**Goal:** Create a solid or hollow cylinder.

**Solid cylinder:**
1. `create_sketch(plane="XY")` -- base profile
2. `draw_circle(center_x=0, center_y=0, radius=3)` -- circular cross-section
3. `finish_sketch()`
4. `extrude(distance=5)` -- cylinder height

**Hollow cylinder (method A -- concentric circles):**
1. `create_sketch(plane="XY")`
2. `draw_circle(center_x=0, center_y=0, radius=3)` -- outer circle
3. `draw_circle(center_x=0, center_y=0, radius=2.5)` -- inner circle
4. `finish_sketch()`
5. `extrude(distance=5, profile_index=0)` -- extrude the ring profile (between circles)

**Hollow cylinder (method B -- extrude + shell):**
1. Create solid cylinder (steps above)
2. `shell(thickness=0.5)` -- hollow it uniformly

**Why two methods:** Method A gives precise control over inner and outer diameters independently. Method B is simpler when you just want a uniform wall thickness and do not need exact inner diameter control.

## Sweep Pattern

**Goal:** Create a pipe, channel, or any geometry that follows a path (e.g., a curved tube).

**Steps:**
1. `create_sketch(plane="YZ")` -- cross-section profile on one plane
2. `draw_circle(center_x=0, center_y=0, radius=0.5)` -- pipe cross-section
3. `finish_sketch()`
4. `create_sketch(plane="XY")` -- path on a different plane
5. `draw_spline(points=[[0,0], [5,2], [10,0]])` -- curved path
6. `finish_sketch()`
7. `sweep()` -- defaults: second-to-last sketch = profile, last sketch = path

**Why this order matters:**
- **Profile and path must be in different sketches** on different planes. Fusion 360 requires the profile to be perpendicular (or at least not coplanar) to the path at the start point.
- **Profile sketch first, path sketch second.** The sweep tool defaults to using the second-to-last sketch for the profile and the last sketch for the path. Creating them in this order avoids needing to specify sketch indices explicitly.

## Loft Pattern

**Goal:** Create a smooth transition between profiles on different planes (e.g., bottle shape, airfoil).

**Steps:**
1. `create_sketch(plane="XY")` -- first profile
2. `draw_circle(center_x=0, center_y=0, radius=3)` -- wide base
3. `finish_sketch()`
4. `construction_plane(mode="offset", plane="XY", offset=5)` -- create offset plane
5. `create_sketch(plane="XY", offset=5)` -- second profile on the offset plane
6. `draw_circle(center_x=0, center_y=0, radius=1.5)` -- narrower top
7. `finish_sketch()`
8. `loft(sketch_indices=[0, 1])` -- connect the two profiles

**Why this order matters:**
- **All profiles must be on separate planes.** Lofting requires each profile to be on a distinct plane so Fusion can interpolate between them in 3D. Two profiles on the same plane would have zero distance to interpolate across.
- **Construction planes for intermediate sections.** If you need more than two profiles, create additional offset planes with `construction_plane()` and sketch on each one.
- **Profile order matters.** The `sketch_indices` list defines the loft direction. The shape transitions from the first profile to the last.

## Assembly Pattern

**Goal:** Create a multi-component assembly with mechanical connections.

**Steps:**
1. Create each part as a separate body (sketch + extrude for each)
2. `create_component(name="base")` -- convert first body to component
3. `create_component(name="arm")` -- convert second body to component
4. `move_component(x=0, y=5, z=0, name="arm")` -- position the arm
5. `create_revolute_joint(component1_index=0, component2_index=1, x=0, y=5, z=0, axis_x=1, axis_y=0, axis_z=0)` -- add hinge
6. `check_interference()` -- verify no overlaps
7. `set_joint_angle(angle=45, joint_index=0)` -- test joint motion

**Why this order matters:**
- **Create components before joints.** Joints connect components, not raw bodies. You must have at least two components before creating any joint.
- **Position before joining.** Move components to their approximate assembled positions first. Joint creation works best when components are already near their intended relative positions.
- **Check interference after assembly.** Verifying clearances after positioning and joining catches collisions early, before adding more complexity.

## Parametric Pattern

**Goal:** Create a design driven by named parameters so changing one value updates the entire model.

**Steps:**
1. `create_parameter(name="width", expression="10", unit="cm")`
2. `create_parameter(name="height", expression="width * 0.5", unit="cm")` -- derived parameter
3. `create_parameter(name="wall", expression="0.2", unit="cm")`
4. Design as usual: `create_sketch`, `draw_rectangle`, `extrude`, `shell`, etc.
5. When dimensions are parametric, changing a parameter updates everything:
   `set_parameter(name="width", expression="15")` -- entire design rescales

**Why this order matters:**
- **Define parameters before using them.** Expressions can reference other parameters, but those parameters must exist first. Create base parameters (like "width") before derived ones (like "height = width * 0.5").
- **Parameters are expressions, not just numbers.** You can write `"width * 2 + 1"` as an expression. Fusion evaluates it and updates when referenced parameters change.

## Gear (Spur) Pattern

**Goal:** Create a spur gear with evenly spaced teeth.

**Steps:**
1. `create_sketch(plane="XY")`
2. Draw one tooth profile using lines and arcs (the involute curve approximation)
3. Add construction geometry for tooth spacing reference
4. `finish_sketch()`
5. `extrude(distance=gear_thickness)` -- extrude single tooth
6. `pattern_circular(count=num_teeth, angle=360, axis="Z")` -- replicate around center
7. Optionally: `draw_circle` for the center bore, `extrude` with cut operation, `fillet` tooth edges

**Why this order matters:**
- **One tooth first, then pattern.** Designing all teeth individually would be tedious and error-prone. Create one tooth with correct geometry, then circular pattern handles the even distribution automatically.
- **Construction geometry for spacing.** Use `set_construction` to mark reference lines that define the pitch circle and tooth spacing angles. These guide the tooth profile without being included in the extruded profiles.
- **Pattern before bore.** The circular pattern duplicates the tooth body. Cutting the center bore after patterning ensures it is a clean cylindrical hole through the final gear shape.

## Tips Across All Patterns

- **Use `get_body_info()` before face/edge operations.** Face and edge indices can change after operations like fillet, chamfer, or shell. Always query the current state before referencing specific indices.
- **Use `get_sketch_info()` before constraints/dimensions.** Curve and point indices are assigned sequentially as geometry is created. Query the sketch state to confirm indices before applying constraints.
- **Use `batch()` for multi-step sequences.** Wrapping 3+ sequential operations in a batch call reduces round-trip overhead significantly.
- **Create markers before risky operations.** Use `create_marker(name="before_fillets")` so you can roll back with `undo_to_marker(name="before_fillets")` if the result is not as expected.
