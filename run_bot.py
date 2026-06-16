import logging
from app import create_app
from bot import create_bot_app
from config import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.warning("BOT_TOKEN not set \u2014 Telegram bot disabled")
        return
    create_app()
    application = create_bot_app()
    logger.info("Telegram bot starting (polling)...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
