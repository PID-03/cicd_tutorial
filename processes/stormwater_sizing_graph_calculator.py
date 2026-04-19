# from extensions import db
# from models.stormwater_output import StormwaterTankCalculation, StormwaterAreaParameters
# from sqlalchemy.exc import SQLAlchemyError
# from models.static_data import PrecastSoakwellSpec, CircularAreaReference, IFDData
# from models.ifd_data import IFDRegion, IFDRegionData
# from models.stormwater_input import StormwaterSizingCalculation
# from models.stormwater_output import AdditionalVolumeOutput
# from models.project import Project
# import math
# import json
# from decimal import Decimal, ROUND_HALF_UP, getcontext
# import logging

# logger = logging.getLogger(__name__)
# getcontext().prec = 28


# def D(value):
#     return Decimal(str(value))


# # ─────────────────────────────────────────────
# # CONSTANTS
# # ─────────────────────────────────────────────
# MODULE_STEP = 1.15   # one AtlanCube module width/length in metres
# MAX_ITER    = 500    # safety cap for infiltration iteration


# # ─────────────────────────────────────────────
# # STANDARD DURATIONS (minutes)
# # ─────────────────────────────────────────────
# DURATIONS = [
#     1, 2, 3, 4, 5, 10, 15, 20,
#     25, 30, 45, 60, 90, 120,
#     180, 270, 360, 540,
#     720, 1080, 1440, 1800,
#     2160, 2880, 4320, 5760,
#     7200, 8640, 10080
# ]


# # ═══════════════════════════════════════════════════════════════
# # CORE GRAPH CALCULATION ENGINE
# # ═══════════════════════════════════════════════════════════════
# def generate_graph_output(
#     aep_percentage,
#     max_storm_duration_min,
#     climate_factor,
#     catchment_area_m2,
#     infiltration_rate_m_per_day,
#     orifice_flow_lps,
#     tank_length_m,
#     tank_width_m,
#     max_infiltration_depth_m,
#     sidewall_enabled,
#     soakwells,
#     region
# ):
#     try:
#         logger.info("Starting stormwater graph generation")
#         logger.info(
#             f"AEP: {aep_percentage}% | Duration: {max_storm_duration_min} min | "
#             f"L={tank_length_m} W={tank_width_m} D={max_infiltration_depth_m}"
#         )

#         # ── Fetch IFD region ─────────────────────────────────────────────────
#         region_obj = (
#             IFDRegion.query
#             .filter(
#                 IFDRegion.id == region,
#                 IFDRegion.is_deleted == False
#             )
#             .first()
#         )

#         if not region_obj:
#             raise ValueError(f"Region '{region}' not found")

#         rows = (
#             IFDRegionData.query
#             .filter(
#                 IFDRegionData.region_id == region_obj.id,
#                 IFDRegionData.aep_percentage == aep_percentage
#             )
#             .order_by(IFDRegionData.duration_minutes.asc())
#             .all()
#         )

#         if not rows:
#             raise ValueError(f"No IFD data found for AEP {aep_percentage}%")

#         logger.info(f"Fetched {len(rows)} IFD rows")

#         intensity_map = {
#             row.duration_minutes: D(row.intensity)
#             for row in rows
#         }

#         # ── Soakwell area ────────────────────────────────────────────────────
#         soakwell_area = D("0")

#         if soakwells:
#             selected_labels = [sw["size"] for sw in soakwells]

#             spec_rows = (
#                 PrecastSoakwellSpec.query
#                 .filter(PrecastSoakwellSpec.model_label.in_(selected_labels))
#                 .all()
#             )

#             if not spec_rows:
#                 raise ValueError("Selected precast soakwell specs not found in DB")

#             soakwell_area_map = {
#                 spec.model_label: D(str(spec.weep_hole_area_m2))
#                 for spec in spec_rows
#             }

#             for sw in soakwells:
#                 label = sw["size"]
#                 qty   = D(sw.get("quantity", 0))

#                 if label not in soakwell_area_map:
#                     raise ValueError(f"Soakwell spec '{label}' not found in DB")

#                 soakwell_area += soakwell_area_map[label] * qty

#             logger.info(f"Total soakwell area: {soakwell_area} m2")

#         # ── Input conversions ────────────────────────────────────────────────
#         climate_factor              = D(climate_factor or 0)
#         catchment_area_m2           = D(catchment_area_m2 or 0)
#         infiltration_rate_m_per_day = D(infiltration_rate_m_per_day or 0)
#         orifice_flow_lps            = D(orifice_flow_lps or 0)
#         tank_length_m               = D(tank_length_m or 0)
#         tank_width_m                = D(tank_width_m or 0)
#         max_infiltration_depth_m    = D(max_infiltration_depth_m or 0)

#         infiltration_rate_m_per_hr = infiltration_rate_m_per_day / D("24")
#         orifice_flow_m3_per_hr     = (orifice_flow_lps / 1000 * 3600)
#         tank_base_area             = tank_length_m * tank_width_m

#         logger.info(f"Tank base area: {tank_base_area} m2")

#         # ── Graph storage ────────────────────────────────────────────────────
#         graph_data = {
#             "minutes":          [],
#             "mm_per_min":       [],
#             "inflow_volume":    [],
#             "drainage":         [],
#             "orifice_discharge":[],
#             "net_volume":       [],
#             "infiltration_area":[],
#             "emptying_hours":   []
#         }

#         net_volume_list       = []
#         infiltration_area_list = []

#         for duration_min in DURATIONS:

#             if duration_min > max_storm_duration_min:
#                 continue

#             if duration_min not in intensity_map:
#                 continue

#             duration    = D(duration_min)
#             duration_hr = duration / D("60")

