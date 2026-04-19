# # # from flask import Blueprint, request, jsonify
# # # from extensions import db
# # # from models.stormwater_input import StormwaterSizingCalculation
# # # from models.ecocube import EcocubeCostCalculation
# # # from processes.stormwater_sizing_tank_calculator import run_megavault_calculation
# # # from processes.stormwater_sizing_graph_calculator import run_stormwater_calculation
# # # from processes.stormwater_ecocube_merge import create_or_update_ecocube_output
# # # import logging
# # # from datetime import datetime
# # # from models.project import Project


# # # tank_bp = Blueprint("stormwater_tank", __name__)
# # # logger = logging.getLogger(__name__)

# # # STORMWATER_FIELDS = [
# # #     "constraint_type",
# # #     "constraint_value",
# # #     "approx_net_volume_depth",
# # #     "tank_width",
# # #     "tank_depth",
# # #     "bluemetal_base_height",
# # #     "bluemetal_base_factor",
# # #     "include_water_half_height_peripheral",
# # # ]

# # # ECOCUBE_FIELDS = [
# # #     "available_depth_to_invert",
# # #     "max_layers_possible",
# # #     "layers_in_system",
# # #     "number_of_outlets",
# # #     "number_of_inlets",
# # # ]


# # # # ------------------------------------------------
# # # # GET TANK
# # # # ------------------------------------------------
# # # @tank_bp.route("/<uuid:project_id>/tank", methods=["GET"])
# # # def get_tank(project_id):
# # #     logger.info(f"GET Tank request received | project_id={project_id}")

# # #     try:
# # #         project = Project.query.filter_by(id=project_id, del_flg=False).first()
# # #         if not project:
# # #             return jsonify({"error": "Project not found"}), 404

# # #         storm = StormwaterSizingCalculation.query.filter_by(project_id=project_id).first()
# # #         if not storm:
# # #             return jsonify({"error": "Stormwater input must be created first"}), 404

# # #         ecocube = EcocubeCostCalculation.query.filter_by(project_id=project_id).first()

# # #         # Build response — stormwater fields always present, ecocube fields null if no record yet
# # #         response = {field: getattr(storm, field) for field in STORMWATER_FIELDS}
# # #         response.update({
# # #             field: getattr(ecocube, field) if ecocube else None
# # #             for field in ECOCUBE_FIELDS
# # #         })

# # #         return jsonify(response), 200

# # #     except Exception as e:
# # #         logger.exception(f"Unhandled error while fetching tank data | project_id={project_id}")
# # #         return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


# # # # ------------------------------------------------
# # # # PATCH TANK
# # # # ------------------------------------------------
# # # @tank_bp.route("/<uuid:project_id>/tank", methods=["PATCH"])
# # # def update_tank(project_id):
# # #     logger.info(f"PATCH Tank request received | project_id={project_id}")

# # #     try:
# # #         project = Project.query.filter_by(id=project_id, del_flg=False).first()
# # #         if not project:
# # #             return jsonify({"error": "Project not found"}), 404

# # #         storm = StormwaterSizingCalculation.query.filter_by(project_id=project_id).first()
# # #         if not storm:
# # #             return jsonify({"error": "Stormwater input must be created first"}), 404

# # #         data = request.get_json(silent=True) or {}

# # #         # ── Update stormwater fields ──────────────────────────────────────────
# # #         stormwater_changed = False
# # #         for field in STORMWATER_FIELDS:
# # #             if field in data:
# # #                 setattr(storm, field, data[field])
# # #                 stormwater_changed = True

# # #         if stormwater_changed:
# # #             storm.updated_at = datetime.utcnow()

# # #         # ── Update ecocube fields ─────────────────────────────────────────────
# # #         ecocube_changed = any(field in data for field in ECOCUBE_FIELDS)

# # #         if ecocube_changed:
# # #             ecocube = EcocubeCostCalculation.query.filter_by(project_id=project_id).first()

