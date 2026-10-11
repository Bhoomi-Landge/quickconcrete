"""Structured concrete order requirements — parsing, validation, and API serialization."""

WORKABILITY_MM_MIN = 1
WORKABILITY_MM_MAX = 1000

PUMP_TYPES = ("BOOM", "LINE", "OTHER")
PLACEMENT_METHODS = ("PUMP", "BUCKET_CRANE", "CHUTE", "DIRECT_DISCHARGE", "OTHER")
WORKABILITY_TEST_TYPES = ("SLUMP", "SLUMP_FLOW")
SPECIAL_CONCRETE_TYPES = (
    "NORMAL",
    "FREE_FLOW",
    "SCC",
    "TEMPERATURE_CONTROLLED",
    "OTHER",
)

_REQUIREMENT_KEYS = frozenset(
    {
        "pump_required",
        "pump_type",
        "pump_boom_reach_m",
        "pump_pipeline_length_m",
        "pump_instructions",
        "placement_method",
        "placement_method_other",
        "workability_test_type",
        "target_slump_mm",
        "minimum_slump_mm",
        "maximum_slump_mm",
        "special_concrete_type",
        "special_concrete_notes",
        "requested_concrete_temp_c",
    }
)


class RequirementError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def requirements_payload_in_request(data):
    return any(key in data for key in _REQUIREMENT_KEYS)


def parse_order_requirements(data):
    if not requirements_payload_in_request(data):
        return {}

    pump_required = _parse_bool(data.get("pump_required"), "Pump requirement")
    if pump_required is None:
        raise RequirementError("Pump requirement (with or without pump) is required.")

    placement_method = _parse_enum(data.get("placement_method"), PLACEMENT_METHODS, "placement method")
    if not placement_method:
        raise RequirementError("Method of concrete placing is required.")

    placement_method_other = (data.get("placement_method_other") or "").strip() or None
    if placement_method == "OTHER" and not placement_method_other:
        raise RequirementError("Please describe the placing method when Other is selected.")

    workability_test_type = _parse_enum(
        data.get("workability_test_type"), WORKABILITY_TEST_TYPES, "workability test type"
    )
    if not workability_test_type:
        raise RequirementError("Workability test type (slump or slump flow) is required.")

    target_slump_mm = _parse_mm(data.get("target_slump_mm"), "Target value")
    minimum_slump_mm = _parse_mm(data.get("minimum_slump_mm"), "Minimum value", optional=True)
    maximum_slump_mm = _parse_mm(data.get("maximum_slump_mm"), "Maximum value", optional=True)
    _validate_workability_range(target_slump_mm, minimum_slump_mm, maximum_slump_mm)

    special_concrete_type = _parse_enum(
        data.get("special_concrete_type"), SPECIAL_CONCRETE_TYPES, "special concrete type"
    )
    if not special_concrete_type:
        raise RequirementError("Special concrete type is required.")

    special_concrete_notes = (data.get("special_concrete_notes") or "").strip() or None
    requested_concrete_temp_c = _parse_temperature(
        data.get("requested_concrete_temp_c"),
        optional=special_concrete_type != "TEMPERATURE_CONTROLLED",
    )

    if special_concrete_type == "OTHER" and not special_concrete_notes:
        raise RequirementError("Please describe the special concrete requirement when Other is selected.")

    pump_type = None
    pump_boom_reach_m = None
    pump_pipeline_length_m = None
    pump_instructions = None

    if pump_required:
        pump_type = _parse_enum(data.get("pump_type"), PUMP_TYPES, "pump type", optional=True)
        pump_boom_reach_m = _parse_positive_metres(
            data.get("pump_boom_reach_m"), "Boom reach", optional=True
        )
        pump_pipeline_length_m = _parse_positive_metres(
            data.get("pump_pipeline_length_m"), "Pipeline length", optional=True
        )
        pump_instructions = (data.get("pump_instructions") or "").strip() or None
    elif _any_pump_detail_in_payload(data):
        raise RequirementError("Pump-specific details cannot be sent when pump is not required.")

    if placement_method == "PUMP" and pump_required is False:
        raise RequirementError(
            "Placing method is Pump but pump requirement is Without pump. "
            "Update pump requirement or choose a different placing method."
        )

    return {
        "pump_required": pump_required,
        "pump_type": pump_type,
        "pump_boom_reach_m": pump_boom_reach_m,
        "pump_pipeline_length_m": pump_pipeline_length_m,
        "pump_instructions": pump_instructions,
        "placement_method": placement_method,
        "placement_method_other": placement_method_other if placement_method == "OTHER" else None,
        "workability_test_type": workability_test_type,
        "target_slump_mm": target_slump_mm,
        "minimum_slump_mm": minimum_slump_mm,
        "maximum_slump_mm": maximum_slump_mm,
        "special_concrete_type": special_concrete_type,
        "special_concrete_notes": special_concrete_notes,
        "requested_concrete_temp_c": requested_concrete_temp_c,
    }