#             intensity_hr      = intensity_map[duration_min]
#             adjusted_intensity = intensity_hr * (D("1") + climate_factor)

#             inflow_m3 = (
#                 (adjusted_intensity / D("1000"))
#                 * catchment_area_m2
#                 * duration_hr
#             )

#             inflow_l   = (inflow_m3 * D("1000")).quantize(D("1"), ROUND_HALF_UP)
#             mm_per_min = (adjusted_intensity / D("60")).quantize(D("0.001"), ROUND_HALF_UP)

#             water_depth     = (inflow_l / D("1000")) / tank_base_area if tank_base_area > 0 else D("0")
#             effective_depth = min(water_depth, max_infiltration_depth_m)

#             sidewall_area = D("0")
#             if sidewall_enabled:
#                 sidewall_area = (tank_length_m + tank_width_m) * effective_depth

#             total_infiltration_area = (
#                 soakwell_area + tank_base_area + sidewall_area
#             ).quantize(D("0.01"), ROUND_HALF_UP)

#             drainage_m3 = (
#                 infiltration_rate_m_per_hr
#                 * total_infiltration_area
#                 * duration_hr
#             )

#             drainage_l  = min(drainage_m3 * D("1000"), inflow_l)
#             drainage_l  = drainage_l.quantize(D("1"), ROUND_HALF_UP)

#             orifice_m3  = orifice_flow_m3_per_hr * duration_hr
#             orifice_l   = min(orifice_m3 * D("1000"), inflow_l - drainage_l)
#             orifice_l   = orifice_l.quantize(D("1"), ROUND_HALF_UP)

#             net_volume_l = max(inflow_l - drainage_l - orifice_l, D("0"))
#             net_volume_l = net_volume_l.quantize(D("1"), ROUND_HALF_UP)

#             total_outflow_rate = (
#                 infiltration_rate_m_per_hr * total_infiltration_area
#                 + orifice_flow_m3_per_hr
#             )

#             emptying_time_hr = (
#                 (net_volume_l / D("1000")) / total_outflow_rate
#                 if total_outflow_rate > 0 else D("0")
#             ).quantize(D("0.01"), ROUND_HALF_UP)

#             graph_data["minutes"].append(duration_min)
#             graph_data["mm_per_min"].append(float(mm_per_min))
#             graph_data["inflow_volume"].append(float(inflow_l))
#             graph_data["drainage"].append(float(drainage_l))
#             graph_data["orifice_discharge"].append(float(orifice_l))
#             graph_data["net_volume"].append(float(net_volume_l))
#             graph_data["infiltration_area"].append(float(total_infiltration_area))
#             graph_data["emptying_hours"].append(float(emptying_time_hr))

#             net_volume_list.append(float(net_volume_l))
#             infiltration_area_list.append(float(total_infiltration_area))

#         logger.info(f"Processed {len(graph_data['minutes'])} storm durations")

#         max_infiltration_area  = max(infiltration_area_list) if infiltration_area_list else 0
#         max_volume_required_m3 = max(net_volume_list) / 1000 if net_volume_list else 0

#         logger.info(f"Max infiltration area : {max_infiltration_area} m2")
#         logger.info(f"Max volume required   : {max_volume_required_m3} m3")
#         logger.info("Graph generation completed")

#         return {
#             "design": {
#                 "stormwater_height_m":  max_infiltration_area,
#                 "volume_required_m3":   max_volume_required_m3
#             },
#             "graph": graph_data
#         }

#     except Exception:
#         logger.exception("Error during stormwater graph generation")
#         raise


# # ═══════════════════════════════════════════════════════════════
# # HELPER — net volume from raw tank dimensions
# # Mirrors stormwater_sizing_tank_calculator exactly (net == gross)
# # ═══════════════════════════════════════════════════════════════
# def _get_net_volume_for_dims(length, width, depth):
#     """
#     FIX 4: boundary now correctly handles depth == 1.0
#             and guards against ml/mw <= 0.
#     """
#     def _module_depth_steps(d):
#         if d < 1:        return None   # below minimum
#         elif d <= 1.38:  return 1      # ✅ 1.0 → 1 (was broken before)
#         elif d <= 2.16:  return 2
#         elif d <= 2.94:  return 4
#         elif d <= 3.34:  return 6
#         else:            return None   # above maximum

#     ml = math.floor((length - 0.06) / 1.15)
#     mw = math.floor((width  - 0.06) / 1.15)
#     md = _module_depth_steps(depth)

#     # ✅ FIX 4 guard: return 0 if any dimension is invalid
#     if md is None or ml <= 0 or mw <= 0:
#         return 0.0

#     gross = ml * mw * (md / 2)
#     return round(gross, 2)   # net == gross per tank calculator


# # ═══════════════════════════════════════════════════════════════
# # PUBLIC ENTRY POINT — routes to correct scenario
# # ═══════════════════════════════════════════════════════════════
# def run_stormwater_calculation(project_id):
#     """
#     Scenario 1 (Detention):  soil_permeability == 0  → iterate free dimension
#     Scenario 2 (Infiltration): soil_permeability > 0  → iterate free dimension
#     """
#     sizing = StormwaterSizingCalculation.query.filter_by(
#         project_id=project_id
#     ).first()

#     if not sizing:
#         raise ValueError("Stormwater sizing data not found")

#     is_infiltration = (
#         sizing.soil_permeability is not None
#         and float(sizing.soil_permeability) > 0
#     )

#     if is_infiltration:
#         logger.info(f"Scenario 2: Infiltration | project_id={project_id}")
#         return _run_infiltration_iteration(project_id, sizing)
#     else:
#         logger.info(f"Scenario 1: Detention/Retention | project_id={project_id}")
#         return _run_detention_iteration(project_id, sizing)


