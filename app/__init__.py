from flask import Flask, render_template
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

    def not_found(error):
        return render_template("public/404.html"), 404

    def internal_error(error):
        return render_template("public/500.html"), 500

    app.register_error_handler(404, not_found)
    app.register_error_handler(500, internal_error)

    return app
