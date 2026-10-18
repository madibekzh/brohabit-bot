from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Dict, Any

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Негізгі төменгі мәзір батырмалары"""
    keyboard = [
        [
            KeyboardButton(text="📋 Бүгінгі әдеттер"),
            KeyboardButton(text="➕ Жаңа әдет қосу")
        ],
        [
            KeyboardButton(text="🏋️ Жаттығу жоспары"),
            KeyboardButton(text="📊 Статистика & Серия")
        ],
        [
            KeyboardButton(text="⚙️ Еске салулар & Баптау")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_cancel_or_skip_keyboard(allow_skip: bool = True) -> ReplyKeyboardMarkup:
    """FSM формасында өткізіп жіберу немесе бас тарту батырмалары"""
    buttons = []
    if allow_skip:
        buttons.append([KeyboardButton(text="⏭ Өткізіп жіберу")])
    buttons.append([KeyboardButton(text="❌ Бас тарту")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_frequency_keyboard() -> InlineKeyboardMarkup:
    """Әдеттің жиілігін таңдауға арналған батырмалар"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Күн сайын (7/7 күн)", callback_data="freq:all")],
        [InlineKeyboardButton(text="🏋️ Аптасына 4 күн (Дүй, Сәр, Жұм, Сен)", callback_data="freq:4_days")],
        [InlineKeyboardButton(text="🏃 Аптасына 3 күн (Дүй, Сәр, Жұм)", callback_data="freq:3_days")],
        [InlineKeyboardButton(text="💼 Жұмыс күндері (Дүй–Жұм, 5 күн)", callback_data="freq:weekdays")],
        [InlineKeyboardButton(text="🎯 Аптасына 4 рет (кез келген күні)", callback_data="freq:weekly_4")]
    ])

def get_today_habits_keyboard(habits: List[Dict[str, Any]], logs: Dict[int, str]) -> InlineKeyboardMarkup:
    """Бүгінгі әдеттер тізімі және орындалу мәртебесін өзгертуге арналған inline батырмалар"""
    from database.models import is_habit_scheduled_today, get_habit_display_title

    inline_keyboard = []

    for habit in habits:
        hid = habit["id"]
        status = logs.get(hid, None)
        streak = habit.get("current_streak", 0)
        streak_icon = f" 🔥{streak}" if streak > 0 else ""
        scheduled = is_habit_scheduled_today(habit)
        display_title = get_habit_display_title(habit)

        if status == "done":
            status_text = "✅ Орындалды"
            callback_action = f"toggle:{hid}:undo"
            btn_text = f"{display_title}{streak_icon} — {status_text}"
        elif scheduled:
            status_text = "⭕️ Орындау"
            callback_action = f"toggle:{hid}:done"
            btn_text = f"{display_title}{streak_icon} — {status_text}"
        else:
            # Демалыс күні (Rest day)
            callback_action = f"toggle:{hid}:done"
            btn_text = f"{display_title} — ⭕️ Қосымша"

        inline_keyboard.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=callback_action
            )
        ])

    inline_keyboard.append([
        InlineKeyboardButton(text="🔄 Жаңарту", callback_data="refresh_today"),
        InlineKeyboardButton(text="➕ Жаңа әдет", callback_data="add_habit_inline")
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_reminder_action_keyboard(habit_id: int) -> InlineKeyboardMarkup:
    """Еске салу келген кезде шығатын inline батырмалар"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Орындадым!", callback_data=f"remind_done:{habit_id}"),
            InlineKeyboardButton(text="⏰ 30 мин кейін", callback_data=f"remind_snooze:{habit_id}")
        ],
        [
            InlineKeyboardButton(text="❌ Бүгін үлгермедім", callback_data=f"remind_skip:{habit_id}")
        ]
    ])

def get_habit_manage_keyboard(habit_id: int) -> InlineKeyboardMarkup:
    """Жеке әдетті басқару (өшіру) батырмалары"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 Әдетті өшіру", callback_data=f"delete_habit:{habit_id}"),
            InlineKeyboardButton(text="🔙 Тізімге қайту", callback_data="back_to_habits")
        ]
    ])

def get_settings_keyboard(reminders_enabled: bool, morning_time: str, evening_time: str) -> InlineKeyboardMarkup:
    """Баптаулар inline батырмалары"""
    status_emoji = "🔔 Қосулы" if reminders_enabled else "🔕 Өшірулі"
    toggle_text = "🔕 Еске салуларды өшіру" if reminders_enabled else "🔔 Еске салуларды қосу"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Күйі: {status_emoji}", callback_data="noop")],
        [InlineKeyboardButton(text=toggle_text, callback_data="toggle_reminder_active")],
        [InlineKeyboardButton(text=f"🌅 Таңғы еске салу: {morning_time or '09:00'}", callback_data="set_morning_time")],
        [InlineKeyboardButton(text=f"🌙 Кешкі қорытынды: {evening_time or '21:00'}", callback_data="set_evening_time")],
        [InlineKeyboardButton(text="🔙 Мәзірге қайту", callback_data="back_to_main")]
    ])
