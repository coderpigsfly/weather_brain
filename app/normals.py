"""
The house's monthly climate normals (house.json: normals:, from its nearest station).
This is the brain's "long-term memory": what each month usually feels like.
Used to decide when the weather is unusual for the time of year.
"""

import house

# How far from normal (in degrees F) counts as "unusual", and month number -> typical values:
# both from house.json (normals:), so the code knows no place.
UNUSUAL_DEGREES = house.UNUSUAL_DEGREES
NORMALS = house.NORMALS

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def compare_to_normal(temp_f, kind, month):
    """
    Compare a temperature to the normal for that month.

    temp_f: the forecast temperature in degrees F
    kind:   "high" (daytime) or "low" (overnight)
    month:  1-12

    Returns how far off it is and whether that's unusually warm or cool.
    """
    normal = NORMALS[month][kind]
    diff = round(temp_f - normal)

    if diff >= UNUSUAL_DEGREES:
        direction = "warm"
    elif diff <= -UNUSUAL_DEGREES:
        direction = "cool"
    else:
        direction = None  # within the normal range, nothing to mention

    return {
        "month": MONTH_NAMES[month],
        "kind": kind,
        "temp": round(temp_f),
        "normal": normal,
        "diff": diff,
        "direction": direction,
    }