# # ═══════════════════════════════════════════════════════════════
# # SCENARIO 1 — DETENTION / RETENTION ITERATION
# # ═══════════════════════════════════════════════════════════════
# def _run_detention_iteration(project_id, sizing):
#     """
#     soil_permeability == 0.

#     Mirrors infiltration sizing:
#       1. hold one dimension fixed per constraint_type
#       2. iterate the free dimension one module (1.15 m) at a time
#       3. run graph for trial dims to get volume_required
#       4. compute volume_provided using the same formula as infiltration:
#          total_additional + net_volume
#       5. stop when volume_provided >= volume_required
#     """
#     area = StormwaterAreaParameters.query.filter_by(project_id=project_id).first()
#     project = Project.query.filter_by(id=project_id).first()
#     additional = AdditionalVolumeOutput.query.filter_by(project_id=project_id).first()

#     if not area or not project:
#         raise ValueError("Missing area parameters or project record")

#     constraint_type = sizing.constraint_type
#     depth = float(sizing.tank_depth or 0)
#     total_additional = float(additional.total_additional_storage if additional else 0)

#     if constraint_type == "length":
#         fixed_dim = float(sizing.tank_length or 0)
#     elif constraint_type == "width":
#         fixed_dim = float(sizing.tank_width or 0)
#     else:
#         raise ValueError("constraint_type must be 'length' or 'width'")

#     if not fixed_dim:
#         raise ValueError(
#             f"Fixed dimension ({constraint_type}) is 0 or missing — "
#             "set tank_length or tank_width via PATCH /tank first"
#         )
#     if not depth:
#         raise ValueError("tank_depth must be set before running detention iteration")

#     free_dim = MODULE_STEP

#     for iteration in range(1, MAX_ITER + 1):
#         if constraint_type == "length":
#             trial_length = fixed_dim
#             trial_width = free_dim
#         else:
#             trial_length = free_dim
#             trial_width = fixed_dim

#         logger.info(
#             f"[DETENTION ITER {iteration}] L={trial_length} W={trial_width} D={depth} | "
#             f"project_id={project_id}"
#         )

#         graph_result = generate_graph_output(
#             aep_percentage             = sizing.annual_exceedence_probability,
#             max_storm_duration_min     = sizing.maximum_storm_duration,
#             climate_factor             = sizing.rainfall_intensity_increase_allowance,
#             catchment_area_m2          = area.equivalent_area,
#             infiltration_rate_m_per_day= 0,
#             orifice_flow_lps           = sizing.detention_tank_discharge_allowance,
#             tank_length_m              = trial_length,
#             tank_width_m               = trial_width,
#             max_infiltration_depth_m   = depth,
#             sidewall_enabled           = False,
#             soakwells                  = [],
#             region                     = project.rainfall_location_id
#         )

#         volume_required = graph_result["design"]["volume_required_m3"]
#         net_volume = _get_net_volume_for_dims(trial_length, trial_width, depth)
#         volume_provided = round(total_additional + net_volume, 2)

#         logger.info(
#             f"[DETENTION ITER {iteration}] vol_required={volume_required} | "
#             f"vol_provided={volume_provided}"
#         )

#         if volume_provided >= volume_required:
#             logger.info(
#                 f"DETENTION VOL SUFFICIENT at iteration {iteration} | "
#                 f"free_dim={free_dim} m | project_id={project_id}"
#             )

#             ml = math.floor((trial_length - 0.06) / 1.15)
#             mw = math.floor((trial_width - 0.06) / 1.15)

#             volume_record = StormwaterTankCalculation.query.filter_by(
#                 project_id=project_id
#             ).first()

#             if not volume_record:
#                 volume_record = StormwaterTankCalculation(project_id=project_id)
#                 db.session.add(volume_record)

#             volume_record.tank_length = trial_length
#             volume_record.tank_width = trial_width
#             volume_record.tank_bredth = depth
#             volume_record.module_length = ml
#             volume_record.module_width = mw
#             volume_record.net_volume = net_volume
#             volume_record.gross_volume = net_volume
#             volume_record.volume_required = volume_required
#             volume_record.volume_provided = volume_provided
#             volume_record.graph = graph_result["graph"]
#             volume_record.tank_base_soakwell_base_max_stormwater_height = (
#                 graph_result["design"]["stormwater_height_m"]
#             )

#             db.session.commit()

#             return {
#                 "status": "VOL_SUFFICIENT",
#                 "iterations_run": iteration,
#                 "tank_length": trial_length,
#                 "tank_width": trial_width,
#                 "tank_depth": depth,
#                 "volume_required_m3": volume_required,
#                 "volume_provided_m3": volume_provided,
#                 "free_dimension": "width" if constraint_type == "length" else "length",
#                 "minimum_free_dim_m": free_dim,
#                 "graph": graph_result["graph"]
#             }

#         free_dim = round(free_dim + MODULE_STEP, 4)

#     db.session.rollback()
#     raise ValueError(
#         f"Could not reach VOL_SUFFICIENT within {MAX_ITER} module steps. "
#         f"Check catchment area, discharge allowance, and depth inputs."
#     )


# # ═══════════════════════════════════════════════════════════════
# # SCENARIO 2 — INFILTRATION ITERATION
# # ═══════════════════════════════════════════════════════════════
# def _run_infiltration_iteration(project_id, sizing):
#     """
#     soil_permeability > 0.

#     Breaks the circular reference by iterating the FREE dimension
#     one module (1.15 m) at a time until volume_provided >= volume_required.

