import asyncio
import os
import tempfile
from datetime import date, timedelta

async def test_full_flow():
    from database.db import init_db
    from database.models import (
        get_or_create_user,
        add_habit,
        get_user_habits,
        log_habit_status,
        get_user_statistics
    )

    print("1. Тестілеу: Деректер қорын бастапқы орнату...")
    await init_db()

    print("2. Тестілеу: Қолданушыны тіркеу...")
    test_uid = 999999999
    user = await get_or_create_user(test_uid, "test_user", "Азамат")
    assert user["user_id"] == test_uid
    print("   -> Қолданушы тіркелді:", user["first_name"])

    print("3. Тестілеу: Әдет қосу...")
    habit_id = await add_habit(
        user_id=test_uid,
        title="Күнде 20 бет кітап оқу",
        goal_description="Жылына 20 кітап бітіру",
        reminder_time="20:00"
    )
    assert habit_id > 0
    print("   -> Әдет қосылды, ID:", habit_id)

    habits = await get_user_habits(test_uid)
    assert len(habits) >= 1

    print("4. Тестілеу: Серияны (streak) есептеу...")
    today = date.today()
    yesterday = today - timedelta(days=1)

    # Кешегі күнге белгілеу
    await log_habit_status(habit_id, test_uid, yesterday.strftime("%Y-%m-%d"), "done")
    # Бүгінгі күнге белгілеу
    streak_info = await log_habit_status(habit_id, test_uid, today.strftime("%Y-%m-%d"), "done")
    assert streak_info["current_streak"] == 2
    print(f"   -> Серия (Streak) дұрыс есептелді: {streak_info['current_streak']} күн!")

    print("5. Тестілеу: Жалпы статистиканы жинау...")
    stats = await get_user_statistics(test_uid, today.strftime("%Y-%m-%d"))
    assert stats["total_habits"] >= 1
    assert stats["completed_today"] == 1
    print("   -> Статистика табысты тексерілді!")

    print("\n✅ БАРЛЫҚ МОДУЛЬДЕР МЕН ЛОГИКА ТАБЫСТЫ ЖҰМЫС ІСТЕП ТҰР!")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
