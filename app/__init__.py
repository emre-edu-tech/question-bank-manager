from flask import Flask
from flask_migrate import Migrate

from config import Config

from app.extensions import db

migrate = Migrate()


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models  # noqa: E402,F401
    from app.seed import register_seed_command  # noqa: E402

    register_seed_command(app)

    from app.auth import bp as auth_bp
    from app.admin import bp as admin_bp
    from app.public import bp as public_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)

    return app