#     constraint_type == "length"  →  tank_length is FIXED, iterate WIDTH
#     constraint_type == "width"   →  tank_width  is FIXED, iterate LENGTH

#     FIX 2: fixed_dim now reads from the correct column per constraint_type.
#     FIX 3: width constraint correctly uses sizing.tank_width as fixed_dim.
#     """
#     area       = StormwaterAreaParameters.query.filter_by(project_id=project_id).first()
#     project    = Project.query.filter_by(id=project_id).first()
#     additional = AdditionalVolumeOutput.query.filter_by(project_id=project_id).first()

#     if not area or not project:
#         raise ValueError("Missing area parameters or project record")

#     constraint_type  = sizing.constraint_type
#     depth            = float(sizing.tank_depth or 0)
#     total_additional = float(additional.total_additional_storage if additional else 0)

#     # ── FIX 2 + FIX 3: read fixed_dim from the correct column ───────────────
#     if constraint_type == "length":
#         fixed_dim = float(sizing.tank_length or 0)   # length is fixed → iterate width
#     elif constraint_type == "width":
#         fixed_dim = float(sizing.tank_width or 0)    # width is fixed  → iterate length
#     else:
#         raise ValueError("constraint_type must be 'length' or 'width'")

#     if not fixed_dim:
#         raise ValueError(
#             f"Fixed dimension ({constraint_type}) is 0 or missing — "
#             "set tank_length or tank_width via PATCH /tank first"
#         )
#     if not depth:
#         raise ValueError("tank_depth must be set before running infiltration iteration")

#     free_dim = MODULE_STEP   # start at 1 module = 1.15 m

#     for iteration in range(1, MAX_ITER + 1):

#         if constraint_type == "length":
#             trial_length = fixed_dim
#             trial_width  = free_dim
#         else:
#             trial_length = free_dim
#             trial_width  = fixed_dim

#         logger.info(
#             f"[ITER {iteration}] L={trial_length} W={trial_width} D={depth} | "
#             f"project_id={project_id}"
#         )

#         # ── Step 1: graph → volume_required ──────────────────────────────────
#         graph_result = generate_graph_output(
#             aep_percentage             = sizing.annual_exceedence_probability,
#             max_storm_duration_min     = sizing.maximum_storm_duration,
#             climate_factor             = sizing.rainfall_intensity_increase_allowance,
#             catchment_area_m2          = area.equivalent_area,
#             infiltration_rate_m_per_day= sizing.soil_permeability,
#             orifice_flow_lps           = sizing.detention_tank_discharge_allowance,
#             tank_length_m              = trial_length,
#             tank_width_m               = trial_width,
#             max_infiltration_depth_m   = depth,
#             sidewall_enabled           = sizing.include_water_half_height_peripheral,
#             soakwells                  = sizing.precast_soakwells or [],
#             region                     = project.rainfall_location_id
#         )

#         volume_required = graph_result["design"]["volume_required_m3"]

#         # ── Step 2: calculate volume_provided for trial dims ─────────────────
#         net_volume      = _get_net_volume_for_dims(trial_length, trial_width, depth)
#         volume_provided = round(total_additional + net_volume, 2)

#         logger.info(
#             f"[ITER {iteration}] vol_required={volume_required} | "
#             f"vol_provided={volume_provided}"
#         )

#         # ── Step 3: check sufficient ─────────────────────────────────────────
#         if volume_provided >= volume_required:
#             logger.info(
#                 f"VOL SUFFICIENT at iteration {iteration} | "
#                 f"free_dim={free_dim} m | project_id={project_id}"
#             )

#             ml = math.floor((trial_length - 0.06) / 1.15)
#             mw = math.floor((trial_width  - 0.06) / 1.15)

#             volume_record = StormwaterTankCalculation.query.filter_by(
#                 project_id=project_id
#             ).first()

#             if not volume_record:
#                 volume_record = StormwaterTankCalculation(project_id=project_id)
#                 db.session.add(volume_record)

#             volume_record.tank_length    = trial_length
#             volume_record.tank_width     = trial_width
#             volume_record.tank_bredth    = depth
#             volume_record.module_length  = ml
#             volume_record.module_width   = mw
#             volume_record.net_volume     = net_volume
#             volume_record.gross_volume   = net_volume   # gross == net in this system
#             volume_record.volume_required = volume_required
#             volume_record.volume_provided = volume_provided
#             volume_record.graph           = graph_result["graph"]
#             volume_record.tank_base_soakwell_base_max_stormwater_height = (
#                 graph_result["design"]["stormwater_height_m"]
#             )

#             db.session.commit()

#             return {
#                 "status":            "VOL_SUFFICIENT",
#                 "iterations_run":    iteration,
#                 "tank_length":       trial_length,
#                 "tank_width":        trial_width,
#                 "tank_depth":        depth,
#                 "volume_required_m3": volume_required,
#                 "volume_provided_m3": volume_provided,
#                 "free_dimension":    "width" if constraint_type == "length" else "length",
#                 "minimum_free_dim_m": free_dim,
#                 "graph":             graph_result["graph"]
#             }

#         # ── Step 4: increment by one module ──────────────────────────────────
#         free_dim = round(free_dim + MODULE_STEP, 4)

#     # Exhausted all iterations
#     db.session.rollback()
#     raise ValueError(
#         f"Could not reach VOL_SUFFICIENT within {MAX_ITER} module steps. "
#         f"Check catchment area, soil permeability, and depth inputs."
#     )