# # #             if not ecocube:
# # #                 # Create the record on first use
# # #                 ecocube = EcocubeCostCalculation(project_id=project_id)
# # #                 db.session.add(ecocube)

# # #             for field in ECOCUBE_FIELDS:
# # #                 if field in data:
# # #                     setattr(ecocube, field, data[field])

# # #             ecocube.updated_at = datetime.utcnow()

# # #         db.session.commit()

# # #         # Run calculations after commit
# # #         run_megavault_calculation(project_id)
# # #         run_stormwater_calculation(project_id)
# # #         # create_or_update_ecocube_output(project_id)

# # #         return jsonify({"message": "Tank updated successfully"}), 200

# # #     except Exception as e:
# # #         db.session.rollback()
# # #         logger.exception(f"Unhandled error while updating tank | project_id={project_id}")
# # #         return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


# # from flask import Blueprint, request, jsonify
# # from extensions import db
# # from models.stormwater_input import StormwaterSizingCalculation
# # from processes.stormwater_sizing_tank_calculator import run_megavault_calculation
# # from processes.stormwater_sizing_graph_calculator import run_stormwater_calculation
# # import logging
# # from datetime import datetime
# # from models.project import Project
# # from flask_jwt_extended import jwt_required, get_jwt
# # from utils.role_required import role_required



# # tank_bp = Blueprint("stormwater_tank", __name__)
# # logger = logging.getLogger(__name__)

# # ALLOWED_ROLES = ["CUSTOMER","ADMIN"]

# # STORMWATER_FIELDS = [
# #     "constraint_type",
# #     "tank_length",
# #     "approx_net_volume_depth",
# #     "tank_width",
# #     "tank_depth",
# #     "bluemetal_base_height",
# #     "bluemetal_base_factor",
# #     "include_water_half_height_peripheral",
# # ]


# # # ------------------------------------------------
# # # GET TANK
# # # ------------------------------------------------
# # @tank_bp.route("/<uuid:project_id>/tank", methods=["GET"])
# # @jwt_required()
# # # @role_required(*ALLOWED_ROLES)
# # def get_tank(project_id):
# #     logger.info(f"GET Tank request received | project_id={project_id}")

# #     try:
# #         project = Project.query.filter_by(id=project_id, del_flg=False).first()
# #         if not project:
# #             return jsonify({"error": "Project not found"}), 404

# #         storm = StormwaterSizingCalculation.query.filter_by(project_id=project_id).first()
# #         if not storm:
# #             return jsonify({"error": "Stormwater input must be created first"}), 404

# #         response = {field: getattr(storm, field) for field in STORMWATER_FIELDS}

# #         return jsonify(response), 200

# #     except Exception as e:
# #         logger.exception(f"Unhandled error while fetching tank data | project_id={project_id}")
# #         return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


# # # ------------------------------------------------
# # # PATCH TANK
# # # ------------------------------------------------
# # @tank_bp.route("/<uuid:project_id>/tank", methods=["PATCH"])
# # @jwt_required()
# # def update_tank(project_id):
# #     logger.info(f"PATCH Tank request | project_id={project_id}")

# #     try:
# #         project = Project.query.filter_by(id=project_id, del_flg=False).first()
# #         if not project:
# #             return jsonify({"error": "Project not found"}), 404

# #         storm = StormwaterSizingCalculation.query.filter_by(
# #             project_id=project_id
# #         ).first()
# #         if not storm:
# #             return jsonify({"error": "Stormwater input must be created first"}), 404

# #         data = request.get_json(silent=True) or {}

# #         for field in STORMWATER_FIELDS:
# #             if field in data:
# #                 setattr(storm, field, data[field])

# #         storm.updated_at = datetime.utcnow()
# #         db.session.commit()

# #         # ── Route based on scenario ──────────────────────────────────────────
# #         is_infiltration = (
# #             storm.soil_permeability is not None
# #             and float(storm.soil_permeability) > 0
# #         )

