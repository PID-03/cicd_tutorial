# from flask import Blueprint, request, jsonify
# from extensions import db
# from models.ifd_data import IFDRegion, IFDRegionData
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.dialects.postgresql import insert
# from sqlalchemy import func
# import logging
# from datetime import datetime

# ifd_bp = Blueprint("ifd", __name__)
# logger = logging.getLogger(__name__)


# # ==========================================================
# # CREATE NEW REGION + DATA
# # ==========================================================
# @ifd_bp.route("/ifd-region", methods=["POST"])
# def create_region_with_data():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"msg": "Request body is missing"}), 400

#         region_name = data.get("region_name")
#         rainfall_data = data.get("data")

#         if not region_name or not rainfall_data:
#             return jsonify({"msg": "Region name and data are required"}), 400

#         # Only check active regions
#         existing_region = IFDRegion.query.filter_by(
#             name=region_name,
#             is_deleted=False
#         ).first()

#         if existing_region:
#             return jsonify({"msg": "Region already exists"}), 409

#         region = IFDRegion(name=region_name)
#         db.session.add(region)
#         db.session.flush()  # get region.id before commit

#         for item in rainfall_data:
#             duration = item.get("duration_minutes")
#             values = item.get("values")

#             if not duration or not values:
#                 continue

#             for aep, intensity in values.items():
#                 record = IFDRegionData(
#                     region_id=region.id,
#                     duration_minutes=int(duration),
#                     aep_percentage=float(aep),
#                     intensity=float(intensity)
#                 )
#                 db.session.add(record)

#         db.session.commit()

#         return jsonify({
#             "msg": "Region created successfully",
#             "region_name": region.name,
#             "region_number": region.region_number
#         }), 201

#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Create Region Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


# @ifd_bp.route("/ifd-region/<string:region_name>", methods=["PUT"])
# def update_region_data(region_name):
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"msg": "Request body is missing"}), 400

#         rainfall_data = data.get("data")
#         if not rainfall_data:
#             return jsonify({"msg": "Data is required"}), 400

#         region = IFDRegion.query.filter_by(
#             name=region_name,
#             is_deleted=False
#         ).first()

#         if not region:
#             return jsonify({"msg": "Region not found"}), 404

#         records_to_insert = []

#         for item in rainfall_data:
#             duration = item.get("duration_minutes")
#             values = item.get("values")

#             if not duration or not values:
#                 continue

#             for aep, intensity in values.items():
#                 records_to_insert.append({
#                     "region_id": region.id,
#                     "duration_minutes": int(duration),
#                     "aep_percentage": float(aep),
#                     "intensity": float(intensity),
#                     "is_deleted": False
#                 })

#         stmt = insert(IFDRegionData).values(records_to_insert)

#         stmt = stmt.on_conflict_do_update(
#             index_elements=[
#                 "region_id",
#                 "duration_minutes",
#                 "aep_percentage"
#             ],
#             set_={
#                 "intensity": stmt.excluded.intensity,
#                 "is_deleted": False,
#                 "updated_at": func.now()
#             }
#         )

#         db.session.execute(stmt)
#         db.session.commit()

#         return jsonify({"msg": "Region data updated successfully"}), 200

#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Update Region Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


# # ==========================================================
# # RENAME REGION
# # ==========================================================
# @ifd_bp.route("/ifd-region/<string:region_name>/rename", methods=["PATCH"])
# def rename_region(region_name):
#     try:
#         data = request.get_json()
#         new_name = data.get("new_name")

#         if not new_name:
#             return jsonify({"msg": "New region name required"}), 400

#         region = IFDRegion.query.filter_by(
#             name=region_name,
#             is_deleted=False
#         ).first()

#         if not region:
#             return jsonify({"msg": "Region not found"}), 404

#         # Prevent duplicate name
#         existing = IFDRegion.query.filter_by(
#             name=new_name,
#             is_deleted=False
#         ).first()

#         if existing:
#             return jsonify({"msg": "Region name already exists"}), 409

#         region.name = new_name
#         db.session.commit()

