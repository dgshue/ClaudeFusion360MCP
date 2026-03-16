# Coordinate System Guide

## Units

All dimensions in Fusion 360 MCP are in **centimeters (cm)**. This is Fusion 360's internal unit. When you specify `distance=5`, that means 5 cm.

If you need to work in other units, convert before passing values:
- 1 inch = 2.54 cm
- 1 mm = 0.1 cm
- 1 m = 100 cm

## Construction Planes

Three construction planes are available for sketching:

| Plane | Orientation | Common Use |
|-------|------------|------------|
| **XY** | Horizontal (flat on the ground) | Top/bottom profiles, default for most designs |
| **XZ** | Vertical, facing front | Front/back profiles, side views |
| **YZ** | Vertical, facing side | Left/right profiles |

Use `create_sketch(plane="XY")` to start on any plane. Use `offset` to create a sketch parallel to a plane at a distance: `create_sketch(plane="XY", offset=5)` places the sketch 5 cm above origin.

## XZ Plane Y-Axis Inversion

When sketching on the **XZ plane**, there is a coordinate inversion to be aware of:

- In the **sketch** coordinate system, you draw using X and Y as usual
- In **world space**, the sketch Y axis maps to **negative Z**
- The add-in's coordinate correction layer handles this transparently for XZ construction plane sketches

This means when you call `draw_line(x1=0, y1=0, x2=5, y2=3)` on an XZ sketch:
- The line extends 5 cm along the world X axis
- The line extends 3 cm **upward** in the sketch, which maps correctly to world Z

You do not need to manually negate values. The correction is automatic.

## When Correction Applies

**XZ construction plane sketches only.** The coordinate correction activates when the sketch is created on the XZ construction plane (including offset XZ planes).

## When Correction Does NOT Apply

- **Face sketches:** When sketching on a body face (`create_sketch(body_index=0, face="top_face")`), coordinates are face-local. No correction is applied. The sketch X/Y axes align with the face's natural orientation.
- **3D operations:** World coordinates are used directly for `move_component`, `construction_point`, `construction_axis`, and other 3D positioning tools. No inversion.
- **XY and YZ plane sketches:** Only XZ has the inversion behavior. XY and YZ planes map directly without correction.

## Common Mistakes

### 1. Expecting Y-up when drawing on XZ
The XZ plane is vertical. In the sketch, Y goes "up" visually, but in world space that maps to the Z axis (with inversion handled automatically). Do not manually negate Y values for XZ sketches -- the add-in handles it.

### 2. Using world coordinates in face sketches
Face sketches use face-local coordinates. A "top_face" sketch has its origin at the face center, not at the world origin. Draw relative to (0, 0) on the face, not in world coordinates.

### 3. Forgetting offset is in cm
`create_sketch(plane="XY", offset=5)` places the sketch 5 cm above the XY plane, not 5 mm. Convert if your design intent is in other units.

### 4. Mixing up plane orientation
- Need a horizontal profile? Use **XY**
- Need a vertical front-facing profile? Use **XZ**
- Need a vertical side-facing profile? Use **YZ**
