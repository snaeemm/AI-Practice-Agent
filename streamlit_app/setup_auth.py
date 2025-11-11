#!/usr/bin/env python3
"""
Complete authentication setup script
Run this once to set up authentication on Streamlit Cloud or local deployment
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🚀 Setting up authentication for GRANITE Bid Assistant\n")

    print("Step 1: Running database migration...")
    from run_auth_migration import run_auth_migration
    if not run_auth_migration():
        print("❌ Migration failed")
        return False

    print("\nStep 2: Initializing users...")
    from initialize_users import initialize_users
    try:
        initialize_users()
    except Exception as e:
        print(f"❌ User initialization failed: {e}")
        return False

    print("\n✅ Authentication setup complete!")
    print("\n" + "="*60)
    print("You can now log in with any of the created user accounts")
    print("All users must change their password on first login")
    print("="*60 + "\n")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
