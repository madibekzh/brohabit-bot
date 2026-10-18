from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

def get_workout_plan_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1️⃣ Кеуде + Трицепс (Push)", callback_data="plan:day1"),
            InlineKeyboardButton(text="2️⃣ Арқа («Крыло») + Бицепс (Pull)", callback_data="plan:day2")
        ],
        [
            InlineKeyboardButton(text="3️⃣ Сан (Аяқ) + Пресс (Legs)", callback_data="plan:day3"),
            InlineKeyboardButton(text="4️⃣ Қолдар суперсет + Иық (Arms)", callback_data="plan:day4")
        ],
        [
            InlineKeyboardButton(text="🔄 Жалпы ережелер мен кеңестер", callback_data="plan:tips")
        ],
        [
            InlineKeyboardButton(text="➕ Осы жаттығуды әдеттерге қосу 📌", callback_data="plan:add_to_habits")
        ]
    ])

DAY_DETAILS = {
    "day1": (
        "🛡 <b>1-КҮН: Кеуде + Трицепс (Итеру күні / Push)</b>\n"
        "<i>Кеудені ашып, қолдың артқы бөлігіне рельеф беру.</i>\n\n"
        "1. <b>Кең отжимания (еденнен):</b> 4 подход × 15–20 рет\n"
        "   <i>(кеуде бұлшықетін максималды созу)</i>\n"
        "2. <b>Аяқты көтеріп отжимания (орындыққа қойып):</b> 3 подход × 12–15 рет\n"
        "   <i>(кеуденің жоғарғы бөлігіне)</i>\n"
        "3. <b>Трицепс тренажерінде төмен басу (блокта):</b> 4 подход × 12–15 рет\n"
        "   <i>(шынтақты денеге жабыстырып, соңында 1 сек ұстау)</i>\n"
        "4. <b>Алмазды (тар) отжимания немесе кері отжимания:</b> 3 подход × 10–12 рет\n"
        "   <i>(трицепсті түбіне дейін шаршату)</i>\n"
        "5. <b>Планка:</b> 3 подход × 60 секунд"
    ),
    "day2": (
        "🦅 <b>2-КҮН: Арқа («Крыло») + Бицепс (Тарту күні / Pull)</b>\n"
        "<i>V-тәрізді кең сымбат және мықты қолдар.</i>\n\n"
        "1. <b>Крыло тренажерінде кеудеге тарту:</b> 4 подход × 10–12 рет\n"
        "   <i>(шынтақты артқа тартып, жауырынды барынша қысу)</i>\n"
        "2. <b>Крыло тренажерінде тар ұстаумен тарту:</b> 3 подход × 12 рет\n"
        "   <i>(арқаның ортасын қалыңдату)</i>\n"
        "3. <b>Крыло тренажерінде түзу қолмен пулловер:</b> 3 подход × 15 рет\n"
        "   <i>(қанатты оқшаулап күйдіру)</i>\n"
        "4. <b>Бицепс тренажерінде қолды бүгу:</b> 4 подход × 10–12 рет\n"
        "   <i>(денені тербетпей, таза күшпен көтеру)</i>\n"
        "5. <b>Бицепске молот (блокта немесе гантельмен):</b> 3 подход × 12 рет\n"
        "   <i>(қолдың қалыңдығы үшін)</i>\n"
        "6. <b>«Қайық» (еденде белді көтеру):</b> 3 подход × 15 рет"
    ),
    "day3": (
        "🦵 <b>3-КҮН: Сан (Аяқ) + Пресс (Legs & Core)</b>\n"
        "<i>Тестостерон мен күш көзі — төменгі денеге толық жүктеме.</i>\n\n"
        "1. <b>Сан тренажерінде аяқты жазу (Разгибания):</b> 4 подход × 15 рет\n"
        "   <i>(санның алдыңғы квадрицепсін күйдіру)</i>\n"
        "2. <b>Приседания (терең отыру):</b> 4 подход × 15–20 рет\n"
        "   <i>(өкшемен итеру, тізені ішке жібермеу)</i>\n"
        "3. <b>Выпады (әр аяққа кезекпен):</b> 3 подход × 12 рет\n"
        "4. <b>Сан тренажерінде аяқты бүгу / Ягодичный мостик:</b> 4 подход × 12–15 рет\n"
        "   <i>(санның артқы бөлігіне)</i>\n"
        "5. <b>Жатып аяқты көтеру (төменгі пресс):</b> 4 подход × 15–20 рет\n"
        "6. <b>Скручивания (пресс):</b> 3 подход × 25 рет"
    ),
    "day4": (
        "⚡️ <b>4-КҮН: Қолдар (Бицепс + Трицепс) + Иық (Arms & Aesthetic)</b>\n"
        "<i>Қолдарға қуатты пампинг және дене пішінін шыңдау.</i>\n\n"
        "1. <b>🔥 СУПЕРСЕТ (демалыссыз кезектесіп):</b>\n"
        "   • Бицепс тренажерінде: 12 рет\n"
        "   • Трицепс блогында: 12 рет\n"
        "   <i>(Осылай 4 айналым, арасында 90 сек демалыс)</i>\n"
        "2. <b>Крыло тренажерінде кеудеге орташа тарту:</b> 3 подход × 12 рет\n"
        "3. <b>Иыққа отжимания (бұрыштап / домик):</b> 4 подход × 10–12 рет\n"
        "   <i>(дельталарды дөңгелету)</i>\n"
        "4. <b>Пресс «Велосипед» + Вакуум:</b> 3 подход × 20 рет"
    ),
    "tips": (
        "💡 <b>Бастапқы 2 айдағы 4 алтын ереже:</b>\n\n"
        "1. <b>Кесте:</b> Дүйсенбі (1), Сейсенбі (2), Бейсенбі (3), Жұма немесе Сенбі (4). Сәрсенбі және Жексенбі — міндетті демалыс!\n"
        "2. <b>Демалыс:</b> Подходтар арасында 60–90 секунд демалыңыз.\n"
        "3. <b>Салмақ:</b> Соңғы 2 қайталауды күшпен, бірақ дұрыс техникамен әрең жасайтындай салмақ қойыңыз.\n"
        "4. <b>Ақуыз:</b> Күнделікті ет, жұмыртқа, сүзбе жеп, жеткілікті су ішіңіз."
    )
}