# #         if is_infiltration:
# #             # Scenario 2: iterator does tank calc + graph in one pass
# #             result = run_stormwater_calculation(project_id)
# #         else:
# #             # Scenario 1: tank calc first, then graph
# #             run_megavault_calculation(project_id)
# #             result = run_stormwater_calculation(project_id)

# #         return jsonify({"message": "Tank updated successfully", "result": result}), 200

# #     except Exception as e:
# #         db.session.rollback()
# #         logger.exception(f"Error updating tank | project_id={project_id}")
# #         return jsonify({"error": "Internal Server Error", "details": str(e)}), 500



# from flask import Blueprint, request, jsonify
# from extensions import db
# from models.stormwater_input import StormwaterSizingCalculation
# from processes.stormwater_sizing_graph_calculator import run_stormwater_calculation
# from models.stormwater_output import StormwaterTankCalculation
# import logging
# from datetime import datetime
# from models.project import Project
# from flask_jwt_extended import jwt_required, get_jwt
# from utils.role_required import role_required
# from processes.volume_required_calculator import calculate_volume_required

# tank_bp = Blueprint("stormwater_tank", __name__)
# logger  = logging.getLogger(__name__)

# ALLOWED_ROLES = ["CUSTOMER", "ADMIN"]

# STORMWATER_FIELDS = [
#     "constraint_type",
#     "tank_length",
#     "approx_net_volume_depth",
#     "tank_width",
#     "tank_depth",
#     "bluemetal_base_height",
#     "bluemetal_base_factor",
#     "include_water_half_height_peripheral",
# ]


# # ──────────────────────────────────────────────────────────────
# # GET TANK
# # ──────────────────────────────────────────────────────────────
# # @tank_bp.route("/<uuid:project_id>/tank", methods=["GET"])
# # @jwt_required()
# # def get_tank(project_id):
# #     logger.info(f"GET Tank | project_id={project_id}")

# #     try:
# #         # ── 1. Project guard ─────────────────────────────
# #         project = Project.query.filter_by(id=project_id, del_flg=False).first()
# #         if not project:
# #             return jsonify({"error": "Project not found"}), 404

# #         # ── 2. Input table ───────────────────────────────
# #         storm = StormwaterSizingCalculation.query.filter_by(
# #             project_id=project_id
# #         ).first()

# #         if not storm:
# #             return jsonify({"error": "Stormwater input must be created first"}), 404

# #         # ── 3. Output table ──────────────────────────────
# #         tank_output = StormwaterTankCalculation.query.filter_by(
# #             project_id=project_id
# #         ).first()

# #         # ── 4. Base response ─────────────────────────────
# #         response = {
# #             field: getattr(storm, field) for field in STORMWATER_FIELDS
# #         }

# #         # ── 5. Override tank values (IMPORTANT) ──────────
# #         if tank_output:
# #             if tank_output.tank_length is not None:
# #                 response["tank_length"] = tank_output.tank_length

# #             if tank_output.tank_width is not None:
# #                 response["tank_width"] = tank_output.tank_width

# #             # if tank_output.volume_required is not None:
# #             #     response["volume_required"] = tank_output.volume_required
# #         # ── 5. Override tank values ──────────
# #         # if tank_output:
# #         #     override_fields = [
# #         #         "tank_length",
# #         #         "tank_width",
# #         #         "volume_required",
# #         #         "volume_provided"   # ✅ added
# #         #     ]

# #         #     for field in override_fields:
# #         #         value = getattr(tank_output, field, None)
# #         #         if value is not None:
# #         #             response[field] = value

# #         return jsonify(response), 200

# #     except Exception as e:
# #         logger.exception(f"Error fetching tank | project_id={project_id}")
# #         return jsonify({
# #             "error": "Internal Server Error",
# #             "details": str(e)
# #         }), 500


# # @tank_bp.route("/<uuid:project_id>/tank", methods=["GET"])
# # @jwt_required()
# # def get_tank(project_id):
# #     logger.info(f"GET Tank | project_id={project_id}")

