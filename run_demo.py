from database import setup_database, get_user_id
from auth import register_user
from transactions import add_transaction
from reports import monthly_trend, category_breakdown
import datetime

setup_database()

username = "demo_user"
password = "demo_pass"

# Register if not exists
registered = register_user(username, password)
if not registered:
    print("User possibly exists, continuing...")
else:
    print("Registered demo_user")

user_id = get_user_id(username)
if not user_id:
    print("Failed to get user id")
    exit(1)

print(f"Using user_id={user_id}")

# Seed some transactions across 6 months
today = datetime.date.today()
for i in range(6):
    m = today.month - i
    y = today.year
    while m <= 0:
        m += 12
        y -= 1
    date = f"{y:04d}-{m:02d}-15"
    # add income and expense
    add_transaction(user_id, 1000 + i * 100, "Salary", "income", date)
    add_transaction(user_id, 200 + i * 50, "Food", "expense", date)

labels, incomes, expenses = monthly_trend(user_id, months=6)
print("Monthly trend:")
for l, inc, exp in zip(labels, incomes, expenses):
    print(f"{l}: income={inc}, expense={exp}")

month = today.strftime("%Y-%m")
cat = category_breakdown(user_id, month)
print(f"Category breakdown for {month}:")
for k, v in cat.items():
    print(f"  {k}: {v}")

print("Charts saved as monthly_trend.png and category_breakdown.png in repo root.")
