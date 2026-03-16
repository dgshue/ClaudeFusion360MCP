# Utility, Query, I/O & Timeline Tools Reference

All dimensions are in **cm** unless noted otherwise.

## Query

### get_design_info
Get information about the current design including name, body count, sketch count, component count, and active sketch status.

No parameters.

### get_body_info
Get detailed information about a body including all edges and faces with indices, lengths, and areas.
- `body_index` (int): Which body (default: most recent)

Returns edge indices with lengths and face indices with areas. Use this to find indices for selective fillet, chamfer, shell, draft, hole, thread, or face-based sketch operations.

### measure
Measure dimensions of bodies, edges, or faces.
- `type` (str): What to measure - "body", "edge", or "face" (default "body")
- `body_index` (int): Which body (default: most recent)
- `edge_index` (int): Edge index (for type="edge")
- `face_index` (int): Face index (for type="face")

Returns: body measurements include volume, surface area, and bounding box with size. Edge returns length. Face returns area.

## Timeline

### get_timeline
Retrieve the design timeline with feature history.

No parameters. Returns: marker position, total feature count, and feature list with index, name, health state (healthy/warning/error/suppressed/rolled_back), suppression status, and group membership.

### edit_at_timeline
Move the timeline marker to a specific position. Features after the marker position are suppressed (not deleted).
- `position` (int): Timeline position (0 = before all features). Use -1 to return to end (all features active).

Positions are between items: 0 means before everything, count means after everything.

### create_marker
Create a named timeline snapshot at the current marker position. Markers are stored in-memory and do not persist across Fusion 360 sessions.
- `name` (str): Marker name (e.g., "before_fillets")

### undo_to_marker
Roll back the timeline to a previously created named marker position.
- `name` (str): Marker name to roll back to

## Utility

### undo
Undo recent operations.
- `count` (int): Number of operations to undo (default 1)

Returns the number of operations actually undone.

### delete_body
Delete a body by index.
- `body_index` (int): Index of body to delete (default: most recent body)

Use `get_design_info()` to see body count, `get_body_info()` for details.

### delete_sketch
Delete a sketch by index.
- `sketch_index` (int): Index of sketch to delete (default: most recent sketch)

Use `get_design_info()` to see sketch count.

### fit_view
Fit the viewport to show all geometry.

No parameters.

## I/O (Export)

### export_stl
Export the design as an STL file for 3D printing.
- `filepath` (str): Full file path for the output STL file

### export_step
Export the design as a STEP file (CAD interchange standard).
- `filepath` (str): Full file path for the output STEP file

### export_3mf
Export the design as a 3MF file (modern 3D printing format with color and material support).
- `filepath` (str): Full file path for the output 3MF file

## I/O (Import)

### import_mesh
Import an STL, OBJ, or 3MF mesh file into the design.
- `filepath` (str): Full file path of the mesh file to import
- `unit` (str): Mesh units - "mm", "cm", or "in" (default "mm")

## Batch Operations

### batch
Execute multiple Fusion commands in a single call for significantly faster complex operations.
- `commands` (list): List of command objects, each with `name` (str) and `params` (dict)

Executes all commands in one round-trip. Stops on first error and returns partial results. Use this when executing sequences of 3+ related operations.
