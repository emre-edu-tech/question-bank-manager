from functools import wraps

from flask import redirect, request, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        from flask import session

        if not session.get("is_admin"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped
