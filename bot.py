import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

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
import os
from aiohttp import web

logger = logging.getLogger(__name__)

async def health_check_handler(request):
    return web.Response(text="BroHabit Bot is running 24/7! 🚀", content_type="text/plain")

async def run_health_server():
    """Бұлтты хостингтерде (Render/Railway) 24/7 өшпей тұру үшін веб-сервер"""
    port_str = os.getenv("PORT")
    if not port_str:
        return
    try:
        port = int(port_str)
        app = web.Application()
        app.router.add_get("/", health_check_handler)
        app.router.add_get("/health", health_check_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"🌐 24/7 Health-check сервері {port} портында қосылды.")
    except Exception as e:
        logger.warning(f"Health-check серверін қосу қатесі: {e}")

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

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error(
            "\n" + "="*60 + "\n"
            "❌ ҚАТЕ: Бот токені табылмады!\n"
            ".env файлына BOT_TOKEN мәнін енгізіңіз.\n"
            "Токенді Telegram-дағы @BotFather арқылы алуға болады.\n"
            + "="*60
        )
        sys.exit(1)

    # Деректер қорын дайындау
    logger.info("Мәліметтер қоры іске қосылуда...")
    await init_db()

    # Бот және диспетчерді жасау
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Маршрутизаторларды (роутерлерді) тіркеу
    dp.include_router(start.router)
    dp.include_router(workout_plan.router)
    dp.include_router(habit_manager.router)
    dp.include_router(checkin.router)
    dp.include_router(stats.router)
    dp.include_router(settings.router)

    # Жоспарлағышты (еске салу жүйесін) іске қосу
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Еске салу жүйесі (Scheduler) сәтті іске қосылды.")

    # Бот командаларын орнату
    try:
        await set_default_commands(bot)
    except Exception as e:
        logger.warning(f"Командаларды орнату кезінде ескерту: {e}")

    logger.info("🚀 Бот сәтті іске қосылды және хабарламаларды күтуде...")

    # Бұлтты серверлерге арналған 24/7 health-check
    await run_health_server()

    try:
        # Ескі оқылмаған хабарламаларды тазартып, жаңаларын тыңдау
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот жұмысын аяқтады.")