#         return jsonify({
#             "msg": "Region renamed successfully",
#             "new_name": new_name
#         }), 200

#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Rename Region Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


# # ==========================================================
# # GET REGION DATA (ACTIVE ONLY)
# # ==========================================================
# @ifd_bp.route("/ifd-region/<string:region_name>", methods=["GET"])
# def get_region_data(region_name):
#     try:
#         region = IFDRegion.query.filter_by(
#             name=region_name,
#             is_deleted=False
#         ).first()

#         if not region:
#             return jsonify({"msg": "Region not found"}), 404

#         records = IFDRegionData.query.filter_by(
#             region_id=region.id,
#             is_deleted=False
#         ).all()

#         response = [
#             {
#                 "duration_minutes": r.duration_minutes,
#                 "aep_percentage": r.aep_percentage,
#                 "intensity": r.intensity
#             }
#             for r in records
#         ]

#         return jsonify({
#             "region": region.name,
#             "region_id": region.id,
#             "data": response
#         }), 200

#     except Exception as e:
#         logger.error(f"Get Region Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


# # ==========================================================
# # SOFT DELETE REGION
# # ==========================================================
# @ifd_bp.route("/ifd-region/<string:region_name>", methods=["DELETE"])
# def soft_delete_region(region_name):
#     try:
#         region = IFDRegion.query.filter_by(
#             name=region_name,
#             is_deleted=False
#         ).first()

#         if not region:
#             return jsonify({"msg": "Region not found"}), 404

#         # Soft delete region
#         region.soft_delete()

#         # Soft delete related data
#         records = IFDRegionData.query.filter_by(
#             region_id=region.id,
#             is_deleted=False
#         ).all()

#         for record in records:
#             record.soft_delete()

#         db.session.commit()

#         return jsonify({"msg": "Region soft deleted successfully"}), 200

#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Soft Delete Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


# # ==========================================================
# # GET ALL ACTIVE REGIONS
# # ==========================================================
# @ifd_bp.route("/ifd-regions", methods=["GET"])
# def get_all_regions():
#     try:
#         regions = IFDRegion.query.filter_by(
#             is_deleted=False
#         ).all()

#         region_list = [
#             {
#                 "region_name": r.name,
#                 "region_id": r.id
#             }
#             for r in regions
#         ]

#         return jsonify({
#             "total_regions": len(region_list),
#             "regions": region_list
#         }), 200

#     except Exception as e:
#         logger.error(f"Get All Regions Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500



# from flask import Blueprint, request, jsonify
# from extensions import db
# from models.ifd_data import IFDRegion, IFDRegionData
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.dialects.postgresql import insert
# from sqlalchemy import func
# import logging
# from datetime import datetime

# ifd_bp = Blueprint("ifd", __name__)
# logger = logging.getLogger(__name__)


# # ==========================================================
# # CREATE NEW REGION + DATA
# # ==========================================================
# @ifd_bp.route("/ifd-region", methods=["POST"])
# def create_region_with_data():
#     """
#     Expected JSON body:
#     {
#         "region_name": "Victoria - Melbourne",
#         "latitude": -37.8136,       # optional
#         "longitude": 144.9631,      # optional
#         "data": [
#             {
#                 "duration_minutes": 10,
#                 "values": { "1": 50.5, "2": 40.0 }
#             }
#         ]
#     }
#     """
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"msg": "Request body is missing"}), 400

#         region_name  = data.get("region_name")
#         rainfall_data = data.get("data")
#         latitude     = data.get("latitude")
#         longitude    = data.get("longitude")

#         if not region_name or not rainfall_data:
#             return jsonify({"msg": "Region name and data are required"}), 400

#         # Validate coordinates if provided
#         if latitude is not None or longitude is not None:
#             try:
#                 latitude  = float(latitude)
#                 longitude = float(longitude)
#             except (TypeError, ValueError):
#                 return jsonify({"msg": "latitude and longitude must be numbers"}), 400

#         # Only check active regions
#         existing_region = IFDRegion.query.filter_by(
#             name=region_name,
#             is_deleted=False
#         ).first()

#         if existing_region:
#             return jsonify({"msg": "Region already exists"}), 409

