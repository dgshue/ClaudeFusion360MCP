import adsk.core
import adsk.fusion

# In-memory named markers (not persistent across Fusion sessions)
_markers = {}


def _health_state_str(health_state):
    """Map FeatureHealthStates enum to human-readable string."""
    mapping = {
        adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState: "healthy",
        adsk.fusion.FeatureHealthStates.WarningFeatureHealthState: "warning",
        adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState: "error",
        adsk.fusion.FeatureHealthStates.SuppressedFeatureHealthState: "suppressed",
        adsk.fusion.FeatureHealthStates.RolledBackFeatureHealthState: "rolled_back",
    }
    return mapping.get(health_state, "unknown")


def get_timeline(design, rootComp, params):
    try:
        timeline = design.timeline
        features = []

        for i in range(timeline.count):
            item = timeline.item(i)
            entry = {
                "index": i,
                "name": item.name if hasattr(item, 'name') else f"Feature {i}",
                "isSuppressed": item.isSuppressed,
                "isRolledBack": item.isRolledBack,
                "healthState": _health_state_str(item.healthState),
                "isGroup": item.isGroup,
            }
            features.append(entry)

        return {
            "success": True,
            "marker_position": timeline.markerPosition,
            "count": timeline.count,
            "features": features
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def edit_at_timeline(design, rootComp, params):
    try:
        position = params['position']
        timeline = design.timeline

        if position == -1:
            timeline.moveToEnd()
            return {
                "success": True,
                "marker_position": timeline.markerPosition,
                "message": "All features active"
            }

        if position < 0 or position > timeline.count:
            return {
                "success": False,
                "error": f"Position {position} out of range. Valid range: 0 to {timeline.count} (or -1 for end)."
            }

        timeline.markerPosition = position

        # Count suppressed features after the marker
        suppressed_count = 0
        for i in range(position, timeline.count):
            if timeline.item(i).isRolledBack:
                suppressed_count += 1

        return {
            "success": True,
            "marker_position": position,
            "suppressed_features": suppressed_count,
            "message": f"Features after position {position} are now suppressed. Use edit_at_timeline(position=-1) to return to end."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_marker(design, rootComp, params):
    try:
        name = params['name']
        timeline = design.timeline
        position = timeline.markerPosition

        _markers[name] = position

        return {
            "success": True,
            "marker": name,
            "position": position,
            "total_markers": len(_markers)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def undo_to_marker(design, rootComp, params):
    try:
        name = params['name']

        if name not in _markers:
            available = list(_markers.keys())
            return {
                "success": False,
                "error": f"Marker '{name}' not found. Available markers: {available}"
            }

        timeline = design.timeline
        current_position = timeline.markerPosition
        target_position = _markers[name]

        timeline.markerPosition = target_position

        return {
            "success": True,
            "marker": name,
            "from_position": current_position,
            "to_position": target_position
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
