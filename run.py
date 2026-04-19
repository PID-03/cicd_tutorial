from authlib.jose import jwt
from flask import Flask
from config import Config
from extensions import db
from routes import register_routes
from flask_jwt_extended import JWTManager
from utils.error_response import error_response
from utils.logging import setup_logging
from flask_cors import CORS 
from flask_mail import Mail


jwt = JWTManager()
@jwt.unauthorized_loader
def unauthorized_callback(err):
    return error_response(401, "UnauthorizedError", "Missing token")


@jwt.invalid_token_loader
def invalid_token_callback(err):
    return error_response(401, "UnauthorizedError", "Invalid token")


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return error_response(401, "TokenExpired", "Token has expired")


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return error_response(401, "TokenRevoked", "Token has been revoked")

mail = Mail()
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    db.init_app(app)
    jwt.init_app(app)
    # jwt = JWTManager(app)
    mail.init_app(app)
    # with app.app_context():
    #     from models import project, stormwater, ecocube
    #     db.create_all()
    from models import project, stormwater_input, ecocube
    register_routes(app)
    setup_logging(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
    