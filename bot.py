import logging
import html as _html
import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, SUPER_ADMINS, WEBAPP_URL

logger = logging.getLogger(__name__)

BOT_LINK = "https://t.me/perehvat_store_bot/app?startapp="
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "ipoint.db")

def _link(sid):
    return f"{BOT_LINK}{sid}"

def _price(p):
    return f"{p:,}".replace(",", ".") + "\u20bd"

# Категории для бота
CATEGORIES_MAP = {
    "iphone": {"emoji": "\u201a", "label": "iPhone"},
    "ipad": {"emoji": "\u201e", "label": "iPad"},
    "mac": {"emoji": "\u2026", "label": "Mac"},
    "watch": {"emoji": "\u231a", "label": "Apple Watch"},
    "airpods": {"emoji": "\u2020", "label": "AirPods"},
    "accessories": {"emoji": "\u2021", "label": "\u0410\u043a\u0441\u0435\u0441\u0441\u0443\u0430\u0440\u044b"}
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

# Проверка бана
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
        await update.message.reply_text("\u274c \u0412\u044b \u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d\u044b \u0432 iPoint Store.")
        return

    kb = [
        [InlineKeyboardButton("\ud83d\udce6 \u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438", callback_data="stock")],
        [InlineKeyboardButton("\ud83d\udecb\ufe0f \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043c\u0430\u0433\u0430\u0437\u0438\u043d", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("\ud83d\udcac \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", url="https://t.me/iPointManager")],
    ]
    await update.message.reply_text(
        f"\u0417\u0434\u0440\u0430\u0432\u0441\u0442\u0432\u0443\u0439\u0442\u0435, {_html.escape(user.first_name)}! \ud83d\udc4b\n\n"
        "\ud83c\udf4f \u0421\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u044b\u0439 \u0441 Mini-App \u043c\u0430\u0433\u0430\u0437\u0438\u043d <b>iPoint Store</b>!\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:",
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
    kb.append([InlineKeyboardButton("\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="back_start")])
    await query.edit_message_text(
        "\ud83d\udce6 <b>\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438</b>\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044e:",
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
        await query.edit_message_text("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
        return
    
    items = get_db_products(key)
    
    lines = [f"{info['emoji']} <b>{_html.escape(info['label'])}</b>\n"]
    if not items:
        lines.append("\u0422\u043e\u0432\u0430\u0440\u043e\u0432 \u043d\u0435\u0442 \u0432 \u043d\u0430\u043b\u0438\u0447\u0438\u0438.")
    else:
        for name, price, sid in items:
            lines.append(f"\u2022 <a href=\"{_link(sid)}\">{_html.escape(name)}</a> \u2014 <b>{_price(price)}</b>")
    lines.append(f"\n\ud83d\udcb0 \u0422\u043e\u0432\u0430\u0440\u043e\u0432: {len(items)}")
    kb = [
        [InlineKeyboardButton("\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="stock")],
        [InlineKeyboardButton("\ud83d\udcac \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", url="https://t.me/iPointManager")],
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
            "\u2195\ufe0f \u041d\u0430\u0432\u0438\u0433\u0430\u0446\u0438\u044f:",
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
    kb = [
        [InlineKeyboardButton("\ud83d\udce6 \u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438", callback_data="stock")],
        [InlineKeyboardButton("\ud83d\udecb\ufe0f \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043c\u0430\u0433\u0430\u0437\u0438\u043d", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("\ud83d\udcac \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", url="https://t.me/iPointManager")],
    ]
    await query.edit_message_text(
        f"\u0417\u0434\u0440\u0430\u0432\u0441\u0442\u0432\u0443\u0439\u0442\u0435, {_html.escape(user.first_name)}! \ud83d\udc4b\n\n"
        "\ud83c\udf4f \u0421\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u044b\u0439 \u0441 Mini-App \u043c\u0430\u0433\u0430\u0437\u0438\u043d <b>iPoint Store</b>!\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in SUPER_ADMINS:
        await update.message.reply_text("\u274c \u0423 \u0432\u0430\u0441 \u043d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430.")
        return

    args = ctx.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "\ud83d\udee0 <b>\u0410\u0434\u043c\u0438\u043d-\u043a\u043e\u043c\u0430\u043d\u0434\u044b:</b>\n\n"
            "\u2022 <code>/admin ban [user_id]</code> \u2014 \u0437\u0430\u0431\u0430\u043d\u0438\u0442\u044c \u044e\u0437\u0435\u0440\u0430\n"
            "\u2022 <code>/admin unban [user_id]</code> \u2014 \u0440\u0430\u0437\u0431\u0430\u043d\u0438\u0442\u044c \u044e\u0437\u0435\u0440\u0430\n"
            "\u2022 <code>/admin grant [user_id]</code> \u2014 \u0440\u0430\u0437\u0440\u0435\u0448\u0438\u0442\u044c \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u0435 \u0442\u043e\u0432\u0430\u0440\u043e\u0432\n"
            "\u2022 <code>/admin revoke [user_id]</code> \u2014 \u0437\u0430\u0431\u0440\u0430\u0442\u044c \u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u0438\u0435",
            parse_mode="HTML"
        )
        return

    action = args[0].lower()
    target_id = args[1]

    if not os.path.exists(DB_PATH):
        await update.message.reply_text("\u274c \u0411\u0430\u0437\u0430 \u0434\u0430\u043d\u043d\u044b\u0445 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
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
            msg = f"\u274c \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c <code>{target_id}</code> <b>\u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d</b>."
        elif action == "unban":
            cursor.execute("UPDATE users SET is_banned = 0 WHERE telegram_id = ?", (target_id,))
            msg = f"\u2705 \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c <code>{target_id}</code> <b>\u0440\u0430\u0437\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d</b>."
        elif action == "grant":
            cursor.execute("UPDATE users SET can_sell = 1 WHERE telegram_id = ?", (target_id,))
            msg = f"\u2705 \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c <code>{target_id}</code> <b>\u043c\u043e\u0436\u0435\u0442 \u0441\u043e\u0437\u0434\u0430\u0432\u0430\u0442\u044c \u0442\u043e\u0432\u0430\u0440\u043e\u0432</b>."
        elif action == "revoke":
            cursor.execute("UPDATE users SET can_sell = 0 WHERE telegram_id = ?", (target_id,))
            msg = f"\u274c \u0423 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f <code>{target_id}</code> <b>\u0437\u0430\u0431\u0440\u0430\u043d\u043e \u043f\u0440\u0430\u0432\u043e \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f \u0442\u043e\u0432\u0430\u0440\u043e\u0432</b>."
        else:
            msg = "\u274c \u041d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u0430\u044f \u043a\u043e\u043c\u0430\u043d\u0434\u0430."
            
        conn.commit()
        conn.close()
        await update.message.reply_text(msg, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430: {e}")


async def send_purchase_log(app_bot, product_title, product_price, user_info, product_id):
    # Отправляем логи всем суперадминам
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    prod_url = f"{WEBAPP_URL}/product/{product_id}"
    # Заменяем суррогатные эмодзи обычными, чтобы не ломался utf-8 кодер в telegram API
    text = (
        "\ud83d\uded2 <b>\u041d\u043e\u0432\u044b\u0439 \u0437\u0430\u043a\u0430\u0437!</b>\n\n"
        f"\ud83d\udce6 \u0422\u043e\u0432\u0430\u0440: <a href=\"{prod_url}\"><b>{_html.escape(product_title)}</b></a>\n"
        f"\ud83d\udcb0 \u0421\u0443\u043c\u043c\u0430: <b>{_price(product_price)}</b>\n"
        f"\ud83d\udc64 \u041f\u043e\u043a\u0443\u043f\u0430\u0442\u0435\u043b\u044c: {_html.escape(user_info)}\n"
        f"\ud83d\udd52 \u0414\u0430\u0442\u0430: {now}"
    )
    # Отправляем лог каждому суперадмину
    for admin_id in SUPER_ADMINS:
        try:
            await app_bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
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
