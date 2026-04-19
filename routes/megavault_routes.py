

from flask import Blueprint, request, jsonify
from processes.megavault_calculator import run_calculator
from extensions import db
from models.megavault_input import MegavaultInput
from models.megavault_output import MegavaultOutput
from sqlalchemy.exc import SQLAlchemyError
import logging
from flask_jwt_extended import get_jwt, jwt_required

from utils.error_response import error_response

megavault_bp = Blueprint("megavault_bp", __name__)
logger = logging.getLogger(__name__)

ALLOWED_ROLES = ["CUSTOMER","ADMIN"]



# ==========================================================
# REQUIRED FIELDS
# ==========================================================
REQUIRED_FIELDS = [
    "rows",
    "cols",
    "grid",
    "internal_height",
    "max_storage_height",
    "tank_grade",
    "direction",
    "target_volume",
    "head_chamber",
    "hed_volume",
    "filter_volume",
    "osd_invert_level"
]


def validate_calculator_input(data: dict) -> list[str]:
    return [field for field in REQUIRED_FIELDS if field not in data]


# ==========================================================
# GRID NORMALIZATION (GLOBAL HELPER)
# ==========================================================
def normalize_grid(grid, rows, cols):
    full_grid = [[0 for _ in range(cols)] for _ in range(rows)]

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            full_grid[i][j] = grid[i][j]

    return full_grid


# ==========================================================
# UPSERT OUTPUT
# ==========================================================
def _upsert_output(project_id, input_id, result: dict):
    record = MegavaultOutput.query.filter_by(input_id=input_id).first()

    if record:
        record.selected_modules = result["selected_modules"]
        record.modules_required = result["modules_required"]
        record.tank_length = result["tank_length"]
        record.tank_width = result["tank_width"]
        record.min_storage_height = result["min_storage_height"]
        record.effective_storage_height = result["effective_storage_height"]
        record.total_volume_per_base = result["total_volume_per_base"]
        record.effective_volume_per_base = result["effective_volume_per_base"]
        record.proposed_total_volume = result["proposed_total_volume"]
        record.proposed_effective_volume = result["proposed_effective_volume"]
        record.elevations = result["elevations"]
        record.surface_areas = result["surface_areas"]
    else:
        record = MegavaultOutput(
            project_id=project_id,
            input_id=input_id,
            selected_modules=result["selected_modules"],
            modules_required=result["modules_required"],
            tank_length=result["tank_length"],
            tank_width=result["tank_width"],
            min_storage_height=result["min_storage_height"],
            effective_storage_height=result["effective_storage_height"],
            total_volume_per_base=result["total_volume_per_base"],
            effective_volume_per_base=result["effective_volume_per_base"],
            proposed_total_volume=result["proposed_total_volume"],
            proposed_effective_volume=result["proposed_effective_volume"],
            elevations=result["elevations"],
            surface_areas=result["surface_areas"],
        )
        db.session.add(record)

    return record


