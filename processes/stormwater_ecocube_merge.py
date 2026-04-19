import math
import logging
from extensions import db
from models.ecocube import EcocubeCostCalculation, EcocubeOutput, EcocubeGeometryOutput, EcocubeData
from models.stormwater_output import StormwaterTankCalculation
from models.stormwater_input import StormwaterSizingCalculation
from models.project import Project

logger = logging.getLogger(__name__)

mod_w     = 1.15
mod_l     = 1.15
mod_h     = 0.78
cube_cap  = 1.00
sp_w      = 25
sb_w      = 1.00
geo_ovlp  = 0.25
liner_wst = 0.10


def to_2dp(val):
    return float(f"{val:.2f}")


# ---------------- COMMON CALCULATIONS ----------------
def common_calculations(CW, CL, L_in_system, metres_wide, metres_long):
    total_cubes  = CW * CL * L_in_system
    tank_height  = L_in_system * mod_h
    width_length = metres_wide + metres_long
    area         = metres_wide * metres_long
    return total_cubes, tank_height, width_length, area


# ---------------- GEOMETRY ----------------
def calculate_geometry(CW, CL):
    metres_wide      = (CW * mod_w) + (sp_w / 500)
    metres_long      = (CL * mod_l) + (sp_w / 500)
    System_footprint = metres_wide * metres_long
    return metres_wide, metres_long, System_footprint


# ---------------- EXCAVATION ----------------
def calculate_excavation(plan_area, D_inv):
    return plan_area * (D_inv / 1000)


# ---------------- BACKFILL ----------------
def calculate_backfill(metres_wide, metres_long, tank_height, sb_w, D_inv):
    plan_area        = (metres_wide + (sb_w * 2)) * (metres_long + (sb_w * 2))
    tank_volume      = metres_wide * metres_long * tank_height
    Initial_Backfill = (plan_area * (tank_height + 0.1)) - tank_volume
    Final_Backfill   = plan_area * max(0, (D_inv / 1000) - (tank_height + 0.1))
    return Initial_Backfill, Final_Backfill


# ---------------- COMPONENTS ----------------
def calculate_components(CW, CL, L_in_system, inlets, outlets):
    no_of_half_cubes   = CW * CL * L_in_system * 2
    no_of_side_plates  = ((CW + CL) * L_in_system * 2) - (inlets + outlets)
    no_of_double_clips = (2 * CL * CW - (CL + CW)) * (L_in_system - 1)
    no_of_single_clips = (2 * CL * CW - (CL + CW)) * 2
    return no_of_half_cubes, no_of_side_plates, no_of_double_clips, no_of_single_clips


# ---------------- GEOTEXTILE ----------------
def calculate_geotextile(width_length, tank_height, area):
    return ((width_length * tank_height * 2) + (area * 2)) * (1 + geo_ovlp)


# ---------------- LINER ----------------
def calculate_liner(liner, width_length, tank_height, area):
    if liner:
        return ((width_length * tank_height * 2) + (area) * (1 + liner_wst) * 2)
    return 0


# =====================================================
# PURE MATH ENGINE
# =====================================================
def ecocube_material_calculation(
    depth_to_invert,
    layers_in_system,
    target_storage_volume,
    constraining_factor,
    constraining_dimension,
    include_liner,
    number_of_inlets,
    number_of_outlets
):
    D_inv       = float(depth_to_invert or 0)
    L_in_system = int(layers_in_system or 0)
    V_target    = float(target_storage_volume or 0)
    constraint  = constraining_factor
    C_dim       = float(constraining_dimension or 0)
    liner       = include_liner
    inlets      = int(number_of_inlets or 0)
    outlets     = int(number_of_outlets or 0)

    if constraint == "Width":
        CW = math.floor(C_dim / mod_w)
        CL = math.ceil(V_target / (CW * L_in_system))
    else:
        CL = math.floor(C_dim / mod_l)
        CW = math.ceil(V_target / (CL * L_in_system))

    metres_wide, metres_long, System_footprint = calculate_geometry(CW, CL)

    total_cubes, tank_height, width_length, area = common_calculations(
        CW, CL, L_in_system, metres_wide, metres_long
    )

    Tank_Storage = total_cubes * cube_cap
    plan_area    = (metres_wide + (sb_w * 2)) * (metres_long + (sb_w * 2))

    Excavation = calculate_excavation(plan_area, D_inv)
    Initial_Backfill, Final_Backfill = calculate_backfill(
        metres_wide, metres_long, tank_height, sb_w, D_inv
    )
    no_of_half_cubes, no_of_side_plates, no_of_double_clips, no_of_single_clips = \
        calculate_components(CW, CL, L_in_system, inlets, outlets)

    no_of_non_woven_geotextile = calculate_geotextile(width_length, tank_height, area)
    liner_req                  = calculate_liner(liner, width_length, tank_height, area)

    return {
        "Metres-Wide":                to_2dp(metres_wide),
        "Metres-Long":                to_2dp(metres_long),
        "cubes_wide":                 CW,
        "cubes_long":                 CL,
        "footprint":                  to_2dp(System_footprint),
        "tank_storage":               to_2dp(Tank_Storage),
        "excavation_volume":          to_2dp(Excavation),
        "initial_backfill":           to_2dp(Initial_Backfill),
        "final_backfill":             to_2dp(Final_Backfill),
        "no_of_half_cubes":           int(no_of_half_cubes),
        "no_of_side_plates":          int(no_of_side_plates),
        "no_of_double_clips":         int(no_of_double_clips),
        "no_of_single_clips":         int(no_of_single_clips),
        "no_of_non_woven_geotextile": to_2dp(no_of_non_woven_geotextile),
        "liner_required":             to_2dp(liner_req)
    }


