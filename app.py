import os
import asyncio
import threading
import logging
from flask import Flask, render_template, request, jsonify, abort
from flask_login import LoginManager, current_user
from models import db, User, Product, CATEGORIES
from config import BOT_TOKEN, SUPER_ADMINS

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")

# Поддержка Persistent Disk на Render
P_DIR = "/opt/render/project/src/data"
if os.path.exists(P_DIR):
    DB_PATH = os.path.join(P_DIR, "ipoint.db")
else:
    DB_PATH = os.path.join(BASE_DIR, "ipoint.db")

bot_application = None


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "ipoint-dev-secret-change-me"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    if os.path.exists(P_DIR):
        os.makedirs(P_DIR, exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "products.index"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        if user and user.is_banned:
            return None
        return user

    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.profile import profile_bp
    from routes.favorites import favorites_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(favorites_bp)

    @app.before_request
    def check_ban():
        if current_user.is_authenticated and current_user.is_banned:
            from flask_login import logout_user
            logout_user()
            abort(403)

    @app.context_processor
    def inject_globals():
        is_admin = False
        if current_user.is_authenticated:
            try:
                t_id = int(current_user.telegram_id) if current_user.telegram_id else 0
                if t_id in SUPER_ADMINS or current_user.can_sell:
                    is_admin = True
            except Exception:
                pass
        return {"CATEGORIES": CATEGORIES, "BRAND": "iPoint Store", "is_admin": is_admin}

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.route("/api/tg-login", methods=["POST"])
    def tg_login():
        from flask_login import login_user
        data = request.get_json(silent=True) or {}
        tg_id = str(data.get("id", ""))
        name = data.get("first_name", "")
        username = data.get("username", "")
        if not tg_id or not name:
            return jsonify({"ok": False, "error": "Missing data"}), 400
        
        user = User.query.filter_by(telegram_id=tg_id).first()
        if not user:
            user = User(telegram_id=tg_id, name=name, username=username)
            db.session.add(user)
            db.session.commit()
        else:
            if user.is_banned:
                return jsonify({"ok": False, "error": "User is banned"}), 403
            if name != user.name or username != user.username:
                user.name = name
                user.username = username
                db.session.commit()
                
        login_user(user, remember=True)
        return jsonify({"ok": True})

    @app.route("/api/purchase-log", methods=["POST"])
    def purchase_log():
        global bot_application
        data = request.get_json(silent=True) or {}
        title = data.get("title", "Unknown")
        price = data.get("price", 0)
        user_info = data.get("user", "Anonymous")
        pid = data.get("id", 0)
        if bot_application and bot_application.bot:
            from bot import send_purchase_log
            loop = bot_loop
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    send_purchase_log(bot_application.bot, title, price, user_info, pid),
                    loop,
                )
            else:
                try:
                    asyncio.run(send_purchase_log(bot_application.bot, title, price, user_info, pid))
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
        name="iPoint Store Admin",
        telegram_id=str(SUPER_ADMINS[0]) if SUPER_ADMINS else "8229778449",
        city="\u041c\u043e\u0441\u043a\u0432\u0430",
        phone="+7 900 000-00-00",
        bio="\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440 iPoint Store.",
    )
    demo.set_password(None)
    db.session.add(demo)
    db.session.commit()


def seed_data_old():
    pass


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
    logger.info("\u1f916 Telegram bot starting...")

    async def _run():
        await bot_application.initialize()
        await bot_application.updater.start_polling(drop_pending_updates=True)
        await bot_application.start()
        logger.info("\u1f916 Telegram bot is running")
        while True:
            await asyncio.sleep(3600)

    try:
        bot_loop.run_until_complete(_run())
    except (KeyboardInterrupt, SystemExit):
        bot_loop.run_until_complete(bot_application.updater.stop())
        bot_loop.run_until_complete(bot_application.stop())
        bot_loop.run_until_complete(bot_application.shutdown())


app = create_app()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"\u1f680 Flask server starting on http://localhost:{port}")
    app.run(debug=False, host="0.0.0.0", port=port, use_reloader=False)
