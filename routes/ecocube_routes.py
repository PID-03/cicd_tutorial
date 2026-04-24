

# import logging
# from flask import Blueprint, request, jsonify
# from extensions import db
# from models.ecocube import EcocubeCostCalculation, EcocubeOutput, EcocubeGeometryOutput
# from processes.ecocube_cost_sheet import create_or_update_ecocube_output
# from flask_jwt_extended import jwt_required, get_jwt
# from utils.role_required import role_required
# from models.stormwater_output import StormwaterTankCalculation
# from models.stormwater_input import StormwaterSizingCalculation

# logger = logging.getLogger(__name__)

# ecocube_bp   = Blueprint("ecocube", __name__)
# ALLOWED_ROLES = ["CUSTOMER", "ADMIN"]


# def check_roles(claims):
#     roles = claims.get("roles", [])
#     return any(role in ALLOWED_ROLES for role in roles)


# # ──────────────────────────────────────────────────────────────
# # POST — create ecocube input + run calculation
# # ──────────────────────────────────────────────────────────────
# @ecocube_bp.route("/<uuid:project_id>/input", methods=["POST"])
# @jwt_required()
# def create_ecocube(project_id):
#     claims = get_jwt()
#     if not check_roles(claims):
#         return jsonify({"msg": "Unauthorized"}), 403

#     logger.info(f"[CREATE ECOCUBE] project_id={project_id}")

#     try:
#         data = request.json or {}

#         with db.session.begin():

#             existing = EcocubeCostCalculation.query.filter_by(
#                 project_id=project_id
#             ).first()

#             if existing:
#                 logger.warning(f"Ecocube already exists | project_id={project_id}")
#                 return jsonify({
#                     "error": "Ecocube input already exists for this project"
#                 }), 409

#             ecocube = EcocubeCostCalculation(
#                 project_id              = project_id,
#                 available_depth_to_invert = data.get("available_depth_to_invert"),
#                 max_layers_possible     = data.get("max_layers_possible"),
#                 layers_in_system        = data.get("layers_in_system"),
#                 include_liner           = data.get("include_liner"),
#                 target_storage_volume   = data.get("target_storage_volume"),
#                 constraining_factor     = data.get("constraining_factor"),
#                 constraining_dimension  = data.get("constraining_dimension"),
#                 number_of_outlets       = data.get("number_of_outlets", 0),
#                 number_of_inlets        = data.get("number_of_inlets", 0),
#             )

#             db.session.add(ecocube)
#             db.session.flush()

#             success, response = create_or_update_ecocube_output(ecocube)

#             if not success:
#                 logger.error(
#                     f"Output calculation failed | project_id={project_id} | {response}"
#                 )
#                 raise ValueError(response)

#         logger.info(f"Ecocube created | project_id={project_id}")
#         return jsonify({"message": "Ecocube input created successfully"}), 201

#     except ValueError as ve:
#         db.session.rollback()
#         logger.warning(f"Validation error | project_id={project_id} | {str(ve)}")
#         return jsonify({"error": str(ve)}), 422

#     except Exception as e:
#         db.session.rollback()
#         logger.exception(f"Unexpected error creating Ecocube | project_id={project_id}")
#         return jsonify({"error": "Failed to create Ecocube", "details": str(e)}), 500


# # ──────────────────────────────────────────────────────────────
# # GET — materials output
# # ──────────────────────────────────────────────────────────────
# @ecocube_bp.route("/<uuid:project_id>/materials", methods=["GET"])
# @jwt_required()
# def get_ecocube(project_id):
#     claims = get_jwt()
#     if not check_roles(claims):
#         return jsonify({"msg": "Unauthorized"}), 403

#     logger.info(f"[GET ECOCUBE MATERIALS] project_id={project_id}")

#     try:
#         input_data  = EcocubeCostCalculation.query.filter_by(project_id=project_id).first()
#         output_data = EcocubeOutput.query.filter_by(project_id=project_id).first()

#         if not input_data:
#             return jsonify({"error": "Not found"}), 404

