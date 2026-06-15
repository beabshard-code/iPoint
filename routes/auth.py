from flask import Blueprint, redirect, url_for
from flask_login import logout_user, login_required

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register")
def register():
    return redirect(url_for("products.index"))

@auth_bp.route("/login")
def login():
    return redirect(url_for("products.index"))

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("products.index"))