# =====================================================
# FETCH INPUTS FROM MULTIPLE TABLES BY project_id
# =====================================================
def fetch_ecocube_inputs(project_id):
    """
    Fetches all inputs needed for ecocube calculation from source models:

    Model                       Column                    → Passed as
    ──────────────────────────────────────────────────────────────────────
    EcocubeCostCalculation    → available_depth_to_invert → depth_to_invert
    EcocubeCostCalculation    → layers_in_system          → layers_in_system
    EcocubeCostCalculation    → max_layers_possible       → max_layers_possible
    EcocubeCostCalculation    → number_of_inlets          → number_of_inlets
    EcocubeCostCalculation    → number_of_outlets         → number_of_outlets
    Project                   → calculator_version        → include_liner
    StormwaterTankCalculation → volume_required           → target_storage_volume
    StormwaterSizingCalculation → constraint_type         → constraining_factor
    StormwaterSizingCalculation → constraint_value        → constraining_dimension
    """

    logger.info(f"Fetching ecocube inputs | project_id={project_id}")

    # ── 1. Project ────────────────────────────────────────────────────────────
    project = Project.query.filter_by(
        id=project_id,
        del_flg=False
    ).first()

    if not project:
        logger.warning(f"Project not found | project_id={project_id}")
        return None, "Project not found"

    # ── 2. EcocubeCostCalculation ─────────────────────────────────────────────
    ecocube = EcocubeCostCalculation.query.filter_by(
        project_id=project_id
    ).first()

    if not ecocube:
        logger.warning(f"EcocubeCostCalculation not found | project_id={project_id}")
        return None, "Ecocube input record not found — please save ecocube fields first"

    # ── 3. StormwaterTankCalculation ──────────────────────────────────────────
    tank = StormwaterTankCalculation.query.filter_by(
        project_id=project_id
    ).first()

    if not tank:
        logger.warning(f"StormwaterTankCalculation not found | project_id={project_id}")
        return None, "Stormwater tank output not found — run stormwater calculation first"

    # ── 4. StormwaterSizingCalculation ────────────────────────────────────────
    constraint = StormwaterSizingCalculation.query.filter_by(
        project_id=project_id
    ).first()

    if not constraint:
        logger.warning(f"StormwaterSizingCalculation not found | project_id={project_id}")
        return None, "Stormwater sizing input not found — please save sizing fields first"

    # ── 5. Validate required fields ───────────────────────────────────────────
    missing = []

    if ecocube.available_depth_to_invert is None:
        missing.append("available_depth_to_invert")
    if ecocube.layers_in_system is None:
        missing.append("layers_in_system")
    if tank.volume_required is None:
        missing.append("volume_required (StormwaterTankCalculation)")
    if constraint.constraint_type is None:
        missing.append("constraint_type (StormwaterSizingCalculation)")
    if constraint.constraint_value is None:
        missing.append("constraint_value (StormwaterSizingCalculation)")
    if project.calculator_version is None:
        missing.append("calculator_version (Project)")

    if missing:
        logger.warning(f"Missing required fields: {missing} | project_id={project_id}")
        return None, f"Missing required fields: {', '.join(missing)}"

    # ── 6. Assemble inputs — mapped to match Code 2 parameter names exactly ──
    inputs = {
        "available_depth_to_invert": ecocube.available_depth_to_invert,   # → depth_to_invert
        "max_layers_possible":       ecocube.max_layers_possible,
        "layers_in_system":          ecocube.layers_in_system,             # → layers_in_system
        "number_of_inlets":          ecocube.number_of_inlets  or 0,       # → number_of_inlets
        "number_of_outlets":         ecocube.number_of_outlets or 0,       # → number_of_outlets
        "include_liner":             project.calculator_version,           # → include_liner
        "target_storage_volume":     tank.volume_required,                 # → target_storage_volume
        "constraining_factor":       constraint.constraint_type,           # → constraining_factor
        "constraining_dimension":    constraint.constraint_value,          # → constraining_dimension
    }

    logger.info(f"Ecocube inputs fetched successfully | project_id={project_id} | inputs={inputs}")
    return inputs, None


