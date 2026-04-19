import math
from extensions import db
from models.ecocube import EcocubeCostCalculation, EcocubeOutput ,EcocubeGeometryOutput
from decimal import Decimal, ROUND_HALF_UP
from models.ecocube import EcocubeData
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)
@lru_cache(maxsize=1)
def get_ecocube_constants():
    data = EcocubeData.query.first()

    if not data:
        raise ValueError("Ecocube data not configured")

    return {
        "mod_w": data.module_width,
        "mod_l": data.module_length,
        "mod_h": data.module_height,
        "cube_cap": data.cube_water_capacity,
        "sp_w": data.side_plate_width,
        "sb_w": data.side_backfill_width,
        "geo_ovlp": data.geotextile_overlap_wastage,
        "liner_wst": data.liner_wastage
    }
def to_2dp(val):
    return float(f"{val:.2f}")

# ---------------- COMMON CALCULATIONS ----------------
def common_calculations(CW, CL, L_in_system, metres_wide, metres_long,mod_h):
    total_cubes  = CW*CL*L_in_system
    tank_height  = L_in_system*mod_h
    width_length = metres_wide+metres_long
    area         = metres_wide*metres_long

    return total_cubes, tank_height, width_length, area


# ---------------- GEOMETRY ----------------

def calculate_geometry(CW, CL, mod_w, mod_l, sp_w):
    metres_wide = (CW * mod_w) + (sp_w / 500)
    metres_long = (CL * mod_l) + (sp_w / 500)
    System_footprint = metres_wide * metres_long
    return metres_wide, metres_long, System_footprint
# ---------------- EXCAVATION ----------------
def calculate_excavation(plan_area, D_inv):
    return plan_area*(D_inv/1000)


# ---------------- BACKFILL ----------------
def calculate_backfill(metres_wide,metres_long,tank_height,sb_w,D_inv):

    # ---- PLAN AREA WITH SIDE BACKFILL ----
    plan_area = (metres_wide + (sb_w * 2)) * (metres_long + (sb_w * 2))

    # ---- TANK GEOMETRIC VOLUME ----
    tank_volume = (metres_wide *metres_long *tank_height)

    # ---- INITIAL BACKFILL ----
    Initial_Backfill = (plan_area * (tank_height + 0.1)) - tank_volume

    # ---- FINAL BACKFILL ----
    # Final_Backfill = (plan_area *((D_inv/1000) - (tank_height + 0.1)))
    Final_Backfill = plan_area * max(0, (D_inv/1000) - (tank_height + 0.1))

    return Initial_Backfill, Final_Backfill


# ---------------- COMPONENTS ----------------
def calculate_components(CW, CL, L_in_system, inlets, outlets):
    no_of_half_cubes   = CW*CL*L_in_system*2
    no_of_side_plates  = ((CW+CL)*L_in_system*2)-inlets-outlets
    print("no of side plates",no_of_side_plates)
    no_of_double_clips = (2*CL*CW-(CL+CW))*(L_in_system-1)
    no_of_single_clips = (2*CL*CW-(CL+CW))*2
    return no_of_half_cubes, no_of_side_plates, no_of_double_clips, no_of_single_clips


# ---------------- GEOTEXTILE ----------------
def calculate_geotextile(width_length, tank_height, area, geo_ovlp):
    return ((width_length*tank_height*2)+(area*2))*(1+geo_ovlp)


# ---------------- LINER ----------------
def calculate_liner(liner, width_length, tank_height, area, liner_wst):
    # if liner:
    if liner == "yes":
        return ((width_length*tank_height*2)+(area)*(1+liner_wst)*2)
    return 0




# =====================================================
# PURE MATH ENGINE  (NO DB / NO PROJECT / NO REQUEST)
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
        # Load DB values
    constants = get_ecocube_constants()

    mod_w      = constants["mod_w"]
    mod_l      = constants["mod_l"]
    mod_h      = constants["mod_h"]
    cube_cap   = constants["cube_cap"]
    sp_w       = constants["sp_w"]
    sb_w       = constants["sb_w"]
    geo_ovlp   = constants["geo_ovlp"]
    liner_wst  = constants["liner_wst"]

    D_inv       = float(depth_to_invert or 0)
    L_in_system = int(layers_in_system or 0)
    V_target    = float(target_storage_volume or 0)
    constraint  = constraining_factor
    C_dim       = float(constraining_dimension or 0)
    liner       = include_liner
    inlets      = int(number_of_inlets or 0)
    outlets     = int(number_of_outlets or 0)

    # if constraint == "Length":
    if constraint == "width":
        CW = math.floor(C_dim/mod_w)
        CL = math.ceil(V_target/(CW*L_in_system))
    else:
        CL = math.floor(C_dim/mod_l)
        CW = math.ceil(V_target/(CL*L_in_system))

    # metres_wide, metres_long, System_footprint = calculate_geometry(CW, CL)
    metres_wide, metres_long, System_footprint = calculate_geometry(CW,CL,mod_w,mod_l,sp_w)

    total_cubes, tank_height, width_length, area = common_calculations(
        CW, CL, L_in_system, metres_wide, metres_long,mod_h
    )

    Tank_Storage = total_cubes*cube_cap
    plan_area    = (metres_wide + (sb_w*2)) * (metres_long + (sb_w*2))

    Excavation = calculate_excavation(plan_area, D_inv)
    Initial_Backfill, Final_Backfill = calculate_backfill(metres_wide,metres_long,tank_height,sb_w,D_inv)
    no_of_half_cubes, no_of_side_plates, no_of_double_clips, no_of_single_clips = \
    calculate_components(CW, CL, L_in_system, inlets, outlets)

    no_of_non_woven_geotextile = calculate_geotextile(width_length, tank_height, area,geo_ovlp)
    liner_req = calculate_liner(liner, width_length, tank_height, area,liner_wst)


    # return {
    #     "Metres-Wide": metres_wide,
    #     "Metres-Long": metres_long,
    #     "cubes_wide": CW,
    #     "cubes_long": CL,
    #     "footprint": System_footprint,
    #     "tank_storage": Tank_Storage,
    #     "excavation_volume": Excavation,
    #     "initial_backfill": Initial_Backfill,
    #     "final_backfill": Final_Backfill,
    #     "no_of_half_cubes": no_of_half_cubes,
    #     "no_of_side_plates": no_of_side_plates,
    #     "no_of_double_clips": no_of_double_clips,
    #     "no_of_single_clips": no_of_single_clips,
    #     "no_of_non_woven_geotextile": no_of_non_woven_geotextile,
    #     "liner_required": liner_req
    # }
    return {
    "Metres-Wide": to_2dp(metres_wide),
    "Metres-Long": to_2dp(metres_long),
    "cubes_wide": CW,
    "cubes_long": CL,
    "footprint": to_2dp(System_footprint),
    "tank_storage": to_2dp(Tank_Storage),
    "excavation_volume": to_2dp(Excavation),
    "initial_backfill": to_2dp(Initial_Backfill),
    "final_backfill": to_2dp(Final_Backfill),
    "no_of_half_cubes": int(no_of_half_cubes),
    "no_of_side_plates": int(no_of_side_plates),
    "no_of_double_clips": int(no_of_double_clips),
    "no_of_single_clips": int(no_of_single_clips),
    "no_of_non_woven_geotextile": to_2dp(no_of_non_woven_geotextile),
    "liner_required": to_2dp(liner_req)
}



