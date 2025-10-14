#!/usr/bin/env python3
"""
Upload config files (capabilities.json, qualification_matrix.json) to database.
Run this once to populate the config_files table.
"""
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent.database.db_manager import DatabaseManager
from agent.config.settings import settings

def upload_config_files():
    """Upload config JSON files to database"""
    print("🚀 Uploading config files to database...")

    db = DatabaseManager()

    # Upload capabilities.json
    config_dir = Path(__file__).parent / "agent" / "config"
    capabilities_path = config_dir / "capabilities.json"

    if capabilities_path.exists():
        print(f"📄 Reading {capabilities_path}...")
        with open(capabilities_path, 'r', encoding='utf-8') as f:
            capabilities_data = json.load(f)

        print(f"💾 Saving capabilities to database...")
        config_id = db.save_config_file('capabilities', capabilities_data)
        print(f"✅ Saved capabilities (ID: {config_id})")
    else:
        print(f"⚠️  Capabilities file not found: {capabilities_path}")

    # Upload qualification_matrix.json
    qual_matrix_path = config_dir / "qualification_matrix.json"

    if qual_matrix_path.exists():
        print(f"📄 Reading {qual_matrix_path}...")
        with open(qual_matrix_path, 'r', encoding='utf-8') as f:
            qual_matrix_data = json.load(f)

        print(f"💾 Saving qualification matrix to database...")
        config_id = db.save_config_file('qualification_matrix', qual_matrix_data)
        print(f"✅ Saved qualification matrix (ID: {config_id})")
    else:
        print(f"⚠️  Qualification matrix file not found: {qual_matrix_path}")

    print("\n✅ Upload complete! Config files are now in the database.")
    print("   These will be used on Streamlit Cloud where local files aren't available.")

if __name__ == "__main__":
    upload_config_files()
