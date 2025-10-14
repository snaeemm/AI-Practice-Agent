#!/usr/bin/env python3
"""
Add rfp_lookup table for deduplication
"""

from agent.database.db_manager import DatabaseManager

def main():
    print("🚀 Adding rfp_lookup table for deduplication...")

    try:
        db = DatabaseManager()
        print("✅ Database connection established")

        migration_sql = """
        -- Create rfp_lookup table
        CREATE TABLE IF NOT EXISTS rfp_lookup (
            id SERIAL PRIMARY KEY,
            canonical_rfp_id TEXT NOT NULL REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
            client_name_normalized TEXT NOT NULL,
            project_title_normalized TEXT NOT NULL,
            submission_deadline TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(client_name_normalized, project_title_normalized)
        );

        CREATE INDEX IF NOT EXISTS idx_rfp_lookup_canonical ON rfp_lookup(canonical_rfp_id);
        CREATE INDEX IF NOT EXISTS idx_rfp_lookup_client ON rfp_lookup(client_name_normalized);
        CREATE INDEX IF NOT EXISTS idx_rfp_lookup_project ON rfp_lookup(project_title_normalized);
        CREATE INDEX IF NOT EXISTS idx_rfp_lookup_deadline ON rfp_lookup(submission_deadline);
        CREATE INDEX IF NOT EXISTS idx_rfp_lookup_updated ON rfp_lookup(updated_at DESC);

        -- Create update trigger (drop first if exists)
        DROP TRIGGER IF EXISTS update_rfp_lookup_updated_at ON rfp_lookup;
        CREATE TRIGGER update_rfp_lookup_updated_at
        BEFORE UPDATE ON rfp_lookup
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        -- Create templates table if not exists
        CREATE TABLE IF NOT EXISTS templates (
            id SERIAL PRIMARY KEY,
            template_name TEXT UNIQUE NOT NULL,
            template_data BYTEA NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_templates_name ON templates(template_name);
        CREATE INDEX IF NOT EXISTS idx_templates_updated ON templates(updated_at DESC);

        DROP TRIGGER IF EXISTS update_templates_updated_at ON templates;
        CREATE TRIGGER update_templates_updated_at
        BEFORE UPDATE ON templates
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        -- Create generated_files table if not exists
        CREATE TABLE IF NOT EXISTS generated_files (
            id SERIAL PRIMARY KEY,
            session_id TEXT,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_data BYTEA NOT NULL,
            rfp_id TEXT REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            downloaded BOOLEAN DEFAULT FALSE
        );

        CREATE INDEX IF NOT EXISTS idx_generated_files_session ON generated_files(session_id);
        CREATE INDEX IF NOT EXISTS idx_generated_files_rfp ON generated_files(rfp_id);
        CREATE INDEX IF NOT EXISTS idx_generated_files_created ON generated_files(created_at DESC);
        """

        with db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(migration_sql)
                conn.commit()
                print("✅ rfp_lookup table created successfully")

        db.close_all_connections()
        print("\n✅ Migration complete!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