#         region = IFDRegion(
#             name=region_name,
#             latitude=latitude,
#             longitude=longitude
#         )
#         db.session.add(region)
#         db.session.flush()  # get region.id before commit

#         for item in rainfall_data:
#             duration = item.get("duration_minutes")
#             values   = item.get("values")

#             if not duration or not values:
#                 continue

#             for aep, intensity in values.items():
#                 record = IFDRegionData(
#                     region_id=region.id,
#                     duration_minutes=int(duration),
#                     aep_percentage=float(aep),
#                     intensity=float(intensity)
#                 )
#                 db.session.add(record)

#         db.session.commit()

#         return jsonify({
#             "msg": "Region created successfully",
#             "region_name": region.name,
#             "region_number": region.region_number,
#             "latitude": region.latitude,
#             "longitude": region.longitude
#         }), 201

#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Create Region Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


# # ==========================================================
# # UPDATE REGION DATA (upsert rainfall rows)
# # ==========================================================
# @ifd_bp.route("/ifd-region/<string:region_name>", methods=["PUT"])
# def update_region_data(region_name):
#     """
#     Update rainfall data rows for an existing region.
#     Optionally update lat/lon by passing them in the body.

#     Expected JSON body:
#     {
#         "latitude": -33.8688,       # optional – update coordinates
#         "longitude": 151.2093,      # optional – update coordinates
#         "data": [
#             {
#                 "duration_minutes": 10,
#                 "values": { "1": 55.0 }
#             }
#         ]
#     }
#     """
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"msg": "Request body is missing"}), 400

#         rainfall_data = data.get("data")
#         if not rainfall_data:
#             return jsonify({"msg": "Data is required"}), 400

#         region = IFDRegion.query.filter_by(
#             name=region_name,
#             is_deleted=False
#         ).first()

#         if not region:
#             return jsonify({"msg": "Region not found"}), 404

#         # Update coordinates if provided
#         latitude  = data.get("latitude")
#         longitude = data.get("longitude")

#         if latitude is not None or longitude is not None:
#             try:
#                 if latitude is not None:
#                     region.latitude = float(latitude)
#                 if longitude is not None:
#                     region.longitude = float(longitude)
#             except (TypeError, ValueError):
#                 return jsonify({"msg": "latitude and longitude must be numbers"}), 400

#         records_to_insert = []

#         for item in rainfall_data:
#             duration = item.get("duration_minutes")
#             values   = item.get("values")

#             if not duration or not values:
#                 continue

#             for aep, intensity in values.items():
#                 records_to_insert.append({
#                     "region_id": region.id,
#                     "duration_minutes": int(duration),
#                     "aep_percentage": float(aep),
#                     "intensity": float(intensity),
#                     "is_deleted": False
#                 })

#         stmt = insert(IFDRegionData).values(records_to_insert)

#         stmt = stmt.on_conflict_do_update(
#             index_elements=[
#                 "region_id",
#                 "duration_minutes",
#                 "aep_percentage"
#             ],
#             set_={
#                 "intensity": stmt.excluded.intensity,
#                 "is_deleted": False,
#                 "updated_at": func.now()
#             }
#         )

#         db.session.execute(stmt)
#         db.session.commit()

#         return jsonify({
#             "msg": "Region data updated successfully",
#             "latitude": region.latitude,
#             "longitude": region.longitude
#         }), 200

#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Update Region Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


# # ==========================================================
# # RENAME REGION
# # ==========================================================
# @ifd_bp.route("/ifd-region/<string:region_name>/rename", methods=["PATCH"])
# def rename_region(region_name):
#     try:
#         data     = request.get_json()
#         new_name = data.get("new_name")

#         if not new_name:
#             return jsonify({"msg": "New region name required"}), 400

#         region = IFDRegion.query.filter_by(
#             name=region_name,
#             is_deleted=False
#         ).first()

#         if not region:
#             return jsonify({"msg": "Region not found"}), 404

#         # Prevent duplicate name
#         existing = IFDRegion.query.filter_by(
#             name=new_name,
#             is_deleted=False
#         ).first()

#         if existing:
#             return jsonify({"msg": "Region name already exists"}), 409

#         region.name = new_name
#         db.session.commit()

#         return jsonify({
#             "msg": "Region renamed successfully",
#             "new_name": new_name
#         }), 200

#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Rename Region Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


# # ==========================================================
# # GET SINGLE REGION DATA (ACTIVE ONLY)
# # ==========================================================
# @ifd_bp.route("/ifd-region/<string:region_name>", methods=["GET"])
# def get_region_data(region_name):
#     try:
#         region = IFDRegion.query.filter_by(
#             name=region_name,
#             is_deleted=False
#         ).first()

#         if not region:
#             return jsonify({"msg": "Region not found"}), 404

#         records = IFDRegionData.query.filter_by(
#             region_id=region.id,
#             is_deleted=False
#         ).all()

#         response = [
#             {
#                 "duration_minutes": r.duration_minutes,
#                 "aep_percentage": r.aep_percentage,
#                 "intensity": r.intensity
#             }
#             for r in records
#         ]

#         return jsonify({
#             "region": region.name,
#             "region_id": str(region.id),
#             "latitude": region.latitude,
#             "longitude": region.longitude,
#             "data": response
#         }), 200

#     except Exception as e:
#         logger.error(f"Get Region Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


# # ==========================================================
# # SOFT DELETE REGION
# # ==========================================================
# @ifd_bp.route("/ifd-region/<string:region_name>", methods=["DELETE"])
# def soft_delete_region(region_name):
#     try:
#         region = IFDRegion.query.filter_by(
#             name=region_name,
#             is_deleted=False
#         ).first()

#         if not region:
#             return jsonify({"msg": "Region not found"}), 404

#         region.soft_delete()

#         records = IFDRegionData.query.filter_by(
#             region_id=region.id,
#             is_deleted=False
#         ).all()

#         for record in records:
#             record.soft_delete()

#         db.session.commit()

#         return jsonify({"msg": "Region soft deleted successfully"}), 200

#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Soft Delete Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


# # ==========================================================
# # GET ALL ACTIVE REGIONS  (now includes lat / lon)
# # ==========================================================
# @ifd_bp.route("/ifd-regions", methods=["GET"])
# def get_all_regions():
#     try:
#         regions = IFDRegion.query.filter_by(
#             is_deleted=False
#         ).order_by(IFDRegion.region_number).all()

#         region_list = [
#             {
#                 "region_name": r.name,
#                 "region_id": str(r.id),
#                 "region_number": r.region_number,
#                 "latitude": r.latitude,
#                 "longitude": r.longitude
#             }
#             for r in regions
#         ]

#         return jsonify({
#             "total_regions": len(region_list),
#             "regions": region_list
#         }), 200

#     except Exception as e:
#         logger.error(f"Get All Regions Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500


from flask import Blueprint, request, jsonify
from extensions import db
from models.ifd_data import IFDRegion, IFDRegionData
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
import logging
import uuid
from datetime import datetime

ifd_bp = Blueprint("ifd", __name__)
logger = logging.getLogger(__name__)


# ==========================================================
# HELPER: Validate & parse UUID from URL
# ==========================================================
def parse_uuid(region_id: str):
    """Returns a UUID object or None if invalid."""
    try:
        return uuid.UUID(region_id)
    except (ValueError, AttributeError):
        return None


