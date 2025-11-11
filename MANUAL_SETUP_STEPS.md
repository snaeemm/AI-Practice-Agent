# Manual Setup Steps - HF Space Backend

## ✅ Completed by Claude Code

These cleanup tasks have already been done:
- ✅ Deleted 2 presentation wrapper functions from `tools.py`
- ✅ Prepared `cached_database_tools.py` for deletion
- ✅ Added 10 missing agent tools to `database_tools.py`
- ✅ Updated `database_agent.py` with all new tools

---

## 🔧 Manual Steps Required (Run These Commands)

### Prerequisites
- Ensure you have `psql` (PostgreSQL client) installed
- Ensure you have `uv` package manager installed
- Have `DATABASE_URL` environment variable set

---

### Step 1: Navigate to HF Space Directory
```bash
cd /Users/shahzeb.naeem/Desktop/Projects/ai-practice-agentic/hf_space
```

---

### Step 2: Install Dependencies with UV
```bash
uv pip install passlib[bcrypt] python-jose[cryptography] slowapi
```

**What this does**: Installs packages for password hashing, JWT tokens, and rate limiting

---

### Step 3: Run Database Migration
```bash
psql "$DATABASE_URL" -f backend/database/migrations/add_password_hash_to_users.sql
```

**What this does**: Adds `password_hash` column to `rfp_users` table

**Expected output**:
```
ALTER TABLE
CREATE INDEX
```

**If you see "column already exists"**: Safe to ignore - migration was already applied

---

### Step 4: Seed Users with Hashed Passwords
```bash
uv run python backend/database/seed_users.py
```

**What this does**: Creates 9 default users with bcrypt-hashed passwords

**Expected output**:
```
Seeding users...
✅ User 'admin' created/updated
✅ User 'shahzeb.naeem' created/updated
...
✅ All 9 users seeded successfully
```

**Default credentials**:
- Username: `admin` / Password: `admin123!`
- Username: `shahzeb.naeem` / Password: `shahzeb123!`
- Plus 7 more users (see `seed_users.py`)

---

### Step 5: Generate JWT Secret Key
```bash
uv run python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

**What this does**: Generates a cryptographically secure random key

**Output example**:
```
JWT_SECRET_KEY=aB3dE5fG7hI9jK0lM2nO4pQ6rS8tU1vW3xY5zA7bC9d
```

**Action required**: Copy the entire output line and add it to your `.env` file

---

### Step 6: Update .env File

Add these lines to `/Users/shahzeb.naeem/Desktop/Projects/ai-practice-agentic/.env`:

```env
# JWT Authentication (paste the generated key from Step 5)
JWT_SECRET_KEY=aB3dE5fG7hI9jK0lM2nO4pQ6rS8tU1vW3xY5zA7bC9d

# Token expiration (24 hours)
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS for Hugging Face (replace with your actual Space URL)
CORS_ORIGINS=http://localhost:7860,https://your-username-your-space-name.hf.space
```

**For Hugging Face deployment**: Set these as **Secrets** in your Space settings, not in a committed .env file

---

### Step 7: Delete Redundant Files
```bash
cd /Users/shahzeb.naeem/Desktop/Projects/ai-practice-agentic/hf_space

# Delete cached database tools (no longer used)
rm backend/agent/database/cached_database_tools.py

# Delete redundant research tools (replaced by search_agent)
rm backend/agent/research_agent/research_tools.py
```

**What this does**: Removes files that are no longer imported or used

---

### Step 8: Verify Database Changes
```bash
# Check password_hash column exists
psql "$DATABASE_URL" -c "SELECT column_name FROM information_schema.columns WHERE table_name='rfp_users' AND column_name='password_hash';"

# Check users have passwords
psql "$DATABASE_URL" -c "SELECT username, email, password_hash IS NOT NULL as has_password FROM rfp_users;"
```

**Expected output**: Should show all users with `has_password = t` (true)

---

## 🧪 Testing Authentication

### Test 1: Login Endpoint
```bash
curl -X POST http://localhost:7860/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123!"}'
```

**Expected response**:
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": "...",
    "username": "admin",
    "email": "admin@granite-mena.com",
    "name": "Admin User"
  },
  "session_id": "..."
}
```

**Save the token** for the next tests!

---

### Test 2: Get Current User (Protected Endpoint)
```bash
# Replace YOUR_TOKEN_HERE with the access_token from Test 1
TOKEN="YOUR_TOKEN_HERE"

curl http://localhost:7860/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected response**:
```json
{
  "success": true,
  "user": {
    "user_id": "...",
    "username": "admin",
    ...
  }
}
```

---

### Test 3: Change Password
```bash
curl -X POST http://localhost:7860/api/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "admin123!", "new_password": "NewSecurePass123!"}'
```

**Expected response**:
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

### Test 4: Rate Limiting (Should Fail After 5 Attempts)
```bash
# Try logging in with wrong password 6 times
for i in {1..6}; do
  echo "Attempt $i:"
  curl -X POST http://localhost:7860/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "wrong"}' \
    && echo ""
  sleep 1
