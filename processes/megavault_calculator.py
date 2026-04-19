import math


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODULE_LENGTH = 3.602
MODULE_WIDTH = 2.402


# ---------------------------------------------------------------------------
# Selected Modules
# ---------------------------------------------------------------------------

def calculate_selected_modules(grid):
    """
    Replicates Excel: =SUM(G4:AR55)
    Each '1' in the grid represents one module.
    """
    total_modules = 0
    for row in grid:
        total_modules += sum(row)
    return total_modules


# ---------------------------------------------------------------------------
# Tank Dimensions
# ---------------------------------------------------------------------------

def calculate_tank_length(grid):
    """
    Replicates Excel logic:
    Tank Length = MODULE_LENGTH * MAX(SUM(row))
    """
    max_modules_in_row = max(sum(row) for row in grid)
    return MODULE_LENGTH * max_modules_in_row


def calculate_tank_width(grid):
    """
    Replicates Excel logic:
    Tank Width = MODULE_WIDTH * MAX(SUM(column))
    """
    column_sums = [sum(col) for col in zip(*grid)]
    max_modules_in_column = max(column_sums)
    return MODULE_WIDTH * max_modules_in_column


# ---------------------------------------------------------------------------
# Storage Heights
# ---------------------------------------------------------------------------

def calculate_min_storage_height(
    max_storage_height,
    tank_grade_percent,
    direction,
    tank_length,
    tank_width
):
    tank_grade = tank_grade_percent / 100

    # if direction in ["→", "←"]:
    #     min_height = max_storage_height - (tank_grade * tank_length)
    # elif direction in ["↑", "↓"]:
    #     min_height = max_storage_height - (tank_grade * tank_width)
    # else:
    #     raise ValueError("Invalid direction. Use →, ←, ↑, or ↓.")
    


    if direction.lower() in ["left", "right"]:


        min_height = max_storage_height - (tank_grade * tank_length)

    elif direction.lower() in ["top", "bottom"]:


        min_height = max_storage_height - (tank_grade * tank_width)

    else:
     
     raise ValueError("Invalid direction. Use Top, Bottom, Left, or Right.")

    return min_height


def calculate_effective_storage_height(max_storage_height, min_storage_height):
    effective_storage_height = (max_storage_height + min_storage_height) / 2
    return effective_storage_height


# ---------------------------------------------------------------------------
# Volumes
# ---------------------------------------------------------------------------

def calculate_total_volume_per_base(internal_height):
    """
    Excel: BR45 = 8.277 + (B9-1)*10*0.827 + (0.26*0.26*B9*2)
    """
    volume = (
        8.277
        + (internal_height - 1) * 10 * 0.827
        + (0.26 * 0.26 * internal_height * 2)
    )
    return volume


def calculate_effective_volume_per_base(
    total_volume_per_base,
    internal_height,
    effective_storage_height
):
    """
    Excel: BR46 = (BR45 / B9) * B10
    """
    return (total_volume_per_base / internal_height) * effective_storage_height


def calculate_modules_required(target_volume, effective_volume, head_chamber):
    """
    Excel:
    =IF(B16="Yes", ROUNDUP((B8)/BR46,0)+1,
                   ROUNDUP((B8)/BR46,0))
    """
    modules = math.ceil(target_volume / effective_volume)
    if head_chamber.lower() == "yes":
        modules += 1
    return modules


def calculate_proposed_total_volume(selected_modules, total_volume_per_base):
    """
    Excel: Proposed Total Volume = B20 * BR45
    """
    return selected_modules * total_volume_per_base


def calculate_proposed_effective_volume(
    selected_modules,
    effective_volume_per_base,
    filter_volume,
    head_chamber
):
    """
    Excel: Proposed Effective Volume
    """
    if head_chamber.lower() == "yes":
        proposed_volume = (
            selected_modules * effective_volume_per_base
        ) - effective_volume_per_base - filter_volume
    else:
        proposed_volume = (
            selected_modules * effective_volume_per_base
        ) - filter_volume
    return proposed_volume