# ==========================================================
# CREATE NEW REGION + DATA
# ==========================================================
@ifd_bp.route("/ifd-region", methods=["POST"])
def create_region_with_data():
    """
    Expected JSON body:
    {
        "region_name": "Victoria - Melbourne",
        "latitude": -37.8136,
        "longitude": 144.9631,
        "data": [
            {
                "duration_minutes": 10,
                "values": { "1": 50.5, "2": 40.0 }
            }
        ]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Request body is missing"}), 400

        region_name   = data.get("region_name")
        rainfall_data = data.get("data")
        latitude      = data.get("latitude")
        longitude     = data.get("longitude")

        if not region_name or not rainfall_data:
            return jsonify({"msg": "Region name and data are required"}), 400

        # Validate coordinates if provided
        if latitude is not None or longitude is not None:
            try:
                latitude  = float(latitude)
                longitude = float(longitude)
            except (TypeError, ValueError):
                return jsonify({"msg": "latitude and longitude must be numbers"}), 400

        # Only check active regions
        existing_region = IFDRegion.query.filter_by(
            name=region_name,
            is_deleted=False
        ).first()

        if existing_region:
            return jsonify({"msg": "Region already exists"}), 409

        region = IFDRegion(
            name=region_name,
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(region)
        db.session.flush()  # get region.id before commit

        for item in rainfall_data:
            duration = item.get("duration_minutes")
            values   = item.get("values")

            if not duration or not values:
                continue

            for aep, intensity in values.items():
                record = IFDRegionData(
                    region_id=region.id,
                    duration_minutes=int(duration),
                    aep_percentage=float(aep),
                    intensity=float(intensity)
                )
                db.session.add(record)

        db.session.commit()

        return jsonify({
            "msg": "Region created successfully",
            "region_id": str(region.id),
            "region_name": region.name,
            "region_number": region.region_number,
            "latitude": region.latitude,
            "longitude": region.longitude
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Create Region Error: {str(e)}")
        return jsonify({"msg": "Something went wrong"}), 500


# ==========================================================
# UPDATE REGION DATA (upsert rainfall rows)  →  by UUID
# ==========================================================
@ifd_bp.route("/ifd-region/<string:region_id>", methods=["PUT"])
def update_region_data(region_id):
    """
    PUT /ifd-region/<uuid>

    Expected JSON body:
    {
        "latitude": -33.8688,
        "longitude": 151.2093,
        "data": [
            {
                "duration_minutes": 10,
                "values": { "1": 55.0 }
            }
        ]
    }
    """
    try:
        parsed_id = parse_uuid(region_id)
        if not parsed_id:
            return jsonify({"msg": "Invalid region UUID"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"msg": "Request body is missing"}), 400

        rainfall_data = data.get("data")
        if not rainfall_data:
            return jsonify({"msg": "Data is required"}), 400

        region = IFDRegion.query.filter_by(
            id=parsed_id,
            is_deleted=False
        ).first()

        if not region:
            return jsonify({"msg": "Region not found"}), 404

        # Update coordinates if provided
        latitude  = data.get("latitude")
        longitude = data.get("longitude")

        if latitude is not None or longitude is not None:
            try:
                if latitude is not None:
                    region.latitude = float(latitude)
                if longitude is not None:
                    region.longitude = float(longitude)
            except (TypeError, ValueError):
                return jsonify({"msg": "latitude and longitude must be numbers"}), 400

        records_to_insert = []

        for item in rainfall_data:
            duration = item.get("duration_minutes")
            values   = item.get("values")

            if not duration or not values:
                continue

            for aep, intensity in values.items():
                records_to_insert.append({
                    "region_id": region.id,
                    "duration_minutes": int(duration),
                    "aep_percentage": float(aep),
                    "intensity": float(intensity),
                    "is_deleted": False
                })

        stmt = insert(IFDRegionData).values(records_to_insert)

        stmt = stmt.on_conflict_do_update(
            index_elements=[
                "region_id",
                "duration_minutes",
                "aep_percentage"
            ],
            set_={
                "intensity": stmt.excluded.intensity,
                "is_deleted": False,
                "updated_at": func.now()
            }
        )

        db.session.execute(stmt)
        db.session.commit()

        return jsonify({
            "msg": "Region data updated successfully",
            "region_id": str(region.id),
            "region_name": region.name,
            "latitude": region.latitude,
            "longitude": region.longitude
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update Region Error: {str(e)}")
        return jsonify({"msg": "Something went wrong"}), 500


# ==========================================================
# RENAME REGION  →  by UUID
# ==========================================================
@ifd_bp.route("/ifd-region/<string:region_id>/rename", methods=["PATCH"])
def rename_region(region_id):
    """
    PATCH /ifd-region/<uuid>/rename

    Expected JSON body:
    {
        "new_name": "NSW - Sydney"
    }
    """
    try:
        parsed_id = parse_uuid(region_id)
        if not parsed_id:
            return jsonify({"msg": "Invalid region UUID"}), 400

        data     = request.get_json()
        new_name = data.get("new_name")

        if not new_name:
            return jsonify({"msg": "New region name required"}), 400

        region = IFDRegion.query.filter_by(
            id=parsed_id,
            is_deleted=False
        ).first()

        if not region:
            return jsonify({"msg": "Region not found"}), 404

        # Prevent duplicate name
        existing = IFDRegion.query.filter_by(
            name=new_name,
            is_deleted=False
        ).first()

        if existing:
            return jsonify({"msg": "Region name already exists"}), 409

        region.name = new_name
        db.session.commit()

        return jsonify({
            "msg": "Region renamed successfully",
            "region_id": str(region.id),
            "new_name": new_name
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Rename Region Error: {str(e)}")
        return jsonify({"msg": "Something went wrong"}), 500


# ==========================================================
# GET SINGLE REGION DATA  →  by UUID
# ==========================================================
@ifd_bp.route("/ifd-region/<string:region_id>", methods=["GET"])
def get_region_data(region_id):
    """
    GET /ifd-region/<uuid>
    """
    try:
        parsed_id = parse_uuid(region_id)
        if not parsed_id:
            return jsonify({"msg": "Invalid region UUID"}), 400

        region = IFDRegion.query.filter_by(
            id=parsed_id,
            is_deleted=False
        ).first()

        if not region:
            return jsonify({"msg": "Region not found"}), 404

        records = IFDRegionData.query.filter_by(
            region_id=region.id,
            is_deleted=False
        ).all()

        response = [
            {
                "duration_minutes": r.duration_minutes,
                "aep_percentage": r.aep_percentage,
                "intensity": r.intensity
            }
            for r in records
        ]

        return jsonify({
            "region_id": str(region.id),
            "region_name": region.name,
            "region_number": region.region_number,
            "latitude": region.latitude,
            "longitude": region.longitude,
            "data": response
        }), 200

    except Exception as e:
        logger.error(f"Get Region Error: {str(e)}")
        return jsonify({"msg": "Something went wrong"}), 500


# ==========================================================
# SOFT DELETE REGION  →  by UUID
# ==========================================================
@ifd_bp.route("/ifd-region/<string:region_id>", methods=["DELETE"])
def soft_delete_region(region_id):
    """
    DELETE /ifd-region/<uuid>
    """
    try:
        parsed_id = parse_uuid(region_id)
        if not parsed_id:
            return jsonify({"msg": "Invalid region UUID"}), 400

        region = IFDRegion.query.filter_by(
            id=parsed_id,
            is_deleted=False
        ).first()

        if not region:
            return jsonify({"msg": "Region not found"}), 404

        region.soft_delete()

        records = IFDRegionData.query.filter_by(
            region_id=region.id,
            is_deleted=False
        ).all()

        for record in records:
            record.soft_delete()

        db.session.commit()

        return jsonify({
            "msg": "Region soft deleted successfully",
            "region_id": str(region.id),
            "region_name": region.name
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Soft Delete Error: {str(e)}")
        return jsonify({"msg": "Something went wrong"}), 500


# ==========================================================
# GET ALL ACTIVE REGIONS
# ==========================================================
@ifd_bp.route("/ifd-regions", methods=["GET"])
def get_all_regions():
    """
    GET /ifd-regions
    """
    try:
        regions = IFDRegion.query.filter_by(
            is_deleted=False
        ).order_by(IFDRegion.region_number).all()

        region_list = [
            {
                "region_id": str(r.id),
                "region_name": r.name,
                "region_number": r.region_number,
                "latitude": r.latitude,
                "longitude": r.longitude
            }
            for r in regions
        ]

        return jsonify({
            "total_regions": len(region_list),
            "regions": region_list
        }), 200

    except Exception as e:
        logger.error(f"Get All Regions Error: {str(e)}")
        return jsonify({"msg": "Something went wrong"}), 500