def enum_to_value(val):
    if hasattr(val, "value"):
        return val.value
    return val