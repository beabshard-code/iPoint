import os
import asyncio
import threading
import logging
from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager
from models import db, User, Product, CATEGORIES
from config import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")

bot_application = None


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "ipoint-dev-secret-change-me"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "ipoint.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "\u0412\u043e\u0439\u0434\u0438\u0442\u0435, \u0447\u0442\u043e\u0431\u044b \u043f\u0440\u043e\u0434\u043e\u043b\u0436\u0438\u0442\u044c."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.profile import profile_bp
    from routes.favorites import favorites_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(favorites_bp)

    @app.context_processor
    def inject_globals():
        return {"CATEGORIES": CATEGORIES, "BRAND": "\u041f\u0435\u0440\u0435\u0445\u0432\u0430\u0442 Store"}

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.route("/api/purchase-log", methods=["POST"])
    def purchase_log():
        global bot_application
        data = request.get_json(silent=True) or {}
        title = data.get("title", "Unknown")
        price = data.get("price", 0)
        user_info = data.get("user", "Anonymous")
        if bot_application and bot_application.bot:
            from bot import send_purchase_log
            loop = bot_loop
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    send_purchase_log(bot_application.bot, title, price, user_info),
                    loop,
                )
            else:
                try:
                    asyncio.run(send_purchase_log(bot_application.bot, title, price, user_info))
                except RuntimeError:
                    pass
        return jsonify({"ok": True})

    with app.app_context():
        db.create_all()
        seed_data()

    return app


def seed_data():
    if User.query.first():
        return
    demo = User(
        name="\u041f\u0435\u0440\u0435\u0445\u0432\u0430\u0442 Store",
        email="store@ipoint.ru",
        city="\u041c\u043e\u0441\u043a\u0432\u0430",
        phone="+7 900 000-00-00",
        bio="\u041c\u0430\u0433\u0430\u0437\u0438\u043d \u0442\u0435\u0445\u043d\u0438\u043a\u0438 Apple. \u0413\u0430\u0440\u0430\u043d\u0442\u0438\u044f \u043d\u0430 \u0432\u0441\u0451.",
    )
    demo.set_password("demo1234")
    db.session.add(demo)
    db.session.commit()

    items = [
        ("iPhone 15 Pro Max 256GB", 119990, "iphone", "\u041a\u0430\u043a \u043d\u043e\u0432\u044b\u0439", "\u0422\u0438\u0442\u0430\u043d, \u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442.", "\u041c\u043e\u0441\u043a\u0432\u0430"),
        ("MacBook Pro 14 M3 Pro", 209990, "mac", "\u041d\u043e\u0432\u044b\u0439", "18GB / 512GB SSD.", "\u041c\u043e\u0441\u043a\u0432\u0430"),
        ("iPad Air 11 M2 128GB", 64990, "ipad", "\u041d\u043e\u0432\u044b\u0439", "Wi-Fi, Space Gray.", "\u041c\u043e\u0441\u043a\u0432\u0430"),
        ("Apple Watch Ultra 2", 84990, "watch", "\u041a\u0430\u043a \u043d\u043e\u0432\u044b\u0439", "Titanium, Alpine Loop.", "\u041c\u043e\u0441\u043a\u0432\u0430"),
        ("AirPods Pro 2 USB-C", 19990, "airpods", "\u041d\u043e\u0432\u044b\u0439", "\u0410\u043a\u0442\u0438\u0432\u043d\u043e\u0435 \u0448\u0443\u043c\u043e\u043f\u043e\u0434\u0430\u0432\u043b\u0435\u043d\u0438\u0435.", "\u041c\u043e\u0441\u043a\u0432\u0430"),
        ("iPhone 14 128GB", 59990, "iphone", "\u0425\u043e\u0440\u043e\u0448\u0435\u0435", "\u0410\u043a\u043a\u0443\u043c\u0443\u043b\u044f\u0442\u043e\u0440 92%.", "\u041c\u043e\u0441\u043a\u0432\u0430"),
    ]
    for title, price, cat, cond, desc, loc in items:
        db.session.add(Product(
            title=title, price=price, category=cat, condition=cond,
            description=desc, location=loc, seller_id=demo.id, images_raw="[]",
        ))
    db.session.commit()


bot_loop = None

def run_bot():
    global bot_application, bot_loop
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.warning("BOT_TOKEN not set \u2014 Telegram bot disabled")
        return
    from bot import create_bot_app
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    bot_application = create_bot_app()
    logger.info("\U0001f916 Telegram bot starting...")
    bot_loop.run_until_complete(bot_application.run_polling(drop_pending_updates=True, close_loop=False))


app = create_app()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"\U0001f680 Flask server starting on http://localhost:{port}")
    app.run(debug=False, host="0.0.0.0", port=port, use_reloader=False)