from extensions import db
from models.stormwater_output import StormwaterTankCalculation, StormwaterAreaParameters
from sqlalchemy.exc import SQLAlchemyError
from models.static_data import PrecastSoakwellSpec, CircularAreaReference, IFDData
from models.ifd_data import IFDRegion, IFDRegionData
from models.stormwater_input import StormwaterSizingCalculation
from models.stormwater_output import AdditionalVolumeOutput
from models.project import Project
import math
import json
from decimal import Decimal, ROUND_HALF_UP, getcontext
import logging

logger = logging.getLogger(__name__)
getcontext().prec = 28


def D(value):
    return Decimal(str(value))


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
MODULE_STEP = 1.15   # one AtlanCube module width/length in metres
MAX_ITER    = 500    # safety cap for iteration


# ─────────────────────────────────────────────
# STANDARD DURATIONS (minutes)
# ─────────────────────────────────────────────
DURATIONS = [
    1, 2, 3, 4, 5, 10, 15, 20,
    25, 30, 45, 60, 90, 120,
    180, 270, 360, 540,
    720, 1080, 1440, 1800,
    2160, 2880, 4320, 5760,
    7200, 8640, 10080
]


# ═══════════════════════════════════════════════════════════════
# CORE GRAPH CALCULATION ENGINE
# ═══════════════════════════════════════════════════════════════
def generate_graph_output(
    aep_percentage,
    max_storm_duration_min,
    climate_factor,
    catchment_area_m2,
    infiltration_rate_m_per_day,
    orifice_flow_lps,
    tank_length_m,
    tank_width_m,
    max_infiltration_depth_m,
    sidewall_enabled,
    soakwells,
    region
):
    try:
        logger.info("Starting stormwater graph generation")
        logger.info(
            f"AEP: {aep_percentage}% | Duration: {max_storm_duration_min} min | "
            f"L={tank_length_m} W={tank_width_m} D={max_infiltration_depth_m}"
        )

        # ── Fetch IFD region ─────────────────────────────────────────────────
        region_obj = (
            IFDRegion.query
            .filter(
                IFDRegion.id == region,
                IFDRegion.is_deleted == False
            )
            .first()
        )

        if not region_obj:
            raise ValueError(f"Region '{region}' not found")

        rows = (
            IFDRegionData.query
            .filter(
                IFDRegionData.region_id == region_obj.id,
                IFDRegionData.aep_percentage == aep_percentage
            )
            .order_by(IFDRegionData.duration_minutes.asc())
            .all()
        )

        if not rows:
            raise ValueError(f"No IFD data found for AEP {aep_percentage}%")

        logger.info(f"Fetched {len(rows)} IFD rows")

        intensity_map = {
            row.duration_minutes: D(row.intensity)
            for row in rows
        }

        # ── Soakwell area ────────────────────────────────────────────────────
        soakwell_area = D("0")

        if soakwells:
            selected_labels = [sw["size"] for sw in soakwells]

            spec_rows = (
                PrecastSoakwellSpec.query
                .filter(PrecastSoakwellSpec.model_label.in_(selected_labels))
                .all()
            )

            if not spec_rows:
                raise ValueError("Selected precast soakwell specs not found in DB")

            soakwell_area_map = {
                spec.model_label: D(str(spec.weep_hole_area_m2))
                for spec in spec_rows
            }

            for sw in soakwells:
                label = sw["size"]
                qty   = D(sw.get("quantity", 0))

                if label not in soakwell_area_map:
                    raise ValueError(f"Soakwell spec '{label}' not found in DB")

                soakwell_area += soakwell_area_map[label] * qty

            logger.info(f"Total soakwell area: {soakwell_area} m2")

        # ── Input conversions ────────────────────────────────────────────────
        climate_factor              = D(climate_factor or 0)
        catchment_area_m2           = D(catchment_area_m2 or 0)
        infiltration_rate_m_per_day = D(infiltration_rate_m_per_day or 0)
        orifice_flow_lps            = D(orifice_flow_lps or 0)
        tank_length_m               = D(tank_length_m or 0)
        tank_width_m                = D(tank_width_m or 0)
        max_infiltration_depth_m    = D(max_infiltration_depth_m or 0)

        infiltration_rate_m_per_hr = infiltration_rate_m_per_day / D("24")
        orifice_flow_m3_per_hr     = (orifice_flow_lps / 1000 * 3600)
        tank_base_area             = tank_length_m * tank_width_m

        logger.info(f"Tank base area: {tank_base_area} m2")

        # ── Graph storage ────────────────────────────────────────────────────
        graph_data = {
            "minutes":           [],
            "mm_per_min":        [],
            "inflow_volume":     [],
            "drainage":          [],
            "orifice_discharge": [],
            "net_volume":        [],
            "infiltration_area": [],
            "emptying_hours":    []
        }

        net_volume_list        = []
        infiltration_area_list = []

        for duration_min in DURATIONS:

            if duration_min > max_storm_duration_min:
                continue

            if duration_min not in intensity_map:
                continue

            duration    = D(duration_min)
            duration_hr = duration / D("60")

            intensity_hr       = intensity_map[duration_min]
            adjusted_intensity = intensity_hr * (D("1") + climate_factor)

            inflow_m3 = (
                (adjusted_intensity / D("1000"))
                * catchment_area_m2
                * duration_hr
            )

            inflow_l   = (inflow_m3 * D("1000")).quantize(D("1"), ROUND_HALF_UP)
            mm_per_min = (adjusted_intensity / D("60")).quantize(D("0.001"), ROUND_HALF_UP)

            water_depth     = (inflow_l / D("1000")) / tank_base_area if tank_base_area > 0 else D("0")
            effective_depth = min(water_depth, max_infiltration_depth_m)

            sidewall_area = D("0")
            if sidewall_enabled:
                sidewall_area = (tank_length_m + tank_width_m) * effective_depth

            total_infiltration_area = (
                soakwell_area + tank_base_area + sidewall_area
            ).quantize(D("0.01"), ROUND_HALF_UP)

            drainage_m3 = (
                infiltration_rate_m_per_hr
                * total_infiltration_area
                * duration_hr
            )

            drainage_l = min(drainage_m3 * D("1000"), inflow_l)
            drainage_l = drainage_l.quantize(D("1"), ROUND_HALF_UP)

            orifice_m3 = orifice_flow_m3_per_hr * duration_hr
            orifice_l  = min(orifice_m3 * D("1000"), inflow_l - drainage_l)
            orifice_l  = orifice_l.quantize(D("1"), ROUND_HALF_UP)

            net_volume_l = max(inflow_l - drainage_l - orifice_l, D("0"))
            net_volume_l = net_volume_l.quantize(D("1"), ROUND_HALF_UP)

            total_outflow_rate = (
                infiltration_rate_m_per_hr * total_infiltration_area
                + orifice_flow_m3_per_hr
            )

            emptying_time_hr = (
                (net_volume_l / D("1000")) / total_outflow_rate
                if total_outflow_rate > 0 else D("0")
            ).quantize(D("0.01"), ROUND_HALF_UP)

            graph_data["minutes"].append(duration_min)
            graph_data["mm_per_min"].append(float(mm_per_min))
            graph_data["inflow_volume"].append(float(inflow_l))
            graph_data["drainage"].append(float(drainage_l))
            graph_data["orifice_discharge"].append(float(orifice_l))
            graph_data["net_volume"].append(float(net_volume_l))
            graph_data["infiltration_area"].append(float(total_infiltration_area))
            graph_data["emptying_hours"].append(float(emptying_time_hr))

            net_volume_list.append(float(net_volume_l))
            infiltration_area_list.append(float(total_infiltration_area))

        logger.info(f"Processed {len(graph_data['minutes'])} storm durations")

        max_infiltration_area  = max(infiltration_area_list) if infiltration_area_list else 0
        max_volume_required_m3 = max(net_volume_list) / 1000 if net_volume_list else 0

        logger.info(f"Max infiltration area : {max_infiltration_area} m2")
        logger.info(f"Max volume required   : {max_volume_required_m3} m3")
        logger.info("Graph generation completed")

        return {
            "design": {
                "stormwater_height_m": max_infiltration_area,
                "volume_required_m3":  max_volume_required_m3
            },
            "graph": graph_data
        }

    except Exception:
        logger.exception("Error during stormwater graph generation")
        raise


