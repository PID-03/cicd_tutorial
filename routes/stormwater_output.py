

# from flask import Blueprint, jsonify
# from sqlalchemy.exc import SQLAlchemyError
# from extensions import db
# from flask_jwt_extended import jwt_required, get_jwt
# from utils.role_required import role_required
# from models.project import Project
# from models.stormwater_output import (
#     StormwaterAreaParameters,
#     AdditionalVolumeOutput,
#     StormwaterTankCalculation
# )
# import uuid
# import logging
# from models.stormwater_input import StormwaterSizingCalculation


# stormwater_bp = Blueprint("stormwater", __name__)
# logger = logging.getLogger(__name__)
# ALLOWED_ROLES = ["CUSTOMER","ADMIN"]


# @stormwater_bp.route("/<project_id>", methods=["GET"])
# @jwt_required()
# # @role_required(*ALLOWED_ROLES)
# def get_full_stormwater_output(project_id):
#     try:
#         # Convert project_id to UUID
#         project_uuid = uuid.UUID(project_id)

#         # -------------------------------------------------
#         # ✅ 1️⃣ CHECK PROJECT EXISTS & NOT SOFT DELETED
#         # -------------------------------------------------
#         project = Project.query.filter_by(
#             id=project_uuid,
#             del_flg=False
#         ).first()

#         if not project:
#             return jsonify({
#                 "success": False,
#                 "message": "Project not found"
#             }), 404

#         # -------------------------------------------------
#         # 2️⃣ FETCH RELATED DATA
#         # -------------------------------------------------
#         area_params = StormwaterAreaParameters.query.filter_by(
#             project_id=project_uuid
#         ).first()

#         additional_output = AdditionalVolumeOutput.query.filter_by(
#             project_id=project_uuid
#         ).first()

#         tank_output = StormwaterTankCalculation.query.filter_by(
#             project_id=project_uuid
#         ).first()

#         tank_input = StormwaterSizingCalculation.query.filter_by(
#             project_id=project_uuid
#         ).first()

#         response = {
#             "project_id": project_id,
#             "area_parameters": None,
#             "additional_area_outputs": None,
#             "tank_outputs": None
#         }

#         # -------- AREA PARAMETERS --------
#         if area_params:
#             response["area_parameters"] = {
#                 "equivalent_area": area_params.equivalent_area,
#                 "soil_permiability_mm_day": area_params.soil_permiability_mm_day,
#                 "detention_tank_allowance_m3_per_hour":
#                     area_params.detention_tank_allowance_m3_per_hour
#             }

#         # -------- ADDITIONAL AREA OUTPUT --------
#         if additional_output:
#             response["additional_area_outputs"] = {
#                 "roof_catchment_area": additional_output.roof_catchment_area,
#                 "carpark_catchment_area": additional_output.carpark_catchment_area,
#                 "landscaping_catchment_area": additional_output.landscaping_catchment_area,
#                 "total_additional_storage": additional_output.total_additional_storage,
#                 "precast_soakwell_area": additional_output.precast_soakwell_area,
#                 "stormwater_pipes": additional_output.stormwater_pipes,
#                 "other_additional_area": additional_output.other_additional_area
#             }

#         # -------- TANK OUTPUT --------
#         if tank_output:
#             # Determine constraint_value based on constraint_type
#             constraint_type = tank_input.constraint_type if tank_input else None

#             if constraint_type == "length":
#                 constraint_value = tank_output.tank_length
#             elif constraint_type == "width":
#                 constraint_value = tank_output.tank_width
#             elif constraint_type == "breadth":
#                 constraint_value = tank_output.tank_bredth
#             else:
#                 constraint_value = None

#             response["tank_outputs"] = {
#                 "volume_provided": tank_output.volume_provided,
#                 "volume_required": tank_output.volume_required,
#                 "contraint_type": constraint_type,
#                 "constraint_value": constraint_value,
#                 "tank_length": tank_output.tank_length,
#                 "tank_width": tank_output.tank_width,
#                 "tank_bredth": tank_output.tank_bredth,
#                 "module_length": tank_output.module_length,
#                 "module_width": tank_output.module_width,
#                 "module_breadth": tank_output.module_breadth,
#                 "gross_volume": tank_output.gross_volume,
#                 "net_volume": tank_output.net_volume,
#                 "bluemetal_gross_volume": tank_output.bluemetal_gross_volume,
#                 "bluemetal_net_volume": tank_output.bluemetal_net_volume,
#                 "tank_base_soakwell_base_max_stormwater_height":
#                     tank_output.tank_base_soakwell_base_max_stormwater_height,
#                 "graph": tank_output.graph
#             }