# #     try:
# #         # ── 1. Validate project ─────────────────────────────
# #         project = Project.query.filter_by(id=project_id, del_flg=False).first()
# #         if not project:
# #             return jsonify({"error": "Project not found"}), 404

# #         # ── 2. Fetch stormwater input ───────────────────────
# #         storm = StormwaterSizingCalculation.query.filter_by(
# #             project_id=project_id
# #         ).first()

# #         if not storm:
# #             return jsonify({
# #                 "error": "Stormwater input must be created first"
# #             }), 404

# #         # ── 3. Fetch tank output (DB values only) ───────────
# #         tank_output = StormwaterTankCalculation.query.filter_by(
# #             project_id=project_id
# #         ).first()

# #         # ── 4. Base response from storm ─────────────────────
# #         response = {
# #             field: getattr(storm, field)
# #             for field in STORMWATER_FIELDS
# #         }

# #         # ── 5. Override ONLY from DB (never from calculation) ─
# #         if tank_output:
# #             if tank_output.tank_length is not None:
# #                 response["tank_length"] = tank_output.tank_length

# #             if tank_output.tank_width is not None:
# #                 response["tank_width"] = tank_output.tank_width

# #             if hasattr(tank_output, "constraint_type"):
# #                 response["constraint_type"] = tank_output.constraint_type

# #         # ── 6. Add volume_required (no override of tank dims) ─
# #         try:
# #             vol = calculate_volume_required(project_id)

# #             response["volume_required_m3"] = vol.get("volume_required_m3")

# #         except ValueError as ve:
# #             logger.warning(
# #                 f"volume_required unavailable | project_id={project_id} | reason={ve}"
# #             )

# #             response["volume_required_m3"] = None

# #         # ── 7. Return response ──────────────────────────────
# #         return jsonify(response), 200

# #     except Exception as e:
# #         logger.exception(f"Error fetching tank | project_id={project_id}")
# #         return jsonify({
# #             "error": "Internal Server Error",
# #             "details": str(e)
# #         }), 500


# @tank_bp.route("/<uuid:project_id>/tank", methods=["GET"])
# @jwt_required()
# def get_tank(project_id):
#     logger.info(f"GET Tank | project_id={project_id}")

#     try:
#         # ── 1. Validate project ─────────────────────────────
#         project = Project.query.filter_by(id=project_id, del_flg=False).first()
#         if not project:
#             return jsonify({"error": "Project not found"}), 404

#         # ── 2. Fetch stormwater input ───────────────────────
#         storm = StormwaterSizingCalculation.query.filter_by(
#             project_id=project_id
#         ).first()

#         # ── 3. Fetch tank output ────────────────────────────
#         tank_output = StormwaterTankCalculation.query.filter_by(
#             project_id=project_id
#         ).first()

#         # ── 4. Base response ────────────────────────────────
#         if storm:
#             response = {
#                 field: getattr(storm, field)
#                 for field in STORMWATER_FIELDS
#             }
#         else:
#             # Return all fields as null instead of error
#             response = {
#                 field: None
#                 for field in STORMWATER_FIELDS
#             }

#         # ── 5. Override ONLY from DB (no calculation override) ─
#         if tank_output:
#             if tank_output.tank_length is not None:
#                 response["tank_length"] = tank_output.tank_length

#             if tank_output.tank_width is not None:
#                 response["tank_width"] = tank_output.tank_width

#             if hasattr(tank_output, "constraint_type"):
#                 response["constraint_type"] = tank_output.constraint_type

#         # ── 6. Add volume_required safely ───────────────────
#         try:
#             vol = calculate_volume_required(project_id)
#             response["volume_required_m3"] = vol.get("volume_required_m3")
#         except Exception as e:
#             logger.warning(
#                 f"volume_required unavailable | project_id={project_id} | reason={e}"
#             )
#             response["volume_required_m3"] = None

