#!/usr/bin/env python3
"""
Run authentication migration automatically
This script adds auth fields to rfp_users table if they don't exist
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent.database.db_singleton import get_db

def run_auth_migration():
    """Run auth migration to add authentication fields"""
    db = get_db()

    print("🔧 Running authentication migration...")

    migration_sql = Path(__file__).parent / "agent" / "database" / "add_auth_to_users.sql"

    if not migration_sql.exists():
        print(f"❌ Migration file not found: {migration_sql}")
        return False

    with open(migration_sql, 'r') as f:
        sql = f.read()

    try:
        with db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
        print("✅ Authentication migration complete")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    try:
        success = run_auth_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