def requirements_dict_from_order(order):
    """API-shaped requirement fields from an existing order (for merge on PATCH)."""
    return {
        "pump_required": order.pump_required,
        "pump_type": order.pump_type,
        "pump_boom_reach_m": order.pump_boom_reach_m,
        "pump_pipeline_length_m": order.pump_pipeline_length_m,
        "pump_instructions": order.pump_instructions,
        "placement_method": order.placement_method,
        "placement_method_other": order.placement_method_other,
        "workability_test_type": order.workability_test_type,
        "target_slump_mm": order.target_slump_mm,
        "minimum_slump_mm": order.minimum_slump_mm,
        "maximum_slump_mm": order.maximum_slump_mm,
        "special_concrete_type": order.special_concrete_type,
        "special_concrete_notes": order.special_concrete_notes,
        "requested_concrete_temp_c": order.requested_concrete_temp_c,
    }


def parse_order_requirements_patch(order, data):
    """If any requirement key is in data, merge with stored order and validate full set."""
    if not requirements_payload_in_request(data):
        return None
    merged = requirements_dict_from_order(order)
    for key in _REQUIREMENT_KEYS:
        if key in data:
            merged[key] = data[key]
    if merged.get("pump_required") is False:
        merged["pump_type"] = None
        merged["pump_boom_reach_m"] = None
        merged["pump_pipeline_length_m"] = None
        merged["pump_instructions"] = None
    return parse_order_requirements(merged)


def requirements_to_dict(order):
    return {
        "pump_required": order.pump_required,
        "pump_type": order.pump_type,
        "pump_boom_reach_m": order.pump_boom_reach_m,
        "pump_pipeline_length_m": order.pump_pipeline_length_m,
        "pump_instructions": order.pump_instructions,
        "placement_method": order.placement_method,
        "placement_method_other": order.placement_method_other,
        "workability_test_type": order.workability_test_type,
        "target_slump_mm": order.target_slump_mm,
        "minimum_slump_mm": order.minimum_slump_mm,
        "maximum_slump_mm": order.maximum_slump_mm,
        "special_concrete_type": order.special_concrete_type,
        "special_concrete_notes": order.special_concrete_notes,
        "requested_concrete_temp_c": order.requested_concrete_temp_c,
    }


def _any_pump_detail_in_payload(data):
    for key in (
        "pump_type",
        "pump_boom_reach_m",
        "pump_pipeline_length_m",
        "pump_instructions",
    ):
        val = data.get(key)
        if val is None:
            continue
        if isinstance(val, str) and not val.strip():
            continue
        return True
    return False


def _parse_bool(value, field_label):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise RequirementError(f"{field_label} must be true or false.")


def _parse_enum(value, allowed, field_label, optional=False):
    if value is None or (isinstance(value, str) and not value.strip()):
        if optional:
            return None
        return None
    key = str(value).strip().upper()
    if key not in allowed:
        raise RequirementError(f"Invalid {field_label}.")
    return key


def _parse_mm(value, field_label, optional=False):
    if value is None or value == "":
        if optional:
            return None
        raise RequirementError(f"{field_label} is required.")
    try:
        if isinstance(value, bool):
            raise ValueError
        mm = int(float(value))
    except (TypeError, ValueError):
        raise RequirementError(f"{field_label} must be a whole number of millimetres.")
    if mm < WORKABILITY_MM_MIN or mm > WORKABILITY_MM_MAX:
        raise RequirementError(
            f"{field_label} must be between {WORKABILITY_MM_MIN} and {WORKABILITY_MM_MAX} mm."
        )
    return mm


def _validate_workability_range(target, minimum, maximum):
    if minimum is not None and maximum is not None and minimum > maximum:
        raise RequirementError("Minimum workability value cannot exceed maximum.")
    if target is not None and minimum is not None and target < minimum:
        raise RequirementError("Target workability value must be at least the minimum.")
    if target is not None and maximum is not None and target > maximum:
        raise RequirementError("Target workability value must not exceed the maximum.")


def _parse_positive_metres(value, field_label, optional=False):
    if value is None or value == "":
        if optional:
            return None
        return None
    try:
        metres = float(value)
    except (TypeError, ValueError):
        raise RequirementError(f"{field_label} must be a number.")
    if metres <= 0 or metres > 200:
        raise RequirementError(f"{field_label} must be between 0 and 200 m.")
    return round(metres, 2)


def _parse_temperature(value, optional=False):
    if value is None or value == "":
        if optional:
            return None
        return None
    try:
        temp = float(value)
    except (TypeError, ValueError):
        raise RequirementError("Requested concrete temperature must be a number.")
    if temp < -5 or temp > 40:
        raise RequirementError("Requested concrete temperature must be between -5 and 40 °C.")
    return round(temp, 1)
