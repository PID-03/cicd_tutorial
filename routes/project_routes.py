

# from flask import Blueprint, request, jsonify
# from sqlalchemy.orm import joinedload
# from extensions import db
# from models.project import CalculatorType, Project, ProjectStatus, normalize_enum
# from sqlalchemy.exc import SQLAlchemyError
# import uuid
# from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt
# from models.user import User, UserRole
# from utils.enum_value import enum_to_value
# from utils.role_required import role_required


# project_bp = Blueprint("projects", __name__)

# ALLOWED_ROLES = ["CUSTOMER","ADMIN"]


# # ==========================================================
# # SERIALIZER
# # ==========================================================
# def serialize_project(project):
#     return {
#         "id": str(project.id),
#         "project_name": project.project_name,
#         "project_address": project.project_address,
#         "client_name": project.client_name,
#         "rainfall_location_id": str(project.rainfall_location_id) if project.rainfall_location_id else None,
#         "calculator_type": enum_to_value(project.calculator_type),
#         "status": enum_to_value(project.status),
#         "volume_known": project.volume_known,

      
#         "user_id": str(project.user_id) if project.user_id else None,

#         "created_at": project.created_at.isoformat() if project.created_at else None,
#         "updated_at": project.updated_at.isoformat() if project.updated_at else None,
#     }


# # ==========================================================
# # CREATE PROJECT
# # ==========================================================
# @project_bp.route("/", methods=["POST"])
# @jwt_required()
# def create_project():
#     try:
#         data = request.get_json()

#         if not data:
#             return jsonify({"error": "Request body is required"}), 400

#         if not data.get("project_name"):
#             return jsonify({"error": "project_name is required"}), 400

#         if not data.get("calculator_type"):
#             return jsonify({"error": "calculator_type is required"}), 400

#         current_user_id = uuid.UUID(get_jwt_identity())

#         # ✅ Validate calculator_type
#         try:
#             calculator_type = normalize_enum(CalculatorType, data.get("calculator_type"))
#         except ValueError:
#             return jsonify({
#                 "error": "Invalid calculator_type",
#                 "allowed": [e.value for e in CalculatorType]
#             }), 400

#         # ✅ Validate status (optional)
#         status = ProjectStatus.DRAFT

#         if data.get("status"):
#             try:
#                 status = normalize_enum(ProjectStatus, data.get("status"))
#             except ValueError:
#                 return jsonify({
#                     "error": "Invalid status",
#                     "allowed": [e.value for e in ProjectStatus]
#                 }), 400

#         # ✅ Duplicate check
#         existing = Project.query.filter_by(
#             project_name=data.get("project_name"),
#             user_id=current_user_id,
#             del_flg=False
#         ).first()

#         if existing:
#             return jsonify({
#                 "error": "Project already exists",
#                 "details": f"A project named '{data.get('project_name')}' already exists for this user."
#             }), 409

#         # ✅ Create project with ENUM values
#         project = Project(
#     project_name=data.get("project_name"),
#     project_address=data.get("project_address"),
#     client_name=data.get("client_name"),
#     rainfall_location_id=uuid.UUID(data["rainfall_location_id"]) if data.get("rainfall_location_id") else None,

#     calculator_type=calculator_type.value,  
#     status=status.value,                   

#     volume_known=data.get("volume_known", False),
#     user_id=current_user_id,
# )

#         db.session.add(project)
#         db.session.commit()

#         return jsonify({
#             "message": "Project created successfully",
#             "project_id": str(project.id)
#         }), 201

