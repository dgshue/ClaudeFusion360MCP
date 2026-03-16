import math

import adsk.core
import adsk.fusion

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from helpers.bodies import get_occurrence


def _get_axis_direction(params):
    """Map axis params (axis_x, axis_y, axis_z) to a JointDirections enum value.

    Returns the JointDirection matching the dominant axis, defaulting to Z.
    """
    ax = abs(params.get('axis_x', 0))
    ay = abs(params.get('axis_y', 0))
    az = abs(params.get('axis_z', 0))

    if ax >= ay and ax >= az and ax > 0:
        return adsk.fusion.JointDirections.XAxisJointDirection
    elif ay >= ax and ay >= az and ay > 0:
        return adsk.fusion.JointDirections.YAxisJointDirection
    else:
        return adsk.fusion.JointDirections.ZAxisJointDirection


def create_revolute_joint(design, rootComp, params):
    """Create a revolute (rotating) joint between two components.

    Supports configurable axis via axis_x/y/z params, optional angle limits,
    and flip direction.
    """
    if rootComp.occurrences.count < 2:
        return {
            "success": False,
            "error": (
                "create_revolute_joint() failed: Need at least 2 components "
                "to create a joint. Use create_component() first."
            )
        }

    idx1 = params.get('component1_index', 0)
    idx2 = params.get('component2_index', 1)

    occ1 = get_occurrence(rootComp, index=idx1)
    occ2 = get_occurrence(rootComp, index=idx2)

    x = params.get('x', 0.0)
    y = params.get('y', 0.0)
    z = params.get('z', 0.0)
    point = adsk.core.Point3D.create(x, y, z)

    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)

    axis_direction = _get_axis_direction(params)
    joint_input.setAsRevoluteJointMotion(axis_direction)

    joint = joints.add(joint_input)

    # Set flip if requested
    if params.get('flip', False):
        joint.isFlipped = True

    # Set rotation limits if provided
    min_angle = params.get('min_angle', None)
    max_angle = params.get('max_angle', None)

    if min_angle is not None:
        joint.jointMotion.rotationLimits.isMinimumValueEnabled = True
        joint.jointMotion.rotationLimits.minimumValue = math.radians(min_angle)

    if max_angle is not None:
        joint.jointMotion.rotationLimits.isMaximumValueEnabled = True
        joint.jointMotion.rotationLimits.maximumValue = math.radians(max_angle)

    return {
        "success": True,
        "joint_name": joint.name,
        "joint_index": rootComp.joints.count - 1
    }


def create_slider_joint(design, rootComp, params):
    """Create a slider (linear motion) joint between two components.

    Supports configurable axis via axis_x/y/z params and optional distance limits.
    """
    if rootComp.occurrences.count < 2:
        return {
            "success": False,
            "error": (
                "create_slider_joint() failed: Need at least 2 components "
                "to create a joint. Use create_component() first."
            )
        }

    idx1 = params.get('component1_index', 0)
    idx2 = params.get('component2_index', 1)

    occ1 = get_occurrence(rootComp, index=idx1)
    occ2 = get_occurrence(rootComp, index=idx2)

    x = params.get('x', 0.0)
    y = params.get('y', 0.0)
    z = params.get('z', 0.0)
    point = adsk.core.Point3D.create(x, y, z)

    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)

    axis_direction = _get_axis_direction(params)
    joint_input.setAsSliderJointMotion(axis_direction)

    joint = joints.add(joint_input)

    # Set distance limits if provided
    min_distance = params.get('min_distance', None)
    max_distance = params.get('max_distance', None)

    if min_distance is not None:
        joint.jointMotion.slideLimits.isMinimumValueEnabled = True
        joint.jointMotion.slideLimits.minimumValue = min_distance

    if max_distance is not None:
        joint.jointMotion.slideLimits.isMaximumValueEnabled = True
        joint.jointMotion.slideLimits.maximumValue = max_distance

    return {
        "success": True,
        "joint_name": joint.name,
        "joint_index": rootComp.joints.count - 1
    }


