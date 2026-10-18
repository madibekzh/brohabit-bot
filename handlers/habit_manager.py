import re
from datetime import date
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.models import (
    add_habit,
    get_user_habits,
    get_habit_logs_for_date,
    get_habit_by_id,
    delete_habit,
    log_habit_status
)
from utils.keyboards import (
    get_main_keyboard,
    get_cancel_or_skip_keyboard,
    get_today_habits_keyboard,
    get_habit_manage_keyboard
)
from utils.fsm_states import AddHabitState
from services.quotes import get_random_quote

router = Router()

# ==================== БАС ТАРТУ (CANCEL) ====================

@router.message(F.text.in_({"❌ Бас тарту", "/cancel"}))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("❌ Әрекет тоқтатылды.", reply_markup=get_main_keyboard())
    else:
        await message.answer("Бас тартатын белсенді әрекет жоқ.", reply_markup=get_main_keyboard())

# ==================== ЖАҢА ӘДЕТ ҚОСУ ====================

@router.message(F.text == "➕ Жаңа әдет қосу")
@router.message(Command("add"))
async def start_add_habit(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddHabitState.waiting_for_title)
    await message.answer(
        "✨ <b>Қандай әдет қалыптастырғыңыз келеді?</b>\n\n"
        "Мысалы:\n"
        "• <i>Күнде 20 бет кітап оқу</i> 📖\n"
        "• <i>10,000 қадам</i> 👟\n"
        "• <i>Күнделікті 15 мин ағылшын тілі</i> 🇬🇧\n"
        "• <i>Спорт / Жаттығу</i> 🏋️\n\n"
        "Әдеттің атын жазыңыз:",
        reply_markup=get_cancel_or_skip_keyboard(allow_skip=False),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "add_habit_inline")
async def start_add_habit_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.set_state(AddHabitState.waiting_for_title)
    await callback.message.answer(
        "✨ <b>Қандай әдет қалыптастырғыңыз келеді?</b>\n\n"
        "Әдеттің атын жазып жіберіңіз:",
        reply_markup=get_cancel_or_skip_keyboard(allow_skip=False),
        parse_mode="HTML"
    )

@router.message(AddHabitState.waiting_for_title)
async def process_habit_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 2:
        await message.answer("⚠️ Өтініш, әдет атауын кемінде 2 әріппен жазыңыз:")
        return

    await state.update_data(title=title)
    await state.set_state(AddHabitState.waiting_for_goal)

    await message.answer(
        f"Тамаша! «<b>{title}</b>» таңдалды 🎯\n\n"
        f"Енді айтыңызшы, <b>бұл әдет сізді қандай үлкен мақсатқа жақындатады?</b>\n"
        f"<i>(Мысалы: «Жылына 20 кітап бітіру», «Денсаулықты түзеу», «Ағылшын тілін еркін сөйлеу» т.б.)</i>\n\n"
        f"Егер мақсатты жазғыңыз келмесе, төмендегі батырманы басыңыз:",
        reply_markup=get_cancel_or_skip_keyboard(allow_skip=True),
        parse_mode="HTML"
    )

