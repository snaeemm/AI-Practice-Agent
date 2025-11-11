#!/usr/bin/env python3
"""
Run templates table migration and upload templates.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.database.db_manager import DatabaseManager

def run_migration():
    """Run templates table migration"""
    print("🚀 Running templates table migration...")

    db = DatabaseManager()

    # Read and execute migration SQL
    migration_path = Path(__file__).parent / "agent" / "database" / "migrations" / "create_templates_table.sql"

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False

    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    try:
        with db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(migration_sql)
                conn.commit()
        print("✅ Templates table created successfully")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if run_migration():
        print("\n" + "="*50)
        print("Now running upload script...")
        print("="*50 + "\n")

        # Import and run upload
        from upload_config_to_db import upload_config_files
        upload_config_files()
