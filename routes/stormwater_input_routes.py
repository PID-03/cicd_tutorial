# from flask import Blueprint, request, jsonify
# from sqlalchemy.exc import IntegrityError
# from extensions import db
# from models.stormwater_input import StormwaterSizingCalculation
# import logging
# from datetime import datetime
# from models.project import Project
# from flask_jwt_extended import jwt_required, get_jwt
# from utils.role_required import role_required

# from processes.stormwater_sizing_input_calculator import input_calculations

# input_bp = Blueprint("stormwater_input", __name__)
# logger = logging.getLogger(__name__)

# ALLOWED_ROLES = ["CUSTOMER","ADMIN"]
# ALLOWED_FIELDS = [
#     "annual_exceedence_probability",
#     "rainfall_intensity_increase_allowance",
#     "maximum_storm_duration",
#     "roof_area",
#     "roof_coefficient",
#     "carpark_area",
#     "carpark_coefficient",
#     "landscaping_area",
#     "landscaping_coefficient",
#     "soil_permeability",
#     "detention_tank_discharge_allowance"
# ]

# # ------------------------------------------------
# # CREATE INPUT (Only if not exists)
# # ------------------------------------------------
# @input_bp.route("/<uuid:project_id>/input", methods=["POST"])
# @jwt_required()
# # @role_required(*ALLOWED_ROLES)
# def create_input(project_id):
#     logger.info(f"POST Stormwater input request received | project_id={project_id}")

#     try:
#         # ✅ Check project exists & not soft deleted
#         project = Project.query.filter_by(
#             id=project_id,
#             del_flg=False
#         ).first()

#         if not project:
#             return jsonify({"error": "Project not found"}), 404

#         existing = StormwaterSizingCalculation.query.filter_by(
#             project_id=project_id
#         ).first()

#         if existing:
#             return jsonify({
#                 "error": "Stormwater input already exists for this project"
#             }), 409

#         data = request.get_json(silent=True) or {}

#         filtered_data = {
#             k: v for k, v in data.items()
#             if k in ALLOWED_FIELDS
#         }

#         storm = StormwaterSizingCalculation(
#             project_id=project_id,
#             **filtered_data
#         )

#         db.session.add(storm)
#         db.session.commit()

#         # Run calculation after commit
#         success, response = input_calculations(project_id, data)

#         if not success:
#             return jsonify({"error": response}), 400

#         return jsonify({
#             "message": "Stormwater input created successfully"
#         }), 201

