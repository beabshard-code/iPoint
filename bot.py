import logging
import html as _html
import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, SUPER_ADMINS, WEBAPP_URL, BOT_USERNAME

logger = logging.getLogger(__name__)

# Постоянное хранилище данных (то же, что в app.py)
_DATA_DIR = os.environ.get("IPOINT_DATA_DIR", "").strip()
if not _DATA_DIR:
    _P_DIR = "/opt/render/project/src/data"
    _DATA_DIR = _P_DIR if os.path.exists(_P_DIR) else os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(_DATA_DIR, "ipoint.db")

BOT_LINK = f"https://t.me/{BOT_USERNAME}/app?startapp="

def _link(sid):
    return f"{BOT_LINK}{sid}"

def _price(p):
    return f"{p:,}".replace(",", ".") + "₽"

# Категории для бота с обычными UTF-8 эмодзи напрямую
CATEGORIES_MAP = {
    "iphone": {"emoji": "📱", "label": "iPhone"},
    "ipad": {"emoji": "📟", "label": "iPad"},
    "mac": {"emoji": "💻", "label": "Mac"},
    "watch": {"emoji": "⌚", "label": "Apple Watch"},
    "airpods": {"emoji": "🎧", "label": "AirPods"},
    "accessories": {"emoji": "🔌", "label": "Аксессуары"}
}

def get_db_products(category_slug=None):
    products = []
    if not os.path.exists(DB_PATH):
        return products
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if category_slug:
            cursor.execute("SELECT id, title, price FROM products WHERE category = ? ORDER BY created_at DESC", (category_slug,))
        else:
            cursor.execute("SELECT id, title, price, category FROM products ORDER BY created_at DESC")
        rows = cursor.fetchall()
        for r in rows:
            if category_slug:
                products.append((r[1], r[2], r[0]))
            else:
                products.append({"title": r[1], "price": r[2], "id": r[0], "category": r[3]})
        conn.close()
    except Exception as e:
        logger.error(f"DB error in bot: {e}")
    return products

