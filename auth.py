import sqlite3
from database import get_connection, setup_database

try:
    import bcrypt
    _USE_BCRYPT = True
except Exception:
    import hashlib
    _USE_BCRYPT = False


def register_user(username, password):
    """Register a new user. Uses bcrypt when available, falls back to SHA256."""
    setup_database()
    conn = get_connection()
    cur = conn.cursor()

    if _USE_BCRYPT:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    else:
        hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()

    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def login_user(username, password):
    """Authenticate user login. Returns True on success, False otherwise."""
    setup_database()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return False

    stored = row[0]
    if _USE_BCRYPT:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored)
        except Exception:
            return False
    else:
        return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored


def update_profile_pic(user_id, path):
    setup_database()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET profile_pic = ? WHERE id = ?", (path, user_id))
    conn.commit()
    conn.close()


def get_profile_pic(user_id):
    setup_database()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT profile_pic FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
