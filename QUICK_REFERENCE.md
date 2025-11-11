# Quick Reference - HF Space Backend Setup

## 🚀 Fastest Way to Get Started

### Option 1: Automated (Recommended)
```bash
cd /Users/shahzeb.naeem/Desktop/Projects/ai-practice-agentic
bash SETUP_COMMANDS.sh
```

### Option 2: Manual Steps
See [MANUAL_SETUP_STEPS.md](MANUAL_SETUP_STEPS.md)

---

## ✅ What's Already Done (Phases 1-3)

### Phase 1: Security ✅
- JWT authentication system (8 API endpoints)
- Bcrypt password hashing
- Rate limiting (5 login/min, 3 pwd change/hour)
- Configurable CORS

### Phase 2: Cleanup ✅
- Deleted 2 presentation wrapper functions
- Removed cached_database_tools usage
- Marked redundant files for deletion

### Phase 3: Missing Tools ✅
- Added 10 new agent tools for CRUD operations
- Updated database_agent with all tools

---

## 🔧 Commands You Need to Run

```bash
# 1. Navigate to hf_space
cd /Users/shahzeb.naeem/Desktop/Projects/ai-practice-agentic/hf_space

# 2. Install dependencies
uv pip install passlib[bcrypt] python-jose[cryptography] slowapi

# 3. Run migration
psql "$DATABASE_URL" -f backend/database/migrations/add_password_hash_to_users.sql

# 4. Seed users
uv run python backend/database/seed_users.py

# 5. Generate JWT secret
uv run python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
# Copy output and add to .env file

# 6. Delete redundant files
rm backend/agent/database/cached_database_tools.py
rm backend/agent/research_agent/research_tools.py
```

---

## 🧪 Test Authentication

```bash
# Test login
curl -X POST http://localhost:7860/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123!"}'

# Save the access_token from response, then test protected endpoint
TOKEN="your_access_token_here"

curl http://localhost:7860/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔑 Default Credentials

- Username: `admin`
- Password: `admin123!`

⚠️ Change in production!

---

## 📚 Documentation Map

- **[SETUP_COMMANDS.sh](SETUP_COMMANDS.sh)** - Automated setup script
- **[MANUAL_SETUP_STEPS.md](MANUAL_SETUP_STEPS.md)** - Step-by-step manual guide
- **[COMPLETE_COMMANDS.md](COMPLETE_COMMANDS.md)** - All phases with detailed commands
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - Setup and testing overview
- **[COMPLETED_IN_THIS_SESSION.md](COMPLETED_IN_THIS_SESSION.md)** - What was just completed
- **[AUTH_IMPLEMENTATION.md](hf_space/backend/AUTH_IMPLEMENTATION.md)** - Auth system deep dive
- **[REFACTORING_NOTES.md](hf_space/backend/REFACTORING_NOTES.md)** - Refactoring details
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Overall project status

---

## ⏳ What's Next (Phases 4-6)

### Phase 4: API Endpoints
- Add marketing campaigns CRUD (8 endpoints)
- Add user management (7 endpoints)
- Add pagination support (4 endpoints)

### Phase 5: Frontend
- Update Login.svelte to use backend auth
- Remove hardcoded passwords
- Implement token storage

### Phase 6: Security
- Protect all 35+ API endpoints
- Add input validation
- Set up monitoring

---

## 🐛 Common Issues

### "command not found: psql"
```bash
# macOS
brew install postgresql

# Ubuntu
sudo apt-get install postgresql-client
```

### "command not found: uv"
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Invalid username or password"
- Ensure seed_users.py ran successfully
- Check username is `admin` (lowercase)
- Check password is `admin123!` (with !)

---

## 🚀 Deploy to Hugging Face

1. Set Secrets in HF Space settings:
   - `JWT_SECRET_KEY`
   - `DATABASE_URL`
   - `CORS_ORIGINS`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`

2. Run migration on HF Postgres:
   ```bash
   psql "$DATABASE_URL" -f backend/database/migrations/add_password_hash_to_users.sql
   python backend/database/seed_users.py
   ```

3. Push changes:
   ```bash
   git add .
   git commit -m "feat: Add JWT auth and missing agent tools"
   git push
   ```

---

## 📊 Progress Status

**Overall**: 50% Complete (Phases 1-3 done, 4-6 pending)

| Phase | Status |
|-------|--------|
| Phase 1: Security | ✅ 100% |
| Phase 2: Cleanup | ✅ 100% |
| Phase 3: Tools | ✅ 100% |
| Phase 4: Endpoints | ⏳ 0% |
| Phase 5: Frontend | ⏳ 0% |
| Phase 6: Security | ⏳ 0% |

---

## 💡 Quick Tips

1. **Check API docs**: Visit `http://localhost:7860/api/docs` after starting server
2. **Use admin account**: Username `admin`, Password `admin123!`
3. **Save JWT token**: You'll need it for protected endpoints
4. **Check rate limits**: Max 5 login attempts per minute
5. **Read logs**: Backend logs show auth attempts and rate limiting

---

**Last Updated**: 2025-01-07
**Status**: Ready for setup commands ✅
**Next Action**: Run `bash SETUP_COMMANDS.sh`
