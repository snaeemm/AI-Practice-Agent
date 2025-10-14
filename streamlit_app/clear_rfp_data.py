#!/usr/bin/env python3
"""
Clear all RFP data from database for testing
"""

from agent.database.db_manager import DatabaseManager

def main():
    print("🗑️  Clearing all RFP data from database...")

    try:
        db = DatabaseManager()
        print("✅ Database connection established")

        with db._get_connection() as conn:
            with conn.cursor() as cursor:
                # Delete in correct order due to foreign key constraints
                print("   Deleting bid_history_insights...")
                cursor.execute("DELETE FROM bid_history_insights")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting capabilities_match...")
                cursor.execute("DELETE FROM capabilities_match")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting qualification_results...")
                cursor.execute("DELETE FROM qualification_results")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting rfp_assignments...")
                cursor.execute("DELETE FROM rfp_assignments")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting rfp_deliverables...")
                cursor.execute("DELETE FROM rfp_deliverables")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting rfp_raw_data...")
                cursor.execute("DELETE FROM rfp_raw_data")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting generated_files...")
                cursor.execute("DELETE FROM generated_files")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting rfp_lookup...")
                cursor.execute("DELETE FROM rfp_lookup")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting rfp_session_rfps...")
                cursor.execute("DELETE FROM rfp_session_rfps")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting rfp_documents...")
                cursor.execute("DELETE FROM rfp_documents")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting rfp_messages...")
                cursor.execute("DELETE FROM rfp_messages")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting rfp_sessions...")
                cursor.execute("DELETE FROM rfp_sessions")
                deleted = cursor.rowcount
                print(f"   ✅ Deleted {deleted} rows")

                print("   Deleting rfp_users (keeping users, just clearing sessions)...")
                # Don't delete users, just sessions

                conn.commit()
                print("\n✅ All RFP data and sessions cleared successfully!")
                print("📊 Database is now clean and ready for testing")

        db.close_all_connections()

    except Exception as e:
        print(f"\n❌ Failed to clear data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
