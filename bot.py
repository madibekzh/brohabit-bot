import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import BOT_TOKEN
from database.db import init_db
from handlers import start, habit_manager, checkin, stats, settings, workout_plan
from services.scheduler import setup_scheduler

# Логтауды баптау
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/webhook"

async def health_check_handler(request):
    """24/7 тексеруге арналған веб-бет (UptimeRobot және браузер үшін)"""
    return web.Response(text="BroHabit Bot is running 24/7! 🚀", content_type="text/plain")

async def set_default_commands(bot: Bot):
    """Телеграмдағы мәзір командаларын орнату"""
    commands = [
        BotCommand(command="start", description="Ботты қайта қосу / Бастау"),
        BotCommand(command="habits", description="Бүгінгі әдеттерді көру және белгілеу"),
        BotCommand(command="plan", description="4 күндік жаттығу жоспарын көру 🏋️"),
        BotCommand(command="add", description="Жаңа әдет қосу"),
        BotCommand(command="stats", description="Жетістіктер мен серия (Streak)"),
        BotCommand(command="settings", description="Еске салу уақыттарын баптау"),
        BotCommand(command="help", description="Көмек және нұсқаулық"),
        BotCommand(command="cancel", description="Әрекеттен бас тарту")
    ]
    await bot.set_my_commands(commands)

def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(workout_plan.router)
    dp.include_router(habit_manager.router)
    dp.include_router(checkin.router)
    dp.include_router(stats.router)
    dp.include_router(settings.router)
    return dp

# ==================== WEBHOOK РЕЖИМІ (RENDER.COM ҮШІН) ====================

async def on_webhook_startup(bot: Bot, base_url: str):
    logger.info("Мәліметтер қоры іске қосылуда...")
    await init_db()

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Еске салу жүйесі (Scheduler) сәтті іске қосылды.")

    try:
        await set_default_commands(bot)
    except Exception as e:
        logger.warning(f"Командаларды орнату кезінде ескерту: {e}")

    webhook_url = f"{base_url}{WEBHOOK_PATH}"
    logger.info(f"Telegram Webhook орнатылуда: {webhook_url}")
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    logger.info("🚀 Бот WEBHOOK режимінде 24/7 сәтті іске қосылды!")

async def on_webhook_shutdown(bot: Bot):
    logger.info("Бот тоқтатылуда...")
    await bot.session.close()

def run_webhook_server(bot: Bot, dp: Dispatcher, base_url: str, port: int):
    """Render сияқты бұлтты платформаларда Webhook серверін қосу"""
    app = web.Application()
    app.router.add_get("/", health_check_handler)
    app.router.add_get("/health", health_check_handler)

    dp.startup.register(lambda: on_webhook_startup(bot, base_url))
    dp.shutdown.register(lambda: on_webhook_shutdown(bot))

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    logger.info(f"🌐 Webhook веб-сервері {port} портында қосылуда...")
    web.run_app(app, host="0.0.0.0", port=port)

# ==================== POLLING РЕЖИМІ (ЛОКАЛДЫ КОМПЬЮТЕР ҮШІН) ====================

async def run_polling(bot: Bot, dp: Dispatcher):
    logger.info("Мәліметтер қоры іске қосылуда...")
    await init_db()

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Еске салу жүйесі (Scheduler) сәтті іске қосылды.")

    try:
        await set_default_commands(bot)
    except Exception as e:
        logger.warning(f"Командаларды орнату кезінде ескерту: {e}")

    logger.info("🚀 Бот POLLING режимінде іске қосылды...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()

# ==================== НЕГІЗГІ НҮКТЕ ====================

def main():
    if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error("❌ ҚАТЕ: Бот токені табылмады!")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    dp = create_dispatcher()

    # Render немесе сыртқы бұлтта жүргенін тексеру
    render_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL")
    port_str = os.getenv("PORT")

    if render_url or port_str:
        base_url = render_url or f"https://brohabit-bot.onrender.com"
        port = int(port_str or 8080)
        run_webhook_server(bot, dp, base_url, port)
    else:
        # Локалды компьютерде Polling арқылы іске қосу
        asyncio.run(run_polling(bot, dp))

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот жұмысын аяқтады.")
