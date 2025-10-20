#!/usr/bin/env python3
"""
Database Migration: Add Edit Tracking Columns

This migration adds audit trail columns to track user edits for:
- qualification_results
- rfp_deliverables
- rfp_assignments
- client_briefs

Run this before deploying edit functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.database.db_singleton import get_db


def run_migration():
    """Add edit tracking columns to relevant tables"""

    db = get_db()

    migration_sql = """
    -- Add edit tracking to qualification_results
    ALTER TABLE qualification_results
    ADD COLUMN IF NOT EXISTS last_edited_by VARCHAR(255),
    ADD COLUMN IF NOT EXISTS last_edited_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS edit_history JSONB DEFAULT '[]';

    -- Add edit tracking to rfp_deliverables
    ALTER TABLE rfp_deliverables
    ADD COLUMN IF NOT EXISTS last_edited_by VARCHAR(255),
    ADD COLUMN IF NOT EXISTS last_edited_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS edit_history JSONB DEFAULT '[]';

    -- Add edit tracking to rfp_assignments
    ALTER TABLE rfp_assignments
    ADD COLUMN IF NOT EXISTS last_edited_by VARCHAR(255),
    ADD COLUMN IF NOT EXISTS last_edited_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS edit_history JSONB DEFAULT '[]';

    -- Add edit tracking to client_briefs
    ALTER TABLE client_briefs
    ADD COLUMN IF NOT EXISTS last_edited_by VARCHAR(255),
    ADD COLUMN IF NOT EXISTS last_edited_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS edit_history JSONB DEFAULT '[]';
    """

    try:
        with db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(migration_sql)
                conn.commit()
                print("✅ Migration completed successfully!")
                print("\nNew columns added to:")
                print("  • qualification_results: last_edited_by, last_edited_at, edit_history")
                print("  • rfp_deliverables: last_edited_by, last_edited_at, edit_history")
                print("  • rfp_assignments: last_edited_by, last_edited_at, edit_history")
                print("  • client_briefs: last_edited_by, last_edited_at, edit_history")
                print("\n✨ Edit tracking is now ready to use!")
                return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔄 Running edit tracking migration...")
    print("=" * 60)

    success = run_migration()

    print("=" * 60)
    if success:
        print("Migration completed. You can now use the edit features.")
        sys.exit(0)
    else:
        print("Migration failed. Check the error above.")
        sys.exit(1)