# ═══════════════════════════════════════════════════════════════
# HELPER — AtlanCube module net volume from raw tank dimensions
# net == gross in this system
# ═══════════════════════════════════════════════════════════════
def _get_net_volume_for_dims(length, width, depth):
    """
    Boundary correctly handles depth == 1.0 and guards against ml/mw <= 0.
    """
    def _module_depth_steps(d):
        if d < 1:        return None
        elif d <= 1.38:  return 1
        elif d <= 2.16:  return 2
        elif d <= 2.94:  return 4
        elif d <= 3.34:  return 6
        else:            return None

    ml = math.floor((length - 0.06) / 1.15)
    mw = math.floor((width  - 0.06) / 1.15)
    md = _module_depth_steps(depth)

    if md is None or ml <= 0 or mw <= 0:
        return 0.0

    gross = ml * mw * (md / 2)
    return round(gross, 2)   # net == gross per tank calculator


# ═══════════════════════════════════════════════════════════════
# HELPER — bluemetal base net volume
# Shared by both detention and infiltration iteration paths.
# ═══════════════════════════════════════════════════════════════
def _get_bluemetal_net_volume(length, width, base_height, base_factor):
    """
    gross = length * width * base_height
    net   = gross * (base_factor / 100)

    Returns (gross, net) both rounded to 2 dp.
    Returns (0.0, 0.0) when base_height or base_factor are 0 / None.
    """
    if not base_height or not base_factor:
        return 0.0, 0.0

    gross = length * width * base_height
    net   = gross * (base_factor / 100)
    return round(gross, 2), round(net, 2)


# ═══════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT — routes to correct scenario
# ═══════════════════════════════════════════════════════════════
def run_stormwater_calculation(project_id):
    """
    Scenario 1 (Detention):    soil_permeability == 0  → iterate free dimension
    Scenario 2 (Infiltration): soil_permeability  > 0  → iterate free dimension
    """
    sizing = StormwaterSizingCalculation.query.filter_by(
        project_id=project_id
    ).first()

    if not sizing:
        raise ValueError("Stormwater sizing data not found")

    is_infiltration = (
        sizing.soil_permeability is not None
        and float(sizing.soil_permeability) > 0
    )

    if is_infiltration:
        logger.info(f"Scenario 2: Infiltration | project_id={project_id}")
        return _run_infiltration_iteration(project_id, sizing)
    else:
        logger.info(f"Scenario 1: Detention/Retention | project_id={project_id}")
        return _run_detention_iteration(project_id, sizing)


