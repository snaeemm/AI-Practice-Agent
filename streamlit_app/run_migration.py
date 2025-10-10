"""Run database migrations"""
import os
from agent.database.db_singleton import get_db

def run_migration():
    db = get_db()

    # Migration 1: Add raw_document_text column
    migration_1 = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'rfp_raw_data'
            AND column_name = 'raw_document_text'
        ) THEN
            ALTER TABLE rfp_raw_data
            ADD COLUMN raw_document_text TEXT;
            RAISE NOTICE 'Column raw_document_text added';
        END IF;
    END $$;
    """

    # Migration 2: Create generated_files table
    migration_2 = """
    CREATE TABLE IF NOT EXISTS generated_files (
        id SERIAL PRIMARY KEY,
        session_id TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_data BYTEA NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        downloaded BOOLEAN DEFAULT FALSE,
        rfp_id TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_generated_files_session ON generated_files(session_id);
    CREATE INDEX IF NOT EXISTS idx_generated_files_created ON generated_files(created_at DESC);
    """

    with db._get_connection() as conn:
        with conn.cursor() as cursor:
            print("Running migration 1: raw_document_text column...")
            cursor.execute(migration_1)

            print("Running migration 2: generated_files table...")
            cursor.execute(migration_2)

            conn.commit()

    print("✅ All migrations executed successfully")
    print("✅ Database schema is up to date")

if __name__ == "__main__":
    run_migration()
