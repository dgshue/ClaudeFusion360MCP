import adsk.core
import adsk.fusion


def create_parameter(design, rootComp, params):
    try:
        name = params['name']
        expression = params['expression']
        unit = params.get('unit', 'cm')
        comment = params.get('comment', '')

        userParams = design.userParameters

        # Check if parameter already exists
        existing = userParams.itemByName(name)
        if existing:
            return {
                "success": False,
                "error": f"Parameter '{name}' already exists with expression '{existing.expression}'. Use set_parameter to update it."
            }

        param = userParams.add(
            name,
            adsk.core.ValueInput.createByString(expression),
            unit,
            comment
        )

        return {
            "success": True,
            "parameter": name,
            "expression": param.expression,
            "value": param.value,
            "unit": param.unit
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_parameter(design, rootComp, params):
    try:
        name = params['name']
        expression = params['expression']

        userParams = design.userParameters
        param = userParams.itemByName(name)

        if not param:
            # List available parameters for helpful error
            available = []
            for i in range(userParams.count):
                available.append(userParams.item(i).name)
            return {
                "success": False,
                "error": f"Parameter '{name}' not found. Available parameters: {available}"
            }

        param.expression = expression

        return {
            "success": True,
            "parameter": name,
            "expression": param.expression,
            "value": param.value,
            "unit": param.unit
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
