from flask import Blueprint

bp = Blueprint('main', __name__)

from app.routes import home_routes, image_routes

bp.register_blueprint(home_routes.bp)
bp.register_blueprint(image_routes.bp)
