

# # from flask import Blueprint, request, jsonify
# # from models.user import User
# # from extensions import db
# # from flask_jwt_extended import create_access_token
# # from datetime import timedelta
# # from sqlalchemy.exc import SQLAlchemyError
# # from werkzeug.security import check_password_hash
# # import logging

# # auth_bp = Blueprint('auth', __name__)
# # logger = logging.getLogger(__name__)
# # @auth_bp.route("/login", methods=["POST"])
# # def login():
# #     try:


# #         data = request.get_json(force=True)

# #         if not data:
      
# #             return jsonify({"msg": "Request body is missing"}), 400

# #         email = data.get("email")
# #         password = data.get("password")



# #         if not email or not password:

# #             return jsonify({"msg": "Email and Password are required"}), 400


# #         print("Trying DB Engine Connect")
# #         db.engine.connect()
# #         print("DB Connected Successfully")

# #         user = User.query.filter_by(email=email).first()

# #         if not user:

# #             return jsonify({"msg": "Invalid email or password"}), 401

# #         if not check_password_hash(user.password, password):

# #             return jsonify({"msg": "Invalid email or password"}), 401

# #         access_token = create_access_token(
# #             identity=str(user.id),
# #             additional_claims={
# #                 "email": user.email,
# #                 "role": user.role
# #             },
# #             expires_delta=timedelta(hours=5)
# #         )

# #         return jsonify({
# #             "token": access_token,
# #             "role": user.role,
# #             "email": user.email
# #         }), 200

# #     except SQLAlchemyError as db_err:
# #         db.session.rollback()
# #         return jsonify({"msg": "Database error occurred"}), 500

# #     except Exception as e:
# #         return jsonify({"msg": "Internal Server Error"}), 500

# from flask import Blueprint, request, jsonify, current_app
# from models.user import User, Role, UserRole
# from extensions import db
# from werkzeug.security import check_password_hash
# from flask_jwt_extended import create_access_token
# import datetime

# auth_bp = Blueprint("auth_bp", __name__)


# # ===============================
# # LOGIN API (RBAC READY)
# # ===============================
# @auth_bp.route("/login", methods=["POST"])
# def login():

#     try:

#         data = request.get_json()

#         if not data:
#             return jsonify({
#                 "msg": "Request body missing"
#             }), 400

#         email = data.get("email")
#         password = data.get("password")

#         if not email or not password:
#             return jsonify({
#                 "msg": "Email and Password required"
#             }), 400


#         # ---------------------------
#         # Check User
#         # ---------------------------
#         user = User.query.filter_by(
#             email=email,
#             del_flg=False,
#             is_active=True
#         ).first()

#         if not user:
#             return jsonify({
#                 "msg": "Invalid Email"
#             }), 401


#         # ---------------------------
#         # Check Password
#         # ---------------------------
#         if not check_password_hash(
#             user.password_hash,
#             password
#         ):
#             return jsonify({
#                 "msg": "Invalid Password"
#             }), 401


#         # ---------------------------
#         # FETCH ALL ROLES
#         # ---------------------------
#         roles = db.session.query(Role.role_name)\
#             .join(UserRole,
#             Role.id == UserRole.role_id)\
#             .filter(UserRole.user_id == user.id)\
#             .all()

#         role_list = [r[0] for r in roles]

#         if not role_list:
#             return jsonify({
#                 "msg": "User has no assigned role"
#             }), 403


#         # ---------------------------
#         # JWT PAYLOAD
#         # ---------------------------
#         token = create_access_token(
#     identity=str(user.id),
#     additional_claims={
#         "email": user.email,
#         "roles": role_list
#     }
# )


#         # ---------------------------
#         # RESPONSE
#         # ---------------------------
#         return jsonify({
#             "access_token": token,
#             "user": {
#                 "id": str(user.id),
#                 "first_name": user.first_name,
#                 "last_name": user.last_name,
#                 "email": user.email,
#                 "roles": role_list
#             }
#         }), 200


#     except Exception as e:

#         db.session.rollback()

#         print("LOGIN ERROR:", str(e))

#         return jsonify({
#             "msg": "Login Failed",
#             "error": str(e)
#         }), 500