#         return jsonify({
#             "metres_wide":              output_data.metres_wide              if output_data else None,
#             "metres_long":              output_data.metres_long              if output_data else None,
#             "cubes_wide":               output_data.cubes_wide               if output_data else None,
#             "cubes_long":               output_data.cubes_long               if output_data else None,
#             "system_footprint":         output_data.system_footprint         if output_data else None,
#             "tank_storage":             output_data.tank_storage             if output_data else None,
#             "excavation_volume":        output_data.excavation_volume        if output_data else None,
#             "initial_backfill_required":output_data.initial_backfill_required if output_data else None,
#             "final_backfill_required":  output_data.final_backfill_required  if output_data else None,
#             # ── FIX 1: removed the typo "out/put_data" ──────────────────────
#             "half_cubes":               output_data.half_cubes               if output_data else None,
#             "side_plates":              output_data.side_plates              if output_data else None,
#             "double_clips":             output_data.double_clips             if output_data else None,
#             "single_clips":             output_data.single_clips             if output_data else None,
#             "non_woven_geotextile":     output_data.non_woven_geotextile     if output_data else None,
#             "liner_required":           output_data.liner_required           if output_data else None,
#         })

#     except Exception as e:
#         logger.exception(f"Failed to fetch Ecocube materials | project_id={project_id}")
#         return jsonify({"error": "Failed to fetch Ecocube", "details": str(e)}), 500


# # ──────────────────────────────────────────────────────────────
# # PATCH — update ecocube input + recalculate
# # ──────────────────────────────────────────────────────────────
# @ecocube_bp.route("/<uuid:project_id>", methods=["PATCH"])
# @jwt_required()
# def update_ecocube(project_id):
#     claims = get_jwt()
#     if not check_roles(claims):
#         return jsonify({"msg": "Unauthorized"}), 403

#     logger.info(f"[UPDATE ECOCUBE] project_id={project_id}")

#     try:
#         with db.session.begin():

#             ecocube = EcocubeCostCalculation.query.filter_by(
#                 project_id=project_id
#             ).first()

#             if not ecocube:
#                 return jsonify({"error": "Not found"}), 404

#             for key, value in request.json.items():
#                 setattr(ecocube, key, value)

#             db.session.flush()

#             success, response = create_or_update_ecocube_output(ecocube)

#             if not success:
#                 logger.error(
#                     f"Output recalculation failed | project_id={project_id} | {response}"
#                 )
#                 raise ValueError(response)

#         logger.info(f"Ecocube updated | project_id={project_id}")
#         return jsonify({"message": "Ecocube updated successfully"})

#     except ValueError as ve:
#         db.session.rollback()
#         logger.warning(f"Validation error | project_id={project_id} | {str(ve)}")
#         return jsonify({"error": str(ve)}), 422

#     except Exception as e:
#         db.session.rollback()
#         logger.exception(f"Unexpected error updating Ecocube | project_id={project_id}")
#         return jsonify({"error": "Failed to update Ecocube", "details": str(e)}), 500


# # ──────────────────────────────────────────────────────────────
# # GET — geometry output
# # ──────────────────────────────────────────────────────────────
# @ecocube_bp.route("/<uuid:project_id>/geometry", methods=["GET"])
# @jwt_required()
# def get_ecocube_geometry(project_id):
#     claims = get_jwt()
#     if not check_roles(claims):
#         return jsonify({"msg": "Unauthorized"}), 403

#     logger.info(f"[GET ECOCUBE GEOMETRY] project_id={project_id}")

#     try:
#         geometry = EcocubeGeometryOutput.query.filter_by(
#             project_id=project_id
#         ).first()

#         if not geometry:
#             return jsonify({"error": "Geometry not found"}), 404

