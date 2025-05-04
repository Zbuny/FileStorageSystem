from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    with app.app_context():
        from app.auth.views import auth_bp
        from app.files.views import files_bp
        app.register_blueprint(auth_bp)
        app.register_blueprint(files_bp)
        db.create_all()

    return app