def set_joint_angle(design, rootComp, params):
    """Drive rotation on a revolute, cylindrical, or pin-slot joint (degrees).

    Validates that the target joint has a rotation DOF.
    """
    joint_index = params.get('joint_index', None)
    angle = params.get('angle', 0)

    if rootComp.joints.count == 0:
        return {
            "success": False,
            "error": (
                f"set_joint_angle(angle={angle}, joint_index={joint_index}) failed: "
                "No joints in design. Create a joint first using create_revolute_joint()."
            )
        }

    if joint_index is None:
        joint_index = rootComp.joints.count - 1

    if joint_index < 0 or joint_index >= rootComp.joints.count:
        return {
            "success": False,
            "error": (
                f"set_joint_angle(angle={angle}, joint_index={joint_index}) failed: "
                f"Joint index {joint_index} out of range. "
                f"Design has {rootComp.joints.count} joints (0-{rootComp.joints.count - 1})."
            )
        }

    joint = rootComp.joints.item(joint_index)

    # Validate joint type -- must have rotation DOF
    rotation_types = {
        adsk.fusion.JointTypes.RevoluteJointType,
        adsk.fusion.JointTypes.CylindricalJointType,
        adsk.fusion.JointTypes.PinSlotJointType,
    }
    if joint.jointMotion.jointType not in rotation_types:
        joint_type_name = str(joint.jointMotion.jointType).split('.')[-1] if '.' in str(joint.jointMotion.jointType) else str(joint.jointMotion.jointType)
        return {
            "success": False,
            "error": (
                f"set_joint_angle(angle={angle}, joint_index={joint_index}) failed: "
                f"Joint '{joint.name}' (index {joint_index}) is not a joint with rotation DOF. "
                f"Joint type: {joint_type_name}. "
                "Valid types: revolute, cylindrical, pin-slot."
            )
        }

    joint.jointMotion.rotationValue = math.radians(angle)

    return {
        "success": True,
        "joint_name": joint.name,
        "angle_degrees": angle
    }


def set_joint_distance(design, rootComp, params):
    """Drive translation on a slider, cylindrical, or pin-slot joint (cm).

    Validates that the target joint has a translation DOF.
    """
    joint_index = params.get('joint_index', None)
    distance = params.get('distance', 0)

    if rootComp.joints.count == 0:
        return {
            "success": False,
            "error": (
                f"set_joint_distance(distance={distance}, joint_index={joint_index}) failed: "
                "No joints in design. Create a joint first using create_slider_joint()."
            )
        }

    if joint_index is None:
        joint_index = rootComp.joints.count - 1

    if joint_index < 0 or joint_index >= rootComp.joints.count:
        return {
            "success": False,
            "error": (
                f"set_joint_distance(distance={distance}, joint_index={joint_index}) failed: "
                f"Joint index {joint_index} out of range. "
                f"Design has {rootComp.joints.count} joints (0-{rootComp.joints.count - 1})."
            )
        }

    joint = rootComp.joints.item(joint_index)

    # Validate joint type -- must have translation DOF
    translation_types = {
        adsk.fusion.JointTypes.SliderJointType,
        adsk.fusion.JointTypes.CylindricalJointType,
        adsk.fusion.JointTypes.PinSlotJointType,
    }
    if joint.jointMotion.jointType not in translation_types:
        joint_type_name = str(joint.jointMotion.jointType).split('.')[-1] if '.' in str(joint.jointMotion.jointType) else str(joint.jointMotion.jointType)
        return {
            "success": False,
            "error": (
                f"set_joint_distance(distance={distance}, joint_index={joint_index}) failed: "
                f"Joint '{joint.name}' (index {joint_index}) is not a joint with translation DOF. "
                f"Joint type: {joint_type_name}. "
                "Valid types: slider, cylindrical, pin-slot."
            )
        }

    joint.jointMotion.slideValue = distance

    return {
        "success": True,
        "joint_name": joint.name,
        "distance_cm": distance
    }


