import logging
import html as _html
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_CHAT_ID, WEBAPP_URL

logger = logging.getLogger(__name__)

BOT_LINK = "https://t.me/perehvat_store_bot/app?startapp="

def _link(sid):
    return f"{BOT_LINK}{sid}"

def _price(p):
    return f"{p:,}".replace(",", ".") + "\u20bd"

CATALOG = [
    {
        "key": "iphone", "emoji": "\U0001f4f1", "label": "iPhone",
        "items": [
            ("iPhone 7 Plus 128gb", 3500, 1577),
            ("iPhone XR 64gb", 8489, 1483),
            ("iPhone 11 128gb", 5000, 1595),
            ("iPhone 11 Pro Max 64gb", 11989, 1470),
            ("iPhone 12 256gb", 13000, 1675),
            ("iPhone 12 Pro Max 128gb", 14500, 1572),
            ("iPhone 12 Pro Max 128GB", 19990, 1183),
            ("iPhone 12 Pro Max 256GB", 18990, 1317),
            ("iPhone 13 mini 128gb Blue", 17000, 960),
            ("iPhone 13 128gb", 17500, 1260),
            ("iPhone 13 128gb", 18000, 1568),
            ("iPhone 14 Pro Max 256GB", 35990, 1605),
            ("iPhone 15 Pro 256gb", 45800, 1580),
            ("iPhone 15 Pro 256gb", 36000, 1653),
            ("iPhone 15 Pro 1024GB", 55990, 1314),
            ("iPhone 15 Pro 1024GB", 53990, 1374),
            ("iPhone 15 Pro Max 256GB", 49900, 1559),
            ("iPhone 15 Pro Max 256gb", 49800, 1581),
            ("iPhone 15 Pro Max 256gb", 51000, 1652),
            ("iPhone 15 Pro Max 256gb", 49900, 1669),
            ("iPhone 15 Pro Max 256gb", 49900, 1671),
            ("iPhone 15 Pro Max 256gb", 34500, 1683),
            ("iPhone 15 Pro Max 512Gb", 49999, 1560),
            ("iPhone 15 Pro Max Blue 512gb", 50990, 1593),
            ("iPhone 16 128gb", 41500, 1554),
            ("iPhone 16 128gb", 42990, 1533),
            ("iPhone 16 256gb", 48800, 1579),
            ("iPhone 16 256gb", 48990, 1681),
            ("iPhone 16 Plus 128gb", 38500, 1069),
            ("iPhone 16 Plus 512GB", 53990, 1508),
            ("iPhone 16 Pro 1024gb (\u043d\u043e\u0432\u044b\u0439)", 87990, 480),
            ("iPhone 16 Pro Max 256gb", 62000, 1462),
            ("iPhone 16 Pro Max 256gb", 64000, 1463),
            ("iPhone 16 Pro Max 256gb", 63990, 1604),
            ("iPhone 16 Pro Max 256gb", 72900, 1620),
            ("iPhone 16 Pro Max 256gb", 73900, 1622),
            ("iPhone 16 Pro Max 256gb", 73900, 1656),
            ("iPhone 16 Pro Max 256gb", 68900, 1658),
            ("iPhone 16 Pro Max 512gb", 67900, 1610),
        ],
    },
    {
        "key": "iphone_air", "emoji": "\u2728", "label": "iPhone Air",
        "items": [
            ("iPhone Air 256gb", 61500, 1661),
            ("iPhone Air 256GB Black", 69600, 1648),
            ("iPhone Air 256GB Gold", 68000, 1650),
            ("iPhone Air 256GB White", 70100, 1649),
        ],
    },
    {
        "key": "iphone17", "emoji": "\U0001f525", "label": "iPhone 17",
        "items": [
            ("iPhone 17 256gb", 57400, 1450),
            ("iPhone 17 256gb", 54000, 1515),
            ("iPhone 17 256GB Black eSIM", 60500, 1625),
            ("iPhone 17 256GB Black Sim+Esim", 65700, 1633),
            ("iPhone 17 256GB Blue eSIM", 60500, 1627),
            ("iPhone 17 256GB White Sim+Esim", 65500, 1631),
            ("iPhone 17 Pro 256GB Blue eSim", 83000, 1636),
            ("iPhone 17 Pro 256GB Blue Sim+eSim", 94200, 1637),
            ("iPhone 17 Pro 256GB Orange eSIM", 82500, 1640),
            ("iPhone 17 Pro 256GB White eSIM", 83500, 1638),
            ("iPhone 17 Pro 256GB White Sim+Esim", 92500, 1639),
            ("iPhone 17 Pro Comic Orange 256GB", 80500, 1540),
            ("iPhone 17 Pro Max 256GB Blue ESIM", 87800, 1642),
            ("iPhone 17 Pro Max 256GB Blue Sim+Esim", 101500, 1643),
            ("iPhone 17 Pro Max 256GB Orange eSIM", 87800, 1646),
            ("iPhone 17 Pro Max 256GB Orange Sim+eSim", 100800, 1647),
            ("iPhone 17 Pro Max 256GB White ESIM", 88800, 1644),
            ("iPhone 17 Pro Max 256GB White Sim+Esim", 101500, 1645),
        ],
    },
    {
        "key": "ipad", "emoji": "\U0001f4f2", "label": "iPad",
        "items": [("iPad 8 2020 128gb Sim", 16000, 1613)],
    },
    {
        "key": "watch", "emoji": "\u231a", "label": "Apple Watch",
        "items": [
            ("Apple Watch 9 41mm", 10990, 1591),
            ("Apple Watch Ultra 1 titanium", 26000, 1456),
        ],
    },
    {
        "key": "airpods", "emoji": "\U0001f3a7", "label": "AirPods",
        "items": [
            ("AirPods 4", 11000, 825),
            ("AirPods 4", 11200, 1676),
            ("AirPods 4 ANC", 16000, 1677),
            ("Airpods Pro 1", 5500, 1592),
            ("AirPods Pro 3", 20900, 817),
            ("AirPods Pro 3 \u041d\u043e\u0432\u044b\u0435", 18100, 1662),
            ("AirPods Max 2", 25990, 1556),
            ("AirPods Max 2 Type-C Blue", 24900, 1621),
            ("AirPods Max Green Lightning", 17900, 1095),
        ],
    },
    {
        "key": "other", "emoji": "\U0001f4e6", "label": "\u0414\u0440\u0443\u0433\u043e\u0435",
        "items": [
            ("Apple Pencil", 10500, 1023),
            ("Dji Osmo Pocket 3 Creator Edition", 43990, 1477),
            ("Harman Kardon Onyx Studio 9", 18990, 1575),
            ("Kodak Charmera 1987", 4500, 1473),
            ("Samsung S24 Ultra 12/256gb", 42990, 1594),
        ],
    },
]


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    kb = [
        [InlineKeyboardButton("\U0001f4e6 \u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438", callback_data="stock")],
        [InlineKeyboardButton("\U0001f6cd\ufe0f \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043c\u0430\u0433\u0430\u0437\u0438\u043d", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("\U0001f4ac \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", url="https://t.me/iPointManager")],
    ]
    await update.message.reply_text(
        f"\u0417\u0434\u0440\u0430\u0432\u0441\u0442\u0432\u0443\u0439\u0442\u0435, {_html.escape(user.first_name)}! \U0001f44b\n\n"
        "\U0001f34f <b>\u041f\u0435\u0440\u0435\u0445\u0432\u0430\u0442 Store</b> \u2014 \u043c\u0430\u0433\u0430\u0437\u0438\u043d \u0442\u0435\u0445\u043d\u0438\u043a\u0438 Apple\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def cb_stock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = []
    for cat in CATALOG:
        total = len(cat["items"])
        kb.append([InlineKeyboardButton(
            f"{cat['emoji']} {cat['label']} ({total})",
            callback_data=f"cat_{cat['key']}",
        )])
    kb.append([InlineKeyboardButton("\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="back_start")])
    await query.edit_message_text(
        "\U0001f4e6 <b>\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438</b>\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044e:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def cb_category(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("cat_", "")
    cat = next((c for c in CATALOG if c["key"] == key), None)
    if not cat:
        await query.edit_message_text("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
        return
    lines = [f"{cat['emoji']} <b>{_html.escape(cat['label'])}</b>\n"]
    for name, price, sid in cat["items"]:
        lines.append(f"\u2022 <a href=\"{_link(sid)}\">{_html.escape(name)}</a> \u2014 <b>{_price(price)}</b>")
    lines.append(f"\n\U0001f4b0 \u0422\u043e\u0432\u0430\u0440\u043e\u0432: {len(cat['items'])}")
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
        "\U0001f34f <b>\u041f\u0435\u0440\u0435\u0445\u0432\u0430\u0442 Store</b> \u2014 \u043c\u0430\u0433\u0430\u0437\u0438\u043d \u0442\u0435\u0445\u043d\u0438\u043a\u0438 Apple\n\n"
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