# def create_or_update_ecocube_output(project_id):
def create_or_update_ecocube_output(ecocube):

    # ecocube = EcocubeCostCalculation.query.filter_by(
    #     project_id=project_id
    # ).first()

    # if not ecocube:
    #     return False, "Ecocube input not found"

    # -----------------------------
    # MATERIAL CALCULATION
    # -----------------------------
    material_result = ecocube_material_calculation(
        ecocube.available_depth_to_invert,
        ecocube.layers_in_system,
        ecocube.target_storage_volume,
        ecocube.constraining_factor,
        ecocube.constraining_dimension,
        ecocube.include_liner,
        ecocube.number_of_inlets,
        ecocube.number_of_outlets
    )

    material_output = EcocubeOutput.query.filter_by(
        project_id=ecocube.project_id
    ).first()

    if not material_output:
        material_output = EcocubeOutput(project_id=ecocube.project_id)
        db.session.add(material_output)

    material_output.metres_wide = material_result["Metres-Wide"]
    material_output.metres_long = material_result["Metres-Long"]
    material_output.cubes_wide  = material_result["cubes_wide"]
    material_output.cubes_long  = material_result["cubes_long"]
    material_output.system_footprint = material_result["footprint"]
    material_output.tank_storage = material_result["tank_storage"]
    material_output.excavation_volume = material_result["excavation_volume"]
    material_output.initial_backfill_required = material_result["initial_backfill"]
    material_output.final_backfill_required   = material_result["final_backfill"]
    material_output.half_cubes    = material_result["no_of_half_cubes"]
    material_output.side_plates   = material_result["no_of_side_plates"]
    material_output.double_clips  = material_result["no_of_double_clips"]
    material_output.single_clips  = material_result["no_of_single_clips"]
    material_output.non_woven_geotextile = material_result["no_of_non_woven_geotextile"]
    material_output.liner_required = material_result["liner_required"]

    # -----------------------------
    # GEOMETRY CALCULATION
    # -----------------------------
    geometry_success, geometry_error = ecocube_geometry_calculation(
        ecocube.project_id,
        ecocube,
        material_output
    )

    if not geometry_success:
        return False, geometry_error
    
    db.session.flush()
    return True, "Calculation completed"


def ecocube_geometry_calculation(project_id, ecocube, material_output):

    try:
        # -------- LOAD CONSTANTS FROM DB --------
        constants = get_ecocube_constants()
        mod_h = constants["mod_h"]
        # -------- CREATE / FETCH FIRST --------
        geometry = EcocubeGeometryOutput.query.filter_by(
            project_id=project_id
        ).first()

        if not geometry:
            geometry = EcocubeGeometryOutput(
                project_id=project_id
            )
            db.session.add(geometry)
       
        # -------- DOUBLE STACK --------
        double_stack_mm = round(
            ecocube.layers_in_system * mod_h * 1000, 0
        )

        # -------- FSL & IL --------
        finished_surface_level_mm = round(
            ecocube.available_depth_to_invert, 0
        )

        outlet_invert_level_mm = finished_surface_level_mm

        # -------- DIMENSIONS --------
        length_mm = round(
            material_output.metres_long * 1000, 0
        )

        breadth_mm = round(
            material_output.metres_wide * 1000, 0
        )

        height_mm = finished_surface_level_mm

         #---------COVER DEPTH CHECK --------
        cover_depth_mm = finished_surface_level_mm - double_stack_mm

        # -------- NOW ASSIGN --------
        geometry.finished_surface_level = finished_surface_level_mm
        geometry.double_stack           = double_stack_mm
        geometry.outlet_invert_level    = outlet_invert_level_mm
        geometry.length_mm              = length_mm
        geometry.breadth_mm             = breadth_mm
        geometry.height_mm              = height_mm
        geometry.minimum_cover_depth    = 100.0
        geometry.cover_depth = cover_depth_mm
        db.session.flush()

        return True, None

    except Exception as e:
        return False, str(e)