def _get_perpendicular_axis(slot_direction):
    """Return a JointDirection perpendicular to the given slot direction.

    If slot is Z, return X. If slot is X, return Z. If slot is Y, return Z.
    """
    if slot_direction == adsk.fusion.JointDirections.ZAxisJointDirection:
        return adsk.fusion.JointDirections.XAxisJointDirection
    elif slot_direction == adsk.fusion.JointDirections.XAxisJointDirection:
        return adsk.fusion.JointDirections.ZAxisJointDirection
    else:  # Y axis
        return adsk.fusion.JointDirections.ZAxisJointDirection


def create_rigid_joint(design, rootComp, params):
    """Create a rigid (fixed) joint between two components. No relative motion."""
    if rootComp.occurrences.count < 2:
        return {
            "success": False,
            "error": (
                "create_rigid_joint() failed: Need at least 2 components "
                "to create a joint. Use create_component() first."
            )
        }

    idx1 = params.get('component1_index', 0)
    idx2 = params.get('component2_index', 1)

    occ1 = get_occurrence(rootComp, index=idx1)
    occ2 = get_occurrence(rootComp, index=idx2)

    x = params.get('x', 0.0)
    y = params.get('y', 0.0)
    z = params.get('z', 0.0)
    point = adsk.core.Point3D.create(x, y, z)

    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)
    joint_input.setAsRigidJointMotion()

    joint = joints.add(joint_input)

    return {
        "success": True,
        "joint_name": joint.name,
        "joint_index": rootComp.joints.count - 1,
        "type": "rigid",
        "dof": "none (fixed)"
    }


def create_cylindrical_joint(design, rootComp, params):
    """Create a cylindrical joint (rotation + translation along same axis)."""
    if rootComp.occurrences.count < 2:
        return {
            "success": False,
            "error": (
                "create_cylindrical_joint() failed: Need at least 2 components "
                "to create a joint. Use create_component() first."
            )
        }

    idx1 = params.get('component1_index', 0)
    idx2 = params.get('component2_index', 1)

    occ1 = get_occurrence(rootComp, index=idx1)
    occ2 = get_occurrence(rootComp, index=idx2)

    x = params.get('x', 0.0)
    y = params.get('y', 0.0)
    z = params.get('z', 0.0)
    point = adsk.core.Point3D.create(x, y, z)

    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)

    axis_direction = _get_axis_direction(params)
    joint_input.setAsCylindricalJointMotion(axis_direction)

    joint = joints.add(joint_input)

    # Set rotation limits if provided
    min_angle = params.get('min_angle', None)
    max_angle = params.get('max_angle', None)

    if min_angle is not None:
        joint.jointMotion.rotationLimits.isMinimumValueEnabled = True
        joint.jointMotion.rotationLimits.minimumValue = math.radians(min_angle)

    if max_angle is not None:
        joint.jointMotion.rotationLimits.isMaximumValueEnabled = True
        joint.jointMotion.rotationLimits.maximumValue = math.radians(max_angle)

    # Set slide limits if provided
    min_distance = params.get('min_distance', None)
    max_distance = params.get('max_distance', None)

    if min_distance is not None:
        joint.jointMotion.slideLimits.isMinimumValueEnabled = True
        joint.jointMotion.slideLimits.minimumValue = min_distance

    if max_distance is not None:
        joint.jointMotion.slideLimits.isMaximumValueEnabled = True
        joint.jointMotion.slideLimits.maximumValue = max_distance

    limits_summary = []
    if min_angle is not None or max_angle is not None:
        limits_summary.append(f"rotation: [{min_angle}, {max_angle}] deg")
    if min_distance is not None or max_distance is not None:
        limits_summary.append(f"slide: [{min_distance}, {max_distance}] cm")

    return {
        "success": True,
        "joint_name": joint.name,
        "joint_index": rootComp.joints.count - 1,
        "type": "cylindrical",
        "dof": "rotation + translation",
        "limits": "; ".join(limits_summary) if limits_summary else "unconstrained"
    }