# ---------------------------------------------------------------------------
# OSD Curve & Surface Area
# ---------------------------------------------------------------------------

def calculate_osd_elevations(osd_invert_level, tank_length, tank_grade_percent, internal_height):
    """
    Replicates Excel formulas:
    Row1: A30
    Row2: A30 + (B24 * B11) / 2
    Row3: A30 + (B24 * B11)
    Row4: A30 + B9
    """
    tank_grade = tank_grade_percent / 100

    elevation_1 = osd_invert_level
    elevation_2 = osd_invert_level + (tank_length * tank_grade) / 2
    elevation_3 = osd_invert_level + (tank_length * tank_grade)
    elevation_4 = osd_invert_level + internal_height

    return [
        round(elevation_1, 2),
        round(elevation_2, 2),
        round(elevation_3, 2),
        round(elevation_4, 2),
    ]


def calculate_surface_area(volume_per_module, internal_height, selected_modules):
    surface_1 = 1
    surface_2 = ((volume_per_module / internal_height) * selected_modules) / 2
    surface_3 = (volume_per_module / internal_height) * selected_modules
    surface_4 = surface_3

    return [
        round(surface_1, 2),
        round(surface_2, 2),
        round(surface_3, 2),
        round(surface_4, 2),
    ]


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_calculator(
    grid,
    rows,
    cols,
    internal_height,
    max_storage_height,
    tank_grade_percent,
    direction,
    target_volume,
    head_chamber,
    filter_volume,
    
    osd_invert_level,
    hed_volume
):
    selected_modules = calculate_selected_modules(grid)

    tank_length = calculate_tank_length(grid)
    tank_width = calculate_tank_width(grid)

    min_storage_height = calculate_min_storage_height(
        max_storage_height,
        tank_grade_percent,
        direction,
        tank_length,
        tank_width
    )

    effective_storage_height = calculate_effective_storage_height(
        max_storage_height,
        min_storage_height
    )

    total_volume_per_base = calculate_total_volume_per_base(internal_height)

    effective_volume_per_base = calculate_effective_volume_per_base(
        total_volume_per_base,
        internal_height,
        effective_storage_height
    )

    modules_required = calculate_modules_required(
        target_volume,
        effective_volume_per_base,
        head_chamber
    )

    proposed_total_volume = calculate_proposed_total_volume(
        selected_modules,
        total_volume_per_base
    )

    proposed_effective_volume = calculate_proposed_effective_volume(
        selected_modules,
        effective_volume_per_base,
        filter_volume,
        head_chamber
    )

    elevations = calculate_osd_elevations(
        osd_invert_level,
        tank_length,
        tank_grade_percent,
        internal_height
    )

    surfaces = calculate_surface_area(
        total_volume_per_base,
        internal_height,
        selected_modules
    )

    def round3(x):
        return round(x, 3) if isinstance(x, (int, float)) else x
    
    # rows = len(grid)
    # cols = len(grid[0]) if grid else 0

    

    return {
    "rows": rows,
    "cols": cols,
    # "grid": grid,
    "selected_modules": selected_modules,
    "modules_required": modules_required,


    "tank_length": round(tank_length, 2),
    "tank_width": round(tank_width, 2),

   
    "min_storage_height": round(min_storage_height, 3),
    "effective_storage_height": round(effective_storage_height, 3),

  
    "total_volume_per_base": round(total_volume_per_base, 3),
    "effective_volume_per_base": round(effective_volume_per_base, 5), 

    "proposed_total_volume": round(proposed_total_volume, 2),
    "proposed_effective_volume": round(proposed_effective_volume, 2),


    "elevations": [round(x, 2) for x in elevations],
    "surface_areas": [round(x, 2) for x in surfaces],

    "hed_volume": hed_volume,
}