#     except ValueError:
#         db.session.rollback()
#         return jsonify({"error": "Invalid UUID format"}), 400

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({
#             "error": "Database error",
#             "details": str(e)
#         }), 500

# # ==========================================================
# # GET ALL PROJECTS (SOFT DELETE FILTERED)
# # ==========================================================
# # @project_bp.route("/", methods=["GET"])
# # @jwt_required()
# # # @role_required(*ALLOWED_ROLES)
# # def get_projects():
# #     try:
# #         projects = (
# #             Project.query
# #             .filter_by(del_flg=False)
# #             .order_by(Project.created_at.desc())
# #             .all()
# #         )

# #         return jsonify([
# #             serialize_project(project) for project in projects
# #         ]), 200

# #     except Exception as e:
# #         return jsonify({
# #             "error": "Internal Server Error",
# #             "details": str(e)
# #         }), 500
    

# # @project_bp.route("/", methods=["GET"])
# # @jwt_required()
# # def get_user_projects():
# #     try:
# #         current_user_id = uuid.UUID(get_jwt_identity())

# #         # ✅ Query params
# #         page = int(request.args.get("page", 1))
# #         per_page = int(request.args.get("per_page", 8))

# #         user = db.session.query(User).options(
# #             joinedload(User.user_roles).joinedload(UserRole.role)
# #         ).get(current_user_id)

# #         if not user:
# #             return jsonify({"error": "User not found"}), 404

# #         roles = [ur.role.role_name.lower() for ur in user.user_roles]
# #         is_super_admin = "super_admin" in roles

# #         # ✅ Base query
# #         query = Project.query.filter_by(del_flg=False)

# #         if not is_super_admin:
# #             query = query.filter_by(user_id=current_user_id)

# #         query = query.order_by(Project.created_at.desc())

# #         # ✅ Pagination
# #         pagination = query.paginate(page=page, per_page=per_page, error_out=False)

# #         projects = pagination.items

# #         return jsonify({
# #             "data": [serialize_project(p) for p in projects],
# #             "pagination": {
# #                 "page": page,
# #                 "per_page": per_page,
# #                 "total": pagination.total,
# #                 "pages": pagination.pages,
# #                 "has_next": pagination.has_next,
# #                 "has_prev": pagination.has_prev
# #             }
# #         }), 200

# #     except Exception as e:
# #         return jsonify({
# #             "error": "Internal Server Error",
# #             "details": str(e)
# #         }), 500
# @project_bp.route("/", methods=["GET"])
# @jwt_required()
# def get_user_projects():
#     try:
#         current_user_id = uuid.UUID(get_jwt_identity())

#         # ✅ Query params
#         page = int(request.args.get("page", 1))
#         per_page = int(request.args.get("per_page", 8))

#         user = db.session.query(User).options(
#             joinedload(User.user_roles).joinedload(UserRole.role)
#         ).get(current_user_id)

#         if not user:
#             return jsonify({"error": "User not found"}), 404

#         roles = [ur.role.role_name.lower() for ur in user.user_roles]
#         is_super_admin = "super_admin" in roles

#         # ✅ Base query
#         query = Project.query.filter_by(del_flg=False)

#         if not is_super_admin:
#             query = query.filter_by(user_id=current_user_id)

#         query = query.order_by(Project.created_at.desc())

#         # ✅ Pagination
#         pagination = query.paginate(page=page, per_page=per_page, error_out=False)

#         projects = pagination.items

#         return jsonify({
#             "data": [serialize_project(p) for p in projects],
#             "pagination": {
#                 "page": page,
#                 "per_page": per_page,
#                 "total": pagination.total,
#                 "pages": pagination.pages,
#                 "has_next": pagination.has_next,
#                 "has_prev": pagination.has_prev
#             }
#         }), 200

#     except Exception as e:
#         return jsonify({
#             "error": "Internal Server Error",
#             "details": str(e)
#         }), 500

        


# # ==========================================================
# # GET SINGLE PROJECT
# # ==========================================================
# @project_bp.route("/<uuid:project_id>", methods=["GET"])
# @jwt_required()
# # @role_required(*ALLOWED_ROLES)
# def get_project(project_id):
#     try:
#         project = Project.query.filter_by(
#             id=project_id,
#             del_flg=False
#         ).first()

#         if not project:
#             return jsonify({"error": "Project not found"}), 404

#         return jsonify(serialize_project(project)), 200

#     except Exception as e:
#         return jsonify({
#             "error": "Internal Server Error",
#             "details": str(e)
#         }), 500


# # ==========================================================
# # UPDATE PROJECT
# # ==========================================================
# @project_bp.route("/<uuid:project_id>", methods=["PATCH"])
# @jwt_required()
# def update_project(project_id):
#     try:
#         current_user_id = uuid.UUID(get_jwt_identity())

#         project = Project.query.filter_by(
#             id=project_id,
#             del_flg=False
#         ).first()

#         if not project:
#             return jsonify({"error": "Project not found"}), 404

#         # ✅ Optional ownership check
#         if project.user_id != current_user_id:
#             return jsonify({"error": "Unauthorized"}), 403

#         data = request.get_json()

#         if not data:
#             return jsonify({"error": "Request body is required"}), 400

#         allowed_fields = [
#             "project_name",
#             "project_address",
#             "client_name",
#             "rainfall_location_id",
#             "calculator_type",
#             "status",
#         ]

#         for field in allowed_fields:
#             if field in data:

#                 if field == "rainfall_location_id":
#                     setattr(
#                         project,
#                         field,
#                         uuid.UUID(data[field]) if data[field] else None
#                     )

#                 elif field == "calculator_type":
#                     try:
#                         enum_val = normalize_enum(CalculatorType, data[field])
#                         setattr(project, field, enum_val.value)  # ✅ FIX
#                     except ValueError:
#                         return jsonify({
#                             "error": "Invalid calculator_type",
#                             "allowed": [e.value for e in CalculatorType]
#                         }), 400

#                 elif field == "status":
#                     try:
#                         enum_val = normalize_enum(ProjectStatus, data[field])
#                         setattr(project, field, enum_val.value)  # ✅ FIX
#                     except ValueError:
#                         return jsonify({
#                             "error": "Invalid status",
#                             "allowed": [e.value for e in ProjectStatus]
#                         }), 400

#                 else:
#                     setattr(project, field, data[field])

#         db.session.commit()

#         return jsonify({
#             "message": "Project updated successfully",
#             "data": serialize_project(project)
#         }), 200

#     except ValueError:
#         db.session.rollback()
#         return jsonify({"error": "Invalid UUID format"}), 400

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({
#             "error": "Database error",
#             "details": str(e)
#         }), 500


# # ==========================================================
# # SOFT DELETE PROJECT
# # ==========================================================
# @project_bp.route("/<uuid:project_id>", methods=["DELETE"])
# @jwt_required()
# def delete_project(project_id):
#     try:
#         current_user_id = uuid.UUID(get_jwt_identity())

#         project = Project.query.filter_by(
#             id=project_id,
#             del_flg=False
#         ).first()

#         if not project:
#             return jsonify({"error": "Project not found"}), 404

#         # ✅ Optional: ownership check (IMPORTANT)
#         if project.user_id != current_user_id:
#             return jsonify({"error": "Unauthorized"}), 403

#         # ✅ Soft delete
#         project.del_flg = True

#         db.session.commit()

#         return jsonify({
#             "message": "Project deleted successfully"
#         }), 200

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({
#             "error": "Internal Server Error",
#             "details": str(e)
#         }), 500

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from extensions import db
from models.project import CalculatorType, Project, ProjectStatus, normalize_enum
from sqlalchemy.exc import SQLAlchemyError
import uuid
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt
from models.user import User, UserRole
from utils.enum_value import enum_to_value
from utils.role_required import role_required
from utils.error_response import error_response  # ✅ ADDED


project_bp = Blueprint("projects", __name__)

ALLOWED_ROLES = ["CUSTOMER","ADMIN"]


# ==========================================================
# SERIALIZER
# ==========================================================
def serialize_project(project):
    return {
        "id": str(project.id),
        "project_name": project.project_name,
        "project_address": project.project_address,
        "client_name": (
            f"{project.customer.first_name} {project.customer.last_name or ''}".strip()
            if project.customer else None
        ),
        "rainfall_location_id": str(project.rainfall_location_id) if project.rainfall_location_id else None,
        "calculator_type": enum_to_value(project.calculator_type),
        "status": enum_to_value(project.status),
        "volume_known": project.volume_known,
        "user_id": str(project.user_id) if project.user_id else None,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


# ==========================================================
# CREATE PROJECT
# ==========================================================

@project_bp.route("/", methods=["POST"])
@jwt_required()
def create_project():
    try:
        data = request.get_json()

        if not data:
            return error_response(400, "ValidationError", "Request body is required")  # ✅

        if not data.get("project_name"):
            return error_response(400, "ValidationError", "project_name is required")  # ✅

        if not data.get("calculator_type"):
            return error_response(400, "ValidationError", "calculator_type is required")  # ✅

        current_user_id = uuid.UUID(get_jwt_identity())

        try:
            calculator_type = normalize_enum(CalculatorType, data.get("calculator_type"))
        except ValueError:
            return error_response(  # ✅
                400,
                "ValidationError",
                f"Invalid calculator_type. Allowed values: {[e.value for e in CalculatorType]}"
            )

        status = ProjectStatus.DRAFT

        if data.get("status"):
            try:
                status = normalize_enum(ProjectStatus, data.get("status"))
            except ValueError:
                return error_response(  # ✅
                    400,
                    "ValidationError",
                    f"Invalid status. Allowed values: {[e.value for e in ProjectStatus]}"
                )

        existing = Project.query.filter_by(
            project_name=data.get("project_name"),
            user_id=current_user_id,
            del_flg=False
        ).first()

        if existing:
            return error_response(  # ✅
                409,
                "ConflictError",
                f"A project named '{data.get('project_name')}' already exists for this user."
            )

        project = Project(
    project_name=data.get("project_name"),
    project_address=data.get("project_address"),
    # client_name=data.get("client_name"),
    customer_id=uuid.UUID(data["customer_id"]) if data.get("customer_id") else None,
    rainfall_location_id=uuid.UUID(data["rainfall_location_id"]) if data.get("rainfall_location_id") else None,

    calculator_type=calculator_type.value,  
    status=status.value,                   

    volume_known=data.get("volume_known", False),
    user_id=current_user_id,
)

        db.session.add(project)
        db.session.commit()

        return jsonify({
            "message": "Project created successfully",
            "project_id": str(project.id)
        }), 201

    except ValueError:
        db.session.rollback()
        return error_response(400, "ValidationError", "Invalid UUID format")  # ✅

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(500, "DatabaseError", "A database error occurred")  # ✅


# ==========================================================
# GET ALL PROJECTS
# ==========================================================
# @project_bp.route("/", methods=["GET"])
# @jwt_required()
# # @role_required(*ALLOWED_ROLES)
# def get_projects():
#     try:
#         projects = (
#             Project.query
#             .filter_by(del_flg=False)
#             .order_by(Project.created_at.desc())
#             .all()
#         )

#         return jsonify([
#             serialize_project(project) for project in projects
#         ]), 200

#     except Exception as e:
#         return jsonify({
#             "error": "Internal Server Error",
#             "details": str(e)
#         }), 500
    

# @project_bp.route("/", methods=["GET"])
# @jwt_required()
# def get_user_projects():
#     try:
#         current_user_id = uuid.UUID(get_jwt_identity())

#         # ✅ Query params
#         page = int(request.args.get("page", 1))
#         per_page = int(request.args.get("per_page", 8))

#         user = db.session.query(User).options(
#             joinedload(User.user_roles).joinedload(UserRole.role)
#         ).get(current_user_id)

#         if not user:
#             return jsonify({"error": "User not found"}), 404

#         roles = [ur.role.role_name.lower() for ur in user.user_roles]
#         is_super_admin = "super_admin" in roles

#         # ✅ Base query
#         query = Project.query.filter_by(del_flg=False)

#         if not is_super_admin:
#             query = query.filter_by(user_id=current_user_id)

#         query = query.order_by(Project.created_at.desc())

#         # ✅ Pagination
#         pagination = query.paginate(page=page, per_page=per_page, error_out=False)

#         projects = pagination.items

#         return jsonify({
#             "data": [serialize_project(p) for p in projects],
#             "pagination": {
#                 "page": page,
#                 "per_page": per_page,
#                 "total": pagination.total,
#                 "pages": pagination.pages,
#                 "has_next": pagination.has_next,
#                 "has_prev": pagination.has_prev
#             }
#         }), 200

#     except Exception as e:
#         return jsonify({
#             "error": "Internal Server Error",
#             "details": str(e)
#         }), 500


@project_bp.route("/", methods=["GET"])
@jwt_required()
def get_user_projects():
    try:
        current_user_id = uuid.UUID(get_jwt_identity())

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 8))

        user = db.session.query(User).options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        ).get(current_user_id)

        if not user:
            return error_response(404, "NotFound", "User not found")  # ✅

        roles = [ur.role.role_name.lower() for ur in user.user_roles]
        is_super_admin = "super_admin" in roles

        query = Project.query.filter_by(del_flg=False)

        if not is_super_admin:
            query = query.filter_by(user_id=current_user_id)

        query = query.order_by(Project.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        projects = pagination.items

        return jsonify({
            "data": [serialize_project(p) for p in projects],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }), 200

    except Exception as e:
        return error_response(500, "InternalServerError", "Something went wrong")  # ✅


# ==========================================================
# GET SINGLE PROJECT
# ==========================================================
@project_bp.route("/<uuid:project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    try:
        project = Project.query.filter_by(
            id=project_id,
            del_flg=False
        ).first()

        if not project:
            return error_response(404, "NotFound", "Project not found")  # ✅

        return jsonify(serialize_project(project)), 200

    except Exception as e:
        return error_response(500, "InternalServerError", "Something went wrong")  # ✅


# ==========================================================
# UPDATE PROJECT
# ==========================================================
@project_bp.route("/<uuid:project_id>", methods=["PATCH"])
@jwt_required()
def update_project(project_id):
    try:
        current_user_id = uuid.UUID(get_jwt_identity())

        project = Project.query.filter_by(
            id=project_id,
            del_flg=False
        ).first()

        if not project:
            return error_response(404, "NotFound", "Project not found")  # ✅

        if project.user_id != current_user_id:
            return error_response(403, "Unauthorized", "You do not have permission to update this project")  # ✅

        data = request.get_json()

        if not data:
            return error_response(400, "ValidationError", "Request body is required")  # ✅

        allowed_fields = [
            "project_name",
            "project_address",
            "customer_id",
            "rainfall_location_id",
            "calculator_type",
            "status",
        ]

        for field in allowed_fields:
            if field in data:
                if field == "rainfall_location_id":
                    setattr(project, field, uuid.UUID(data[field]) if data[field] else None)

                elif field == "calculator_type":
                    try:
                        enum_val = normalize_enum(CalculatorType, data[field])
                        setattr(project, field, enum_val.value)
                    except ValueError:
                        return error_response(  # ✅
                            400,
                            "ValidationError",
                            f"Invalid calculator_type. Allowed values: {[e.value for e in CalculatorType]}"
                        )

                elif field == "status":
                    try:
                        enum_val = normalize_enum(ProjectStatus, data[field])
                        setattr(project, field, enum_val.value)
                    except ValueError:
                        return error_response(  # ✅
                            400,
                            "ValidationError",
                            f"Invalid status. Allowed values: {[e.value for e in ProjectStatus]}"
                        )

                else:
                    setattr(project, field, data[field])

        db.session.commit()

        return jsonify({
            "message": "Project updated successfully",
            "data": serialize_project(project)
        }), 200

    except ValueError:
        db.session.rollback()
        return error_response(400, "ValidationError", "Invalid UUID format")  # ✅

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(500, "DatabaseError", "A database error occurred")  # ✅


# ==========================================================
# SOFT DELETE PROJECT
# ==========================================================
@project_bp.route("/<uuid:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    try:
        current_user_id = uuid.UUID(get_jwt_identity())

        project = Project.query.filter_by(
            id=project_id,
            del_flg=False
        ).first()

        if not project:
            return error_response(404, "NotFound", "Project not found")  # ✅

        if project.user_id != current_user_id:
            return error_response(403, "Unauthorized", "You do not have permission to delete this project")  # ✅

        project.del_flg = True
        db.session.commit()

        return jsonify({"message": "Project deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return error_response(500, "InternalServerError", "Something went wrong")  # ✅