"""
volume_required_calculator.py

Returns the best available volume-required value for a project.

There are two fundamentally different cases:

1. Detention / Retention (soil_permeability == 0)
   volume_required is independent of tank infiltration area, so it can be
   calculated directly from the graph inputs coming from the first screens.

2. Infiltration (soil_permeability > 0)
   volume_required depends on tank dimensions because infiltration area changes
   with length / width / depth. That means there is no single pre-tank "final"
   value. The best we can return is one of:
   - the converged value written by PATCH /tank, if it is still fresh
   - a current-dimension estimate, if tank dimensions are available
   - unavailable, if there are not enough tank dimensions yet
"""

from models.project import Project
from models.stormwater_input import StormwaterSizingCalculation
from models.stormwater_output import StormwaterAreaParameters, StormwaterTankCalculation
from processes.stormwater_sizing_graph_calculator import MODULE_STEP, generate_graph_output
import logging

logger = logging.getLogger(__name__)


def _is_infiltration(sizing) -> bool:
    return (
        sizing.soil_permeability is not None
        and float(sizing.soil_permeability) > 0
    )


def _to_float(value):
    return float(value) if value is not None else None


def _resolve_dims(tank, sizing):
    """
    Resolve the most current tank dimensions we have in DB.

    Preference order:
    1. StormwaterTankCalculation output record
    2. Tank inputs stored on StormwaterSizingCalculation
    """
    length = _to_float((tank.tank_length if tank else None) or sizing.tank_length)
    width = _to_float((tank.tank_width if tank else None) or sizing.tank_width)
    depth = _to_float((tank.tank_bredth if tank else None) or sizing.tank_depth)
    return length, width, depth


def _resolve_starter_dims(sizing):
    """
    Build a minimum trial tank from the tank-input screen fields when the free
    dimension has not been solved yet.

    constraint_type == "length": user fixes length, width starts at 1 module
    constraint_type == "width":  user fixes width,  length starts at 1 module
    """
    constraint_type = sizing.constraint_type
    depth = _to_float(sizing.tank_depth)

    if constraint_type == "length":
        fixed_length = _to_float(sizing.tank_length)
        if fixed_length and depth:
            return fixed_length, MODULE_STEP, depth

    if constraint_type == "width":
        fixed_width = _to_float(sizing.tank_width)
        if fixed_width and depth:
            return MODULE_STEP, fixed_width, depth

    return None, None, depth


def _run_graph_for_dims(project, sizing, area, tank_length, tank_width, tank_depth):
    infiltration = _is_infiltration(sizing)

    return generate_graph_output(
        aep_percentage=sizing.annual_exceedence_probability,
        max_storm_duration_min=sizing.maximum_storm_duration,
        climate_factor=sizing.rainfall_intensity_increase_allowance,
        catchment_area_m2=area.equivalent_area,
        infiltration_rate_m_per_day=sizing.soil_permeability if infiltration else 0,
        orifice_flow_lps=sizing.detention_tank_discharge_allowance,
        tank_length_m=tank_length,
        tank_width_m=tank_width,
        max_infiltration_depth_m=tank_depth,
        sidewall_enabled=bool(sizing.include_water_half_height_peripheral) if infiltration else False,
        soakwells=sizing.precast_soakwells or [] if infiltration else [],
        region=project.rainfall_location_id,
    )


def _tank_result_is_fresh(tank, sizing):
    """
    A stored converged value is only safe to reuse if the tank output is at
    least as recent as the latest sizing/catchment update.
    """
    if not tank or tank.volume_required is None:
        return False

    if tank.updated_at is None or sizing.updated_at is None:
        return True

    return tank.updated_at >= sizing.updated_at


