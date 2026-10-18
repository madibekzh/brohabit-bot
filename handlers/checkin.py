from datetime import date
from aiogram import Router, types, F
from database.models import (
    log_habit_status,
    get_habit_by_id,
    get_user_habits,
    get_habit_logs_for_date,
    delete_habit
)
from utils.keyboards import get_today_habits_keyboard
from services.quotes import get_random_quote

router = Router()

@router.callback_query(F.data.startswith("toggle:"))
async def handle_toggle_habit(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    habit_id = int(parts[1])
    action = parts[2]
    user_id = callback.from_user.id
    today_str = date.today().strftime("%Y-%m-%d")

    habit = await get_habit_by_id(habit_id)
    if not habit or habit["user_id"] != user_id:
        await callback.answer("⚠️ Әдет табылмады немесе қолжетімді емес.", show_alert=True)
        return

    if action == "done":
        streak_info = await log_habit_status(habit_id, user_id, today_str, status="done")
        streak = streak_info.get("current_streak", 1)
        alert_msg = f"Жарайсың! ✅ «{habit['title']}» орындалды!\n🔥 Үздіксіз серия: {streak} күн!"
        await callback.answer(alert_msg, show_alert=False)
    else:
        # Undo / қайтару
        await log_habit_status(habit_id, user_id, today_str, status="skipped")
        await callback.answer("⭕️ Орындалу белгісі алынып тасталды.", show_alert=False)

    # Хабарламаны жаңарту
    habits = await get_user_habits(user_id)
    logs = await get_habit_logs_for_date(user_id, today_str)

    from handlers.habit_manager import build_today_habits_text
    text = build_today_habits_text(habits, logs)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_today_habits_keyboard(habits, logs),
            parse_mode="HTML"
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("remind_done:"))
async def handle_reminder_done(callback: types.CallbackQuery):
    habit_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    today_str = date.today().strftime("%Y-%m-%d")

    habit = await get_habit_by_id(habit_id)
    if not habit:
        await callback.answer("Әдет табылмады.")
        return

    streak_info = await log_habit_status(habit_id, user_id, today_str, status="done")
    streak = streak_info.get("current_streak", 1)

    await callback.answer("Тамаша!", show_alert=False)
    await callback.message.edit_text(
        f"✅ <b>«{habit['title']}» орындалды!</b>\n\n"
        f"🔥 <b>Үздіксіз серия:</b> {streak} күн!\n"
        f"🎯 Мақсатыңызға тағы бір қадам жақындадыңыз!\n\n"
        f"<i>{get_random_quote()}</i>",
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("remind_skip:"))
async def handle_reminder_skip(callback: types.CallbackQuery):
    habit_id = int(callback.data.split(":")[1])
    habit = await get_habit_by_id(habit_id)
    title = habit["title"] if habit else "Әдет"

    await callback.answer()
    await callback.message.edit_text(
        f"👌 Түсінікті. «{title}» бүгінге өткізілді.\n\n"
        f"💪 Бастысы — еңсеңді түсірмеу! Ертең жаңа күн, жаңа мүмкіндік!",
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("remind_snooze:"))
async def handle_reminder_snooze(callback: types.CallbackQuery):
    await callback.answer("⏰ Жақсы, сәлден соң тағы еске саламын!", show_alert=True)
    await callback.message.edit_text(
        "⏰ Еске салу кейінге қалдырылды. Уақытыңыз болғанда «📋 Бүгінгі әдеттер» мәзірінен белгілей аласыз."
    )

@router.callback_query(F.data.startswith("delete_habit:"))
async def handle_delete_habit(callback: types.CallbackQuery):
    habit_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success = await delete_habit(habit_id, user_id)
    if success:
        await callback.answer("Әдет өшірілді 🗑", show_alert=True)
        await callback.message.edit_text("✅ Әдет сәтті өшірілді.")
    else:
        await callback.answer("Өшіру мүмкін болмады.", show_alert=True)
