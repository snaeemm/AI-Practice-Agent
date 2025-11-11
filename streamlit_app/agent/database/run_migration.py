#!/usr/bin/env python3
"""
Run database migration
Usage: python run_migration.py <migration_file>
"""

import sys
from pathlib import Path
from agent.database.db_manager import DatabaseManager


def run_migration(migration_file: str):
    """Run a specific migration SQL file"""
    print(f"🚀 Running migration: {migration_file}")

    migration_path = Path(__file__).parent / "migrations" / migration_file

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        sys.exit(1)

    print(f"📋 Reading migration from: {migration_path}")

    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    try:
        db = DatabaseManager()
        print("✅ Database connection established")

        print("📊 Executing migration...")

        with db._get_connection() as conn:
            with conn.cursor() as cursor:
                # Execute the migration SQL
                cursor.execute(migration_sql)
                conn.commit()

        print(f"✅ Migration {migration_file} completed successfully!")

        db.close_all_connections()

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file>")
        print("\nExample: python run_migration.py add_marketing_tables.sql")
        sys.exit(1)

    migration_file = sys.argv[1]
    run_migration(migration_file)