# =====================================================
# MAIN ENTRY POINT
# =====================================================
def create_or_update_ecocube_output(project_id):
    """
    Called after PATCH /tank with project_id.
    Fetches inputs from DB, runs calculations, saves outputs.
    Silently skips if ecocube record doesn't exist yet.
    """

    logger.info(f"Ecocube calculation started | project_id={project_id}")

    # ── 1. Fetch all inputs from their source models ──────────────────────────
    inputs, error = fetch_ecocube_inputs(project_id)

    if error:
        logger.warning(f"Ecocube calculation skipped | reason={error} | project_id={project_id}")
        return False, error

    # ── 2. Run material calculation ───────────────────────────────────────────
    try:
        material_result = ecocube_material_calculation(
            depth_to_invert        = inputs["available_depth_to_invert"],
            layers_in_system       = inputs["layers_in_system"],
            target_storage_volume  = inputs["target_storage_volume"],
            constraining_factor    = inputs["constraining_factor"],
            constraining_dimension = inputs["constraining_dimension"],
            include_liner          = inputs["include_liner"],
            number_of_inlets       = inputs["number_of_inlets"],
            number_of_outlets      = inputs["number_of_outlets"],
        )
    except Exception as e:
        logger.exception(f"Ecocube material calculation failed | project_id={project_id}")
        return False, f"Material calculation error: {str(e)}"

    # ── 3. Save EcocubeOutput ─────────────────────────────────────────────────
    try:
        material_output = EcocubeOutput.query.filter_by(
            project_id=project_id
        ).first()

        if not material_output:
            material_output = EcocubeOutput(project_id=project_id)
            db.session.add(material_output)
            logger.info(f"Creating new EcocubeOutput | project_id={project_id}")
        else:
            logger.info(f"Updating existing EcocubeOutput | project_id={project_id}")

        material_output.metres_wide               = material_result["Metres-Wide"]
        material_output.metres_long               = material_result["Metres-Long"]
        material_output.cubes_wide                = material_result["cubes_wide"]
        material_output.cubes_long                = material_result["cubes_long"]
        material_output.system_footprint          = material_result["footprint"]
        material_output.tank_storage              = material_result["tank_storage"]
        material_output.excavation_volume         = material_result["excavation_volume"]
        material_output.initial_backfill_required = material_result["initial_backfill"]
        material_output.final_backfill_required   = material_result["final_backfill"]
        material_output.half_cubes                = material_result["no_of_half_cubes"]
        material_output.side_plates               = material_result["no_of_side_plates"]
        material_output.double_clips              = material_result["no_of_double_clips"]
        material_output.single_clips              = material_result["no_of_single_clips"]
        material_output.non_woven_geotextile      = material_result["no_of_non_woven_geotextile"]
        material_output.liner_required            = material_result["liner_required"]

        db.session.flush()

    except Exception as e:
        logger.exception(f"Failed to save EcocubeOutput | project_id={project_id}")
        return False, f"Failed to save material output: {str(e)}"

    # ── 4. Run and save geometry calculation ──────────────────────────────────
    geometry_success, geometry_error = ecocube_geometry_calculation(
        project_id,
        inputs,
        material_output
    )

    if not geometry_success:
        logger.error(f"Geometry calculation failed | project_id={project_id} | error={geometry_error}")
        return False, geometry_error

    db.session.flush()
    logger.info(f"Ecocube calculation completed successfully | project_id={project_id}")
    return True, "Calculation completed"


# =====================================================
# GEOMETRY CALCULATION
# =====================================================
def ecocube_geometry_calculation(project_id, inputs, material_output):
    try:
        geometry = EcocubeGeometryOutput.query.filter_by(
            project_id=project_id
        ).first()

        if not geometry:
            geometry = EcocubeGeometryOutput(project_id=project_id)
            db.session.add(geometry)
            logger.info(f"Creating new EcocubeGeometryOutput | project_id={project_id}")
        else:
            logger.info(f"Updating existing EcocubeGeometryOutput | project_id={project_id}")

        # ── Calculations — identical to Code 2 ───────────────────────────────
        layers_in_system          = int(inputs["layers_in_system"] or 0)
        available_depth_to_invert = float(inputs["available_depth_to_invert"] or 0)

        double_stack_mm           = round(layers_in_system * mod_h * 1000, 0)
        finished_surface_level_mm = round(available_depth_to_invert, 0)
        outlet_invert_level_mm    = finished_surface_level_mm
        length_mm                 = round(material_output.metres_long * 1000, 0)
        breadth_mm                = round(material_output.metres_wide * 1000, 0)
        height_mm                 = finished_surface_level_mm
        cover_depth_mm            = finished_surface_level_mm - double_stack_mm

        logger.info(
            f"Geometry values | double_stack={double_stack_mm}mm "
            f"cover_depth={cover_depth_mm}mm | project_id={project_id}"
        )

        # ── Assign ────────────────────────────────────────────────────────────
        geometry.finished_surface_level = finished_surface_level_mm
        geometry.double_stack           = double_stack_mm
        geometry.outlet_invert_level    = outlet_invert_level_mm
        geometry.length_mm              = length_mm
        geometry.breadth_mm             = breadth_mm
        geometry.height_mm              = height_mm
        geometry.minimum_cover_depth    = 100.0
        geometry.cover_depth            = cover_depth_mm

        db.session.flush()
        return True, None

    except Exception as e:
        logger.exception(f"Geometry calculation exception | project_id={project_id}")
        return False, str(e)