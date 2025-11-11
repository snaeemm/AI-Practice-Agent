#!/usr/bin/env python3
"""
Upload config files and templates to database.
Run this once to populate the config_files and templates tables.
"""
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent.database.db_manager import DatabaseManager
from agent.config.settings import settings

def upload_config_files():
    """Upload config JSON files and Excel templates to database"""
    print("🚀 Uploading config files and templates to database...")

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

    # Upload Bid Plan template
    templates_dir = Path(__file__).parent / "agent" / "related_files"
    bid_plan_template_path = templates_dir / "Bid Plan - [Client  Opp Name]_BB_140125.xlsx"

    if bid_plan_template_path.exists():
        print(f"\n📄 Reading bid plan template...")
        with open(bid_plan_template_path, 'rb') as f:
            template_data = f.read()

        print(f"💾 Saving bid plan template to database ({len(template_data)} bytes)...")
        template_id = db.save_template(
            'bid_plan_template',
            template_data,
            'Default bid plan Excel template for report generation'
        )
        print(f"✅ Saved bid plan template (ID: {template_id})")
    else:
        print(f"⚠️  Bid plan template not found: {bid_plan_template_path}")

    print("\n✅ Upload complete! Config files and templates are now in the database.")
    print("   These will be used on Streamlit Cloud where local files aren't available.")

if __name__ == "__main__":
    upload_config_files()