def create_pin_slot_joint(design, rootComp, params):
    """Create a pin-slot joint (rotation + sliding on different axes).

    Axis params define the slot direction; rotation axis is perpendicular.
    """
    if rootComp.occurrences.count < 2:
        return {
            "success": False,
            "error": (
                "create_pin_slot_joint() failed: Need at least 2 components "
                "to create a joint. Use create_component() first."
            )
        }

    idx1 = params.get('component1_index', 0)
    idx2 = params.get('component2_index', 1)

    occ1 = get_occurrence(rootComp, index=idx1)
    occ2 = get_occurrence(rootComp, index=idx2)

    x = params.get('x', 0.0)
    y = params.get('y', 0.0)
    z = params.get('z', 0.0)
    point = adsk.core.Point3D.create(x, y, z)

    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)

    slot_direction = _get_axis_direction(params)
    rotation_axis = _get_perpendicular_axis(slot_direction)
    joint_input.setAsPinSlotJointMotion(rotation_axis, slot_direction)

    joint = joints.add(joint_input)

    # Set rotation limits if provided
    min_angle = params.get('min_angle', None)
    max_angle = params.get('max_angle', None)

    if min_angle is not None:
        joint.jointMotion.rotationLimits.isMinimumValueEnabled = True
        joint.jointMotion.rotationLimits.minimumValue = math.radians(min_angle)

    if max_angle is not None:
        joint.jointMotion.rotationLimits.isMaximumValueEnabled = True
        joint.jointMotion.rotationLimits.maximumValue = math.radians(max_angle)

    # Set slide limits if provided
    min_distance = params.get('min_distance', None)
    max_distance = params.get('max_distance', None)

    if min_distance is not None:
        joint.jointMotion.slideLimits.isMinimumValueEnabled = True
        joint.jointMotion.slideLimits.minimumValue = min_distance

    if max_distance is not None:
        joint.jointMotion.slideLimits.isMaximumValueEnabled = True
        joint.jointMotion.slideLimits.maximumValue = max_distance

    return {
        "success": True,
        "joint_name": joint.name,
        "joint_index": rootComp.joints.count - 1,
        "type": "pin_slot",
        "dof": "rotation + slide"
    }


def create_planar_joint(design, rootComp, params):
    """Create a planar joint (2D sliding + rotation on a plane).

    Axis params define the plane normal (e.g., Z normal = XY plane sliding).
    All DOF unconstrained by default.
    """
    if rootComp.occurrences.count < 2:
        return {
            "success": False,
            "error": (
                "create_planar_joint() failed: Need at least 2 components "
                "to create a joint. Use create_component() first."
            )
        }

    idx1 = params.get('component1_index', 0)
    idx2 = params.get('component2_index', 1)

    occ1 = get_occurrence(rootComp, index=idx1)
    occ2 = get_occurrence(rootComp, index=idx2)

    x = params.get('x', 0.0)
    y = params.get('y', 0.0)
    z = params.get('z', 0.0)
    point = adsk.core.Point3D.create(x, y, z)

    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)

    normal_direction = _get_axis_direction(params)
    joint_input.setAsPlanarJointMotion(normal_direction)

    joint = joints.add(joint_input)

    # Set primary slide limits if provided
    min_primary = params.get('min_primary_slide', None)
    max_primary = params.get('max_primary_slide', None)

    if min_primary is not None:
        joint.jointMotion.primarySlideLimits.isMinimumValueEnabled = True
        joint.jointMotion.primarySlideLimits.minimumValue = min_primary

    if max_primary is not None:
        joint.jointMotion.primarySlideLimits.isMaximumValueEnabled = True
        joint.jointMotion.primarySlideLimits.maximumValue = max_primary

    # Set secondary slide limits if provided
    min_secondary = params.get('min_secondary_slide', None)
    max_secondary = params.get('max_secondary_slide', None)

    if min_secondary is not None:
        joint.jointMotion.secondarySlideLimits.isMinimumValueEnabled = True
        joint.jointMotion.secondarySlideLimits.minimumValue = min_secondary

    if max_secondary is not None:
        joint.jointMotion.secondarySlideLimits.isMaximumValueEnabled = True
        joint.jointMotion.secondarySlideLimits.maximumValue = max_secondary

    # Set rotation limits if provided
    min_angle = params.get('min_angle', None)
    max_angle = params.get('max_angle', None)

    if min_angle is not None:
        joint.jointMotion.rotationLimits.isMinimumValueEnabled = True
        joint.jointMotion.rotationLimits.minimumValue = math.radians(min_angle)

    if max_angle is not None:
        joint.jointMotion.rotationLimits.isMaximumValueEnabled = True
        joint.jointMotion.rotationLimits.maximumValue = math.radians(max_angle)

    return {
        "success": True,
        "joint_name": joint.name,
        "joint_index": rootComp.joints.count - 1,
        "type": "planar",
        "dof": "2D slide + rotation"
    }