def calculate_volume_required(project_id) -> dict:
    """
    Returns the best available volume-required payload for the project.

    Return shape:
        {
            "volume_required_m3": float | None,
            "scenario": "detention" | "infiltration",
            "source": str,
            "is_final": bool,
            "is_estimate": bool,
            "tank_length": float | None,
            "tank_width": float | None,
            "tank_depth": float | None,
            "message": str | None,
        }
    """
    sizing = StormwaterSizingCalculation.query.filter_by(project_id=project_id).first()
    area = StormwaterAreaParameters.query.filter_by(project_id=project_id).first()
    project = Project.query.filter_by(id=project_id).first()
    tank = StormwaterTankCalculation.query.filter_by(project_id=project_id).first()

    if not sizing:
        raise ValueError("Stormwater sizing input not found")
    if not area:
        raise ValueError("Area parameters not found — complete the input step first")
    if not project:
        raise ValueError("Project not found")

    infiltration = _is_infiltration(sizing)
    scenario = "infiltration" if infiltration else "detention"

    logger.info(
        f"calculate_volume_required | scenario={scenario} | project_id={project_id}"
    )

    # Detention is easy: the graph result is stable and does not depend on tank
    # infiltration area, so we can calculate it even before the tank step.
    if not infiltration:
        tank_length, tank_width, tank_depth = _resolve_dims(tank, sizing)

        # Zero dimensions are acceptable for detention because infiltration is
        # forced to zero. volume_required depends on inflow and orifice only.
        graph_result = _run_graph_for_dims(
            project=project,
            sizing=sizing,
            area=area,
            tank_length=tank_length or 0,
            tank_width=tank_width or 0,
            tank_depth=tank_depth or 0,
        )

        volume_required = graph_result["design"]["volume_required_m3"]

        logger.info(
            f"Detention volume_required={volume_required} m3 | project_id={project_id}"
        )

        return {
            "volume_required_m3": volume_required,
            "scenario": scenario,
            "source": "graph_calculated",
            "is_final": True,
            "is_estimate": False,
            "tank_length": tank_length,
            "tank_width": tank_width,
            "tank_depth": tank_depth,
            "message": None,
        }

    # Infiltration has a circular dependency with tank dimensions.
    # Use the converged stored result if it is fresh for the current inputs.
    if _tank_result_is_fresh(tank, sizing):
        volume_required = float(tank.volume_required)

        logger.info(
            f"Infiltration fresh converged volume_required={volume_required} m3 | "
            f"project_id={project_id}"
        )

        return {
            "volume_required_m3": volume_required,
            "scenario": scenario,
            "source": "converged_tank_result",
            "is_final": True,
            "is_estimate": False,
            "tank_length": _to_float(tank.tank_length),
            "tank_width": _to_float(tank.tank_width),
            "tank_depth": _to_float(tank.tank_bredth),
            "message": None,
        }

    # If the stored converged result is stale or missing, we can still return a
    # current-dimension estimate when enough tank dimensions exist.
    tank_length, tank_width, tank_depth = _resolve_dims(tank, sizing)

    if tank_length and tank_width and tank_depth:
        graph_result = _run_graph_for_dims(
            project=project,
            sizing=sizing,
            area=area,
            tank_length=tank_length,
            tank_width=tank_width,
            tank_depth=tank_depth,
        )
        volume_required = graph_result["design"]["volume_required_m3"]

        logger.info(
            f"Infiltration estimate from current dims | "
            f"L={tank_length} W={tank_width} D={tank_depth} | "
            f"volume_required={volume_required} m3 | project_id={project_id}"
        )

        return {
            "volume_required_m3": volume_required,
            "scenario": scenario,
            "source": "current_dimension_estimate",
            "is_final": False,
            "is_estimate": True,
            "tank_length": tank_length,
            "tank_width": tank_width,
            "tank_depth": tank_depth,
            "message": (
                "This is an estimate using the current tank dimensions. "
                "The final infiltration volume required is confirmed when the tank "
                "calculator converges."
            ),
        }

    # If we only know the fixed dimension + depth, return a starter estimate
    # using one module for the free dimension. This is useful for the tank
    # screen before convergence has run, but it is still only an estimate.
    starter_length, starter_width, starter_depth = _resolve_starter_dims(sizing)

    if starter_length and starter_width and starter_depth:
        graph_result = _run_graph_for_dims(
            project=project,
            sizing=sizing,
            area=area,
            tank_length=starter_length,
            tank_width=starter_width,
            tank_depth=starter_depth,
        )
        volume_required = graph_result["design"]["volume_required_m3"]

        logger.info(
            f"Infiltration starter estimate | "
            f"L={starter_length} W={starter_width} D={starter_depth} | "
            f"volume_required={volume_required} m3 | project_id={project_id}"
        )

        return {
            "volume_required_m3": volume_required,
            "scenario": scenario,
            "source": "starter_dimension_estimate",
            "is_final": False,
            "is_estimate": True,
            "tank_length": starter_length,
            "tank_width": starter_width,
            "tank_depth": starter_depth,
            "message": (
                "This is a starter estimate for infiltration using the fixed tank "
                "dimension and one module for the free dimension. The final value "
                "changes as tank dimensions change."
            ),
        }

    return {
        "volume_required_m3": None,
        "scenario": scenario,
        "source": "unavailable",
        "is_final": False,
        "is_estimate": False,
        "tank_length": tank_length,
        "tank_width": tank_width,
        "tank_depth": tank_depth,
        "message": (
            "Infiltration volume required cannot be determined yet because tank "
            "dimensions are not available. Provide tank depth and the constrained "
            "dimension, or run the tank calculator."
        ),
    }