#         return jsonify({
#             "finished_surface_level": geometry.finished_surface_level,
#             "double_stack":           geometry.double_stack,
#             "outlet_invert_level":    geometry.outlet_invert_level,
#             "minimum_cover_depth":    geometry.minimum_cover_depth,
#             "length_mm":              geometry.length_mm,
#             "breadth_mm":             geometry.breadth_mm,
#             "height_mm":              geometry.height_mm,
#             "cover_depth":            geometry.cover_depth,
#         })

#     except Exception as e:
#         logger.exception(f"Failed to fetch geometry | project_id={project_id}")
#         return jsonify({"error": "Failed to fetch Ecocube Geometry", "details": str(e)}), 500


# # ──────────────────────────────────────────────────────────────
# # GET — ecocube input draft
# # ──────────────────────────────────────────────────────────────

# @ecocube_bp.route("/<uuid:project_id>/input", methods=["GET"])
# @jwt_required()
# def get_ecocube_input(project_id):
#     logger.info(f"[GET ECOCUBE INPUT] project_id={project_id}")

#     try:
#         # Fetch ecocube (can be None)
#         ecocube = EcocubeCostCalculation.query.filter_by(
#             project_id=project_id
#         ).first()

#         # Fetch sizing input (primary source of truth)
#         sizing = StormwaterSizingCalculation.query.filter_by(
#             project_id=project_id
#         ).first()

#         # Fetch tank output ALWAYS
#         tank_output = StormwaterTankCalculation.query.filter(
#             StormwaterTankCalculation.project_id == project_id,
#             StormwaterTankCalculation.volume_required.isnot(None)
#         ).order_by(
#             StormwaterTankCalculation.created_at.desc()
#         ).first()

#         volume_required_value = (
#             tank_output.volume_required if tank_output else None
#         )
#         volume_provided_value = (
#             tank_output.volume_provided if tank_output else None
#         )

#         # include_liner logic
#         include_liner_value = None
#         if ecocube and ecocube.project:
#             calculator_type = ecocube.project.calculator_type
#             if calculator_type == "infiltration":
#                 include_liner_value = "no"
#             elif calculator_type == "detention":
#                 include_liner_value = "yes"

#         # ─── available_depth_to_invert ───────────────────────────────────────
#         # Primary: sizing.tank_depth → convert m to mm
#         # Fallback: ecocube.available_depth_to_invert (already in mm)
#         tank_depth_m = getattr(sizing, "tank_depth", None)
#         if tank_depth_m is not None:
#             tank_depth_value = tank_depth_m * 1000
#         else:
#             tank_depth_value = getattr(ecocube, "available_depth_to_invert", None)

#         # ─── constraining_factor ─────────────────────────────────────────────
#         # Primary: sizing.constraint_type
#         # Fallback: ecocube.constraining_factor
#         constraint_type_value = getattr(sizing, "constraint_type", None)
#         if constraint_type_value is None:
#             constraint_type_value = getattr(ecocube, "constraining_factor", None)

#         # ─── constraining_dimension ──────────────────────────────────────────
#         # Primary: derived from sizing based on constraint_type
#         # Fallback: ecocube.constraining_dimension
#         constraining_dimension_value = None
#         if sizing:
#             if constraint_type_value == "length":
#                 constraining_dimension_value = sizing.tank_length
#             elif constraint_type_value == "width":
#                 constraining_dimension_value = sizing.tank_width

#         if constraining_dimension_value is None:
#             constraining_dimension_value = getattr(ecocube, "constraining_dimension", None)

#         # ─── max_layers_possible ─────────────────────────────────────────────
#         # Primary: sizing.max_layers_possible (if field exists)
#         # Fallback: ecocube.max_layers_possible
#         max_layers_possible_value = getattr(sizing, "max_layers_possible", None)
#         if max_layers_possible_value is None:
#             max_layers_possible_value = getattr(ecocube, "max_layers_possible", None)

#         # ─── layers_in_system ────────────────────────────────────────────────
#         # Primary: sizing.layers_in_system (if field exists)
#         # Fallback: ecocube.layers_in_system
#         layers_in_system_value = getattr(sizing, "layers_in_system", None)
#         if layers_in_system_value is None:
#             layers_in_system_value = getattr(ecocube, "layers_in_system", None)

