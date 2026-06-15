import logging
import html as _html
import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_CHAT_ID, WEBAPP_URL

logger = logging.getLogger(__name__)

BOT_LINK = "https://t.me/perehvat_store_bot/app?startapp="
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "ipoint.db")

def _link(sid):
    return f"{BOT_LINK}{sid}"

def _price(p):
    return f"{p:,}".replace(",", ".") + "\u20bd"

# Категории для бота
CATEGORIES_MAP = {
    "iphone": {"emoji": "\U0001f4f1", "label": "iPhone"},
    "ipad": {"emoji": "\U0001f4f2", "label": "iPad"},
    "mac": {"emoji": "\u1f4bb", "label": "Mac"},
    "watch": {"emoji": "\u231a", "label": "Apple Watch"},
    "airpods": {"emoji": "\U0001f3a7", "label": "AirPods"},
    "accessories": {"emoji": "\U0001f50c", "label": "\u0410\u043a\u0441\u0435\u0441\u0441\u0443\u0430\u0440\u044b"}
}

def get_db_products(category_slug=None):
    """Получает товары из SQLite базы данных динамически"""
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


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    kb = [
        [InlineKeyboardButton("\U0001f4e6 \u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438", callback_data="stock")],
        [InlineKeyboardButton("\U0001f6cd\ufe0f \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043c\u0430\u0433\u0430\u0437\u0438\u043d", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("\U0001f4ac \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", url="https://t.me/iPointManager")],
    ]
    await update.message.reply_text(
        f"\u0417\u0434\u0440\u0430\u0432\u0441\u0442\u0432\u0443\u0439\u0442\u0435, {_html.escape(user.first_name)}! \U0001f44b\n\n"
        "\u0421\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u044b\u0439 \u0441 Mini-App \u043c\u0430\u0433\u0430\u0437\u0438\u043d <b>iPoint Store</b>!\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def cb_stock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Считаем количество по категориям динамически
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
        "\U0001f4e6 <b>\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438</b>\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440и\u044e:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def cb_category(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
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
    lines.append(f"\n\U0001f4b0 \u0422\u043e\u0432\u0430\u0440\u043e\u0432: {len(items)}")
    kb = [
        [InlineKeyboardButton("\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="stock")],
        [InlineKeyboardButton("\U0001f4ac \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", url="https://t.me/iPointManager")],
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
    await query.answer()
    user = update.effective_user
    kb = [
        [InlineKeyboardButton("\U0001f4e6 \u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438", callback_data="stock")],
        [InlineKeyboardButton("\U0001f6cd\ufe0f \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043c\u0430\u0433\u0430\u0437\u0438\u043d", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("\U0001f4ac \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", url="https://t.me/iPointManager")],
    ]
    await query.edit_message_text(
        f"\u0417\u0434\u0440\u0430\u0432\u0441\u0442\u0432\u0443\u0439\u0442\u0435, {_html.escape(user.first_name)}! \U0001f44b\n\n"
        "\u0421\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u044b\u0439 \u0441 Mini-App \u043c\u0430\u0433\u0430\u0437\u0438\u043d <b>iPoint Store</b>!\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def send_purchase_log(app_bot, product_title, product_price, user_info):
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID not set, skipping purchase log")
        return
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    text = (
        "\U0001f6d2 <b>\u041d\u043e\u0432\u044b\u0439 \u0437\u0430\u043a\u0430\u0437!</b>\n\n"
        f"\U0001f4e6 \u0422\u043e\u0432\u0430\u0440: <b>{_html.escape(product_title)}</b>\n"
        f"\U0001f4b0 \u0421\u0443\u043c\u043c\u0430: <b>{_price(product_price)}</b>\n"
        f"\U0001f464 \u041f\u043e\u043a\u0443\u043f\u0430\u0442\u0435\u043b\u044c: {_html.escape(user_info)}\n"
        f"\U0001f552 \u0414\u0430\u0442\u0430: {now}"
    )
    try:
        await app_bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send purchase log: {e}")


def create_bot_app():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(cb_stock, pattern="^stock$"))
    app.add_handler(CallbackQueryHandler(cb_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(cb_back_start, pattern="^back_start$"))
    return app
