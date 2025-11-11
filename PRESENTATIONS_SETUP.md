# Presentations System - Setup & Migration Guide

## Current Error

```
psycopg2.errors.UndefinedColumn: column "presentation_title" does not exist
```

**Root Cause:** The database schema hasn't been updated yet to include the new `presentation_title` column.

## Fix: Run the Migration

### Option 1: Fresh Database (Recommended for Development)

Use the updated schema file directly:
```bash
psql $DATABASE_URL < streamlit_app/agent/database/postgres_schema.sql
```

This has the correct schema with:
- `presentation_title` TEXT NOT NULL UNIQUE
- `presentation_description` TEXT
- `rfp_id` NULLABLE (optional foreign key)

### Option 2: Existing Database (Migration)

Run the migration that adds columns safely:
```bash
psql $DATABASE_URL < streamlit_app/agent/database/migrations/update_presentations_table.sql
```

**What this migration does:**
1. Adds new columns: `presentation_title`, `presentation_description`
2. Populates `presentation_title` for existing records (as `Presentation_<rfp_id>`)
3. Makes `rfp_id` nullable
4. Adds unique constraint on `presentation_title`
5. Updates foreign key to allow NULL values

## What Changed

### Database Schema
```sql
-- OLD (Broken)
presentations (
  id, rfp_id (NOT NULL, FK), presentation_structure, created_at, updated_at
)

-- NEW (Fixed)
presentations (
  id,
  presentation_title (NOT NULL, UNIQUE),    -- NEW
  presentation_description,                  -- NEW
  rfp_id (NULLABLE, FK),                    -- CHANGED
  presentation_structure,
  created_at,
  updated_at
)
```

### Code Changes

#### 1. PPT Agent Tool - Updated Signature

**Before:**
```python
tool_save_presentation_structure(rfp_id: str, slides: List[Dict])
```

**After:**
```python
tool_save_presentation_structure(
    presentation_title: str,
    slides: List[Dict],
    presentation_description: str = None
)
```

#### 2. Database Methods

**New Methods (for presentations):**
- `list_presentations(limit=50)` - Get all presentations with slide counts
- `get_presentation_by_title(title)` - Get single presentation by title

**Legacy Methods (kept for backward compatibility):**
- `save_presentation_structure(rfp_id, structure)` - Still works, creates title as `Presentation_<rfp_id>`
- `get_presentation_structure(rfp_id)` - Still works, queries by rfp_id

#### 3. Presentations Page

**Before:** Showed RFP documents (WRONG!)
```python
rfps = db.list_recent_rfps()  # Shows PDFs, not presentations
```

**After:** Shows actual presentations (CORRECT!)
```python
presentations = db.list_presentations()  # Shows presentations
```

## Complete Flow (After Migration)

### 1. Create New Presentation

User → Agent Chat → Agent collects title & slides → Agent calls:
```python
tool_save_presentation_structure(
    "Q4 Strategy",
    [{title: "Intro", points: ["...", "..."]}, ...],
    "Strategic planning for Q4"
)
```

Database Result:
```
INSERT INTO presentations (presentation_title, presentation_description, presentation_structure)
VALUES ('Q4 Strategy', 'Strategic planning for Q4', {...})
```

### 2. Update Existing Presentation

User talks to agent again about "Q4 Strategy" → Agent calls same function with updated slides

Database Result:
```
UPDATE presentations
SET presentation_structure = {...}, updated_at = NOW()
WHERE presentation_title = 'Q4 Strategy'
```

**Key:** `updated_at` auto-updates via database trigger!

### 3. View on Presentations Page

```
presentations = db.list_presentations()
# Returns [{
#   id: 1,
#   presentation_title: "Q4 Strategy",
#   presentation_description: "...",
#   slide_count: 5,  (auto-calculated)
#   updated_at: "2025-01-20 10:30:00",
#   presentation_structure: {...}
# }]
```

### 4. Download Presentation

User clicks "Download .pptx" button:
```python
slides = presentation['presentation_structure']['slides']
ppt_bytes = _create_presentation_bytes(slides)  # Generate bytes
# User downloads as "Q4_Strategy.pptx"
```

Import into Gamma.app ✅

## Files Modified

| File | Changes |
|------|---------|
| `postgres_schema.sql` | Updated presentations table schema |
| `migrations/update_presentations_table.sql` | Safe migration script |
| `db_manager.py` | Added new methods, updated old ones for backward compatibility |
| `ppt_tools.py` | Changed function signature to use `presentation_title` |
| `ppt_agent.py` | Updated agent prompt with new parameters |
| `pages/4_Presentations.py` | Complete rewrite to use presentations table |
| `agent/tools.py` | Updated wrapper function signature |

## Backward Compatibility

✅ **Backward Compatible after migration:**
- Old methods (`save_presentation_structure`, `get_presentation_structure`) still work
- They create presentations with auto-generated titles like `Presentation_<rfp_id>`
- New methods (`list_presentations`, `get_presentation_by_title`) work alongside old ones
- No breaking changes for existing RFP features

## Testing After Migration

Run these checks:

```bash
# 1. Test migration
psql $DATABASE_URL -c "\d presentations"
# Should show: presentation_title, presentation_description, rfp_id (nullable)

# 2. Start app and go to Presentations page
streamlit run streamlit_app/app.py

# 3. Test creating presentation via agent
# Look for messages like:
# "Presentation 'My Title' saved successfully with X slides"

# 4. Test viewing on Presentations page
# Should show presentation list (not RFP list)
# Should show slide count, updated date

# 5. Test downloading
# Click "Download .pptx" and verify file is generated

# 6. Test updating presentation
# Chat with agent again about same presentation title
# Check database: updated_at should change
# Presentations page should show new slide count
```

## Next Steps

1. **If starting fresh:** Use `postgres_schema.sql` (already has correct schema)
2. **If existing database:** Run migration file
3. **Start app:** `streamlit run streamlit_app/app.py`
4. **Test:** Go to Presentations page, create via agent, download & test in Gamma.app

## Support Files

- Migration: `streamlit_app/agent/database/migrations/update_presentations_table.sql`
- Schema: `streamlit_app/agent/database/postgres_schema.sql`
- Docs: This file
