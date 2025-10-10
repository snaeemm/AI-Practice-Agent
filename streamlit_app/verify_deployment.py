#!/usr/bin/env python3
"""
Pre-deployment verification script
Run this before deploying to Streamlit Cloud to catch issues early
"""

import os
import sys
from pathlib import Path

def check_env_vars():
    """Check required environment variables"""
    print("🔍 Checking environment variables...")
    required = ["GOOGLE_API_KEY", "DATABASE_URL"]
    missing = []

    for var in required:
        if not os.getenv(var):
            missing.append(var)
            print(f"  ❌ Missing: {var}")
        else:
            print(f"  ✅ Found: {var}")

    return len(missing) == 0

def check_files():
    """Check required files exist"""
    print("\n📁 Checking required files...")
    required_files = [
        "app.py",
        "requirements.txt",
        ".streamlit/config.toml",
        "agent/agent.py",
        "agent/tools.py",
        "agent/database/db_manager.py",
        "components/chat.py",
        "related_files/capabilities.json",
        "related_files/qualification_matrix.json",
    ]

    missing = []
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ Missing: {file}")
            missing.append(file)

    return len(missing) == 0

def check_database_connection():
    """Test database connection"""
    print("\n🗄️  Testing database connection...")
    try:
        import psycopg2
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            print("  ⚠️  DATABASE_URL not set, skipping connection test")
            return True

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        print("  ✅ Database connection successful")
        return True
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False

def check_imports():
    """Check critical imports work"""
    print("\n📦 Checking critical imports...")
    imports = [
        ("streamlit", "streamlit"),
        ("google.adk.agents", "google-adk"),
        ("psycopg2", "psycopg2-binary"),
        ("openpyxl", "openpyxl"),
        ("pydantic", "pydantic"),
    ]

    failed = []
    for module, package in imports:
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ Missing: {package}")
            failed.append(package)

    return len(failed) == 0

def main():
    print("=" * 60)
    print("🚀 STREAMLIT CLOUD DEPLOYMENT VERIFICATION")
    print("=" * 60)

    checks = [
        ("Environment Variables", check_env_vars),
        ("Required Files", check_files),
        ("Critical Imports", check_imports),
        ("Database Connection", check_database_connection),
    ]

    results = []
    for name, check_fn in checks:
        try:
            result = check_fn()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error during {name}: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✅ All checks passed! Ready to deploy to Streamlit Cloud.")
        print("\nNext steps:")
        print("1. Push to GitHub: git push origin main")
        print("2. Go to share.streamlit.io")
        print("3. Create new app and configure secrets")
        return 0
    else:
        print("\n❌ Some checks failed. Fix the issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
