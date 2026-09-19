from app.admin import bp


@bp.route("/admin")
def dashboard():
    return "admin placeholder"