#     except IntegrityError:
#         db.session.rollback()
#         return jsonify({
#             "error": "Database constraint violation"
#         }), 400

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({
#             "error": "Internal Server Error",
#             "details": str(e)
#         }), 500


# # ------------------------------------------------
# # GET INPUT
# # ------------------------------------------------
# @input_bp.route("/<uuid:project_id>/input", methods=["GET"])
# @jwt_required()
# # @role_required(*ALLOWED_ROLES)
# def get_input(project_id):
#     logger.info(f"GET Stormwater input request received | project_id={project_id}")

#     try:
#         # ✅ Check project first
#         project = Project.query.filter_by(
#             id=project_id,
#             del_flg=False
#         ).first()

#         if not project:
#             return jsonify({"error": "Project not found"}), 404

#         storm = StormwaterSizingCalculation.query.filter_by(
#             project_id=project_id
#         ).first()

#         if not storm:
#             return jsonify({"error": "Stormwater input not found"}), 404

#         return jsonify({
#             field: getattr(storm, field)
#             for field in ALLOWED_FIELDS
#         }), 200

#     except Exception as e:
#         return jsonify({
#             "error": "Internal Server Error",
#             "details": str(e)
#         }), 500



# @input_bp.route("/<uuid:project_id>/input", methods=["PATCH"])
# @jwt_required()
# # @role_required(*ALLOWED_ROLES)
# def update_input(project_id):
#     logger.info(f"PATCH Stormwater input request received | project_id={project_id}")

#     try:
#         # ✅ Check project exists
#         project = Project.query.filter_by(
#             id=project_id,
#             del_flg=False
#         ).first()

#         if not project:
#             return jsonify({"error": "Project not found"}), 404

#         storm = StormwaterSizingCalculation.query.filter_by(
#             project_id=project_id
#         ).first()

#         if not storm:
#             return jsonify({
#                 "error": "Stormwater input does not exist. Create it first."
#             }), 404

#         data = request.get_json(silent=True) or {}

#         for field in ALLOWED_FIELDS:
#             if field in data:
#                 setattr(storm, field, data[field])

#         storm.updated_at = datetime.utcnow()

#         db.session.commit()

#         # Recalculate
#         success, response = input_calculations(project_id, data)

#         if not success:
#             return jsonify({"error": response}), 400

#         return jsonify({
#             "message": "Stormwater input updated successfully"
#         }), 200

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({
#             "error": "Internal Server Error",
#             "details": str(e)
#         }), 500


from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from extensions import db
from models.stormwater_input import StormwaterSizingCalculation
import logging
from datetime import datetime
from models.project import Project
from flask_jwt_extended import jwt_required, get_jwt
from utils.role_required import role_required
from utils.error_response import error_response

from processes.stormwater_sizing_input_calculator import input_calculations

input_bp = Blueprint("stormwater_input", __name__)
logger = logging.getLogger(__name__)

ALLOWED_ROLES = ["CUSTOMER", "ADMIN"]
ALLOWED_FIELDS = [
    "annual_exceedence_probability",
    "rainfall_intensity_increase_allowance",
    "maximum_storm_duration",
    "roof_area",
    "roof_coefficient",
    "carpark_area",
    "carpark_coefficient",
    "landscaping_area",
    "landscaping_coefficient",
    "soil_permeability",
    "detention_tank_discharge_allowance"
]


# ------------------------------------------------
# CREATE INPUT (Only if not exists)
# ------------------------------------------------
@input_bp.route("/<uuid:project_id>/input", methods=["POST"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def create_input(project_id):
    logger.info(f"POST Stormwater input request received | project_id={project_id}")

    try:
        project = Project.query.filter_by(
            id=project_id,
            del_flg=False
        ).first()

        if not project:
            return error_response(404, "ProjectNotFound", "Project not found")

        existing = StormwaterSizingCalculation.query.filter_by(
            project_id=project_id
        ).first()

        if existing:
            return error_response(409, "ConflictError", "Stormwater input already exists for this project")

        data = request.get_json(silent=True) or {}

        filtered_data = {
            k: v for k, v in data.items()
            if k in ALLOWED_FIELDS
        }

        storm = StormwaterSizingCalculation(
            project_id=project_id,
            **filtered_data
        )

        db.session.add(storm)
        db.session.commit()

        success, response = input_calculations(project_id, data)

        if not success:
            return error_response(400, "CalculationError", response)

        return jsonify({
            "message": "Stormwater input created successfully"
        }), 201

    except IntegrityError:
        db.session.rollback()
        logger.exception(f"Integrity error on create input | project_id={project_id}")
        return error_response(400, "IntegrityError", "Database constraint violation")

    except Exception:
        db.session.rollback()
        logger.exception(f"Unhandled error on create input | project_id={project_id}")
        return error_response(500, "InternalServerError", "Something went wrong")


# ------------------------------------------------
# GET INPUT
# ------------------------------------------------
@input_bp.route("/<uuid:project_id>/input", methods=["GET"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def get_input(project_id):
    logger.info(f"GET Stormwater input request received | project_id={project_id}")

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
            return error_response(404, "StormwaterNotFound", "Stormwater input not found")

        return jsonify({
            field: getattr(storm, field)
            for field in ALLOWED_FIELDS
        }), 200

    except Exception:
        logger.exception(f"Unhandled error on get input | project_id={project_id}")
        return error_response(500, "InternalServerError", "Something went wrong")


# ------------------------------------------------
# PATCH INPUT
# ------------------------------------------------
@input_bp.route("/<uuid:project_id>/input", methods=["PATCH"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def update_input(project_id):
    logger.info(f"PATCH Stormwater input request received | project_id={project_id}")

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
            return error_response(404, "StormwaterNotFound", "Stormwater input does not exist. Create it first.")

        data = request.get_json(silent=True) or {}

        for field in ALLOWED_FIELDS:
            if field in data:
                setattr(storm, field, data[field])

        storm.updated_at = datetime.utcnow()

        db.session.commit()

        success, response = input_calculations(project_id, data)

        if not success:
            return error_response(400, "CalculationError", response)

        return jsonify({
            "message": "Stormwater input updated successfully"
        }), 200

    except Exception:
        db.session.rollback()
        logger.exception(f"Unhandled error on update input | project_id={project_id}")
        return error_response(500, "InternalServerError", "Something went wrong")