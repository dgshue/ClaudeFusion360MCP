import adsk.core
import adsk.fusion


def create_revolute_joint(design, rootComp, params):
    if rootComp.occurrences.count < 2:
        return {"success": False, "error": "Need at least 2 components to create a joint. Use create_component first."}

    idx1 = params.get('component1_index', 0)
    idx2 = params.get('component2_index', 1)

    if idx1 >= rootComp.occurrences.count or idx2 >= rootComp.occurrences.count:
        return {
            "success": False,
            "error": f"Component index out of range. Design has {rootComp.occurrences.count} components (0-{rootComp.occurrences.count - 1})."
        }

    occ1 = rootComp.occurrences.item(idx1)
    occ2 = rootComp.occurrences.item(idx2)

    x = params.get('x', 0)
    y = params.get('y', 0)
    z = params.get('z', 0)
    point = adsk.core.Point3D.create(x, y, z)

    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)
    joint_input.setAsRevoluteJointMotion(
        adsk.fusion.JointDirections.ZAxisJointDirection
    )

    joint = joints.add(joint_input)
    if params.get('flip', False):
        joint.isFlipped = True

    return {"success": True, "joint_name": joint.name}


def create_slider_joint(design, rootComp, params):
    if rootComp.occurrences.count < 2:
        return {"success": False, "error": "Need at least 2 components to create a joint. Use create_component first."}

    idx1 = params.get('component1_index', 0)
    idx2 = params.get('component2_index', 1)

    if idx1 >= rootComp.occurrences.count or idx2 >= rootComp.occurrences.count:
        return {
            "success": False,
            "error": f"Component index out of range. Design has {rootComp.occurrences.count} components (0-{rootComp.occurrences.count - 1})."
        }

    occ1 = rootComp.occurrences.item(idx1)
    occ2 = rootComp.occurrences.item(idx2)

    x = params.get('x', 0)
    y = params.get('y', 0)
    z = params.get('z', 0)
    point = adsk.core.Point3D.create(x, y, z)

    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)
    joint_input.setAsSliderJointMotion(
        adsk.fusion.JointDirections.ZAxisJointDirection
    )

    joint = joints.add(joint_input)
    return {"success": True, "joint_name": joint.name}


def set_joint_angle(design, rootComp, params):
    joint_index = params.get('joint_index', 0)
    angle = params.get('angle', 0)

    if rootComp.joints.count == 0:
        return {"success": False, "error": "No joints in design. Create a joint first."}

    if joint_index >= rootComp.joints.count:
        return {
            "success": False,
            "error": f"Joint index {joint_index} out of range. Design has {rootComp.joints.count} joints (0-{rootComp.joints.count - 1})."
        }

    joint = rootComp.joints.item(joint_index)
    import math
    joint.jointMotion.rotationValue = math.radians(angle)

    return {"success": True, "joint_name": joint.name, "angle": angle}


def set_joint_distance(design, rootComp, params):
    joint_index = params.get('joint_index', 0)
    distance = params.get('distance', 0)

    if rootComp.joints.count == 0:
        return {"success": False, "error": "No joints in design. Create a joint first."}

    if joint_index >= rootComp.joints.count:
        return {
            "success": False,
            "error": f"Joint index {joint_index} out of range. Design has {rootComp.joints.count} joints (0-{rootComp.joints.count - 1})."
        }

    joint = rootComp.joints.item(joint_index)
    joint.jointMotion.slideValue = distance

    return {"success": True, "joint_name": joint.name, "distance": distance}
