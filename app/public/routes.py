from flask import render_template

from app.public import bp


@bp.route("/")
def index():
    return render_template("base.html")