# ═══════════════════════════════════════════════════════════════
# SCENARIO 1 — DETENTION / RETENTION ITERATION
# ═══════════════════════════════════════════════════════════════
def _run_detention_iteration(project_id, sizing):
    """
    soil_permeability == 0.

    1. Hold one dimension fixed per constraint_type.
    2. Iterate the free dimension one module (1.15 m) at a time.
    3. Run graph for trial dims → volume_required.
    4. volume_provided = total_additional + net_volume + bluemetal_net  ← FIX
    5. Stop when volume_provided >= volume_required.
    """
    area       = StormwaterAreaParameters.query.filter_by(project_id=project_id).first()
    project    = Project.query.filter_by(id=project_id).first()
    additional = AdditionalVolumeOutput.query.filter_by(project_id=project_id).first()

    if not area or not project:
        raise ValueError("Missing area parameters or project record")

    constraint_type  = sizing.constraint_type
    depth            = float(sizing.tank_depth or 0)
    total_additional = float(additional.total_additional_storage if additional else 0)

    # ── Bluemetal parameters (now used in detention too) ─────────────────────
    base_height = float(sizing.bluemetal_base_height or 0)
    base_factor = float(sizing.bluemetal_base_factor or 0)

    if constraint_type == "length":
        fixed_dim = float(sizing.tank_length or 0)
    elif constraint_type == "width":
        fixed_dim = float(sizing.tank_width or 0)
    else:
        raise ValueError("constraint_type must be 'length' or 'width'")

    if not fixed_dim:
        raise ValueError(
            f"Fixed dimension ({constraint_type}) is 0 or missing — "
            "set tank_length or tank_width via PATCH /tank first"
        )
    if not depth:
        raise ValueError("tank_depth must be set before running detention iteration")

    free_dim = MODULE_STEP

    for iteration in range(1, MAX_ITER + 1):
        if constraint_type == "length":
            trial_length = fixed_dim
            trial_width  = free_dim
        else:
            trial_length = free_dim
            trial_width  = fixed_dim

        logger.info(
            f"[DETENTION ITER {iteration}] L={trial_length} W={trial_width} D={depth} | "
            f"project_id={project_id}"
        )

        graph_result = generate_graph_output(
            aep_percentage              = sizing.annual_exceedence_probability,
            max_storm_duration_min      = sizing.maximum_storm_duration,
            climate_factor              = sizing.rainfall_intensity_increase_allowance,
            catchment_area_m2           = area.equivalent_area,
            infiltration_rate_m_per_day = 0,
            orifice_flow_lps            = sizing.detention_tank_discharge_allowance,
            tank_length_m               = trial_length,
            tank_width_m                = trial_width,
            max_infiltration_depth_m    = depth,
            sidewall_enabled            = False,
            soakwells                   = [],
            region                      = project.rainfall_location_id
        )

        volume_required = graph_result["design"]["volume_required_m3"]
        net_volume      = _get_net_volume_for_dims(trial_length, trial_width, depth)

        # ── FIX: include bluemetal base net volume ────────────────────────────
        bluemetal_gross, bluemetal_net = _get_bluemetal_net_volume(
            trial_length, trial_width, base_height, base_factor
        )

        volume_provided = round(total_additional + net_volume + bluemetal_net, 2)

        logger.info(
            f"[DETENTION ITER {iteration}] "
            f"vol_required={volume_required} | net_vol={net_volume} | "
            f"bluemetal_net={bluemetal_net} | vol_provided={volume_provided}"
        )

        if volume_provided >= volume_required:
            logger.info(
                f"DETENTION VOL SUFFICIENT at iteration {iteration} | "
                f"free_dim={free_dim} m | project_id={project_id}"
            )

            ml = math.floor((trial_length - 0.06) / 1.15)
            mw = math.floor((trial_width  - 0.06) / 1.15)

            volume_record = StormwaterTankCalculation.query.filter_by(
                project_id=project_id
            ).first()

            if not volume_record:
                volume_record = StormwaterTankCalculation(project_id=project_id)
                db.session.add(volume_record)

            volume_record.tank_length    = trial_length
            volume_record.tank_width     = trial_width
            volume_record.tank_bredth    = depth
            volume_record.module_length  = ml
            volume_record.module_width   = mw
            volume_record.net_volume     = net_volume
            volume_record.gross_volume   = net_volume
            # ── FIX: persist bluemetal volumes ───────────────────────────────
            volume_record.bluemetal_gross_volume = bluemetal_gross
            volume_record.bluemetal_net_volume   = bluemetal_net
            volume_record.volume_required = volume_required
            volume_record.volume_provided = volume_provided
            volume_record.graph           = graph_result["graph"]
            volume_record.tank_base_soakwell_base_max_stormwater_height = (
                graph_result["design"]["stormwater_height_m"]
            )

            db.session.commit()

            return {
                "status":               "VOL_SUFFICIENT",
                "iterations_run":       iteration,
                "tank_length":          trial_length,
                "tank_width":           trial_width,
                "tank_depth":           depth,
                "volume_required_m3":   volume_required,
                "volume_provided_m3":   volume_provided,
                "net_volume_m3":        net_volume,
                "bluemetal_gross_m3":   bluemetal_gross,
                "bluemetal_net_m3":     bluemetal_net,
                "free_dimension":       "width" if constraint_type == "length" else "length",
                "minimum_free_dim_m":   free_dim,
                "graph":                graph_result["graph"]
            }

        free_dim = round(free_dim + MODULE_STEP, 4)

    db.session.rollback()
    raise ValueError(
        f"Could not reach VOL_SUFFICIENT within {MAX_ITER} module steps. "
        f"Check catchment area, discharge allowance, and depth inputs."
    )