def is_user_banned(tg_id):
    if not os.path.exists(DB_PATH):
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT is_banned FROM users WHERE telegram_id = ?", (str(tg_id),))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return True
    except Exception:
        pass
    return False


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_user_banned(user.id):
        await update.message.reply_text("❌ Вы заблокированы в iPoint Store.")
        return

    first_name = user.first_name.encode('utf-8', 'ignore').decode('utf-8')

    kb = [
        [InlineKeyboardButton("🛍️ Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("💬 Поддержка", url="https://t.me/iPointManager")],
    ]
    await update.message.reply_text(
        f"Здравствуйте, {_html.escape(first_name)}! 👋\n\n"
        "🍏 Совместимый с Mini-App магазин <b>iPoint Store</b>!\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def cb_stock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if is_user_banned(query.from_user.id):
        await query.answer("Вы заблокированы", show_alert=True)
        return
    await query.answer()
    
    db_prods = get_db_products()
    counts = {}
    for p in db_prods:
        counts[p["category"]] = counts.get(p["category"], 0) + 1
        
    kb = []
    for key, info in CATEGORIES_MAP.items():
        total = counts.get(key, 0)
        kb.append([InlineKeyboardButton(
            f"{info['emoji']} {info['label']} ({total})",
            callback_data=f"cat_{key}",
        )])
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_start")])
    await query.edit_message_text(
        "📦 <b>В наличии</b>\n\n"
        "Выберите категорию:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def cb_category(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if is_user_banned(query.from_user.id):
        await query.answer("Вы заблокированы", show_alert=True)
        return
    await query.answer()
    key = query.data.replace("cat_", "")
    info = CATEGORIES_MAP.get(key)
    if not info:
        await query.edit_message_text("Категория не найдена.")
        return
    
    items = get_db_products(key)
    
    lines = [f"{info['emoji']} <b>{_html.escape(info['label'])}</b>\n"]
    if not items:
        lines.append("Товаров нет в наличии.")
    else:
        for name, price, sid in items:
            lines.append(f"• <a href=\"{_link(sid)}\">{_html.escape(name)}</a> — <b>{_price(price)}</b>")
    lines.append(f"\n💰 Товаров: {len(items)}")
    kb = [
        [InlineKeyboardButton("◀️ Назад", callback_data="stock")],
        [InlineKeyboardButton("💬 Поддержка", url="https://t.me/iPointManager")],
    ]
    text = "\n".join(lines)
    if len(text) > 4000:
        parts = []
        current = []
        for line in lines:
            current.append(line)
            if len("\n".join(current)) > 3800:
                parts.append("\n".join(current))
                current = []
        if current:
            parts.append("\n".join(current))
        await query.edit_message_text(parts[0], parse_mode="HTML", disable_web_page_preview=True)
        for part in parts[1:]:
            await query.message.reply_text(part, parse_mode="HTML", disable_web_page_preview=True)
        await query.message.reply_text(
            "↕️ Навигация:",
            reply_markup=InlineKeyboardMarkup(kb),
        )
    else:
        await query.edit_message_text(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(kb))


async def cb_back_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if is_user_banned(query.from_user.id):
        return
    await query.answer()
    user = update.effective_user
    first_name = user.first_name.encode('utf-8', 'ignore').decode('utf-8')
    kb = [
        [InlineKeyboardButton("🛍️ Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("💬 Поддержка", url="https://t.me/iPointManager")],
    ]
    await query.edit_message_text(
        f"Здравствуйте, {_html.escape(first_name)}! 👋\n\n"
        "🍏 Совместимый с Mini-App магазин <b>iPoint Store</b>!\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in SUPER_ADMINS:
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    args = ctx.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "🛠️ <b>Админ-команды:</b>\n\n"
            "• <code>/admin ban [user_id]</code> — забанить юзера\n"
            "• <code>/admin unban [user_id]</code> — разбанить\n"
            "• <code>/admin grant [user_id]</code> — разрешить создание товаров\n"
            "• <code>/admin revoke [user_id]</code> — забрать разрешение",
            parse_mode="HTML"
        )
        return

    action = args[0].lower()
    target_id = args[1]

    if not os.path.exists(DB_PATH):
        await update.message.reply_text("❌ База данных не найдена.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (target_id,))
        user_exists = cursor.fetchone()
        if not user_exists:
            cursor.execute("INSERT INTO users (name, telegram_id, created_at) VALUES (?, ?, ?)", 
                           (f"User {target_id}", target_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

        if action == "ban":
            cursor.execute("UPDATE users SET is_banned = 1 WHERE telegram_id = ?", (target_id,))
            msg = f"❌ Пользователь <code>{target_id}</code> <b>заблокирован</b>."
        elif action == "unban":
            cursor.execute("UPDATE users SET is_banned = 0 WHERE telegram_id = ?", (target_id,))
            msg = f"✅ Пользователь <code>{target_id}</code> <b>разблокирован</b>."
        elif action == "grant":
            cursor.execute("UPDATE users SET can_sell = 1 WHERE telegram_id = ?", (target_id,))
            msg = f"✅ Пользователь <code>{target_id}</code> <b>может создавать товары</b>."
        elif action == "revoke":
            cursor.execute("UPDATE users SET can_sell = 0 WHERE telegram_id = ?", (target_id,))
            msg = f"❌ У пользователя <code>{target_id}</code> <b>забрано право создания товаров</b>."
        else:
            msg = "❌ Неизвестная команда."
            
        conn.commit()
        conn.close()
        await update.message.reply_text(msg, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def send_purchase_log(app_bot, product_title, product_price, user_info, product_id):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    prod_url = f"{WEBAPP_URL}/product/{product_id}"
    raw_text = (
        "🛒 <b>Новый заказ!</b>\n\n"
        f"📦 Товар: <a href=\"{prod_url}\"><b>{_html.escape(product_title)}</b></a>\n"
        f"💰 Сумма: <b>{_price(product_price)}</b>\n"
        f"👤 Покупатель: {_html.escape(user_info)}\n"
        f"🕒 Дата: {now}"
    )
    clean_text = raw_text.encode('utf-8', 'ignore').decode('utf-8')
    for admin_id in SUPER_ADMINS:
        try:
            await app_bot.send_message(chat_id=admin_id, text=clean_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send purchase log to {admin_id}: {e}")


def create_bot_app():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(cb_stock, pattern="^stock$"))
    app.add_handler(CallbackQueryHandler(cb_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(cb_back_start, pattern="^back_start$"))
    return app