@megavault_bp.route("/preview", methods=["PATCH"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def preview_calculation():

    data = request.get_json()

    grid = normalize_grid(data["grid"], data["rows"], data["cols"])

    results = run_calculator(
        grid=grid,
        rows=data["rows"],
        cols=data["cols"],
        internal_height=data["internal_height"],
        max_storage_height=data["max_storage_height"],
        tank_grade_percent=data["tank_grade"],
        direction=data["direction"],
        target_volume=data["target_volume"],
        head_chamber=data["head_chamber"],
        filter_volume=data["filter_volume"],
        osd_invert_level=data["osd_invert_level"],
        hed_volume=data["hed_volume"]
    )

    return jsonify({
        "msg": "Preview calculation",
        "results": results
    }), 200


# ==========================================================
# POST CALCULATE
# ==========================================================
@megavault_bp.route("/<uuid:project_id>/calculate", methods=["POST"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def calculate(project_id):
    try:
        data = request.get_json()

        if not data:
            return error_response(400, "ValidationError", "Request body is missing")

        missing = validate_calculator_input(data)
        if missing:
            return error_response(
                400,
                "ValidationError",
                f"Missing required fields: {', '.join(missing)}"
            )

        rows = data["rows"]
        cols = data["cols"]

        grid = normalize_grid(data["grid"], rows, cols)

     
        results = run_calculator(
            grid=grid,
            rows=rows,
            cols=cols,
            internal_height=data["internal_height"],
            max_storage_height=data["max_storage_height"],
            tank_grade_percent=data["tank_grade"],
            direction=data["direction"],
            target_volume=data["target_volume"],
            head_chamber=data["head_chamber"],
            filter_volume=data["filter_volume"],
            osd_invert_level=data["osd_invert_level"],
            hed_volume=data["hed_volume"]
        )

        # UPSERT INPUT
        input_record = MegavaultInput.query.filter_by(project_id=project_id).first()

        if input_record:
            input_record.grid = data["grid"]
            input_record.direction = data["direction"]
            input_record.internal_height = data["internal_height"]
            input_record.max_storage_height = data["max_storage_height"]
            input_record.tank_grade = data["tank_grade"]
            input_record.target_volume = data["target_volume"]
            input_record.head_chamber = data["head_chamber"]
            input_record.filter_volume = data["filter_volume"]
            input_record.hed_volume = data["hed_volume"]
            input_record.osd_invert_level = data["osd_invert_level"]
        else:
            input_record = MegavaultInput(
                project_id=project_id,
                grid=data["grid"],
                direction=data["direction"],
                internal_height=data["internal_height"],
                max_storage_height=data["max_storage_height"],
                tank_grade=data["tank_grade"],
                target_volume=data["target_volume"],
                head_chamber=data["head_chamber"],
                filter_volume=data["filter_volume"],
                hed_volume=data["hed_volume"],
                osd_invert_level=data["osd_invert_level"]
            )
            db.session.add(input_record)

        db.session.flush()

        _upsert_output(project_id, input_record.id, results)

        db.session.commit()

        return jsonify({
            "msg": "Calculation successful",
            "project_id": str(project_id),
            "results": results
        }), 200

    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error")
        return error_response(
            500,
            "DatabaseError",
            "A database error occurred"
        )

    except Exception:
        db.session.rollback()
        logger.exception("Calculate error")
        return error_response(
            500,
            "InternalServerError",
            "Something went wrong"
        )



@megavault_bp.route("/<uuid:project_id>", methods=["GET"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def get_megavault(project_id):
    try:
        input_record = MegavaultInput.query.filter_by(project_id=project_id).first()

        if not input_record:
            return error_response(
                404,
                "MegavaultNotFound",
                "No megavault configuration found"
            )

        output_record = MegavaultOutput.query.filter_by(input_id=input_record.id).first()

        return jsonify({
            "msg": "Megavault data fetched successfully",
            "input": {
                "grid": input_record.grid,
                "direction": input_record.direction,
                "internal_height": input_record.internal_height,
                "max_storage_height": input_record.max_storage_height,
                "tank_grade": input_record.tank_grade,
                "target_volume": input_record.target_volume,
                "head_chamber": input_record.head_chamber,
                "hed_volume": input_record.hed_volume,
                "filter_volume": input_record.filter_volume,
                "osd_invert_level": input_record.osd_invert_level
            },
            "output": None if not output_record else {
                "selected_modules": output_record.selected_modules,
                "modules_required": output_record.modules_required,
                "tank_length": output_record.tank_length,
                "tank_width": output_record.tank_width,
                "min_storage_height": output_record.min_storage_height,
                "effective_storage_height": output_record.effective_storage_height,
                "total_volume_per_base": output_record.total_volume_per_base,
                "effective_volume_per_base": output_record.effective_volume_per_base,
                "proposed_total_volume": output_record.proposed_total_volume,
                "proposed_effective_volume": output_record.proposed_effective_volume,
                "elevations": output_record.elevations,
                "surface_areas": output_record.surface_areas
            }
        }), 200

    except Exception:
        logger.exception("Get megavault error")
        return error_response(
            500,
            "InternalServerError",
            "Something went wrong"
        )
 