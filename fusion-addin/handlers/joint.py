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
    """Drive a revolute joint to a specified angle in degrees.

    Validates that the target joint is actually a revolute joint.
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

    # Validate joint type
    if joint.jointMotion.jointType != adsk.fusion.JointTypes.RevoluteJointType:
        joint_type_name = str(joint.jointMotion.jointType).split('.')[-1] if '.' in str(joint.jointMotion.jointType) else str(joint.jointMotion.jointType)
        return {
            "success": False,
            "error": (
                f"set_joint_angle(angle={angle}, joint_index={joint_index}) failed: "
                f"Joint '{joint.name}' (index {joint_index}) is not a RevoluteJoint. "
                f"Joint type: {joint_type_name}. "
                "Use set_joint_distance() for slider joints."
            )
        }

    joint.jointMotion.rotationValue = math.radians(angle)

    return {
        "success": True,
        "joint_name": joint.name,
        "angle_degrees": angle
    }


def set_joint_distance(design, rootComp, params):
    """Drive a slider joint to a specified distance in cm.

    Validates that the target joint is actually a slider joint.
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

    # Validate joint type
    if joint.jointMotion.jointType != adsk.fusion.JointTypes.SliderJointType:
        joint_type_name = str(joint.jointMotion.jointType).split('.')[-1] if '.' in str(joint.jointMotion.jointType) else str(joint.jointMotion.jointType)
        return {
            "success": False,
            "error": (
                f"set_joint_distance(distance={distance}, joint_index={joint_index}) failed: "
                f"Joint '{joint.name}' (index {joint_index}) is not a SliderJoint. "
                f"Joint type: {joint_type_name}. "
                "Use set_joint_angle() for revolute joints."
            )
        }

    joint.jointMotion.slideValue = distance

    return {
        "success": True,
        "joint_name": joint.name,
        "distance_cm": distance
    }
