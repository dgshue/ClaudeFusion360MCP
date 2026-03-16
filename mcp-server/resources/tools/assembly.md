# Assembly Tools Reference

All positions are in **cm** and angles in **degrees**.

## Components

### create_component
Convert the most recent body into a new component for assembly.
- `name` (str): Component name (optional)

Always create bodies first (sketch + extrude), then convert to components before adding joints.

### list_components
List all components with names, positions, and bounding boxes.

No parameters. Returns an inventory of all components in the design.

### delete_component
Delete a component by name or index.
- `name` (str): Component name (optional)
- `index` (int): Component index (optional)

Provide either name or index.

### move_component
Move a component to a new position.
- `x` (float): X position or offset (default 0)
- `y` (float): Y position or offset (default 0)
- `z` (float): Z position or offset (default 0)
- `index` (int): Component index from `list_components()` (optional)
- `name` (str): Component name (optional)
- `absolute` (bool): If True, set absolute position. If False, move by offset (default True).

Use this to position components after creation to avoid overlaps.

### rotate_component
Rotate a component around an axis.
- `angle` (float): Rotation angle in degrees
- `axis` (str): Rotation axis - "X", "Y", or "Z" (default "Z")
- `index` (int): Component index (optional)
- `name` (str): Component name (optional)
- `origin_x` (float): Rotation origin X (default 0)
- `origin_y` (float): Rotation origin Y (default 0)
- `origin_z` (float): Rotation origin Z (default 0)

### check_interference
Check if any components overlap (bounding box collision detection).

No parameters. Returns interference results for all component pairs.

## Joints

All joint tools connect two components. Provide `component1_index` and `component2_index` to specify which components. Position (`x`, `y`, `z`) defines the joint origin.

### create_revolute_joint
Create a revolute (rotating) joint between two components. One degree of freedom: rotation around the specified axis.
- `component1_index` (int): First component index (optional)
- `component2_index` (int): Second component index (optional)
- `x` (float): Joint origin X (default 0)
- `y` (float): Joint origin Y (default 0)
- `z` (float): Joint origin Z (default 0)
- `axis_x` (float): Rotation axis X component (default 0)
- `axis_y` (float): Rotation axis Y component (default 0)
- `axis_z` (float): Rotation axis Z component (default 1)
- `min_angle` (float): Minimum rotation limit in degrees (optional)
- `max_angle` (float): Maximum rotation limit in degrees (optional)
- `flip` (bool): Flip joint direction (default False)

### create_slider_joint
Create a slider (linear) joint between two components. One degree of freedom: translation along the specified axis.
- `component1_index` (int): First component index (optional)
- `component2_index` (int): Second component index (optional)
- `x` (float): Joint origin X (default 0)
- `y` (float): Joint origin Y (default 0)
- `z` (float): Joint origin Z (default 0)
- `axis_x` (float): Slide axis X component (default 1)
- `axis_y` (float): Slide axis Y component (default 0)
- `axis_z` (float): Slide axis Z component (default 0)
- `min_distance` (float): Minimum slide limit (optional)
- `max_distance` (float): Maximum slide limit (optional)

### create_rigid_joint
Create a rigid (fixed) joint between two components. No relative motion allowed.
- `component1_index` (int): First component index (optional)
- `component2_index` (int): Second component index (optional)
- `x` (float): Joint origin X (default 0)
- `y` (float): Joint origin Y (default 0)
- `z` (float): Joint origin Z (default 0)

### create_cylindrical_joint
Create a cylindrical joint (rotation + translation along the same axis). Two degrees of freedom.
- `component1_index` (int): First component index (optional)
- `component2_index` (int): Second component index (optional)
- `x` (float): Joint origin X (default 0)
- `y` (float): Joint origin Y (default 0)
- `z` (float): Joint origin Z (default 0)
- `axis_x` (float): Axis X component (default 0)
- `axis_y` (float): Axis Y component (default 0)
- `axis_z` (float): Axis Z component (default 1)
- `min_angle` (float): Minimum rotation limit (optional)
- `max_angle` (float): Maximum rotation limit (optional)
- `min_distance` (float): Minimum slide limit (optional)
- `max_distance` (float): Maximum slide limit (optional)

### create_pin_slot_joint
Create a pin-slot joint (rotation + sliding). The axis defines the slot direction; rotation is perpendicular to it.
- `component1_index` (int): First component index (optional)
- `component2_index` (int): Second component index (optional)
- `x` (float): Joint origin X (default 0)
- `y` (float): Joint origin Y (default 0)
- `z` (float): Joint origin Z (default 0)
- `axis_x` (float): Slot direction X (default 0)
- `axis_y` (float): Slot direction Y (default 0)
- `axis_z` (float): Slot direction Z (default 1)
- `min_angle` (float): Minimum rotation limit (optional)
- `max_angle` (float): Maximum rotation limit (optional)
- `min_distance` (float): Minimum slide limit (optional)
- `max_distance` (float): Maximum slide limit (optional)

### create_planar_joint
Create a planar joint (2D sliding + rotation on a plane). Axis defines the plane normal. Three degrees of freedom.
- `component1_index` (int): First component index (optional)
- `component2_index` (int): Second component index (optional)
- `x` (float): Joint origin X (default 0)
- `y` (float): Joint origin Y (default 0)
- `z` (float): Joint origin Z (default 0)
- `axis_x` (float): Plane normal X (default 0)
- `axis_y` (float): Plane normal Y (default 1)
- `axis_z` (float): Plane normal Z (default 0)
- `min_primary_slide` (float): Primary slide minimum (optional)
- `max_primary_slide` (float): Primary slide maximum (optional)
- `min_secondary_slide` (float): Secondary slide minimum (optional)
- `max_secondary_slide` (float): Secondary slide maximum (optional)
- `min_angle` (float): Rotation minimum (optional)
- `max_angle` (float): Rotation maximum (optional)

### create_ball_joint
Create a ball joint (spherical rotation). Three rotational degrees of freedom. No axis needed.
- `component1_index` (int): First component index (optional)
- `component2_index` (int): Second component index (optional)
- `x` (float): Joint origin X (default 0)
- `y` (float): Joint origin Y (default 0)
- `z` (float): Joint origin Z (default 0)
- `min_pitch` (float): Pitch minimum (optional)
- `max_pitch` (float): Pitch maximum (optional)
- `min_roll` (float): Roll minimum (optional)
- `max_roll` (float): Roll maximum (optional)
- `min_yaw` (float): Yaw minimum (optional)
- `max_yaw` (float): Yaw maximum (optional)

## Joint Control

### set_joint_angle
Drive rotation on a revolute, cylindrical, or pin-slot joint.
- `angle` (float): Target angle in degrees
- `joint_index` (int): Which joint to drive (optional)

### set_joint_distance
Drive translation on a slider, cylindrical, or pin-slot joint.
- `distance` (float): Target distance in cm
- `joint_index` (int): Which joint to drive (optional)
