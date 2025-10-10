#!/usr/bin/env python3
"""
Initialize PostgreSQL database with schema
Run this once to set up the database tables
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.database.db_manager import DatabaseManager

def main():
    print("🚀 Initializing PostgreSQL database...")

    try:
        db = DatabaseManager()
        print("✅ Database connection established")

        print("📋 Creating tables and indexes...")
        db._init_database()

        print("\n✅ Database initialization complete!")
        print("📊 Tables created:")
        print("   - rfp_documents")
        print("   - rfp_raw_data")
        print("   - rfp_deliverables")
        print("   - rfp_assignments")
        print("   - qualification_results")
        print("   - capabilities_match")
        print("   - bid_history_insights")

        db.close_all_connections()

    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