def create_ball_joint(design, rootComp, params):
    """Create a ball joint (spherical rotation, 3 DOF). No axis needed."""
    if rootComp.occurrences.count < 2:
        return {
            "success": False,
            "error": (
                "create_ball_joint() failed: Need at least 2 components "
                "to create a joint. Use create_component() first."
            )
        }

    idx1 = params.get('component1_index', 0)
    idx2 = params.get('component2_index', 1)

    occ1 = get_occurrence(rootComp, index=idx1)
    occ2 = get_occurrence(rootComp, index=idx2)

    x = params.get('x', 0.0)
    y = params.get('y', 0.0)
    z = params.get('z', 0.0)
    point = adsk.core.Point3D.create(x, y, z)

    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)

    pitch_dir = adsk.fusion.JointDirections.ZAxisJointDirection
    yaw_dir = adsk.fusion.JointDirections.XAxisJointDirection
    joint_input.setAsBallJointMotion(pitch_dir, yaw_dir)

    joint = joints.add(joint_input)

    # Set pitch limits if provided
    min_pitch = params.get('min_pitch', None)
    max_pitch = params.get('max_pitch', None)

    if min_pitch is not None:
        joint.jointMotion.pitchLimits.isMinimumValueEnabled = True
        joint.jointMotion.pitchLimits.minimumValue = math.radians(min_pitch)

    if max_pitch is not None:
        joint.jointMotion.pitchLimits.isMaximumValueEnabled = True
        joint.jointMotion.pitchLimits.maximumValue = math.radians(max_pitch)

    # Set roll limits if provided
    min_roll = params.get('min_roll', None)
    max_roll = params.get('max_roll', None)

    if min_roll is not None:
        joint.jointMotion.rollLimits.isMinimumValueEnabled = True
        joint.jointMotion.rollLimits.minimumValue = math.radians(min_roll)

    if max_roll is not None:
        joint.jointMotion.rollLimits.isMaximumValueEnabled = True
        joint.jointMotion.rollLimits.maximumValue = math.radians(max_roll)

    # Set yaw limits if provided
    min_yaw = params.get('min_yaw', None)
    max_yaw = params.get('max_yaw', None)

    if min_yaw is not None:
        joint.jointMotion.yawLimits.isMinimumValueEnabled = True
        joint.jointMotion.yawLimits.minimumValue = math.radians(min_yaw)

    if max_yaw is not None:
        joint.jointMotion.yawLimits.isMaximumValueEnabled = True
        joint.jointMotion.yawLimits.maximumValue = math.radians(max_yaw)

    return {
        "success": True,
        "joint_name": joint.name,
        "joint_index": rootComp.joints.count - 1,
        "type": "ball",
        "dof": "spherical rotation (3 DOF)"
    }