@router.message(F.text.in_({"🏋️ Жаттығу жоспары", "/plan"}))
@router.message(Command("plan"))
async def show_workout_plan(message: types.Message):
    text = (
        "🏋️ <b>Сіздің жеке 4 күндік жаттығу бағдарламаңыз:</b>\n\n"
        "Бұл бағдарлама сіздің тренажерлеріңізге арнайы биомеханикалық заңдармен (Push / Pull / Legs / Arms) жасалған.\n\n"
        "Күндердің бірін таңдап, нақты жаттығуларды қараңыз:"
    )
    await message.answer(text, reply_markup=get_workout_plan_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("plan:"))
async def plan_callback(callback: types.CallbackQuery):
    day_key = callback.data.split(":")[1]

    if day_key == "add_to_habits":
        from database.models import get_user_habits, add_habit
        from utils.keyboards import get_main_keyboard

        user_id = callback.from_user.id
        habits = await get_user_habits(user_id)
        existing = any("Треннировка" in h["title"] for h in habits)

        if existing:
            await callback.answer("Бұл әдет сіздің тізіміңізде бар! ✅", show_alert=True)
            return

        await add_habit(
            user_id=user_id,
            title="🏋️ Треннировка (4 күндік сплит)",
            goal_description="Күшті арттыру және дене сымбатын қалыптастыру",
            reminder_time="19:00",
            target_days="1,2,4,5",
            weekly_target=4
        )
        await callback.answer("Жаттығу әдеттер тізіміңізге сәтті қосылды! 🎉", show_alert=True)
        await callback.message.answer(
            "🎉 <b>«🏋️ Треннировка (4 күндік сплит)» әдетіңіз қосылды!</b>\n\n"
            "Енді «📋 Бүгінгі әдеттер» мәзірін бассаңыз, треннировка күндері тізімде пайда болады!",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        return

    content = DAY_DETAILS.get(day_key, "Ақпарат табылмады.")

    await callback.answer()
    try:
        await callback.message.edit_text(
            content,
            reply_markup=get_workout_plan_keyboard(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            content,
            reply_markup=get_workout_plan_keyboard(),
            parse_mode="HTML"
        )
