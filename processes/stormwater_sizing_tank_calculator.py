from extensions import db
from models.stormwater_output import (
    StormwaterTankCalculation,
    AdditionalVolumeOutput
)
from models.stormwater_input import StormwaterSizingCalculation
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal, ROUND_HALF_UP, getcontext
import math
import logging

logger = logging.getLogger(__name__)
getcontext().prec = 12


# ═══════════════════════════════════════════════════════════════
# ROUNDING HELPER
# ═══════════════════════════════════════════════════════════════
def round_decimal(value, places=2):
    if value is None:
        return None
    return float(
        Decimal(str(value)).quantize(
            Decimal(f"1.{'0'*places}"),
            rounding=ROUND_HALF_UP
        )
    )


# ═══════════════════════════════════════════════════════════════
# MODULE DEPTH STEPPED LOOKUP
# Mirrors Excel F25 logic exactly.
# Returns 1, 2, 4, or 6 — or None if depth is out of valid range.
# ═══════════════════════════════════════════════════════════════
def get_module_depth_steps(depth):
    if depth < 1:        return None
    elif depth <= 1.38:  return 1
    elif depth <= 2.16:  return 2
    elif depth <= 2.94:  return 4
    elif depth <= 3.34:  return 6
    else:                return None


# ═══════════════════════════════════════════════════════════════
# MODULE COUNTS  (Excel D25, E25, F25)
# ═══════════════════════════════════════════════════════════════
def calculate_modules(length, width, depth):
    """
    module_length = ROUNDDOWN((length - 0.06) / 1.15, 0)
    module_width  = ROUNDDOWN((width  - 0.06) / 1.15, 0)
    module_depth  = stepped lookup (1 / 2 / 4 / 6 or None)
    """
    module_length = math.floor((length - 0.06) / 1.15)
    module_width  = math.floor((width  - 0.06) / 1.15)
    module_depth  = get_module_depth_steps(depth)
    return module_length, module_width, module_depth


# ═══════════════════════════════════════════════════════════════
# CONSTRAINT CALCULATIONS  (Detention — volume_required is known)
#
# Both functions use stepped module_depth (F25), not raw depth.
# Formula pattern (Excel D26):
#   modules = ROUNDUP(volume_required / 0.96 / fixed_dim / module_depth / 0.575, 0)
#   free_dim = modules * 0.575 + 0.06
#
# constraint_type == "length"  →  length is FIXED, calculate WIDTH
# constraint_type == "width"   →  width  is FIXED, calculate LENGTH
# ═══════════════════════════════════════════════════════════════

def calculate_free_length(volume_required, fixed_width, depth, fallback_length):
    """
    Width is the constrained (fixed) dimension.
    Calculate the minimum required LENGTH to meet volume_required.

    If volume_required is 0 or None, return fallback_length unchanged.
    """
    module_depth = get_module_depth_steps(depth)

    if volume_required and volume_required > 0 and module_depth and fixed_width > 0:
        modules = math.ceil(
            volume_required / 0.96 / fixed_width / module_depth / 0.575
        )
        length = modules * 0.575 + 0.06
        logger.info(
            f"calculate_free_length | "
            f"vol={volume_required} fixed_width={fixed_width} depth={depth} "
            f"→ modules={modules} length={length}"
        )
        return round_decimal(length, 3)

    return fallback_length


def calculate_free_width(volume_required, fixed_length, depth, fallback_width):
    """
    Length is the constrained (fixed) dimension.
    Calculate the minimum required WIDTH to meet volume_required.

    If volume_required is 0 or None, return fallback_width unchanged.
    """
    module_depth = get_module_depth_steps(depth)

    if volume_required and volume_required > 0 and module_depth and fixed_length > 0:
        modules = math.ceil(
            volume_required / 0.96 / fixed_length / module_depth / 0.575
        )
        width = modules * 0.575 + 0.06
        logger.info(
            f"calculate_free_width | "
            f"vol={volume_required} fixed_length={fixed_length} depth={depth} "
            f"→ modules={modules} width={width}"
        )
        return round_decimal(width, 3)

    return fallback_width


# ═══════════════════════════════════════════════════════════════
# VOLUME CALCULATIONS  (Excel G26 / I26)
# ═══════════════════════════════════════════════════════════════
def calculate_gross_volume(module_length, module_width, module_depth):
    """
    Excel G26: = module_length * module_width * (module_depth / 2)
    Uses integer module counts — NOT raw tank dimensions.
    Returns 0.0 when module_depth is None.
    """
    if module_depth is None:
        return 0.0
    gross = module_length * module_width * (module_depth / 2)
    return round_decimal(gross, 2)


def calculate_net_volume(gross_volume):
    """
    Excel I26: net = gross  (no 0.95 reduction in this system)
    """
    return gross_volume


def calculate_bluemetal_volume(length, width, base_height, factor):
    gross_base = length * width * base_height
    net_base   = gross_base * (factor / 100)
    return round_decimal(gross_base, 2), round_decimal(net_base, 2)