#         return jsonify({
#             "success": True,
#             "data": response
#         }), 200

#     except ValueError:
#         return jsonify({
#             "success": False,
#             "message": "Invalid project_id format"
#         }), 400

#     except SQLAlchemyError as e:
#         logger.error(str(e))
#         return jsonify({
#             "success": False,
#             "message": "Database error occurred"
#         }), 500

#     except Exception as e:
#         logger.error(str(e))
#         return jsonify({
#             "success": False,
#             "message": "Something went wrong"
#         }), 500

from flask import Blueprint, jsonify
from sqlalchemy.exc import SQLAlchemyError
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt
from utils.role_required import role_required
from utils.error_response import error_response  # ✅ ADDED
from models.project import Project
from models.stormwater_output import (
    StormwaterAreaParameters,
    AdditionalVolumeOutput,
    StormwaterTankCalculation
)
import uuid
import logging
from models.stormwater_input import StormwaterSizingCalculation


stormwater_bp = Blueprint("stormwater", __name__)
logger = logging.getLogger(__name__)
ALLOWED_ROLES = ["CUSTOMER", "ADMIN"]


@stormwater_bp.route("/<project_id>", methods=["GET"])
@jwt_required()
def get_full_stormwater_output(project_id):
    try:
        project_uuid = uuid.UUID(project_id)

        project = Project.query.filter_by(
            id=project_uuid,
            del_flg=False
        ).first()

        if not project:
            return error_response(404, "NotFound", "Project not found")  # ✅

        area_params = StormwaterAreaParameters.query.filter_by(
            project_id=project_uuid
        ).first()

        additional_output = AdditionalVolumeOutput.query.filter_by(
            project_id=project_uuid
        ).first()

        tank_output = StormwaterTankCalculation.query.filter_by(
            project_id=project_uuid
        ).first()

        tank_input = StormwaterSizingCalculation.query.filter_by(
            project_id=project_uuid
        ).first()

        response = {
            "project_id": project_id,
            "area_parameters": None,
            "additional_area_outputs": None,
            "tank_outputs": None
        }

        if area_params:
            response["area_parameters"] = {
                "equivalent_area": area_params.equivalent_area,
                "soil_permiability_mm_day": area_params.soil_permiability_mm_day,
                "detention_tank_allowance_m3_per_hour":
                    area_params.detention_tank_allowance_m3_per_hour
            }

        if additional_output:
            response["additional_area_outputs"] = {
                "roof_catchment_area": additional_output.roof_catchment_area,
                "carpark_catchment_area": additional_output.carpark_catchment_area,
                "landscaping_catchment_area": additional_output.landscaping_catchment_area,
                "total_additional_storage": additional_output.total_additional_storage,
                "precast_soakwell_area": additional_output.precast_soakwell_area,
                "stormwater_pipes": additional_output.stormwater_pipes,
                "other_additional_area": additional_output.other_additional_area
            }

        if tank_output:
            constraint_type = tank_input.constraint_type if tank_input else None

            if constraint_type == "length":
                constraint_value = tank_output.tank_length
            elif constraint_type == "width":
                constraint_value = tank_output.tank_width
            elif constraint_type == "breadth":
                constraint_value = tank_output.tank_bredth
            else:
                constraint_value = None

            response["tank_outputs"] = {
                "volume_provided": tank_output.volume_provided,
                "volume_required": tank_output.volume_required,
                "contraint_type": constraint_type,
                "constraint_value": constraint_value,
                "tank_length": tank_output.tank_length,
                "tank_width": tank_output.tank_width,
                "tank_bredth": tank_output.tank_bredth,
                "module_length": tank_output.module_length,
                "module_width": tank_output.module_width,
                "module_breadth": tank_output.module_breadth,
                "gross_volume": tank_output.gross_volume,
                "net_volume": tank_output.net_volume,
                "bluemetal_gross_volume": tank_output.bluemetal_gross_volume,
                "bluemetal_net_volume": tank_output.bluemetal_net_volume,
                "tank_base_soakwell_base_max_stormwater_height":
                    tank_output.tank_base_soakwell_base_max_stormwater_height,
                "graph": tank_output.graph
            }

        return jsonify({
            "success": True,
            "data": response
        }), 200

    except ValueError:
        return error_response(400, "ValidationError", "Invalid project_id format")  # ✅

    except SQLAlchemyError as e:
        logger.error(str(e))
        return error_response(500, "DatabaseError", "A database error occurred")  # ✅

    except Exception as e:
        logger.error(str(e))
        return error_response(500, "InternalServerError", "Something went wrong")  # ✅