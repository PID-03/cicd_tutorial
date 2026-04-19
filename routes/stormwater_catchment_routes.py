# from flask import Blueprint, request, jsonify
# from extensions import db
# from models.stormwater_input import StormwaterSizingCalculation
# import logging
# from datetime import datetime
# from processes.stormwater_sizing_additional_storage_calculator import calculate_additional_storage
# from models.project import Project
# from flask_jwt_extended import jwt_required, get_jwt
# from utils.role_required import role_required



# catchment_bp = Blueprint("stormwater_catchment", __name__)
# logger = logging.getLogger(__name__)

# ALLOWED_ROLES = ["CUSTOMER","ADMIN"]

# ALLOWED_FIELDS = [
#     "roof_depth_mm",
#     "carpark_depth_mm",
#     "landscaping_depth_mm",
#     "precast_soakwells",
#     "stormwater_pipes",
#     "other_additional_volume"
    
# ]


# # ------------------------------------------------
# # GET CATCHMENT
# # ------------------------------------------------
# @catchment_bp.route("/<uuid:project_id>/catchment", methods=["GET"])
# @jwt_required()
# # @role_required(*ALLOWED_ROLES)
# def get_catchment(project_id):
#     logger.info(f"GET Catchment request received | project_id={project_id}")

#     try:
#         # ✅ 1️⃣ Check project exists & not soft deleted
#         project = Project.query.filter_by(
#             id=project_id,
#             del_flg=False
#         ).first()

#         if not project:
#             return jsonify({
#                 "error": "Project not found"
#             }), 404

#         # ✅ 2️⃣ Check stormwater input exists
#         storm = StormwaterSizingCalculation.query.filter_by(
#             project_id=project_id
#         ).first()

#         if not storm:
#             return jsonify({
#                 "error": "Stormwater input not created yet"
#             }), 404

#         return jsonify({
#             field: getattr(storm, field)
#             for field in ALLOWED_FIELDS
#         }), 200

#     except Exception as e:
#         logger.exception(
#             f"Unhandled error while fetching catchment | project_id={project_id}"
#         )
#         return jsonify({
#             "error": "Internal Server Error",
#             "details": str(e)
#         }), 500


# # ------------------------------------------------
# # PATCH CATCHMENT (Update only, never create)
# # ------------------------------------------------
# @catchment_bp.route("/<uuid:project_id>/catchment", methods=["PATCH"])
# @jwt_required()
# # @role_required(*ALLOWED_ROLES)
# def update_catchment(project_id):
#     logger.info(f"PATCH Catchment request received | project_id={project_id}")

#     try:
#         # ✅ 1️⃣ Validate project
#         project = Project.query.filter_by(
#             id=project_id,
#             del_flg=False
#         ).first()

#         if not project:
#             return error_response(404, "ProjectNotFound", "Project not found")

#         # ✅ 2️⃣ Validate stormwater input exists
#         storm = StormwaterSizingCalculation.query.filter_by(
#             project_id=project_id
#         ).first()

#         if not storm:
#             return error_response(404, "StormwaterNotFound", "Stormwater input must be created first")

#         data = request.get_json(silent=True) or {}

#         # ✅ Update allowed fields
#         for field in ALLOWED_FIELDS:
#             if field in data:
#                 setattr(storm, field, data[field])

#         storm.updated_at = datetime.utcnow()

#         db.session.commit()

#         # ✅ Run calculation
#         success, response = calculate_additional_storage(
#             project_id, data
#         )

#         if not success:
#             return error_response(400, "CalculationError", response)

#         return jsonify({
#             "message": "Catchment updated successfully"
#         }), 200

#     except Exception as e:
#         db.session.rollback()
#         logger.exception(
#             f"Unhandled error while updating catchment | project_id={project_id}"
#         )
#         return error_response(500, "InternalServerError", "Internal Server Error")



from flask import Blueprint, request, jsonify
from extensions import db
from models.stormwater_input import StormwaterSizingCalculation
import logging
from datetime import datetime
from processes.stormwater_sizing_additional_storage_calculator import calculate_additional_storage
from models.project import Project
from flask_jwt_extended import jwt_required, get_jwt
from utils.role_required import role_required
from utils.error_response import error_response


catchment_bp = Blueprint("stormwater_catchment", __name__)
logger = logging.getLogger(__name__)

ALLOWED_ROLES = ["CUSTOMER", "ADMIN"]

ALLOWED_FIELDS = [
    "roof_depth_mm",
    "carpark_depth_mm",
    "landscaping_depth_mm",
    "precast_soakwells",
    "stormwater_pipes",
    "other_additional_volume"
]


# ------------------------------------------------
# GET CATCHMENT
# ------------------------------------------------
@catchment_bp.route("/<uuid:project_id>/catchment", methods=["GET"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def get_catchment(project_id):
    logger.info(f"GET Catchment request received | project_id={project_id}")

    try:
        project = Project.query.filter_by(
            id=project_id,
            del_flg=False
        ).first()

        if not project:
            return error_response(404, "ProjectNotFound", "Project not found")

        storm = StormwaterSizingCalculation.query.filter_by(
            project_id=project_id
        ).first()

        if not storm:
            return error_response(404, "StormwaterNotFound", "Stormwater input not created yet")

        return jsonify({
            field: getattr(storm, field)
            for field in ALLOWED_FIELDS
        }), 200

    except Exception:
        logger.exception(f"Unhandled error while fetching catchment | project_id={project_id}")
        return error_response(500, "InternalServerError", "Something went wrong")


# ------------------------------------------------
# PATCH CATCHMENT (Update only, never create)
# ------------------------------------------------
@catchment_bp.route("/<uuid:project_id>/catchment", methods=["PATCH"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def update_catchment(project_id):
    logger.info(f"PATCH Catchment request received | project_id={project_id}")

    try:
        project = Project.query.filter_by(
            id=project_id,
            del_flg=False
        ).first()

        if not project:
            return error_response(404, "ProjectNotFound", "Project not found")

        storm = StormwaterSizingCalculation.query.filter_by(
            project_id=project_id
        ).first()

        if not storm:
            return error_response(404, "StormwaterNotFound", "Stormwater input must be created first")

        data = request.get_json(silent=True) or {}

        for field in ALLOWED_FIELDS:
            if field in data:
                setattr(storm, field, data[field])

        storm.updated_at = datetime.utcnow()

        db.session.commit()

        success, response = calculate_additional_storage(project_id, data)

        if not success:
            return error_response(400, "CalculationError", response)

        return jsonify({
            "message": "Catchment updated successfully"
        }), 200

    except Exception:
        db.session.rollback()
        logger.exception(f"Unhandled error while updating catchment | project_id={project_id}")
        return error_response(500, "InternalServerError", "Something went wrong")