# ═══════════════════════════════════════════════════════════════
# MAIN SERVICE — DETENTION TANK SIZING
#
# Behaviour with constraint_type:
#
#   "length"  →  tank_length is FIXED by user
#                calculate free WIDTH from volume_required
#                (same pattern as infiltration iterator, but direct formula)
#
#   "width"   →  tank_width is FIXED by user
#                calculate free LENGTH from volume_required
#
# volume_required comes from sizing.approx_net_volume_depth
# (set by the graph run / user input for detention).
# ═══════════════════════════════════════════════════════════════
def run_megavault_calculation(project_id):

    logger.info(f"Megavault (Detention) calculation | project_id={project_id}")

    try:
        # ── Fetch sizing record ───────────────────────────────────────────────
        sizing = StormwaterSizingCalculation.query.filter_by(
            project_id=project_id
        ).first()

        if not sizing:
            raise ValueError("Sizing data not found")

        constraint_type  = sizing.constraint_type
        volume_required  = sizing.approx_net_volume_depth or 0
        tank_length_in   = float(sizing.tank_length or 0)
        tank_width_in    = float(sizing.tank_width  or 0)
        depth            = float(sizing.tank_depth  or 0)
        base_height      = float(sizing.bluemetal_base_height or 0)
        base_factor      = float(sizing.bluemetal_base_factor or 0)

        if not depth:
            raise ValueError("tank_depth must be provided")

        if constraint_type not in ("length", "width"):
            raise ValueError("constraint_type must be 'length' or 'width'")

        # ── Apply constraint to derive the free dimension ─────────────────────
        #
        # constraint_type == "length"  →  tank_length is FIXED
        #                                 calculate WIDTH
        # constraint_type == "width"   →  tank_width  is FIXED
        #                                 calculate LENGTH

        if constraint_type == "length":
            # Fixed: length.  Free: width.
            if not tank_length_in:
                raise ValueError(
                    "constraint_type is 'length' — tank_length must be provided"
                )
            length = tank_length_in
            width  = calculate_free_width(
                volume_required, length, depth, tank_width_in
            )
            logger.info(
                f"Detention | constraint=length fixed | "
                f"L={length} → W calculated={width}"
            )

        else:
            # Fixed: width.  Free: length.
            if not tank_width_in:
                raise ValueError(
                    "constraint_type is 'width' — tank_width must be provided"
                )
            width  = tank_width_in
            length = calculate_free_length(
                volume_required, width, depth, tank_length_in
            )
            logger.info(
                f"Detention | constraint=width fixed | "
                f"W={width} → L calculated={length}"
            )

        # ── Module counts ─────────────────────────────────────────────────────
        module_length, module_width, module_depth = calculate_modules(
            length, width, depth
        )

        if module_depth is None:
            raise ValueError(
                f"tank_depth={depth} is outside the valid AtlanCube range (1.0 – 3.34 m)"
            )

        # ── Volume ───────────────────────────────────────────────────────────
        gross_volume = calculate_gross_volume(module_length, module_width, module_depth)
        net_volume   = calculate_net_volume(gross_volume)

        # ── Bluemetal ─────────────────────────────────────────────────────────
        bluemetal_gross, bluemetal_net = calculate_bluemetal_volume(
            length, width, base_height, base_factor
        )

        # ── Additional storage ────────────────────────────────────────────────
        additional = AdditionalVolumeOutput.query.filter_by(
            project_id=project_id
        ).first()
        total_additional = float(
            additional.total_additional_storage if additional else 0
        )

        # ── Volume provided ───────────────────────────────────────────────────
        volume_provided = round_decimal(
            total_additional + net_volume + bluemetal_net, 2
        )

        # ── Upsert StormwaterTankCalculation ──────────────────────────────────
        existing = StormwaterTankCalculation.query.filter_by(
            project_id=project_id
        ).first()

        if existing:
            existing.tank_length  = length
            existing.tank_width   = width
            existing.tank_bredth  = depth

            existing.module_length  = module_length
            existing.module_width   = module_width
            existing.module_breadth = module_depth

            existing.gross_volume = gross_volume
            existing.net_volume   = net_volume

            existing.bluemetal_gross_volume = bluemetal_gross
            existing.bluemetal_net_volume   = bluemetal_net

            existing.volume_provided = volume_provided
            existing.volume_required = None   # set by graph run
            existing.tank_base_soakwell_base_max_stormwater_height = None
            existing.graph = None

        else:
            existing = StormwaterTankCalculation(
                project_id      = project_id,
                tank_length     = length,
                tank_width      = width,
                tank_bredth     = depth,
                module_length   = module_length,
                module_width    = module_width,
                module_breadth  = module_depth,
                gross_volume    = gross_volume,
                net_volume      = net_volume,
                bluemetal_gross_volume = bluemetal_gross,
                bluemetal_net_volume   = bluemetal_net,
                volume_provided = volume_provided,
                volume_required = None,
                tank_base_soakwell_base_max_stormwater_height = None,
                graph           = None
            )
            db.session.add(existing)

        db.session.commit()

        logger.info(
            f"Detention calculation done | "
            f"L={length} W={width} D={depth} | "
            f"vol_provided={volume_provided} | project_id={project_id}"
        )

        return {
            "constraint_type":        constraint_type,
            "tank_length":            length,
            "tank_width":             width,
            "tank_depth":             depth,
            "module_length":          module_length,
            "module_width":           module_width,
            "module_depth":           module_depth,
            "gross_volume":           gross_volume,
            "net_volume":             net_volume,
            "bluemetal_gross_volume": bluemetal_gross,
            "bluemetal_net_volume":   bluemetal_net,
            "total_additional_storage": total_additional,
            "volume_provided":        volume_provided
        }

    except SQLAlchemyError:
        db.session.rollback()
        logger.exception(f"DB error | project_id={project_id}")
        raise Exception("Database error occurred")

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Unexpected error | project_id={project_id}")
        raise Exception(str(e))