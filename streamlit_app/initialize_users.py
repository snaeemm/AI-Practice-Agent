#!/usr/bin/env python3
"""
Initialize users with default credentials
Run this script once to create initial user accounts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent.database.db_singleton import get_db_manager
from auth import hash_password

USERS = [
    {"username": "paul.wallis", "password": "paul-wallis-123!", "full_name": "Paul Wallis"},
    {"username": "lionel.laulhe", "password": "lionel-laulhe-123!", "full_name": "Lionel Laulhe"},
    {"username": "bethany.bromfield", "password": "bethany-bromfield-123!", "full_name": "Bethany Bromfield"},
    {"username": "sowjanya.gummella", "password": "sowjanya-gummella-123!", "full_name": "Sowjanya Gummella"},
    {"username": "sharif.kamyab", "password": "sharif-kamyab-123!", "full_name": "Sharif Kamyab"},
    {"username": "anna.fakir", "password": "anna-fakir-123!", "full_name": "Anna Fakir"},
    {"username": "rana.alnajjar", "password": "rana-alnajjar-123!", "full_name": "Rana Al Najjar"},
    {"username": "ghalya.shamo", "password": "ghalya-shamo-123!", "full_name": "Ghalya Shamo"},
    {"username": "nadine.khair", "password": "nadine-khair-123!", "full_name": "Nadine Khair"},
    {"username": "julien.recan", "password": "julien-recan-123!", "full_name": "Julien Recan"},
]

def initialize_users():
    """Create initial user accounts"""
    db = get_db_manager()

    print("🔧 Initializing users...")

    with db._get_connection() as conn:
        with conn.cursor() as cursor:
            for user in USERS:
                username = user["username"]
                password_hash = hash_password(user["password"])
                full_name = user["full_name"]

                try:
                    cursor.execute("""
                        INSERT INTO rfp_users (username, password_hash, full_name, must_change_password)
                        VALUES (%s, %s, %s, true)
                        ON CONFLICT (username) DO UPDATE
                        SET password_hash = EXCLUDED.password_hash,
                            full_name = EXCLUDED.full_name,
                            must_change_password = true
                    """, (username, password_hash, full_name))

                    print(f"✅ Created/Updated user: {username} ({full_name})")

                except Exception as e:
                    print(f"❌ Error creating user {username}: {e}")

            conn.commit()

    print("\n🎉 User initialization complete!")
    print("\nDefault credentials:")
    print("Username format: firstname.lastname (e.g., paul.wallis)")
    print("Password format: firstname-lastname-123! (e.g., paul-wallis-123!)")
    print("\n⚠️  All users will be required to change their password on first login")

if __name__ == "__main__":
    try:
        initialize_users()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
