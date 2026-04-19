from routes.project_routes import project_bp
from routes.stormwater_input_routes import input_bp
from routes.stormwater_catchment_routes import catchment_bp
from routes.stormwater_tank_routes import tank_bp
from routes.ecocube_routes import ecocube_bp
# from routes.login_routes import auth_bp
from routes.user_auth import auth_bp
from routes.ifd_routes import ifd_bp
from routes.stormwater_output import stormwater_bp
from routes.ifd_fetch import rainfall_bp
from routes.bulk_insert_routes import excel_bp
from routes.megavault_routes import megavault_bp



def register_routes(app):
    app.register_blueprint(ifd_bp, url_prefix="/api/ifd")
    app.register_blueprint(project_bp, url_prefix="/api/projects")
    app.register_blueprint(input_bp, url_prefix="/api/stormwater")
    app.register_blueprint(catchment_bp, url_prefix="/api/stormwater")
    app.register_blueprint(tank_bp, url_prefix="/api/stormwater")
    app.register_blueprint(ecocube_bp, url_prefix="/api/ecocube")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(stormwater_bp, url_prefix="/api/stormwater")
    app.register_blueprint(rainfall_bp, url_prefix="/api/ifd")
    app.register_blueprint(excel_bp, url_prefix="/api/excel")
    app.register_blueprint(megavault_bp, url_prefix="/api/megavault")

