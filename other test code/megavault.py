"""
MegaVault Storage Calculation Test File
----------------------------------------
Includes:
- Length or Width constraint selection
- Module calculation
- Gross Volume
- Net Volume (95%)
- Bluemetal Base Volume
"""

import math


# ==========================================================
# MODULE CALCULATION
# ==========================================================

def calculate_modules(length, width, depth):
    modules_length = (length - 0.06) / 1.15
    modules_width = (width - 0.06) / 1.15
    modules_depth = (depth - 0.03) / 0.5

    return (
        round(modules_length, 3),
        round(modules_width, 3),
        round(modules_depth, 3),
    )


# ==========================================================
# LENGTH CONSTRAINT
# ==========================================================

def calculate_length_from_constraint(required_volume, width, depth):
    modules = math.ceil(required_volume / 0.96 / width / depth / 0.575)
    length = modules * 0.575 + 0.06
    return round(length, 3)


# ==========================================================
# WIDTH CONSTRAINT
# ==========================================================

def calculate_width_from_constraint(required_volume, length, depth):
    modules = math.ceil(required_volume / 0.96 / length / depth / 0.575)
    width = modules * 0.575 + 0.06
    return round(width, 3)


# ==========================================================
# GROSS VOLUME
# ==========================================================

def calculate_gross_volume(length, width, depth):
    gross = (
        length * width * (depth - 0.03)
        + (length - 0.06) * (width - 0.06) * 0.03
    )
    return round(gross, 2)


# ==========================================================
# NET VOLUME (95%)
# ==========================================================

def calculate_net_volume(gross_volume):
    return round(gross_volume * 0.95, 2)


# ==========================================================
# BLUEMETAL BASE
# ==========================================================

def calculate_bluemetal_volume(length, width, base_height, factor):
    gross_base = length * width * base_height
    print("gross_base",gross_base)
    print("factor",factor)
    net_base = gross_base * (factor/100)
    return round(gross_base, 2), round(net_base, 2)


# ==========================================================
# MASTER MEGAVAULT FUNCTION
# ==========================================================

def calculate_megavault(
    required_volume,
    length,
    width,
    depth,
    constraint_type="length",   # "length" or "width"
    base_height=0,
    base_factor=1
):

    if constraint_type == "length":
        length = calculate_length_from_constraint(
            required_volume, width, depth
        )

    elif constraint_type == "width":
        width = calculate_width_from_constraint(
            required_volume, length, depth
        )

    else:
        raise ValueError("constraint_type must be 'length' or 'width'")

    modules = calculate_modules(length, width, depth)

    gross_volume = calculate_gross_volume(length, width, depth)
    net_volume = calculate_net_volume(gross_volume)

    gross_base, net_base = calculate_bluemetal_volume(
        length, width, base_height, base_factor
    )

    return {
        "Length (m)": length,
        "Width (m)": width,
        "Depth (m)": depth,
        "Modules (L, W, D)": modules,
        "Gross Volume (m³)": gross_volume,
        "Net Volume (m³)": net_volume,
        "Bluemetal Gross (m³)": gross_base,
        "Bluemetal Net (m³)": net_base
    }


# ==========================================================
# TEST RUN
# ==========================================================

if __name__ == "__main__":

    print("\n========== MEGAVAULT TEST ==========\n")

    result = calculate_megavault(
        required_volume=1,   # Volume Required
        length=13,             # Initial length (used if width constraint)
        width=12.135,
        depth=1.53,
        constraint_type="length",  # Try "width" also
        base_height=1,
        base_factor=32
    )

    for key, value in result.items():
        print(f"{key:<25}: {value}")

    print("\n====================================\n")