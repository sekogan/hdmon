_DURATION_UNITS = {
    "h": 60 * 60,
    "m": 60,
    "s": 1,
}


def duration_to_seconds(value):
    value = value.strip()
    unit = value[-1].lower()
    if unit in _DURATION_UNITS.keys():
        return float(value[:-1].strip()) * _DURATION_UNITS[unit]
    return float(value)
