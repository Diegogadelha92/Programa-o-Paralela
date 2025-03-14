from flask import Flask
import os

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'app', 'templates'))

    from app.config import Config
    app.config.from_object(Config)

    from app.routes import bp
    app.register_blueprint(bp)

    return app