#         return jsonify({
#             "available_depth_to_invert": tank_depth_value,
#             "max_layers_possible": max_layers_possible_value,
#             "layers_in_system": layers_in_system_value,
#             "include_liner": include_liner_value,
#             "target_storage_volume": volume_required_value,
#             "volumn_provided": volume_provided_value,
#             "constraining_factor": constraint_type_value,
#             "constraining_dimension": constraining_dimension_value,
#             "number_of_inlets": getattr(ecocube, "number_of_inlets", None),
#             "number_of_outlets": getattr(ecocube, "number_of_outlets", None),
#         }), 200

#     except Exception as e:
#         logger.exception(f"Failed to fetch Ecocube draft | project_id={project_id}")
#         return jsonify({
#             "error": "Failed to fetch Ecocube draft",
#             "details": str(e)
#         }), 500

import logging
from flask import Blueprint, request, jsonify
from extensions import db
from models.ecocube import EcocubeCostCalculation, EcocubeOutput, EcocubeGeometryOutput
from processes.ecocube_cost_sheet import create_or_update_ecocube_output
from flask_jwt_extended import jwt_required, get_jwt
from utils.role_required import role_required
from utils.error_response import error_response  # ✅ ADDED
from models.stormwater_output import StormwaterTankCalculation
from models.stormwater_input import StormwaterSizingCalculation

logger = logging.getLogger(__name__)

ecocube_bp   = Blueprint("ecocube", __name__)
ALLOWED_ROLES = ["CUSTOMER", "ADMIN"]


def check_roles(claims):
    roles = claims.get("roles", [])
    return any(role in ALLOWED_ROLES for role in roles)


# ──────────────────────────────────────────────────────────────
# POST — create ecocube input + run calculation
# ──────────────────────────────────────────────────────────────
@ecocube_bp.route("/<uuid:project_id>/input", methods=["POST"])
@jwt_required()
def create_ecocube(project_id):
    claims = get_jwt()
    if not check_roles(claims):
        return error_response(403, "Unauthorized", "You do not have permission to perform this action")  # ✅

    logger.info(f"[CREATE ECOCUBE] project_id={project_id}")

    try:
        data = request.json or {}

        with db.session.begin():

            existing = EcocubeCostCalculation.query.filter_by(
                project_id=project_id
            ).first()

            if existing:
                logger.warning(f"Ecocube already exists | project_id={project_id}")
                return error_response(409, "ConflictError", "Ecocube input already exists for this project")  # ✅

            ecocube = EcocubeCostCalculation(
                project_id                = project_id,
                available_depth_to_invert = data.get("available_depth_to_invert"),
                max_layers_possible       = data.get("max_layers_possible"),
                layers_in_system          = data.get("layers_in_system"),
                include_liner             = data.get("include_liner"),
                target_storage_volume     = data.get("target_storage_volume"),
                constraining_factor       = data.get("constraining_factor"),
                constraining_dimension    = data.get("constraining_dimension"),
                number_of_outlets         = data.get("number_of_outlets", 0),
                number_of_inlets          = data.get("number_of_inlets", 0),
            )

            db.session.add(ecocube)
            db.session.flush()

            success, response = create_or_update_ecocube_output(ecocube)

            if not success:
                logger.error(
                    f"Output calculation failed | project_id={project_id} | {response}"
                )
                raise ValueError(response)

        logger.info(f"Ecocube created | project_id={project_id}")

        
        return jsonify({"message": "Ecocube input created successfully"}), 201

    except ValueError as ve:
        db.session.rollback()
        logger.warning(f"Validation error | project_id={project_id} | {str(ve)}")
        return error_response(422, "ValidationError", str(ve))  # ✅

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Unexpected error creating Ecocube | project_id={project_id}")
        return error_response(500, "InternalServerError", "Failed to create Ecocube")  # ✅