@router.message(AddHabitState.waiting_for_goal)
async def process_habit_goal(message: types.Message, state: FSMContext):
    text = message.text.strip()
    goal = "" if text == "⏭ Өткізіп жіберу" else text
    await state.update_data(goal=goal)
    await state.set_state(AddHabitState.waiting_for_frequency)

    await message.answer(
        "🗓 <b>Бұл әдетті аптасына қанша рет орындайсыз?</b>\n\n"
        "Мысалы, егер жаттығуды аптасына 4 күн істесеңіз — қалған демалыс күндері (rest days) бот мазаламайды және серияңыз үзілмейді! 🔥\n\n"
        "Төмендегі батырмалардың бірін таңдаңыз:",
        reply_markup=get_frequency_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(AddHabitState.waiting_for_frequency, F.data.startswith("freq:"))
async def process_frequency_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    choice = callback.data.split(":")[1]

    if choice == "4_days":
        target_days = "1,3,5,6"  # Дүйсенбі, Сәрсенбі, Жұма, Сенбі
        weekly_target = 4
        desc = "Аптасына 4 күн (Дүй, Сәр, Жұм, Сен)"
    elif choice == "3_days":
        target_days = "1,3,5"    # Дүйсенбі, Сәрсенбі, Жұма
        weekly_target = 3
        desc = "Аптасына 3 күн (Дүй, Сәр, Жұм)"
    elif choice == "weekdays":
        target_days = "1,2,3,4,5"
        weekly_target = 5
        desc = "Жұмыс күндері (Дүй–Жұм)"
    elif choice == "weekly_4":
        target_days = "all"
        weekly_target = 4
        desc = "Аптасына 4 рет (кез келген күні)"
    else:
        target_days = "all"
        weekly_target = 7
        desc = "Күн сайын (7/7 күн)"

    await state.update_data(target_days=target_days, weekly_target=weekly_target, freq_desc=desc)
    await state.set_state(AddHabitState.waiting_for_reminder_time)

    await callback.message.answer(
        f"Таңдалды: <b>{desc}</b> 🗓\n\n"
        f"⏰ <b>Осы күндері қай уақытта еске салайын?</b>\n"
        f"Уақытты <code>САҒАТ:МИНУТ</code> форматында жазыңыз (мысалы: <code>19:00</code>, <code>20:30</code>).\n"
        f"Немесе «⏭ Өткізіп жіберу» түймесін басыңыз (әдепкі: 20:00):",
        reply_markup=get_cancel_or_skip_keyboard(allow_skip=True),
        parse_mode="HTML"
    )

@router.message(AddHabitState.waiting_for_frequency)
async def process_frequency_text(message: types.Message, state: FSMContext):
    # Егер мәтін жазса
    text = message.text.strip().lower()
    if "4" in text:
        target_days = "1,3,5,6"
        weekly_target = 4
        desc = "Аптасына 4 күн (Дүй, Сәр, Жұм, Сен)"
    elif "3" in text:
        target_days = "1,3,5"
        weekly_target = 3
        desc = "Аптасына 3 күн (Дүй, Сәр, Жұм)"
    else:
        target_days = "all"
        weekly_target = 7
        desc = "Күн сайын"

    await state.update_data(target_days=target_days, weekly_target=weekly_target, freq_desc=desc)
    await state.set_state(AddHabitState.waiting_for_reminder_time)

    await message.answer(
        f"Таңдалды: <b>{desc}</b> 🗓\n\n"
        f"⏰ <b>Осы күндері қай уақытта еске салайын?</b>\n"
        f"Уақытты жазыңыз (мысалы: <code>19:00</code> немесе /skip):",
        reply_markup=get_cancel_or_skip_keyboard(allow_skip=True),
        parse_mode="HTML"
    )

@router.message(AddHabitState.waiting_for_reminder_time)
async def process_reminder_time(message: types.Message, state: FSMContext):
    text = message.text.strip()
    reminder_time = "20:00"

    if text != "⏭ Өткізіп жіберу":
        time_match = re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", text)
        if not time_match:
            await message.answer(
                "⚠️ Уақыт форматы дұрыс емес. Өтініш, <code>20:00</code> немесе <code>09:30</code> сияқты жазыңыз, немесе «⏭ Өткізіп жіберу» басыңыз:",
                reply_markup=get_cancel_or_skip_keyboard(allow_skip=True),
                parse_mode="HTML"
            )
            return
        reminder_time = text

    data = await state.get_data()
    title = data["title"]
    goal = data.get("goal", "")
    target_days = data.get("target_days", "all")
    weekly_target = data.get("weekly_target", 7)
    freq_desc = data.get("freq_desc", "Күн сайын")

    habit_id = await add_habit(
        user_id=message.from_user.id,
        title=title,
        goal_description=goal,
        reminder_time=reminder_time,
        target_days=target_days,
        weekly_target=weekly_target
    )

    await state.clear()

    goal_str = f"\n🎯 <b>Басты мақсат:</b> {goal}" if goal else ""
    success_text = (
        f"🎉 <b>Жаңа әдет сәтті қосылды!</b>\n\n"
        f"📌 <b>Әдет:</b> {title}{goal_str}\n"
        f"🗓 <b>Жиілігі:</b> {freq_desc}\n"
        f"⏰ <b>Еске салу уақыты:</b> {reminder_time}\n\n"
        f"💡 <i>{get_random_quote()}</i>\n\n"
        f"Жаттығу күндері бот уақытында еске салып тұрады, ал демалыс күндері серияңыз үзілмейді! 🔥"
    )

    await message.answer(success_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

KZ_WEEKDAYS = {
    1: "Дүйсенбі",
    2: "Сейсенбі",
    3: "Сәрсенбі",
    4: "Бейсенбі",
    5: "Жұма",
    6: "Сенбі",
    7: "Жексенбі"
}

def build_today_habits_text(habits, logs) -> str:
    today = date.today()
    today_str = today.strftime("%d.%m.%Y")
    dow_name = KZ_WEEKDAYS.get(today.isoweekday(), "")

    completed_count = sum(1 for hid in habits if logs.get(hid["id"]) == "done")
    total_count = len(habits)

    progress_percent = int((completed_count / total_count) * 100) if total_count > 0 else 0
    filled_blocks = int(progress_percent / 10)
    progress_bar = "▓" * filled_blocks + "░" * (10 - filled_blocks)

    # Жаттығу күні ме әлде демалыс күні ме анықтау
    workout_note = ""
    for h in habits:
        if "4 күндік" in h["title"] or "сплит" in h["title"].lower() or "треннировка" in h["title"].lower():
            dow = today.isoweekday()
            if dow in (1, 2, 4, 5):
                from database.models import SPLIT_DAY_NAMES
                workout_note = f"\n🏋️ <b>Бүгінгі жаттығу:</b> {SPLIT_DAY_NAMES.get(dow, '')}\n"
            else:
                workout_note = f"\n🌴 <b>Бүгін жаттығуда ДЕМАЛЫС (Rest Day).</b> Серияңыз сақтаулы! 🔥\n"
            break

    return (
        f"📋 <b>Бүгінгі әдеттеріңіз ({today_str}, {dow_name}):</b>\n"
        f"{workout_note}\n"
        f"Прогресс: <code>[{progress_bar}] {progress_percent}%</code> ({completed_count}/{total_count})\n\n"
        f"<i>Төмендегі батырмаларды басып, орындалғандарын белгілеңіз:</i>"
    )

@router.message(F.text == "📋 Бүгінгі әдеттер")
@router.message(Command("habits"))
async def show_habits_list(message: types.Message):
    user_id = message.from_user.id
    today_str = date.today().strftime("%Y-%m-%d")

    habits = await get_user_habits(user_id)
    if not habits:
        await message.answer(
            "Сізде әлі қосылған әдеттер жоқ.\n«➕ Жаңа әдет қосу» батырмасын басып, алғашқы әдетіңізді енгізіңіз!",
            reply_markup=get_main_keyboard()
        )
        return

    logs = await get_habit_logs_for_date(user_id, today_str)
    text = build_today_habits_text(habits, logs)

    await message.answer(
        text,
        reply_markup=get_today_habits_keyboard(habits, logs),
        parse_mode="HTML"
    )

# ==================== ТІЗІМДІ ЖАҢАРТУ & БАСҚАРУ ====================

@router.callback_query(F.data == "refresh_today")
@router.callback_query(F.data == "back_to_habits")
async def refresh_today_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    today_str = date.today().strftime("%Y-%m-%d")

    habits = await get_user_habits(user_id)
    if not habits:
        await callback.message.edit_text(
            "Әзірге белсенді әдеттер жоқ.",
            reply_markup=None
        )
        await callback.answer()
        return

    logs = await get_habit_logs_for_date(user_id, today_str)
    text = build_today_habits_text(habits, logs)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_today_habits_keyboard(habits, logs),
            parse_mode="HTML"
        )
    except Exception:
        pass
    await callback.answer()
