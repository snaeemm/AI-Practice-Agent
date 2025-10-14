# RFP Deduplication Solution

## Problem
When processing RFPs, the system was creating a new database entry every time, even for the same RFP, because each upload generated a unique `rfp_id` (timestamp + hash based).

## Solution Implemented

### 1. Database Schema Changes (`postgres_schema.sql`)
Added `rfp_lookup` table for tracking canonical RFP IDs:
```sql
CREATE TABLE rfp_lookup (
    id SERIAL PRIMARY KEY,
    canonical_rfp_id TEXT NOT NULL REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
    client_name_normalized TEXT NOT NULL,
    project_title_normalized TEXT NOT NULL,
    submission_deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_name_normalized, project_title_normalized)
);
```

**Key Features:**
- Normalized client/project names for fuzzy matching
- Unique constraint prevents duplicate entries
- Foreign key ensures data integrity
- Indexes for fast lookups

### 2. Database Manager Updates (`db_manager.py`)

Added three new methods:

#### `_normalize_text(text: str) -> str`
Normalizes text for matching:
- Converts to lowercase
- Removes punctuation
- Trims whitespace
- Collapses multiple spaces

#### `find_existing_rfp(client_name, project_title, submission_deadline) -> Optional[str]`
Searches for existing RFP by normalized names:
- Returns `canonical_rfp_id` if found
- Returns `None` if no match

#### `register_rfp_lookup(rfp_id, client_name, project_title, submission_deadline)`
Registers new RFP in lookup table:
- Uses `ON CONFLICT` to update if exists
- Automatically normalizes names

#### Updated `create_rfp_document()`
Added `check_duplicates` parameter (default `True`):
- Checks for existing RFP before creating new one
- Returns existing `rfp_id` if duplicate found
- Automatically registers new RFPs in lookup table

### 3. Processor Updates

Both `new_rfp_qualifier.py` and `new_rfp_bid_planner.py` now:
1. Call `create_rfp_document()` with `check_duplicates=True`
2. Check if returned `rfp_id` differs from generated one
3. Use existing RFP ID if duplicate detected
4. Log deduplication events

Example:
```python
actual_rfp_id = db.create_rfp_document(
    rfp_id=rfp_id,
    client_name=client_name,
    project_title=project_title,
    pdf_path=None,
    submission_deadline=submission_deadline,
    check_duplicates=True  # Enable deduplication
)

if actual_rfp_id != rfp_id:
    print(f"🔄 Using existing RFP ID: {actual_rfp_id}")
    rfp_id = actual_rfp_id  # Use existing ID for all subsequent operations
```

## How It Works

### Flow Diagram
```
New RFP Upload
    ↓
Generate temporary rfp_id (timestamp + hash)
    ↓
Normalize client_name and project_title
    ↓
Query rfp_lookup table
    ↓
    ├─ Match Found?
    │   ├─ YES → Return existing canonical_rfp_id
    │   │         Update data for existing RFP
    │   │         ✅ No duplicate entry created!
    │   │
    │   └─ NO → Create new RFP entry
    │             Register in rfp_lookup table
    │             ✅ New RFP properly tracked!
```

### Example Scenario

**First Upload:**
- Client: "ABC Corporation"
- Project: "Website Redesign 2025"
- Generated ID: `context_rfp_20250114_123456_abc123`
- Result: New entry created, registered in lookup table

**Second Upload (same RFP):**
- Client: "ABC Corporation!!!"  (extra punctuation)
- Project: "website redesign 2025"  (different case)
- Generated ID: `context_rfp_20250114_130000_def456`
- Normalized names match existing entry
- Result: Returns existing ID `context_rfp_20250114_123456_abc123`
- ✅ No duplicate created!

## Benefits

1. **No More Duplicates**: Same RFP uploaded multiple times uses single database entry
2. **Data Consolidation**: All data (qualification, deliverables, assignments) links to one canonical RFP
3. **Robust Matching**: Normalization handles case differences, punctuation, spacing
4. **Backward Compatible**: Existing code works unchanged, deduplication can be disabled with `check_duplicates=False`
5. **Fast Lookups**: Indexed normalized names provide instant duplicate detection

## Migration

Run the migration script to add the new table:
```bash
cd streamlit_app
source ../.venv/bin/activate
python add_rfp_lookup_table.py
```

## Testing

To verify deduplication works:
```python
from agent.database.db_manager import DatabaseManager

db = DatabaseManager()

# Test normalization
assert db._normalize_text("ABC Corp!!!") == "abc corp"
assert db._normalize_text("  Test   Project  ") == "test project"

# Test lookup (should return None for non-existent)
result = db.find_existing_rfp("New Client", "New Project")
assert result is None

# Test duplicate detection
rfp_id1 = db.create_rfp_document("rfp_001", "Test Client", "Test Project", check_duplicates=True)
rfp_id2 = db.create_rfp_document("rfp_002", "TEST CLIENT!!!", "test project", check_duplicates=True)
assert rfp_id1 == rfp_id2  # Should return same ID!
```

## Future Enhancements

Possible improvements:
1. **Fuzzy String Matching**: Use Levenshtein distance for even better matching
2. **Deadline Proximity**: Consider RFPs with similar deadlines as potential duplicates
3. **Manual Override**: UI to merge/split RFP entries manually
4. **Duplicate Dashboard**: Show all potential duplicates for review
5. **Confidence Scores**: Return match confidence (0-100%) for borderline cases
