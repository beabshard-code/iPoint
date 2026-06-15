from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255), default="")
    bio = db.Column(db.String(500), default="")
    city = db.Column(db.String(80), default="")
    phone = db.Column(db.String(40), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship("Product", backref="seller", lazy=True, cascade="all, delete-orphan")
    favorites = db.relationship("Favorite", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def initials(self):
        parts = self.name.strip().split()
        return "".join(p[0].upper() for p in parts[:2]) or "U"


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(40), nullable=False)
    condition = db.Column(db.String(40), nullable=False)
    description = db.Column(db.Text, default="")
    images_raw = db.Column(db.Text, default="[]")
    location = db.Column(db.String(80), default="")
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    favorited_by = db.relationship("Favorite", backref="product", lazy=True, cascade="all, delete-orphan")

    @property
    def images(self):
        try:
            data = json.loads(self.images_raw or "[]")
            return data if isinstance(data, list) else []
        except (ValueError, TypeError):
            return []

    @images.setter
    def images(self, value):
        self.images_raw = json.dumps(value or [])

    @property
    def cover(self):
        imgs = self.images
        return imgs[0] if imgs else ""


class Favorite(db.Model):
    __tablename__ = "favorites"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_user_product"),)


CATEGORIES = [
    {"slug": "iphone", "name": "iPhone", "icon": "phone"},
    {"slug": "ipad", "name": "iPad", "icon": "tablet"},
    {"slug": "mac", "name": "Mac", "icon": "laptop"},
    {"slug": "watch", "name": "Watch", "icon": "watch"},
    {"slug": "airpods", "name": "AirPods", "icon": "headphones"},
    {"slug": "accessories", "name": "\u0410\u043a\u0441\u0435\u0441\u0441\u0443\u0430\u0440\u044b", "icon": "plug"},
]

CONDITIONS = ["\u041d\u043e\u0432\u044b\u0439", "\u041a\u0430\u043a \u043d\u043e\u0432\u044b\u0439", "\u0425\u043e\u0440\u043e\u0448\u0435\u0435", "\u0411/\u0443"]