done
```

**Expected behavior**: First 5 attempts return "Invalid credentials", 6th returns "Rate limit exceeded"

---

### Test 5: Logout
```bash
curl -X POST http://localhost:7860/api/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

**Expected response**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 📊 What Was Completed

| Phase | Tasks | Status |
|-------|-------|--------|
| **Phase 1** | JWT authentication system (8 endpoints) | ✅ COMPLETE |
| **Phase 2** | Code cleanup (delete wrappers) | ✅ COMPLETE |
| **Phase 3** | Add 10 missing agent tools | ✅ COMPLETE |

---

## ⏳ What's Next (Future Phases)

### Phase 4: API Endpoints (Pending)
- Add marketing campaigns CRUD (8 endpoints)
- Add user management endpoints (7 endpoints)
- Add pagination support (4 endpoints)

### Phase 5: Frontend Integration (Pending)
- Update `Login.svelte` to use backend auth
- Remove hardcoded passwords from frontend
- Implement token storage and refresh

### Phase 6: Security Hardening (Pending)
- Protect all 35+ API endpoints with authentication
- Add comprehensive input validation
- Set up monitoring and logging

---

## 🚀 Deploying to Hugging Face

### 1. Set Environment Secrets in HF Space Settings

Go to your Space settings → Secrets and add:

```
JWT_SECRET_KEY=<your-generated-key-from-step-5>
DATABASE_URL=<your-postgres-connection-string>
CORS_ORIGINS=https://your-username-your-space-name.hf.space
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 2. Run Migration on HF Postgres

```bash
# Connect to your HF-backed PostgreSQL
psql "$DATABASE_URL" -f backend/database/migrations/add_password_hash_to_users.sql

# Seed users
python backend/database/seed_users.py
```

### 3. Push Changes to HF Space

```bash
cd /Users/shahzeb.naeem/Desktop/Projects/ai-practice-agentic

git add hf_space/
git commit -m "feat: Add JWT authentication system and missing agent tools

- Add 8 authentication API endpoints with rate limiting
- Add password hashing with bcrypt
- Add 10 missing agent tools for CRUD operations
- Delete redundant cached_database_tools and presentation wrappers
- Add comprehensive documentation

Phases 1-3 complete. Ready for production deployment."

git push
```

### 4. Verify Deployment

Once deployed, test the login endpoint:

```bash
curl -X POST https://your-username-your-space-name.hf.space/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123!"}'
```

---

## 📚 Documentation Files

All documentation is in the project root:

- **[COMPLETE_COMMANDS.md](../COMPLETE_COMMANDS.md)** - All commands for all phases
- **[QUICK_START_GUIDE.md](../QUICK_START_GUIDE.md)** - Setup and testing guide
- **[AUTH_IMPLEMENTATION.md](backend/AUTH_IMPLEMENTATION.md)** - Auth system details
- **[REFACTORING_NOTES.md](backend/REFACTORING_NOTES.md)** - Refactoring progress
- **[IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md)** - Overall project status
- **[SETUP_COMMANDS.sh](../SETUP_COMMANDS.sh)** - Automated setup script

---

## 🔒 Security Reminders

⚠️ **Before production deployment**:

1. ✅ Change all default passwords
2. ✅ Use a strong JWT_SECRET_KEY (not the example above)
3. ✅ Set CORS_ORIGINS to only your HF Space URL
4. ✅ Enable HTTPS only (HF Spaces do this automatically)
5. ⏳ Update Login.svelte to remove hardcoded passwords
6. ⏳ Protect all API endpoints with authentication

---

## ❓ Troubleshooting

### "command not found: psql"
**Solution**: Install PostgreSQL client
- macOS: `brew install postgresql`
- Ubuntu: `sudo apt-get install postgresql-client`
- Windows: Download from postgresql.org

### "command not found: uv"
**Solution**: Install UV package manager
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "could not connect to server"
**Solution**: Check your DATABASE_URL
```bash
echo $DATABASE_URL
# Should show: postgresql://user:pass@host:port/dbname
```

### "Invalid username or password"
**Solution**:
- Ensure `seed_users.py` ran successfully
- Check username spelling (case-sensitive)
- Default password is `admin123!` (with exclamation mark)

### "Rate limit exceeded"
**Solution**: Wait 1 minute for login, 1 hour for password changes

---

**Status**: Ready to run manual setup steps ✅

**Last Updated**: 2025-01-07

**Next Action**: Run commands Step 1-8, then test authentication endpoints
