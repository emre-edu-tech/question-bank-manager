import secrets

from flask import current_app, flash, redirect, render_template, request, session, url_for

from app.auth import bp


def _is_safe_next(target):
    return (
        isinstance(target, str)
        and target.startswith("/")
        and not target.startswith("//")
    )


@bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        expected_username = current_app.config.get("ADMIN_USERNAME") or ""
        expected_password = current_app.config.get("ADMIN_PASSWORD") or ""
        username_ok = secrets.compare_digest(username, expected_username)
        password_ok = secrets.compare_digest(password, expected_password)
        if username_ok and password_ok:
            session["is_admin"] = True
            next_page = request.args.get("next")
            if _is_safe_next(next_page):
                return redirect(next_page)
            return redirect(url_for("admin.dashboard"))
        flash("Kullanıcı adı veya şifre hatalı.", "error")
    return render_template("auth/login.html")


@bp.route("/admin/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("auth.login"))
