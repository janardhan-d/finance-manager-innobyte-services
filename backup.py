import os
import shutil
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "finance_app.db")

def backup_database(backup_file="finance_app_backup.db"):
    """Create a backup copy of the database."""
    try:
        backup_dest = backup_file if os.path.isabs(backup_file) else os.path.join(BASE_DIR, backup_file)
        shutil.copy(DB_NAME, backup_dest)
        print(f"✅ Backup created: {backup_dest}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def restore_database(backup_file="finance_app_backup.db"):
    """Restore database from backup."""
    try:
        backup_source = backup_file if os.path.isabs(backup_file) else os.path.join(BASE_DIR, backup_file)
        if not os.path.isfile(backup_source):
            raise FileNotFoundError(f"Backup file not found: {backup_source}")

        pre_restore_file = os.path.join(BASE_DIR, f"finance_app_pre_restore_{datetime.datetime.now():%Y%m%d_%H%M%S}.db")
        if os.path.isfile(DB_NAME):
            shutil.copy(DB_NAME, pre_restore_file)
            print(f"🔒 Current database saved before restore: {pre_restore_file}")

        shutil.copy(backup_source, DB_NAME)
        print(f"✅ Database restored from: {backup_source}")
        return True, pre_restore_file if os.path.isfile(pre_restore_file) else None
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False, None
