import re
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.models import (
    get_or_create_user,
    update_user_reminders,
    get_user_habits,
    delete_habit
)
from utils.keyboards import (
    get_main_keyboard,
    get_settings_keyboard,
    get_cancel_or_skip_keyboard,
    get_habit_manage_keyboard
)
from utils.fsm_states import SettingsState

router = Router()

@router.message(F.text == "⚙️ Еске салулар & Баптау")
@router.message(Command("settings"))
async def show_settings(message: types.Message):
    user_id = message.from_user.id
    user = await get_or_create_user(user_id, message.from_user.username, message.from_user.first_name)

    enabled = bool(user.get("reminders_enabled", 1))
    morning = user.get("morning_reminder_time", "09:00")
    evening = user.get("evening_reminder_time", "21:00")

    text = (
        "⚙️ <b>Еске салулар және баптаулар</b>\n\n"
        "Бот мақсаттарыңызды ұмытпау үшін күнделікті белгіленген уақытта хабарлама жібереді:\n"
        f"• <b>Таңғы хабарлама:</b> {morning} (күнді жоспарлау)\n"
        f"• <b>Кешкі қорытынды:</b> {evening} (нәтижелерді белгілеу)\n"
        f"• <b>Жалпы күйі:</b> {'Қосулы 🔔' if enabled else 'Өшірулі 🔕'}\n\n"
        "Өзгерту үшін төмендегі батырмаларды таңдаңыз:"
    )

    await message.answer(
        text,
        reply_markup=get_settings_keyboard(enabled, morning, evening),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "toggle_reminder_active")
async def toggle_reminders(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await get_or_create_user(user_id, callback.from_user.username, callback.from_user.first_name)

    current_status = bool(user.get("reminders_enabled", 1))
    new_status = not current_status

    await update_user_reminders(user_id, enabled=new_status)
    await callback.answer(f"Еске салулар {'қосылды 🔔' if new_status else 'өшірілді 🔕'}")

    user = await get_or_create_user(user_id, callback.from_user.username, callback.from_user.first_name)
    morning = user.get("morning_reminder_time", "09:00")
    evening = user.get("evening_reminder_time", "21:00")

    text = (
        "⚙️ <b>Еске салулар және баптаулар</b>\n\n"
        f"• <b>Таңғы хабарлама:</b> {morning}\n"
        f"• <b>Кешкі қорытынды:</b> {evening}\n"
        f"• <b>Жалпы күйі:</b> {'Қосулы 🔔' if new_status else 'Өшірулі 🔕'}"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_settings_keyboard(new_status, morning, evening),
            parse_mode="HTML"
        )
    except Exception:
        pass

@router.callback_query(F.data == "set_morning_time")
async def set_morning_time_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(SettingsState.waiting_for_morning_time)
    await callback.message.answer(
        "🌅 <b>Таңғы еске салу уақытын енгізіңіз:</b>\n"
        "Мысалы: <code>08:00</code> немесе <code>09:30</code>",
        reply_markup=get_cancel_or_skip_keyboard(allow_skip=False),
        parse_mode="HTML"
    )

@router.message(SettingsState.waiting_for_morning_time)
async def process_morning_time(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", text):
        await message.answer("⚠️ Уақыт форматы қате. Мысалы <code>08:30</code> деп жазыңыз:")
        return

    await update_user_reminders(message.from_user.id, morning_time=text)
    await state.clear()
    await message.answer(
        f"✅ Таңғы еске салу уақыты <b>{text}</b> болып орнатылды!",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "set_evening_time")
async def set_evening_time_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(SettingsState.waiting_for_evening_time)
    await callback.message.answer(
        "🌙 <b>Кешкі қорытынды уақытын енгізіңіз:</b>\n"
        "Мысалы: <code>21:00</code> немесе <code>22:30</code>",
        reply_markup=get_cancel_or_skip_keyboard(allow_skip=False),
        parse_mode="HTML"
    )

@router.message(SettingsState.waiting_for_evening_time)
async def process_evening_time(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", text):
        await message.answer("⚠️ Уақыт форматы қате. Мысалы <code>21:00</code> деп жазыңыз:")
        return

    await update_user_reminders(message.from_user.id, evening_time=text)
    await state.clear()
    await message.answer(
        f"✅ Кешкі қорытынды уақыты <b>{text}</b> болып орнатылды!",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer("Басты мәзір:", reply_markup=get_main_keyboard())
