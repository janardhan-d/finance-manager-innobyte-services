import sqlite3
from database import get_connection

def set_budget(user_id, category, budget_limit, month):
    """Set a monthly budget for a category."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO budgets (user_id, category, budget_limit, month)
    VALUES (?, ?, ?, ?)
    """, (user_id, category, budget_limit, month))

    conn.commit()
    conn.close()
    print("✅ Budget set successfully!")

def check_budget(user_id, category, month):
    """Return budget status dict for category+month: {limit, spent, exceeded, percent} or None if no budget."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT budget_limit FROM budgets
    WHERE user_id = ? AND category = ? AND month = ?
    """, (user_id, category, month))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return None

    budget_limit = result[0]

    cursor.execute("""
    SELECT SUM(amount) FROM transactions
    WHERE user_id = ? AND category = ? AND type = 'expense' AND substr(date, 1, 7) = ?
    """, (user_id, category, month))
    expense_total = cursor.fetchone()[0] or 0

    conn.close()

    exceeded = expense_total > budget_limit
    percent = (expense_total / budget_limit * 100) if budget_limit else 0

    return {
        "limit": budget_limit,
        "spent": expense_total,
        "exceeded": exceeded,
        "percent": percent
    }


def get_budget_progress(user_id, category, month):
    """Alias for check_budget to return progress details."""
    return check_budget(user_id, category, month)


def list_budgets(user_id, month=None):
    """Return list of budgets for a user. If month provided, filter by month."""
    conn = get_connection()
    cur = conn.cursor()
    if month:
        cur.execute("SELECT id, category, budget_limit, month FROM budgets WHERE user_id = ? AND month = ?", (user_id, month))
    else:
        cur.execute("SELECT id, category, budget_limit, month FROM budgets WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows
