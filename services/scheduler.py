import asyncio
import logging
from datetime import datetime, date
import pytz
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.models import (
    get_all_users_for_reminder,
    get_user_habits,
    get_habit_logs_for_date
)
from utils.keyboards import get_reminder_action_keyboard, get_today_habits_keyboard
from services.quotes import get_random_quote

logger = logging.getLogger(__name__)

async def check_and_send_reminders(bot: Bot):
    """Әр минут сайын қолданушылардың уақытын тексеріп, тиісті еске салуларды жолдау"""
    try:
        users = await get_all_users_for_reminder()
        today_date = date.today()
        today_str = today_date.strftime("%Y-%m-%d")

        for user in users:
            user_id = user["user_id"]
            tz_name = user.get("timezone") or "Asia/Almaty"
            try:
                user_tz = pytz.timezone(tz_name)
            except Exception:
                user_tz = pytz.timezone("Asia/Almaty")

            now_user = datetime.now(user_tz)
            current_hm = now_user.strftime("%H:%M")

            habits = await get_user_habits(user_id, only_active=True)
            if not habits:
                continue

            logs = await get_habit_logs_for_date(user_id, today_str)

            # 1. Таңғы жалпы еске салу
            morning_time = user.get("morning_reminder_time", "09:00")
            if current_hm == morning_time:
                today_scheduled = [h for h in habits if is_habit_scheduled_today(h, now_user.date())]
                if today_scheduled:
                    habit_lines = [f"• {h['title']}" for h in today_scheduled]
                    habits_text = "\n".join(habit_lines)
                    morning_msg = (
                        f"🌅 <b>Қайырлы таң, {user.get('first_name', 'досым')}!</b>\n\n"
                        f"Бүгін орындалуы тиіс мақсаттар:\n"
                        f"{habits_text}\n\n"
                        f"💡 <i>{get_random_quote()}</i>\n\n"
                        f"Сәтті әрі өнімді күн тілеймін! 🚀"
                    )
                    try:
                        await bot.send_message(user_id, morning_msg, parse_mode="HTML")
                    except Exception as e:
                        logger.warning(f"Таңғы хабарлама жіберу қатесі ({user_id}): {e}")

            # 2. Кешкі қорытынды еске салу
            evening_time = user.get("evening_reminder_time", "21:00")
            if current_hm == evening_time:
                uncompleted = [h for h in habits if is_habit_scheduled_today(h, now_user.date()) and logs.get(h["id"]) != "done"]
                if uncompleted:
                    evening_msg = (
                        f"🌙 <b>Кеш жарық, {user.get('first_name', 'досым')}!</b>\n\n"
                        f"Бүгінгі күнді қорытындылайтын уақыт келді.\n"
                        f"Мақсаттарыңызды орындап, серияңызды сақтап қалдыңыз ба? 🔥\n\n"
                        f"<i>Төмендегі батырмалармен орындалғандарын белгілеп қойыңыз:</i>"
                    )
                    try:
                        await bot.send_message(
                            user_id,
                            evening_msg,
                            reply_markup=get_today_habits_keyboard(habits, logs),
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.warning(f"Кешкі хабарлама жіберу қатесі ({user_id}): {e}")

            # 3. Нақты әр әдеттің өзіндік еске салу уақыты
            for habit in habits:
                if habit.get("reminder_time") == current_hm:
                    # Егер бүгін демалыс күні (rest day) болса, еске салмаймыз
                    if not is_habit_scheduled_today(habit, now_user.date()):
                        continue
                    # Егер бүгін әлі орындалмаған болса ғана еске саламыз
                    if logs.get(habit["id"]) != "done":
                        goal_note = f"\n🎯 <i>Мақсат: {habit['goal_description']}</i>" if habit.get("goal_description") else ""
                        habit_remind_msg = (
                            f"⏰ <b>Мақсатыңызды еске саламын!</b>\n\n"
                            f"📌 «<b>{habit['title']}</b>»{goal_note}\n\n"
                            f"Бүгін орындадыңыз ба?"
                        )
                        try:
                            await bot.send_message(
                                user_id,
                                habit_remind_msg,
                                reply_markup=get_reminder_action_keyboard(habit["id"]),
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            logger.warning(f"Әдет еске салуын жіберу қатесі ({user_id}): {e}")

    except Exception as e:
        logger.error(f"Еске салу циклінде қате орын алды: {e}")

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Жоспарлағышты іске қосу"""
    scheduler = AsyncIOScheduler()
    # Әр 60 секунд сайын еске салуларды тексереді
    scheduler.add_job(
        check_and_send_reminders,
        trigger="interval",
        seconds=60,
        args=[bot],
        id="check_reminders",
        replace_existing=True
    )
    return scheduler
