from flask import Blueprint

bp = Blueprint('main', __name__)

from app.routes import main_routes

bp.register_blueprint(main_routes.bp)
