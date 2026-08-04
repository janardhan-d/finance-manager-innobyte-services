import sqlite3
from database import get_connection

def monthly_report(user_id, month):
    """Generate monthly financial report for a given user and month (YYYY-MM)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT type, SUM(amount) 
    FROM transactions 
    WHERE user_id = ? AND substr(date, 1, 7) = ?
    GROUP BY type
    """, (user_id, month))

    results = cursor.fetchall()
    conn.close()

    income = sum(r[1] for r in results if r[0] == "income")
    expenses = sum(r[1] for r in results if r[0] == "expense")
    savings = income - expenses

    return {"income": income, "expenses": expenses, "expense": expenses, "savings": savings}

def yearly_report(user_id, year):
    """Generate yearly financial report for a given user and year (YYYY)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT type, SUM(amount) 
    FROM transactions 
    WHERE user_id = ? AND substr(date, 1, 4) = ?
    GROUP BY type
    """, (user_id, year))

    results = cursor.fetchall()
    conn.close()

    income = sum(r[1] for r in results if r[0] == "income")
    expenses = sum(r[1] for r in results if r[0] == "expense")
    savings = income - expenses

    return {"income": income, "expenses": expenses, "expense": expenses, "savings": savings}


def category_breakdown(user_id, month):
    """Return a dict mapping category -> total expense+income for the given month (YYYY-MM)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT category, SUM(amount) FROM transactions
    WHERE user_id = ? AND substr(date,1,7) = ?
    GROUP BY category
    """, (user_id, month))
    rows = cur.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def monthly_trend(user_id, months=6):
    """Return tuples (labels, incomes, expenses) for the last `months` months including current."""
    import datetime

    today = datetime.date.today()
    labels = []
    incomes = []
    expenses = []

    for i in range(months - 1, -1, -1):
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1
        label = f"{y:04d}-{m:02d}"
        labels.append(label)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND substr(date,1,7) = ? GROUP BY type",
                    (user_id, label))
        res = cur.fetchall()
        conn.close()

        inc = sum(r[1] for r in res if r[0] == "income")
        exp = sum(r[1] for r in res if r[0] == "expense")

        incomes.append(inc)
        expenses.append(exp)

    return labels, incomes, expenses


def build_report_chart_data(user_id, period):
    """Build chart-friendly data for a monthly or yearly report."""
    if len(str(period)) == 4:
        report = yearly_report(user_id, period)
    else:
        report = monthly_report(user_id, period)

    income = report.get("income", 0)
    expense = report.get("expenses", report.get("expense", 0))
    return {
        "labels": ["Income", "Expense"],
        "values": [income, expense],
        "colors": ["#00E5FF", "#FF6B6B"],
        "savings": report.get("savings", income - expense),
    }