#         # ── 7. Return response (always 200) ─────────────────
#         return jsonify(response), 200

#     except Exception as e:
#         logger.exception(f"Error fetching tank | project_id={project_id}")
#         return jsonify({
#             "error": "Internal Server Error",
#             "details": str(e)
#         }), 500


# # ──────────────────────────────────────────────────────────────
# # PATCH TANK
# # ──────────────────────────────────────────────────────────────
# @tank_bp.route("/<uuid:project_id>/tank", methods=["PATCH"])
# @jwt_required()
# def update_tank(project_id):
#     logger.info(f"PATCH Tank | project_id={project_id}")

#     try:
#         # ── 1. Project guard ──────────────────────────────────────────────────
#         project = Project.query.filter_by(id=project_id, del_flg=False).first()
#         if not project:
#             return jsonify({"error": "Project not found"}), 404

#         # ── 2. Stormwater input guard ─────────────────────────────────────────
#         storm = StormwaterSizingCalculation.query.filter_by(
#             project_id=project_id
#         ).first()
#         if not storm:
#             return jsonify({"error": "Stormwater input must be created first"}), 404

#         # ── FIX 5: soil_permeability must be set via /input before /tank ──────
#         if storm.soil_permeability is None:
#             return jsonify({
#                 "error": (
#                     "soil_permeability is not set. "
#                 )
#             }), 400

#         # ── 3. Apply incoming fields ──────────────────────────────────────────
#         data = request.get_json(silent=True) or {}

#         for field in STORMWATER_FIELDS:
#             if field in data:
#                 setattr(storm, field, data[field])

#         storm.updated_at = datetime.utcnow()
#         db.session.commit()

#         # ── 4. Route to correct calculation scenario ──────────────────────────
#         is_infiltration = float(storm.soil_permeability) > 0

#         if is_infiltration:
#             # Scenario 2 — Infiltration
#             # Iterator handles both tank sizing AND graph in one pass.
#             # run_megavault_calculation is intentionally skipped here.
#             logger.info(f"Routing to Infiltration iteration | project_id={project_id}")
#             result = run_stormwater_calculation(project_id)

#         else:
#             # Scenario 1 — Detention / Retention
#             # Sizing and graph now follow the same iterative convergence
#             # pattern as infiltration.
#             logger.info(f"Routing to Detention iteration | project_id={project_id}")
#             result = run_stormwater_calculation(project_id)

#         return jsonify({
#             "message": "Tank updated successfully",
#             "result":  result
#         }), 200

#     except ValueError as ve:
#         db.session.rollback()
#         logger.warning(f"Validation error | project_id={project_id} | {str(ve)}")
#         return jsonify({"error": str(ve)}), 400

#     except Exception as e:
#         db.session.rollback()
#         logger.exception(f"Error updating tank | project_id={project_id}")
#         return jsonify({"error": "Internal Server Error", "details": str(e)}), 500



from flask import Blueprint, request, jsonify
from extensions import db
from models.stormwater_input import StormwaterSizingCalculation
from processes.stormwater_sizing_graph_calculator import run_stormwater_calculation
from models.stormwater_output import StormwaterTankCalculation
import logging
from datetime import datetime
from models.project import Project
from flask_jwt_extended import jwt_required
from utils.role_required import role_required
from processes.volume_required_calculator import calculate_volume_required
from utils.error_response import error_response

tank_bp = Blueprint("stormwater_tank", __name__)
logger = logging.getLogger(__name__)

ALLOWED_ROLES = ["CUSTOMER", "ADMIN"]

STORMWATER_FIELDS = [
    "constraint_type",
    "tank_length",
    "approx_net_volume_depth",
    "tank_width",
    "tank_depth",
    "bluemetal_base_height",
    "bluemetal_base_factor",
    "include_water_half_height_peripheral",
]


# ──────────────────────────────────────────────────────────────
# GET TANK
# ──────────────────────────────────────────────────────────────
@tank_bp.route("/<uuid:project_id>/tank", methods=["GET"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def get_tank(project_id):
    logger.info(f"GET Tank | project_id={project_id}")

    try:
        # ── 1. Validate project ──────────────────────────────────────────────
        project = Project.query.filter_by(id=project_id, del_flg=False).first()
        if not project:
            return error_response(404, "ProjectNotFound", "Project not found")

        # ── 2. Fetch stormwater input ────────────────────────────────────────
        storm = StormwaterSizingCalculation.query.filter_by(
            project_id=project_id
        ).first()

        # ── 3. Fetch tank output ─────────────────────────────────────────────
        tank_output = StormwaterTankCalculation.query.filter_by(
            project_id=project_id
        ).first()

        # ── 4. Base response (null-safe if storm not yet created) ────────────
        if storm:
            response = {field: getattr(storm, field) for field in STORMWATER_FIELDS}
        else:
            response = {field: None for field in STORMWATER_FIELDS}

        # ── 5. Override with saved tank output values (DB only, no recalc) ───
        if tank_output:
            if tank_output.tank_length is not None:
                response["tank_length"] = tank_output.tank_length
            if tank_output.tank_width is not None:
                response["tank_width"] = tank_output.tank_width
            if hasattr(tank_output, "constraint_type"):
                response["constraint_type"] = tank_output.constraint_type

        # ── 6. Add volume_required safely ────────────────────────────────────
        try:
            vol = calculate_volume_required(project_id)
            response["volume_required_m3"] = vol.get("volume_required_m3")
        except Exception:
            logger.warning(f"volume_required unavailable | project_id={project_id}")
            response["volume_required_m3"] = None

        return jsonify(response), 200

    except Exception:
        logger.exception(f"Error fetching tank | project_id={project_id}")
        return error_response(500, "InternalServerError", "Something went wrong")


# ──────────────────────────────────────────────────────────────
# PATCH TANK
# ──────────────────────────────────────────────────────────────
@tank_bp.route("/<uuid:project_id>/tank", methods=["PATCH"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def update_tank(project_id):
    logger.info(f"PATCH Tank | project_id={project_id}")

    try:
        # ── 1. Project guard ─────────────────────────────────────────────────
        project = Project.query.filter_by(id=project_id, del_flg=False).first()
        if not project:
            return error_response(404, "ProjectNotFound", "Project not found")

        # ── 2. Stormwater input guard ────────────────────────────────────────
        storm = StormwaterSizingCalculation.query.filter_by(
            project_id=project_id
        ).first()
        if not storm:
            return error_response(
                404,
                "StormwaterNotFound",
                "Stormwater input must be created first"
            )

        # ── 3. soil_permeability must be set before tank updates ─────────────
        if storm.soil_permeability is None:
            return error_response(
                400,
                "ValidationError",
                "soil_permeability is not set. Please update it via the /input endpoint first."
            )

        # ── 4. Apply incoming fields ─────────────────────────────────────────
        data = request.get_json(silent=True) or {}

        for field in STORMWATER_FIELDS:
            if field in data:
                setattr(storm, field, data[field])

        storm.updated_at = datetime.utcnow()
        db.session.commit()

        # ── 5. Run calculation ───────────────────────────────────────────────
        is_infiltration = float(storm.soil_permeability) > 0

        if is_infiltration:
            logger.info(f"Routing to Infiltration iteration | project_id={project_id}")
        else:
            logger.info(f"Routing to Detention iteration | project_id={project_id}")

        result = run_stormwater_calculation(project_id)

        return jsonify({
            "message": "Tank updated successfully",
            "result": result
        }), 200

    except ValueError as ve:
        db.session.rollback()
        logger.warning(f"Validation error | project_id={project_id} | {str(ve)}")
        return error_response(400, "ValidationError", str(ve))

    except Exception:
        db.session.rollback()
        logger.exception(f"Error updating tank | project_id={project_id}")
        return error_response(500, "InternalServerError", "Something went wrong")