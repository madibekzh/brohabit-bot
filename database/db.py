import aiosqlite
from config import DB_PATH

async def init_db():
    """Мәліметтер қорын және кестелерді бастапқы дайындау"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                timezone TEXT DEFAULT 'Asia/Almaty',
                morning_reminder_time TEXT DEFAULT '09:00',
                evening_reminder_time TEXT DEFAULT '21:00',
                reminders_enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                goal_description TEXT,
                reminder_time TEXT DEFAULT '20:00',
                target_days TEXT DEFAULT 'all',
                weekly_target INTEGER DEFAULT 7,
                is_active INTEGER DEFAULT 1,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                created_at DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """)

        # Бағаналар бұрыннан бар кестелерде жоқ болса қосу (миграция)
        try:
            await db.execute("ALTER TABLE habits ADD COLUMN target_days TEXT DEFAULT 'all'")
        except Exception:
            pass

        try:
            await db.execute("ALTER TABLE habits ADD COLUMN weekly_target INTEGER DEFAULT 7")
        except Exception:
            pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                status TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(habit_id, log_date),
                FOREIGN KEY (habit_id) REFERENCES habits (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """)

        await db.commit()
