from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import jwt
import os

from extensions import db

# UserRole, UserSession,User, Role,
from models.user import User,UserSession,UserRole,Role

from flask_jwt_extended import get_jwt_identity, get_jwt
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from utils.error_response import error_response


# auth_bp = Blueprint("auth", __name__)

# SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret-key")


auth_bp = Blueprint("auth_bp", __name__)

from services.auth_service import AuthService
from validators.auth_validator import AuthValidator


@auth_bp.route("/signup", methods=["POST"])

def signup():
    try:
        data = request.get_json()

        valid, error = AuthValidator.validate_signup(data)
        if not valid:
            return error_response(400, "ValidationError", error)

        success, message = AuthService.signup(data)

        if not success:
            return error_response(400, "SignupError", message)

        return jsonify({
            "status": True,
            "msg": message
        }), 201

    except Exception as e:
        db.session.rollback()
        print("SIGNUP ERROR:", str(e))
    
      # 👈 important for debugging

        return error_response(
        500,
        "InternalServerError",
        str(e)   # now works
    )
    


@auth_bp.route("/customer-by-staff", methods=["POST"])
@jwt_required()
def create_customer_by_staff():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()

        valid, error = AuthValidator.validate_signup(data)
        if not valid:
            return error_response(400, "ValidationError", error)

        success, message = AuthService.create_by_staff(data, user_id)

        if not success:
            return error_response(400, "CustomerCreateError", message)

        return jsonify({
            "status": True,
            "msg": message
        }), 201

    except Exception as e:
        db.session.rollback()
        return error_response(500, "InternalServerError", "Failed to create customer")
    
@auth_bp.route("/customers", methods=["GET"])
@jwt_required()
def get_staff_customers():
    try:
        user_id = get_jwt_identity()
        search = request.args.get("search")

        success, data = AuthService.get_staff_customers(user_id,search)

        if not success:
            return error_response(403, "Forbidden", data)

        return jsonify({
            "status": True,
            "data": data
        }), 200

    except Exception as e:
        return error_response(500, "InternalServerError", str(e))
    

    
    
@auth_bp.route("/login", methods=["POST"])
def login_customer():
    return _handle_login("CUSTOMER")


@auth_bp.route("/login/staff", methods=["POST"])
def login_staff():
    return _handle_login("STAFF")

def _handle_login(expected_role):
    try:
        data = request.get_json()

        valid, error = AuthValidator.validate_login(data)
        if not valid:
            return error_response(400, "ValidationError", error)

        success, message, response = AuthService.login(
            data, request, expected_role
        )

        if not success:
            return error_response(401, "UnauthorizedError", message)

        return jsonify(response), 200

    except Exception as e:
        db.session.rollback()
        print("LOGIN ERROR:", str(e))
        return error_response(500, "InternalServerError", "Login Failed")

# @auth_bp.route("/login", methods=["POST"])
# # @jwt_required()
# def login():

#     try:

#         data = request.get_json()

#         # ---------------------------
#         # VALIDATION
#         # ---------------------------
#         valid, error = AuthValidator.validate_login(data)

#         if not valid:
#             return error_response(400, "ValidationError", error)
#         # ---------------------------
#         # SERVICE
#         # ---------------------------
#         success, message, response = AuthService.login(data, request)

#         if not success:
#             return error_response(401, "UnauthorizedError", message)

#         return jsonify(response), 200


#     except Exception as e:

#         db.session.rollback()

#         print("LOGIN ERROR:", str(e))

#         return error_response(500, "InternalServerError", "Login Failed")
    


@auth_bp.route("/internal-signup", methods=["POST"])
def internal_signup():
    try:
        data = request.get_json()

        # ---------------------------
        # VALIDATION
        # ---------------------------
        valid, error = AuthValidator.validate_internal_signup(data)
        if not valid:
            return error_response(400, "ValidationError", error)

        # ---------------------------
        # SERVICE
        # ---------------------------
        success, message = AuthService.internal_signup(data)

        if not success:
            return error_response(400, "InternalSignupError", message)

        return jsonify({
            "status": True,
            "msg": message
        }), 201

    except Exception as e:
        db.session.rollback()
        return error_response(
            500,
            "InternalServerError",
            "Internal Signup Failed"
        )


@auth_bp.route("/google-login", methods=["POST"])
def google_login():
    try:
        data = request.get_json()

        valid, error = AuthValidator.validate_google_login(data)
        if not valid:
            return error_response(400, "ValidationError", error)

        success, message, response = AuthService.google_login(data, request)

        if not success:
            return error_response(401, "GoogleAuthError", message)

        return jsonify(response), 200

    except Exception as e:
        db.session.rollback()
        return error_response(
            500,
            "InternalServerError",
            "Google Login Failed"
        )


@auth_bp.route("/me", methods=["GET", "OPTIONS"])
@jwt_required()
# @role_required(*ALLOWED_ROLES)
def get_me():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        user_id = get_jwt_identity()
        valid, error = AuthValidator.validate_get_me(user_id)

        if not valid:
            return error_response(400, "ValidationError", error)
       

        success, message, response = AuthService.get_me(user_id)
        if not success:
            return error_response(404, "UserNotFound", message)

        return jsonify(response), 200
    except Exception as e:
        return error_response(
            500,
            "InternalServerError",
            "Internal server error"
        )
    
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = request.get_json()
        valid, error = AuthValidator.validate_forgot_password(data)
        if not valid:
            return jsonify({
                "status": False,
                "msg": error
            }), 400
        
        
        success, message = AuthService.forgot_password(data)
        if not success:
            return error_response(404, "UserNotFound", message)
        
        return jsonify({
            "status": True,
            "msg": message
        }), 200
    except Exception as e:
        db.session.rollback()
        return error_response(
            500,
            "InternalServerError",
            "Forgot Password Failed"
        )
    
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():

    try:
        data = request.get_json()

       
        valid, error = AuthValidator.validate_reset_password(data)

        if not valid:
            return error_response(400, "ValidationError", error)

       
        success, message = AuthService.reset_password(data)

        if not success:
            return error_response(400, "ResetPasswordError", message)

        return jsonify({
            "status": True,
            "msg": message
        }), 200

    except Exception as e:
        return error_response(
            500,
            "InternalServerError",
            "Failed to reset password"
        )
    
