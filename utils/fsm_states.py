from aiogram.fsm.state import State, StatesGroup

class AddHabitState(StatesGroup):
    waiting_for_title = State()          # Әдеттің атауы
    waiting_for_goal = State()           # Бұл әдет жетелейтін үлкен мақсат
    waiting_for_frequency = State()      # Жиілігі (күн сайын, аптасына 4 күн және т.б.)
    waiting_for_reminder_time = State()  # Еске салу уақыты (HH:MM)

class SettingsState(StatesGroup):
    waiting_for_morning_time = State()   # Таңғы жоспар уақыты
    waiting_for_evening_time = State()   # Кешкі қорытынды уақыты
    waiting_for_timezone = State()       # Уақыт белдеуі
