# Template Setup for Bid Plan Downloads

## Problem
Bid plan downloads were failing on Streamlit Cloud because the template file couldn't be accessed from the file system.

## Solution
Store the bid plan Excel template in the database, just like we did with config files.

## Setup Instructions

### 1. Run the Migration (One-Time Setup)

Make sure your database is accessible, then run:

```bash
source ../.venv/bin/activate
python run_template_migration.py
```

This will:
1. Create the `templates` table in your database
2. Upload the bid plan template (`Bid Plan - [Client  Opp Name]_BB_140125.xlsx`)
3. Re-upload config files (capabilities.json, qualification_matrix.json)

### 2. Verify Upload

```bash
python -c "from agent.database.db_manager import DatabaseManager; db = DatabaseManager(); t = db.get_template('bid_plan_template'); print('✅ Template loaded:', len(t), 'bytes' if t else '❌ Template NOT found')"
```

### 3. Deploy to Streamlit Cloud

The code is already pushed to GitHub. Streamlit Cloud will:
1. Auto-detect the push and redeploy
2. The migration will need to be run **once** on the production database
3. After that, bid plan downloads will work!

## How It Works

**Before:**
- `generate_bid_plan_excel_bytes()` tried to load from `settings.FILES_DIR / "Bid Plan...xlsx"`
- Failed on Streamlit Cloud (no file system access)

**After:**
- Template stored in `templates` table as bytea
- `generate_bid_plan_excel_bytes()` loads from `db.get_template('bid_plan_template')`
- Works on both local and Streamlit Cloud ✅

## Database Schema

```sql
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    template_name TEXT UNIQUE NOT NULL,
    template_data BYTEA NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Troubleshooting

**If template not found:**
```bash
python run_template_migration.py
```

**If database connection fails:**
Check your `.env` file has correct `DATABASE_URL`

**If Streamlit Cloud still fails:**
Run migration on production database via connection string
