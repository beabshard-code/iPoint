import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Product

profile_bp = Blueprint("profile", __name__)
ALLOWED = {"png", "jpg", "jpeg", "webp"}


@profile_bp.route("/profile")
@login_required
def me():
    products = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template("profile.html", user=current_user, products=products, owner=True)


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.city = request.form.get("city", "").strip()
        current_user.phone = request.form.get("phone", "").strip()
        current_user.bio = request.form.get("bio", "").strip()
        avatar = request.files.get("avatar")
        if avatar and avatar.filename:
            ext = avatar.filename.rsplit(".", 1)[-1].lower() if "." in avatar.filename else ""
            if ext in ALLOWED:
                name = f"avatar_{uuid.uuid4().hex}.{ext}"
                avatar.save(os.path.join(current_app.config["UPLOAD_FOLDER"], secure_filename(name)))
                current_user.avatar = name
        db.session.commit()
        flash("\u041f\u0440\u043e\u0444\u0438\u043b\u044c \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d.", "success")
        return redirect(url_for("profile.me"))
    return render_template("profile_edit.html", user=current_user)


@profile_bp.route("/seller/<int:uid>")
def seller(uid):
    user = User.query.get_or_404(uid)
    products = Product.query.filter_by(seller_id=uid).order_by(Product.created_at.desc()).all()
    owner = current_user.is_authenticated and current_user.id == uid
    return render_template("profile.html", user=user, products=products, owner=owner)
