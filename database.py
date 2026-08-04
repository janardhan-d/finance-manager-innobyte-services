import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "finance_app.db")


def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_NAME)
    return conn


def setup_database():
    """Create necessary tables if they don't exist, and migrate older user tables safely."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        profile_pic TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        type TEXT CHECK(type IN ('income','expense')) NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT NOT NULL,
        budget_limit REAL NOT NULL,
        month TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()

    # Migration for older databases that already have a users table without profile_pic.
    cursor.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cursor.fetchall()]
    if "profile_pic" not in cols:
        try:
            cursor.execute("DROP TABLE IF EXISTS users_old")
            cursor.execute("ALTER TABLE users RENAME TO users_old")
            cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                profile_pic TEXT
            )
            """)
            cursor.execute("INSERT INTO users (id, username, password) SELECT id, username, password FROM users_old")
            cursor.execute("DROP TABLE users_old")
            conn.commit()
        except Exception:
            conn.rollback()
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
                conn.commit()
            except Exception:
                pass

    conn.close()
    print("✅ Database setup complete!")


def get_user_id(username):
    """Return the user id for a given username, or None if not found."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

# Run setup when file is executed directly
if __name__ == "__main__":
    setup_database()
