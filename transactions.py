import sqlite3
from database import get_connection

def add_transaction(user_id, amount, category, t_type, date):
    """Add a new income or expense transaction."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO transactions (user_id, amount, category, type, date)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, category, t_type, date))

    conn.commit()
    conn.close()
    print("✅ Transaction added successfully!")

def view_transactions(user_id):
    """View all transactions for a user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, amount, category, type, date FROM transactions WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()

    conn.close()
    return rows


def get_transaction_by_id(t_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, amount, category, type, date FROM transactions WHERE id = ?", (t_id,))
    row = cur.fetchone()
    conn.close()
    return row


def search_transactions(user_id, category=None, start_date=None, end_date=None):
    """Search transactions with optional category and date range (inclusive)."""
    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT id, amount, category, type, date FROM transactions WHERE user_id = ?"
    params = [user_id]

    if category:
        query += " AND lower(category) = ?"
        params.append(category.lower())

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    return rows

def update_transaction(t_id, amount=None, category=None, t_type=None, date=None):
    """Update an existing transaction."""
    conn = get_connection()
    cursor = conn.cursor()

    if amount:
        cursor.execute("UPDATE transactions SET amount = ? WHERE id = ?", (amount, t_id))
    if category:
        cursor.execute("UPDATE transactions SET category = ? WHERE id = ?", (category, t_id))
    if t_type:
        cursor.execute("UPDATE transactions SET type = ? WHERE id = ?", (t_type, t_id))
    if date:
        cursor.execute("UPDATE transactions SET date = ? WHERE id = ?", (date, t_id))

    conn.commit()
    conn.close()
    print("✅ Transaction updated successfully!")

def delete_transaction(t_id):
    """Delete a transaction by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions WHERE id = ?", (t_id,))
    conn.commit()
    conn.close()
    print("✅ Transaction deleted successfully!")
