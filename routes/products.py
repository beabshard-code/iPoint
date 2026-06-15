import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Product, Favorite, CATEGORIES, CONDITIONS

products_bp = Blueprint("products", __name__)

ALLOWED = {"png", "jpg", "jpeg", "webp", "gif"}


def _save_images(files):
    saved = []
    for f in files:
        if not f or not f.filename:
            continue
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED:
            continue
        name = f"{uuid.uuid4().hex}.{ext}"
        f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], secure_filename(name)))
        saved.append(name)
    return saved


@products_bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    condition = request.args.get("condition", "").strip()
    sort = request.args.get("sort", "new")
    pmin = request.args.get("min", type=int)
    pmax = request.args.get("max", type=int)

    query = Product.query
    if q:
        query = query.filter(Product.title.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category=category)
    if condition:
        query = query.filter_by(condition=condition)
    if pmin is not None:
        query = query.filter(Product.price >= pmin)
    if pmax is not None:
        query = query.filter(Product.price <= pmax)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    products = query.all()
    fav_ids = set()
    if current_user.is_authenticated:
        fav_ids = {f.product_id for f in Favorite.query.filter_by(user_id=current_user.id).all()}

    return render_template("index.html", products=products, fav_ids=fav_ids,
                           conditions=CONDITIONS, filters={"q": q, "category": category,
                           "condition": condition, "sort": sort, "min": pmin, "max": pmax})


@products_bp.route("/product/<int:pid>")
def detail(pid):
    product = Product.query.get_or_404(pid)
    is_fav = False
    if current_user.is_authenticated:
        is_fav = Favorite.query.filter_by(user_id=current_user.id, product_id=pid).first() is not None
    related = Product.query.filter(Product.category == product.category, Product.id != pid)\
        .order_by(Product.created_at.desc()).limit(4).all()
    return render_template("product.html", product=product, is_fav=is_fav, related=related)


@products_bp.route("/sell", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        price = request.form.get("price", type=int)
        category = request.form.get("category", "").strip()
        condition = request.form.get("condition", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        if not title or price is None or price < 0 or not category or not condition:
            flash("\u0417\u0430\u043f\u043e\u043b\u043d\u0438\u0442\u0435 \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u043f\u043e\u043b\u044f.", "error")
            return render_template("product_form.html", conditions=CONDITIONS, product=None)
        images = _save_images(request.files.getlist("images"))
        product = Product(title=title, price=price, category=category, condition=condition,
                          description=description, location=location, seller_id=current_user.id)
        product.images = images
        db.session.add(product)
        db.session.commit()
        flash("\u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0435 \u043e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043e!", "success")
        return redirect(url_for("products.detail", pid=product.id))
    return render_template("product_form.html", conditions=CONDITIONS, product=None)


@products_bp.route("/product/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def edit(pid):
    product = Product.query.get_or_404(pid)
    if product.seller_id != current_user.id:
        abort(403)
    if request.method == "POST":
        product.title = request.form.get("title", product.title).strip()
        product.price = request.form.get("price", type=int) or product.price
        product.category = request.form.get("category", product.category).strip()
        product.condition = request.form.get("condition", product.condition).strip()
        product.description = request.form.get("description", "").strip()
        product.location = request.form.get("location", "").strip()
        new_imgs = _save_images(request.files.getlist("images"))
        if new_imgs:
            product.images = product.images + new_imgs
        db.session.commit()
        flash("\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b.", "success")
        return redirect(url_for("products.detail", pid=product.id))
    return render_template("product_form.html", conditions=CONDITIONS, product=product)


@products_bp.route("/product/<int:pid>/delete", methods=["POST"])
@login_required
def delete(pid):
    product = Product.query.get_or_404(pid)
    if product.seller_id != current_user.id:
        abort(403)
    db.session.delete(product)
    db.session.commit()
    flash("\u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0435 \u0443\u0434\u0430\u043b\u0435\u043d\u043e.", "success")
    return redirect(url_for("profile.me"))


MANAGER_URL = "https://t.me/iPointManager"
SERVICE_FEE = 1000


@products_bp.route("/product/<int:pid>/buy")
def checkout(pid):
    product = Product.query.get_or_404(pid)
    return render_template("checkout.html", product=product, fee=SERVICE_FEE)


@products_bp.route("/api/cities")
def api_cities():
    import urllib.request
    import json as _json
    q = request.args.get("q", "").strip().lower()
    if len(q) < 2:
        return {"cities": []}
    try:
        url = "https://api.hh.ru/suggests/areas?text=" + urllib.parse.quote(q)
        req = urllib.request.Request(url, headers={"User-Agent": "iPoint/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        items = []
        for it in data.get("items", []):
            text = it.get("text", "")
            if text:
                items.append(text)
        return {"cities": items[:8]}
    except Exception:
        fallback = ["\u041c\u043e\u0441\u043a\u0432\u0430", "\u0421\u0430\u043d\u043a\u0442-\u041f\u0435\u0442\u0435\u0440\u0431\u0443\u0440\u0433", "\u041d\u043e\u0432\u043e\u0441\u0438\u0431\u0438\u0440\u0441\u043a", "\u0415\u043a\u0430\u0442\u0435\u0440\u0438\u043d\u0431\u0443\u0440\u0433", "\u041a\u0430\u0437\u0430\u043d\u044c", "\u041d\u0438\u0436\u043d\u0438\u0439 \u041d\u043e\u0432\u0433\u043e\u0440\u043e\u0434"]
        return {"cities": [c for c in fallback if q in c.lower()][:8]}


@products_bp.route("/api/pickup")
def api_pickup():
    city = request.args.get("city", "").strip()
    if not city:
        return {"points": []}
    streets = ["\u043f\u0440. \u041c\u0438\u0440\u0430", "\u0443\u043b. \u041b\u0435\u043d\u0438\u043d\u0430", "\u0443\u043b. \u0421\u043e\u0432\u0435\u0442\u0441\u043a\u0430\u044f", "\u0443\u043b. \u0426\u0435\u043d\u0442\u0440\u0430\u043b\u044c\u043d\u0430\u044f", "\u043f\u0440. \u041f\u043e\u0431\u0435\u0434\u044b"]
    points = []
    for i, s in enumerate(streets, 1):
        points.append({
            "code": f"CDEK-{abs(hash(city + s)) % 9000 + 1000}",
            "name": f"\u0421\u0414\u042d\u041a, {s}, {i * 7}",
            "address": f"{city}, {s}, {i * 7}",
            "work": "\u041f\u043d-\u0412\u0441 10:00\u201320:00",
        })
    return {"points": points}