# ──────────────────────────────────────────────────────────────
# GET — materials output
# ──────────────────────────────────────────────────────────────
@ecocube_bp.route("/<uuid:project_id>/materials", methods=["GET"])
@jwt_required()
def get_ecocube(project_id):
    claims = get_jwt()
    if not check_roles(claims):
        return error_response(403, "Unauthorized", "You do not have permission to perform this action")  # ✅

    logger.info(f"[GET ECOCUBE MATERIALS] project_id={project_id}")

    try:
        input_data  = EcocubeCostCalculation.query.filter_by(project_id=project_id).first()
        output_data = EcocubeOutput.query.filter_by(project_id=project_id).first()

        if not input_data:
            return error_response(404, "NotFound", "Ecocube input not found for this project")  # ✅

        return jsonify({
            "metres_wide":               output_data.metres_wide               if output_data else None,
            "metres_long":               output_data.metres_long               if output_data else None,
            "cubes_wide":                output_data.cubes_wide                if output_data else None,
            "cubes_long":                output_data.cubes_long                if output_data else None,
            "system_footprint":          output_data.system_footprint          if output_data else None,
            "tank_storage":              output_data.tank_storage              if output_data else None,
            "excavation_volume":         output_data.excavation_volume         if output_data else None,
            "initial_backfill_required": output_data.initial_backfill_required if output_data else None,
            "final_backfill_required":   output_data.final_backfill_required   if output_data else None,
            "half_cubes":                output_data.half_cubes                if output_data else None,
            "side_plates":               output_data.side_plates               if output_data else None,
            "double_clips":              output_data.double_clips              if output_data else None,
            "single_clips":              output_data.single_clips              if output_data else None,
            "non_woven_geotextile":      output_data.non_woven_geotextile      if output_data else None,
            "liner_required":            output_data.liner_required            if output_data else None,
        })

    except Exception as e:
        logger.exception(f"Failed to fetch Ecocube materials | project_id={project_id}")
        return error_response(500, "InternalServerError", "Failed to fetch Ecocube materials")  # ✅


# ──────────────────────────────────────────────────────────────
# PATCH — update ecocube input + recalculate
# ──────────────────────────────────────────────────────────────
@ecocube_bp.route("/<uuid:project_id>", methods=["PATCH"])
@jwt_required()
def update_ecocube(project_id):
    claims = get_jwt()
    if not check_roles(claims):
        return error_response(403, "Unauthorized", "You do not have permission to perform this action")  # ✅

    logger.info(f"[UPDATE ECOCUBE] project_id={project_id}")

    try:
        with db.session.begin():

            ecocube = EcocubeCostCalculation.query.filter_by(
                project_id=project_id
            ).first()

            if not ecocube:
                return error_response(404, "NotFound", "Ecocube input not found for this project")  # ✅

            for key, value in request.json.items():
                setattr(ecocube, key, value)

            db.session.flush()

            success, response = create_or_update_ecocube_output(ecocube)

            if not success:
                logger.error(
                    f"Output recalculation failed | project_id={project_id} | {response}"
                )
                raise ValueError(response)

        logger.info(f"Ecocube updated | project_id={project_id}")
        return jsonify({"message": "Ecocube updated successfully"})

    except ValueError as ve:
        db.session.rollback()
        logger.warning(f"Validation error | project_id={project_id} | {str(ve)}")
        return error_response(422, "ValidationError", str(ve))  # ✅

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Unexpected error updating Ecocube | project_id={project_id}")
        return error_response(500, "InternalServerError", "Failed to update Ecocube")  # ✅


