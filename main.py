import datetime
from auth import register_user, login_user

# ---------------- DATE VALIDATION ----------------
def validate_date(date_str):
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

from transactions import add_transaction, view_transactions, update_transaction, delete_transaction
from reports import monthly_report, yearly_report
from budget import set_budget, check_budget
from backup import backup_database, restore_database
from database import setup_database, get_user_id

# ---------------- MAIN APP ----------------
def main():
    setup_database()
    logged_in_user = None

    while True:
        print("\n--- Personal Finance Manager ---")
        if not logged_in_user:
            print("1. Register")
            print("2. Login")
            print("3. Exit")
            choice = input("Enter choice: ")

            if choice == "1":
                username = input("Enter username: ")
                password = input("Enter password: ")
                register_user(username, password)

            elif choice == "2":
                username = input("Enter username: ")
                password = input("Enter password: ")
                if login_user(username, password):
                    logged_in_user = username

            elif choice == "3":
                print("👋 Goodbye!")
                break

            else:
                print("⚠️ Invalid choice, try again.")

        else:
            print(f"\nWelcome, {logged_in_user}!")
            print("1. Add Transaction")
            print("2. View Transactions")
            print("3. Update Transaction")
            print("4. Delete Transaction")
            print("5. Monthly Report")
            print("6. Yearly Report")
            print("7. Set Budget")
            print("8. Check Budget")
            print("9. Backup Database")
            print("10. Restore Database")
            print("11. Logout")

            choice = input("Enter choice: ")

            # ---------------- ADD TRANSACTION ----------------
            if choice == "1":
                amount = float(input("Enter amount: "))
                category = input("Enter category: ").strip().lower()
                t_type = input("Enter type (income/expense): ").strip().lower()
                date = input("Enter date (YYYY-MM-DD): ")

                if not validate_date(date):
                    print("❌ Invalid date format! Use YYYY-MM-DD")
                    continue
                user_id = get_user_id(logged_in_user)
                if not user_id:
                    print("⚠️ Unable to find user id. Please re-login.")
                    logged_in_user = None
                    continue
                add_transaction(user_id, amount, category, t_type, date)

            # ---------------- VIEW TRANSACTIONS ----------------
            elif choice == "2":
                user_id = get_user_id(logged_in_user)
                transactions = view_transactions(user_id)
                for t in transactions:
                    print(t)

            # ---------------- UPDATE TRANSACTION ----------------
            elif choice == "3":
                t_id = int(input("Enter transaction ID to update: "))
                new_amount = float(input("Enter new amount: "))
                update_transaction(t_id, amount=new_amount)

            # ---------------- DELETE TRANSACTION ----------------
            elif choice == "4":
                t_id = int(input("Enter transaction ID to delete: "))
                delete_transaction(t_id)

            # ---------------- MONTHLY REPORT ----------------
            elif choice == "5":
                month = input("Enter month (YYYY-MM): ")
                user_id = get_user_id(logged_in_user)
                report = monthly_report(user_id, month)
                print(report)

            # ---------------- YEARLY REPORT ----------------
            elif choice == "6":
                year = input("Enter year (YYYY): ")
                user_id = get_user_id(logged_in_user)
                report = yearly_report(user_id, year)
                print(report)

            # ---------------- SET BUDGET ----------------
            elif choice == "7":
                category = input("Enter category: ").strip().lower()
                budget_limit = float(input("Enter budget limit: "))
                month = input("Enter month (YYYY-MM): ")
                user_id = get_user_id(logged_in_user)
                set_budget(user_id, category, budget_limit, month)

            # ---------------- CHECK BUDGET ----------------
            elif choice == "8":
                category = input("Enter category: ").strip().lower()
                month = input("Enter month (YYYY-MM): ")
                user_id = get_user_id(logged_in_user)
                result = check_budget(user_id, category, month)
                if not result:
                    print("⚠️ No budget set for this category/month.")
                else:
                    status = "❌ Exceeded" if result["exceeded"] else "✅ Within budget"
                    print(f"{status} — Limit: {result['limit']}, Spent: {result['spent']}, {result['percent']:.1f}%")

            # ---------------- BACKUP ----------------
            elif choice == "9":
                backup_database()

            # ---------------- RESTORE ----------------
            elif choice == "10":
                restore_database()

            # ---------------- LOGOUT ----------------
            elif choice == "11":
                logged_in_user = None
                print("✅ Logged out successfully.")

            else:
                print("⚠️ Invalid choice, try again.")

if __name__ == "__main__":
    main()
