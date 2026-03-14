import adsk.core
import adsk.fusion


def get_body(rootComp, body_index=None):
    """Get a BRepBody by index, defaulting to the most recent (last).

    Args:
        rootComp: The root component
        body_index: Optional body index. If None, returns the last body.

    Returns:
        BRepBody object

    Raises:
        ValueError: If no bodies exist or index is out of range
    """
    if rootComp.bRepBodies.count == 0:
        raise ValueError(
            "No bodies in design. Create geometry first "
            "(create_sketch -> draw shapes -> extrude)."
        )

    if body_index is None:
        body_index = rootComp.bRepBodies.count - 1

    if body_index < 0 or body_index >= rootComp.bRepBodies.count:
        raise ValueError(
            f"Body index {body_index} out of range. "
            f"Design has {rootComp.bRepBodies.count} bodies (0-{rootComp.bRepBodies.count - 1}). "
            f"Use get_design_info() to see body count."
        )

    return rootComp.bRepBodies.item(body_index)


def get_sketch(rootComp, sketch_index=None):
    """Get a Sketch by index, defaulting to the most recent (last).

    Args:
        rootComp: The root component
        sketch_index: Optional sketch index. If None, returns the last sketch.

    Returns:
        Sketch object

    Raises:
        ValueError: If no sketches exist or index is out of range
    """
    if rootComp.sketches.count == 0:
        raise ValueError(
            "No sketches in design. Call create_sketch() first."
        )

    if sketch_index is None:
        sketch_index = rootComp.sketches.count - 1

    if sketch_index < 0 or sketch_index >= rootComp.sketches.count:
        raise ValueError(
            f"Sketch index {sketch_index} out of range. "
            f"Design has {rootComp.sketches.count} sketches (0-{rootComp.sketches.count - 1}). "
            f"Use get_design_info() to see sketch count."
        )

    return rootComp.sketches.item(sketch_index)


def get_occurrence(rootComp, index=None, name=None):
    """Get an Occurrence by index or name.

    Args:
        rootComp: The root component
        index: Optional occurrence index
        name: Optional component name to search for

    Returns:
        Occurrence object

    Raises:
        ValueError: If no occurrences exist, index is out of range,
                     or name is not found
    """
    if rootComp.occurrences.count == 0:
        raise ValueError(
            "No components in design. Use create_component() first."
        )

    if name is not None:
        for i in range(rootComp.occurrences.count):
            occ = rootComp.occurrences.item(i)
            if occ.component.name == name:
                return occ
        available = [rootComp.occurrences.item(i).component.name
                     for i in range(rootComp.occurrences.count)]
        raise ValueError(
            f"No component named '{name}'. "
            f"Available components: {', '.join(available)}. "
            f"Use list_components() to see all components."
        )

    if index is None:
        index = 0

    if index < 0 or index >= rootComp.occurrences.count:
        raise ValueError(
            f"Component index {index} out of range. "
            f"Design has {rootComp.occurrences.count} components (0-{rootComp.occurrences.count - 1}). "
            f"Use list_components() to see all components."
        )

    return rootComp.occurrences.item(index)