# ──────────────────────────────────────────────────────────────
# GET — geometry output
# ──────────────────────────────────────────────────────────────
@ecocube_bp.route("/<uuid:project_id>/geometry", methods=["GET"])
@jwt_required()
def get_ecocube_geometry(project_id):
    claims = get_jwt()
    if not check_roles(claims):
        return error_response(403, "Unauthorized", "You do not have permission to perform this action")  # ✅

    logger.info(f"[GET ECOCUBE GEOMETRY] project_id={project_id}")

    try:
        geometry = EcocubeGeometryOutput.query.filter_by(
            project_id=project_id
        ).first()

        if not geometry:
            return error_response(404, "NotFound", "Geometry not found for this project")  # ✅

        return jsonify({
            "finished_surface_level": geometry.finished_surface_level,
            "double_stack":           geometry.double_stack,
            "outlet_invert_level":    geometry.outlet_invert_level,
            "minimum_cover_depth":    geometry.minimum_cover_depth,
            "length_mm":              geometry.length_mm,
            "breadth_mm":             geometry.breadth_mm,
            "height_mm":              geometry.height_mm,
            "cover_depth":            geometry.cover_depth,
        })

    except Exception as e:
        logger.exception(f"Failed to fetch geometry | project_id={project_id}")
        return error_response(500, "InternalServerError", "Failed to fetch Ecocube geometry")  # ✅


# ──────────────────────────────────────────────────────────────
# GET — ecocube input draft
# ──────────────────────────────────────────────────────────────
@ecocube_bp.route("/<uuid:project_id>/input", methods=["GET"])
@jwt_required()
def get_ecocube_input(project_id):
    logger.info(f"[GET ECOCUBE INPUT] project_id={project_id}")

    try:
        ecocube = EcocubeCostCalculation.query.filter_by(
            project_id=project_id
        ).first()

        sizing = StormwaterSizingCalculation.query.filter_by(
            project_id=project_id
        ).first()

        tank_output = StormwaterTankCalculation.query.filter(
            StormwaterTankCalculation.project_id == project_id,
            StormwaterTankCalculation.volume_required.isnot(None)
        ).order_by(
            StormwaterTankCalculation.created_at.desc()
        ).first()

        volume_required_value = tank_output.volume_required if tank_output else None
        volume_provided_value = tank_output.volume_provided if tank_output else None

        include_liner_value = None
        if ecocube and ecocube.project:
            calculator_type = ecocube.project.calculator_type
            if calculator_type == "infiltration":
                include_liner_value = "no"
            elif calculator_type == "detention":
                include_liner_value = "yes"

        tank_depth_m = getattr(sizing, "tank_depth", None)
        if tank_depth_m is not None:
            tank_depth_value = tank_depth_m * 1000
        else:
            tank_depth_value = getattr(ecocube, "available_depth_to_invert", None)

        constraint_type_value = getattr(sizing, "constraint_type", None)
        if constraint_type_value is None:
            constraint_type_value = getattr(ecocube, "constraining_factor", None)

        constraining_dimension_value = None
        if sizing:
            if constraint_type_value == "length":
                constraining_dimension_value = sizing.tank_length
            elif constraint_type_value == "width":
                constraining_dimension_value = sizing.tank_width
        if constraining_dimension_value is None:
            constraining_dimension_value = getattr(ecocube, "constraining_dimension", None)

        max_layers_possible_value = getattr(sizing, "max_layers_possible", None)
        if max_layers_possible_value is None:
            max_layers_possible_value = getattr(ecocube, "max_layers_possible", None)

        layers_in_system_value = getattr(sizing, "layers_in_system", None)
        if layers_in_system_value is None:
            layers_in_system_value = getattr(ecocube, "layers_in_system", None)

        return jsonify({
            "available_depth_to_invert": tank_depth_value,
            "max_layers_possible":       max_layers_possible_value,
            "layers_in_system":          layers_in_system_value,
            "include_liner":             include_liner_value,
            "target_storage_volume":     volume_required_value,
            "volumn_provided":           volume_provided_value,
            "constraining_factor":       constraint_type_value,
            "constraining_dimension":    constraining_dimension_value,
            "number_of_inlets":          getattr(ecocube, "number_of_inlets", None),
            "number_of_outlets":         getattr(ecocube, "number_of_outlets", None),
        }), 200

    except Exception as e:
        logger.exception(f"Failed to fetch Ecocube draft | project_id={project_id}")
        return error_response(500, "InternalServerError", "Failed to fetch Ecocube input draft")  # ✅