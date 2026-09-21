from flask import render_template

from app.admin import bp
from app.auth.decorators import login_required


@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/admin")
def dashboard():
    return render_template("admin/dashboard.html")