# ═══════════════════════════════════════════════════════════════
# SCENARIO 2 — INFILTRATION ITERATION
# ═══════════════════════════════════════════════════════════════
def _run_infiltration_iteration(project_id, sizing):
    """
    soil_permeability > 0.

    Breaks the circular reference by iterating the FREE dimension
    one module (1.15 m) at a time until volume_provided >= volume_required.

    constraint_type == "length"  →  tank_length is FIXED, iterate WIDTH
    constraint_type == "width"   →  tank_width  is FIXED, iterate LENGTH

    volume_provided = total_additional + net_volume + bluemetal_net  ← FIX
    """
    area       = StormwaterAreaParameters.query.filter_by(project_id=project_id).first()
    project    = Project.query.filter_by(id=project_id).first()
    additional = AdditionalVolumeOutput.query.filter_by(project_id=project_id).first()

    if not area or not project:
        raise ValueError("Missing area parameters or project record")

    constraint_type  = sizing.constraint_type
    depth            = float(sizing.tank_depth or 0)
    total_additional = float(additional.total_additional_storage if additional else 0)

    # ── Bluemetal parameters ──────────────────────────────────────────────────
    base_height = float(sizing.bluemetal_base_height or 0)
    base_factor = float(sizing.bluemetal_base_factor or 0)

    # ── Fixed dimension from correct column per constraint_type ───────────────
    if constraint_type == "length":
        fixed_dim = float(sizing.tank_length or 0)   # length is fixed → iterate width
    elif constraint_type == "width":
        fixed_dim = float(sizing.tank_width or 0)    # width is fixed  → iterate length
    else:
        raise ValueError("constraint_type must be 'length' or 'width'")

    if not fixed_dim:
        raise ValueError(
            f"Fixed dimension ({constraint_type}) is 0 or missing — "
            "set tank_length or tank_width via PATCH /tank first"
        )
    if not depth:
        raise ValueError("tank_depth must be set before running infiltration iteration")

    free_dim = MODULE_STEP   # start at 1 module = 1.15 m

    for iteration in range(1, MAX_ITER + 1):

        if constraint_type == "length":
            trial_length = fixed_dim
            trial_width  = free_dim
        else:
            trial_length = free_dim
            trial_width  = fixed_dim

        logger.info(
            f"[INFILTRATION ITER {iteration}] L={trial_length} W={trial_width} D={depth} | "
            f"project_id={project_id}"
        )

        # ── Step 1: graph → volume_required ──────────────────────────────────
        graph_result = generate_graph_output(
            aep_percentage              = sizing.annual_exceedence_probability,
            max_storm_duration_min      = sizing.maximum_storm_duration,
            climate_factor              = sizing.rainfall_intensity_increase_allowance,
            catchment_area_m2           = area.equivalent_area,
            infiltration_rate_m_per_day = sizing.soil_permeability,
            orifice_flow_lps            = sizing.detention_tank_discharge_allowance,
            tank_length_m               = trial_length,
            tank_width_m                = trial_width,
            max_infiltration_depth_m    = depth,
            sidewall_enabled            = sizing.include_water_half_height_peripheral,
            soakwells                   = sizing.precast_soakwells or [],
            region                      = project.rainfall_location_id
        )

        volume_required = graph_result["design"]["volume_required_m3"]

        # ── Step 2: volume_provided for trial dims ────────────────────────────
        net_volume = _get_net_volume_for_dims(trial_length, trial_width, depth)

        # ── FIX: include bluemetal base net volume ────────────────────────────
        bluemetal_gross, bluemetal_net = _get_bluemetal_net_volume(
            trial_length, trial_width, base_height, base_factor
        )

        volume_provided = round(total_additional + net_volume + bluemetal_net, 2)

        logger.info(
            f"[INFILTRATION ITER {iteration}] "
            f"vol_required={volume_required} | net_vol={net_volume} | "
            f"bluemetal_net={bluemetal_net} | vol_provided={volume_provided}"
        )

        # ── Step 3: check sufficient ─────────────────────────────────────────
        if volume_provided >= volume_required:
            logger.info(
                f"VOL SUFFICIENT at iteration {iteration} | "
                f"free_dim={free_dim} m | project_id={project_id}"
            )

            ml = math.floor((trial_length - 0.06) / 1.15)
            mw = math.floor((trial_width  - 0.06) / 1.15)

            volume_record = StormwaterTankCalculation.query.filter_by(
                project_id=project_id
            ).first()

            if not volume_record:
                volume_record = StormwaterTankCalculation(project_id=project_id)
                db.session.add(volume_record)

            volume_record.tank_length    = trial_length
            volume_record.tank_width     = trial_width
            volume_record.tank_bredth    = depth
            volume_record.module_length  = ml
            volume_record.module_width   = mw
            volume_record.net_volume     = net_volume
            volume_record.gross_volume   = net_volume   # gross == net in this system
            # ── FIX: persist bluemetal volumes ───────────────────────────────
            volume_record.bluemetal_gross_volume = bluemetal_gross
            volume_record.bluemetal_net_volume   = bluemetal_net
            volume_record.volume_required = volume_required
            volume_record.volume_provided = volume_provided
            volume_record.graph           = graph_result["graph"]
            volume_record.tank_base_soakwell_base_max_stormwater_height = (
                graph_result["design"]["stormwater_height_m"]
            )

            db.session.commit()

            return {
                "status":             "VOL_SUFFICIENT",
                "iterations_run":     iteration,
                "tank_length":        trial_length,
                "tank_width":         trial_width,
                "tank_depth":         depth,
                "volume_required_m3": volume_required,
                "volume_provided_m3": volume_provided,
                "net_volume_m3":      net_volume,
                "bluemetal_gross_m3": bluemetal_gross,
                "bluemetal_net_m3":   bluemetal_net,
                "free_dimension":     "width" if constraint_type == "length" else "length",
                "minimum_free_dim_m": free_dim,
                "graph":              graph_result["graph"]
            }

        # ── Step 4: increment by one module ──────────────────────────────────
        free_dim = round(free_dim + MODULE_STEP, 4)

    # Exhausted all iterations
    db.session.rollback()
    raise ValueError(
        f"Could not reach VOL_SUFFICIENT within {MAX_ITER} module steps. "
        f"Check catchment area, soil permeability, and depth inputs."
    )