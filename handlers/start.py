from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from database.models import get_or_create_user, get_user_habits
from utils.keyboards import get_main_keyboard, get_cancel_or_skip_keyboard
from utils.fsm_states import AddHabitState

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Досым"
    username = message.from_user.username

    # Қолданушыны тіркеу
    await get_or_create_user(user_id, username, first_name)
    existing_habits = await get_user_habits(user_id)

    # Егер әлі әдеттері болмаса, бірден не әдет қалыптастырғысы келетінін сұраймыз!
    if not existing_habits:
        welcome_text = (
            f"👋 Сәлеметсіз бе, <b>{first_name}</b>!\n\n"
            f"🎯 Мен — сізді үлкен мақсаттарыңызға жақындататын <b>жеке трекер-ботыңызбын</b>.\n"
            f"Үлкен жетістік күнделікті кішкентай әдеттерден құралады.\n\n"
            f"Келіңіз, бастайық! <b>Қандай әдет қалыптастырғыңыз келеді?</b>\n\n"
            f"<i>Мысалы:</i>\n"
            f"• Күнде 20 бет кітап оқу 📖\n"
            f"• 10,000 қадам жүру 👟\n"
            f"• Ағылшынша 15 сөз жаттау 🇬🇧\n"
            f"• Таңғы жаттығу жасау 🏋️‍♂️\n"
            f"• 2 литр су ішу 💧\n\n"
            f"Өз әдетіңізді жазып жіберіңіз:"
        )
        await state.set_state(AddHabitState.waiting_for_title)
        await message.answer(welcome_text, reply_markup=get_cancel_or_skip_keyboard(allow_skip=False), parse_mode="HTML")
    else:
        welcome_back_text = (
            f"👋 Қайта оралуыңызбен, <b>{first_name}</b>!\n\n"
            f"Бүгінгі мақсаттарыңыз бен әдеттеріңіз күтіп тұр. "
            f"Төмендегі мәзірді пайдаланып, бүгінгі нәтижелерді белгілеңіз немесе жаңа әдет қосыңыз."
        )
        await message.answer(welcome_back_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "💡 <b>Ботты қалай тиімді пайдалануға болады?</b>\n\n"
        "1. <b>Әдет қосу</b> — Сізді мақсатыңызға апаратын күнделікті әрекетті белгілеңіз.\n"
        "2. <b>Еске салу</b> — Бот уақытында хабарлап, мақсатты ұмытпауға септігін тигізеді.\n"
        "3. <b>Белгілеу</b> — Әр орындаған сайын ✅ түймесін басыңыз. Үздіксіз серияңыз (🔥 Streak) өседі!\n"
        "4. <b>Статистика</b> — Апталық және айлық қарқыныңызды бақылаңыз.\n\n"
        "<b>Командалар:</b>\n"
        "/start — Ботты бастау\n"
        "/habits — Бүгінгі әдеттерді көру\n"
        "/add — Жаңа әдет қосу\n"
        "/stats — Статистика & Серия\n"
        "/settings — Еске салуларды баптау\n"
        "/cancel — Кез келген енгізуден бас тарту"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard(), parse_mode="HTML")
