from flask import Blueprint, redirect, url_for, request, render_template
from flask_login import login_required, current_user
from models import db, Favorite, Product

favorites_bp = Blueprint("favorites", __name__)


@favorites_bp.route("/favorites")
@login_required
def list_favorites():
    favs = Favorite.query.filter_by(user_id=current_user.id).all()
    products = [f.product for f in favs]
    return render_template("favorites.html", products=products)


@favorites_bp.route("/favorites/toggle/<int:product_id>", methods=["POST"])
@login_required
def toggle(product_id):
    Product.query.get_or_404(product_id)
    fav = Favorite.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
        active = False
    else:
        db.session.add(Favorite(user_id=current_user.id, product_id=product_id))
        db.session.commit()
        active = True
    if request.headers.get("X-Requested-With") == "fetch":
        return {"active": active}
    return redirect(request.referrer or url_for("products.index"))
