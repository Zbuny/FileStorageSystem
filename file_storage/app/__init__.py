from flask import Flask
from config import Config
from app.extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    with app.app_context():
        from app.auth.views import auth_bp
        from app.files.views import files_bp
        from app.main import main
        from app.models.models_form import User
        from app.chat.views import chat_bp
        app.register_blueprint(chat_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(files_bp)
        app.register_blueprint(main)

        db.create_all()

    return app
