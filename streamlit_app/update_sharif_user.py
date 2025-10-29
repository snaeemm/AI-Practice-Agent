#!/usr/bin/env python3
"""
Update Sharif's user account
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent.database.db_singleton import get_db
from auth import hash_password

def update_sharif_user():
    """Delete old sharif.kamyab user and create new sharif user"""
    db = get_db()

    print("🔧 Updating Sharif's user account...")

    with db._get_connection() as conn:
        with conn.cursor() as cursor:
            # Delete old user
            try:
                cursor.execute("""
                    DELETE FROM rfp_users WHERE username = 'sharif.kamyab'
                """)
                print("✅ Deleted old user: sharif.kamyab")
            except Exception as e:
                print(f"⚠️  Note: {e}")

            # Create new user
            username = "sharif"
            password = "Password123"
            password_hash = hash_password(password)
            full_name = "Sharif Kamyab"

            try:
                cursor.execute("""
                    INSERT INTO rfp_users (username, password_hash, full_name, must_change_password, is_active)
                    VALUES (%s, %s, %s, false, true)
                    ON CONFLICT (username) DO UPDATE
                    SET password_hash = EXCLUDED.password_hash,
                        full_name = EXCLUDED.full_name,
                        must_change_password = false,
                        is_active = true
                """, (username, password_hash, full_name))

                print(f"✅ Created/Updated user: {username} ({full_name})")

            except Exception as e:
                print(f"❌ Error creating user {username}: {e}")
                conn.rollback()
                sys.exit(1)

            conn.commit()

    print("\n🎉 User update complete!")
    print("\n📝 New credentials:")
    print(f"   Username: sharif")
    print(f"   Password: Password123")
    print("\n✅ User can log in immediately (no password change required)")

if __name__ == "__main__":
    try:
        update_sharif_user()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
