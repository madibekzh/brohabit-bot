from datetime import date
from aiogram import Router, types, F
from aiogram.filters import Command
from database.models import get_user_statistics
from utils.keyboards import get_main_keyboard, get_habit_manage_keyboard
from services.quotes import get_random_quote

router = Router()

@router.message(F.text == "📊 Статистика & Серия")
@router.message(Command("stats"))
async def show_statistics(message: types.Message):
    user_id = message.from_user.id
    today_str = date.today().strftime("%Y-%m-%d")

    stats = await get_user_statistics(user_id, today_str)

    total_habits = stats["total_habits"]
    if total_habits == 0:
        await message.answer(
            "📊 Статистика көру үшін алдымен кем дегенде бір әдет қосыңыз.\n"
            "«➕ Жаңа әдет қосу» батырмасын басыңыз!",
            reply_markup=get_main_keyboard()
        )
        return

    completed_today = stats["completed_today"]
    rate_today = int(stats["completion_rate_today"])
    filled_blocks = int(rate_today / 10)
    progress_bar = "▓" * filled_blocks + "░" * (10 - filled_blocks)

    week_completions = stats["week_completions"]
    total_completions = stats["total_completions"]
    max_streak = stats["max_current_streak"]
    best_streak = stats["best_streak"]
    habits = stats["habits"]
    today_logs = stats["today_logs"]

    habits_list_text = []
    for h in habits:
        is_done = today_logs.get(h["id"]) == "done"
        icon = "✅" if is_done else "⭕️"
        streak = h.get("current_streak", 0)
        goal_text = f" (Мақсат: <i>{h['goal_description']}</i>)" if h.get("goal_description") else ""
        habits_list_text.append(f"{icon} <b>{h['title']}</b> — 🔥 Серия: {streak} күн{goal_text}")

    habits_block = "\n".join(habits_list_text)

    response_text = (
        f"📊 <b>Сіздің жетістіктер статистикасы:</b>\n\n"
        f"📅 <b>Бүгінгі орындалу:</b>\n"
        f"<code>[{progress_bar}] {rate_today}%</code> ({completed_today}/{total_habits})\n\n"
        f"🔥 <b>Ағымдағы ең ұзақ серия:</b> {max_streak} күн\n"
        f"🏆 <b>Рекордтық үздіксіздік:</b> {best_streak} күн\n"
        f"📈 <b>Соңғы 7 күнде:</b> {week_completions} рет орындалды\n"
        f"⭐️ <b>Жалпы барлық уақытта:</b> {total_completions} рет орындалды\n\n"
        f"────────────────────\n"
        f"<b>Әдеттер мен мақсаттар тізімі:</b>\n"
        f"{habits_block}\n\n"
        f"<i>{get_random_quote()}</i>"
    )

    await message.answer(response_text, reply_markup=get_main_keyboard(), parse_mode="HTML")
