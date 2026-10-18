from datetime import datetime, date, timedelta
import aiosqlite
from typing import List, Optional, Dict, Any
from config import DB_PATH

async def get_or_create_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> Dict[str, Any]:
    """Қолданушыны табу немесе жаңадан тіркеу"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if user:
                return dict(user)

        # Жаңа қолданушы қосу
        await db.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        """, (user_id, username or "", first_name or ""))
        await db.commit()

        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            new_user = await cursor.fetchone()
            return dict(new_user)

async def update_user_timezone(user_id: int, timezone: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (timezone, user_id))
        await db.commit()

async def update_user_reminders(user_id: int, morning_time: Optional[str] = None, evening_time: Optional[str] = None, enabled: Optional[bool] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if morning_time is not None:
            await db.execute("UPDATE users SET morning_reminder_time = ? WHERE user_id = ?", (morning_time, user_id))
        if evening_time is not None:
            await db.execute("UPDATE users SET evening_reminder_time = ? WHERE user_id = ?", (evening_time, user_id))
        if enabled is not None:
            await db.execute("UPDATE users SET reminders_enabled = ? WHERE user_id = ?", (1 if enabled else 0, user_id))
        await db.commit()

async def get_all_users_for_reminder() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE reminders_enabled = 1") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

# ==================== ӘДЕТТЕР / HABITS ====================

SPLIT_DAY_NAMES = {
    1: "1-күн: Кеуде + Трицепс (Push)",
    2: "2-күн: Арқа («Крыло») + Бицепс (Pull)",
    3: "Демалыс (Rest Day)",
    4: "3-күн: Сан (Аяқ) + Пресс (Legs)",
    5: "4-күн: Қолдар суперсет + Иық (Arms)",
    6: "Демалыс (Rest Day)",
    7: "Демалыс (Rest Day)",
}

def is_habit_scheduled_today(habit: Dict[str, Any], check_date: Optional[date] = None) -> bool:
    """Әдеттің бүгінгі күнге жоспарланғанын анықтау"""
    target_days = habit.get("target_days") or "all"
    if target_days == "all":
        return True
    if check_date is None:
        check_date = date.today()
    dow = str(check_date.isoweekday())  # 1: Дүйсенбі ... 7: Жексенбі
    allowed = [d.strip() for d in target_days.split(",") if d.strip()]
    return dow in allowed

def get_habit_display_title(habit: Dict[str, Any], check_date: Optional[date] = None) -> str:
    """Егер әдет сплит жаттығуы болса, бүгінгі күннің нақты түрін береді"""
    title = habit.get("title", "")
    if "4 күндік" in title or "сплит" in title.lower() or "треннировка" in title.lower():
        if check_date is None:
            check_date = date.today()
        dow = check_date.isoweekday()
        if dow in (3, 6, 7):
            return "🌴 Треннировка: Демалыс (Rest Day)"
        elif dow in SPLIT_DAY_NAMES:
            return f"🏋️ {SPLIT_DAY_NAMES[dow]}"
    return title

def get_habit_days_label(target_days: str) -> str:
    """Күндердің қазақша қысқа атауы"""
    if not target_days or target_days == "all":
        return "Күн сайын"
    names = {"1": "Дүй", "2": "Сей", "3": "Сәр", "4": "Бей", "5": "Жұм", "6": "Сен", "7": "Жек"}
    parts = [names.get(d.strip(), d.strip()) for d in target_days.split(",") if d.strip()]
    return ", ".join(parts)

async def add_habit(
    user_id: int,
    title: str,
    goal_description: str = "",
    reminder_time: str = "20:00",
    target_days: str = "all",
    weekly_target: int = 7
) -> int:
    """Жаңа әдет қосу (жиілік және нақты күндермен)"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO habits (user_id, title, goal_description, reminder_time, target_days, weekly_target)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, title.strip(), goal_description.strip(), reminder_time.strip(), target_days.strip(), weekly_target))
        await db.commit()
        return cursor.lastrowid

async def get_user_habits(user_id: int, only_active: bool = True) -> List[Dict[str, Any]]:
    """Қолданушының барлық әдеттерін алу"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM habits WHERE user_id = ?"
        params = [user_id]
        if only_active:
            query += " AND is_active = 1"
        query += " ORDER BY id ASC"

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_habit_by_id(habit_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def delete_habit(habit_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id))
        await db.commit()
        return cursor.rowcount > 0

# ==================== ОРЫНДАЛУ & БЕЛГІЛЕУ / LOGS ====================

async def log_habit_status(habit_id: int, user_id: int, target_date: str, status: str = "done") -> Dict[str, Any]:
    """Әдеттің күндік мәртебесін жазу және сериясын (streak) қайта есептеу"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO habit_logs (habit_id, user_id, log_date, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(habit_id, log_date) DO UPDATE SET status = excluded.status
        """, (habit_id, user_id, target_date, status))
        await db.commit()

    streak_info = await update_habit_streaks(habit_id, target_date)
    return streak_info

async def get_habit_logs_for_date(user_id: int, target_date: str) -> Dict[int, str]:
    """Белгілі бір күндегі әдеттердің күйін сөздік түрінде қайтару {habit_id: status}"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT habit_id, status FROM habit_logs
            WHERE user_id = ? AND log_date = ?
        """, (user_id, target_date)) as cursor:
            rows = await cursor.fetchall()
            return {r["habit_id"]: r["status"] for r in rows}

async def update_habit_streaks(habit_id: int, ref_date_str: str) -> Dict[str, int]:
    """
    Тарих бойынша үздіксіз серияны (current_streak) есептеу.
    Егер әдет аптасына 4 күн болса, демалыс күндері (rest days) серияны бұзбайды!
    """
    habit = await get_habit_by_id(habit_id)
    if not habit:
        return {"current_streak": 0, "longest_streak": 0}

    target_days = habit.get("target_days") or "all"
    is_all_days = (target_days == "all")
    allowed_dows = [int(d.strip()) for d in target_days.split(",") if d.strip()] if not is_all_days else list(range(1, 8))

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT log_date FROM habit_logs
            WHERE habit_id = ? AND status = 'done'
            ORDER BY log_date ASC
        """, (habit_id,)) as cursor:
            rows = await cursor.fetchall()

        if not rows:
            await db.execute("""
                UPDATE habits SET current_streak = 0, longest_streak = 0
                WHERE id = ?
            """, (habit_id,))
            await db.commit()
            return {"current_streak": 0, "longest_streak": 0}

        done_set = set(datetime.strptime(r["log_date"], "%Y-%m-%d").date() for r in rows)

        # Бүгіннен бастап кері санаймыз
        today_date = date.today()
        current_streak = 0

        # Соңғы жоспарланған күнді анықтау (бүгін немесе өткен жоспарланған күн)
        check_d = today_date
        # Егер бүгін жоспарланбаған күн (демалыс) болса және бүгін жасалмаса:
        if check_d.isoweekday() not in allowed_dows and check_d not in done_set:
            check_d = check_d - timedelta(days=1)
            while check_d.isoweekday() not in allowed_dows:
                check_d -= timedelta(days=1)

        # Тексеру: соңғы жоспарланған күнде немесе оның алдындағы күнде орындалды ма?
        if check_d in done_set:
            # Артқа қарай тек ЖОСПАРЛАНҒАН күндерді тексереміз
            step_d = check_d
            while True:
                if step_d.isoweekday() in allowed_dows:
                    if step_d in done_set:
                        current_streak += 1
                    else:
                        break
                step_d -= timedelta(days=1)
                # Шегі 365 күн
                if (today_date - step_d).days > 365:
                    break
        else:
            # Соңғы жоспарланған күн өткізіп алынды, бірақ кешегі соңғы күн орындалды ма?
            prev_scheduled = check_d - timedelta(days=1)
            while prev_scheduled.isoweekday() not in allowed_dows:
                prev_scheduled -= timedelta(days=1)
            if prev_scheduled in done_set:
                step_d = prev_scheduled
                while True:
                    if step_d.isoweekday() in allowed_dows:
                        if step_d in done_set:
                            current_streak += 1
                        else:
                            break
                    step_d -= timedelta(days=1)
                    if (today_date - step_d).days > 365:
                        break

        longest_streak = max(habit.get("longest_streak", 0) or 0, current_streak)

        await db.execute("""
            UPDATE habits SET current_streak = ?, longest_streak = ?
            WHERE id = ?
        """, (current_streak, longest_streak, habit_id))
        await db.commit()

        return {"current_streak": current_streak, "longest_streak": longest_streak}

# ==================== СТАТИСТИКА / STATS ====================

async def get_user_statistics(user_id: int, today_str: str) -> Dict[str, Any]:
    """Қолданушының жалпы статистикасын жинау"""
    habits = await get_user_habits(user_id, only_active=True)
    total_habits = len(habits)

    today_logs = await get_habit_logs_for_date(user_id, today_str)
    completed_today = sum(1 for hid, status in today_logs.items() if status == "done")

    async with aiosqlite.connect(DB_PATH) as db:
        # Соңғы 7 күндегі орындалу саны
        seven_days_ago = (datetime.strptime(today_str, "%Y-%m-%d").date() - timedelta(days=6)).strftime("%Y-%m-%d")
        async with db.execute("""
            SELECT COUNT(*) FROM habit_logs
            WHERE user_id = ? AND status = 'done' AND log_date >= ? AND log_date <= ?
        """, (user_id, seven_days_ago, today_str)) as cursor:
            row = await cursor.fetchone()
            week_completions = row[0] if row else 0

        # Барлық уақыттағы орындалғандар саны
        async with db.execute("""
            SELECT COUNT(*) FROM habit_logs
            WHERE user_id = ? AND status = 'done'
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            total_completions = row[0] if row else 0

    max_streak = max([h.get("current_streak", 0) for h in habits], default=0)
    best_streak = max([h.get("longest_streak", 0) for h in habits], default=0)

    return {
        "total_habits": total_habits,
        "completed_today": completed_today,
        "completion_rate_today": (completed_today / total_habits * 100) if total_habits > 0 else 0,
        "week_completions": week_completions,
        "total_completions": total_completions,
        "max_current_streak": max_streak,
        "best_streak": best_streak,
        "habits": habits,
        "today_logs": today_logs
    }
